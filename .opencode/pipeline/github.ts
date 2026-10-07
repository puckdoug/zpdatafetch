import type { PluginInput } from "@opencode-ai/plugin";
import type { PrioritySnapshot } from "./priority.ts";
import { parsePriorityJson } from "./priority.ts";
import type { StatusCategory } from "./state.ts";
import type { IssueContent } from "./issue-change.ts";
import { parseStatusSnapshot, planStatusUpdates } from "./board.ts";

type Shell = PluginInput["$"];

export const PIPELINE_MARKER = "<!-- pipeline -->";

export interface IssueComment {
  author: string;
  body: string;
  createdAt: string;
}

export function humanReplySince(
  comments: IssueComment[],
  sinceIso: string,
  marker: string = PIPELINE_MARKER,
): boolean {
  return comments.some(
    (c) => !c.body.includes(marker) && Date.parse(c.createdAt) > Date.parse(sinceIso),
  );
}

/** Counts human (non-pipeline-marker) comments; the basis for follow-up detection. */
export function countHumanComments(
  comments: IssueComment[],
  marker: string = PIPELINE_MARKER,
): number {
  return comments.filter((c) => !c.body.includes(marker)).length;
}

export function isMergedState(raw: string): boolean {
  try {
    const v = JSON.parse(raw) as { state?: unknown };
    return v.state === "MERGED";
  } catch {
    return false;
  }
}

export interface IssueStateSplit {
  open: number[];
  closed: number[];
}

/**
 * Splits issue refs by state. `gh` returns uppercase `OPEN`/`CLOSED`; compare
 * case-insensitively and treat a missing/unknown state as open.
 */
export function splitIssuesByState(issues: readonly IssueRef[]): IssueStateSplit {
  const open: number[] = [];
  const closed: number[] = [];
  for (const i of issues) {
    if ((i.state ?? "").toUpperCase() === "CLOSED") closed.push(i.number);
    else open.push(i.number);
  }
  return { open, closed };
}

export interface IssueRef {
  number: number;
  title: string;
  state?: string;
}

export interface StatusSyncResult {
  synced: boolean;
  error: string | null;
}

export interface Gh {
  listIssues(state?: "open" | "all"): Promise<IssueRef[]>;
  comments(issue: number): Promise<IssueComment[]>;
  /** Current title, body, and comments for one issue. */
  issueContent(issue: number): Promise<IssueContent>;
  comment(issue: number, body: string): Promise<void>;
  prExists(branch: string): Promise<boolean>;
  /** Web URL of the PR for a branch, or null if none. */
  prUrl(branch: string): Promise<string | null>;
  /** Web URL of the open PR for a branch, or null if none (merged/closed ignored). */
  openPrUrl(branch: string): Promise<string | null>;
  prMerged(branch: string): Promise<boolean>;
  defaultBranch(): Promise<string>;
  /** Base web URL for this repo, e.g. https://github.com/puckdoug/zpdatafetch (cached; null if unknown). */
  repoBase(): Promise<string | null>;
  /** Best-effort priority lookup; never throws, degrades to an `error` snapshot. */
  prioritySnapshot(issueNumbers: number[]): Promise<PrioritySnapshot>;
  /**
   * Best-effort: move the issue's card(s) to the option matching `target`.
   * Never throws. `synced` is true when at least one project item matched.
   */
  applyIssueStatus(issue: number, target: StatusCategory): Promise<StatusSyncResult>;
}

/** One aliased issue block per number, reading only the priority single-select field. */
function priorityQuery(numbers: number[]): string {
  const blocks = numbers
    .map(
      (n) => `i${n}: issue(number: ${n}) {
        projectItems(first: 20) {
          nodes {
            fieldValues(first: 100) {
              nodes {
                ... on ProjectV2ItemFieldSingleSelectValue {
                  name
                  field { ... on ProjectV2SingleSelectField { name options { name } } }
                }
              }
            }
          }
        }
      }`,
    )
    .join("\n");
  return `query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      ${blocks}
    }
  }`;
}

/** Per-issue project items with their project's single-select fields. */
function statusQuery(number: number): string {
  return `query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      issue(number: ${number}) {
        projectItems(first: 20) {
          nodes {
            id
            project {
              id
              fields(first: 50) {
                nodes {
                  ... on ProjectV2SingleSelectField { id name options { id name } }
                }
              }
            }
          }
        }
      }
    }
  }`;
}

function statusMutation(): string {
  return `mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
    updateProjectV2ItemFieldValue(input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: {singleSelectOptionId: $optionId}}) {
      projectV2Item { id }
    }
  }`;
}

