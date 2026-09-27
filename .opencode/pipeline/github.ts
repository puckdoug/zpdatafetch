import type { PluginInput } from "@opencode-ai/plugin";

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

export function isMergedState(raw: string): boolean {
  try {
    const v = JSON.parse(raw) as { state?: unknown };
    return v.state === "MERGED";
  } catch {
    return false;
  }
}

export interface IssueRef {
  number: number;
  title: string;
}

export interface Gh {
  listIssues(): Promise<IssueRef[]>;
  comments(issue: number): Promise<IssueComment[]>;
  comment(issue: number, body: string): Promise<void>;
  prExists(branch: string): Promise<boolean>;
  prMerged(branch: string): Promise<boolean>;
  defaultBranch(): Promise<string>;
}

export function createGh($: Shell, label: string): Gh {
  return {
    async listIssues(): Promise<IssueRef[]> {
      const out =
        await $`gh issue list --label ${label} --state open --limit 50 --json number,title`.text();
      const rows = JSON.parse(out) as { number: number; title: string }[];
      return rows.map((r) => ({ number: r.number, title: r.title }));
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
    async comment(issue: number, body: string): Promise<void> {
      await $`gh issue comment ${issue} --body ${`${PIPELINE_MARKER}\n${body}`}`.quiet();
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
  };
}