export function createGh($: Shell, label: string): Gh {
  let nameCache: string | null | undefined;

  async function repoName(): Promise<string | null> {
    if (nameCache !== undefined) return nameCache;
    const out = await $`gh repo view --json nameWithOwner --jq .nameWithOwner`.nothrow().text();
    const name = out.trim();
    nameCache = name ? name : null;
    return nameCache;
  }

  return {
    async listIssues(state: "open" | "all" = "open"): Promise<IssueRef[]> {
      const out =
        await $`gh issue list --label ${label} --state ${state} --limit 50 --json number,title,state`.text();
      const rows = JSON.parse(out) as { number: number; title: string; state: string }[];
      return rows.map((r) => ({ number: r.number, title: r.title, state: r.state }));
    },
    async comments(issue: number): Promise<IssueComment[]> {
      const out = await $`gh issue view ${issue} --json comments`.text();
      const data = JSON.parse(out) as {
        comments: { author: { login: string }; body: string; createdAt: string }[];
      };
      return data.comments.map((c) => ({
        author: c.author.login,
        body: c.body,
        createdAt: c.createdAt,
      }));
    },
    async issueContent(issue: number): Promise<IssueContent> {
      const out = await $`gh issue view ${issue} --json title,body,comments`.text();
      const data = JSON.parse(out) as {
        title: string;
        body: string | null;
        comments: { author: { login: string }; body: string; createdAt: string }[];
      };
      return {
        title: data.title,
        body: data.body ?? "",
        comments: data.comments.map((c) => ({
          author: c.author.login,
          body: c.body,
          createdAt: c.createdAt,
        })),
      };
    },
    async comment(issue: number, body: string): Promise<void> {
      await $`gh issue comment ${issue} --body ${`${PIPELINE_MARKER}\n${body}`}`.quiet();
    },
    async prUrl(branch: string): Promise<string | null> {
      const out = await $`gh pr view ${branch} --json url --jq .url`.nothrow().text();
      const url = out.trim();
      return url.startsWith("http") ? url : null;
    },
    async openPrUrl(branch: string): Promise<string | null> {
      const out =
        await $`gh pr list --head ${branch} --state open --json url --jq ".[0].url"`
          .nothrow()
          .text();
      const url = out.trim();
      return url.startsWith("http") ? url : null;
    },
    async prExists(branch: string): Promise<boolean> {
      const out =
        await $`gh pr list --head ${branch} --state open --json number`.text();
      const rows = JSON.parse(out) as { number: number }[];
      return rows.length > 0;
    },
    async prMerged(branch: string): Promise<boolean> {
      // gh exits non-zero with empty stdout when no PR exists for the branch;
      // nothrow keeps that as "not merged" instead of a throw.
      const out = await $`gh pr view ${branch} --json state`.nothrow().text();
      return isMergedState(out);
    },
    async defaultBranch(): Promise<string> {
      const out =
        await $`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.nothrow().text();
      const name = out.trim();
      if (!name) throw new Error("could not determine default branch via gh");
      return name;
    },
    async repoBase(): Promise<string | null> {
      const name = await repoName();
      return name ? `https://github.com/${name}` : null;
    },
    async prioritySnapshot(issueNumbers: number[]): Promise<PrioritySnapshot> {
      if (issueNumbers.length === 0) return { order: [], values: {}, error: null };
      try {
        const spec = await repoName();
        if (!spec) return { order: [], values: {}, error: "could not determine repository" };
        const [owner, name] = spec.split("/");
        const query = priorityQuery(issueNumbers);
        const out =
          await $`gh api graphql -f ${`query=${query}`} -f ${`owner=${owner}`} -f ${`name=${name}`}`.text();
        return parsePriorityJson(out, issueNumbers);
      } catch (err) {
        return { order: [], values: {}, error: String(err) };
      }
    },
    async applyIssueStatus(issue, target) {
      try {
        const spec = await repoName();
        if (!spec) return { synced: false, error: "could not determine repository" };
        const [owner, name] = spec.split("/");
        const query = statusQuery(issue);
        const out =
          await $`gh api graphql -f ${`query=${query}`} -f ${`owner=${owner}`} -f ${`name=${name}`}`.text();
        const snap = parseStatusSnapshot(out);
        if (snap.error) return { synced: false, error: snap.error };
        const plan = planStatusUpdates(target, snap.items);
        if (plan.length === 0) return { synced: false, error: null };
        const mutation = statusMutation();
        for (const p of plan) {
          await $`gh api graphql -f ${`query=${mutation}`} -f ${`projectId=${p.projectId}`} -f ${`itemId=${p.itemId}`} -f ${`fieldId=${p.fieldId}`} -f ${`optionId=${p.optionId}`}`.text();
        }
        return { synced: true, error: null };
      } catch (err) {
        return { synced: false, error: String(err) };
      }
    },
  };
}