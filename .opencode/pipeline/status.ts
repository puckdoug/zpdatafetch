import { STAGE_AGENT } from "./transitions.ts";
import type { Stage } from "./state.ts";

export function humanDuration(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

export type IssueStatusEntry = {
  issue: number;
  stage: Stage;
  archived?: boolean;
  /** Open PR URL for an unarchived done issue; null/undefined = no PR needed. */
  prUrl?: string | null;
  /** Issue is closed on GitHub; rendered as completed "— closed". */
  closed?: boolean;
};

export interface Summary {
  notStarted: number[];
  awaitingInput: IssueStatusEntry[];
  inProgress: IssueStatusEntry[];
  completed: IssueStatusEntry[];
}

const IN_PROGRESS_ORDER: readonly Stage[] = [
  "review",
  "design",
  "dev",
  "quality",
  "docs",
  "finalize",
];

/** Groups known issues into the four summary sections, each ordered. */
export function classifyIssues(input: {
  openIssues?: readonly number[];
  closedIssues?: readonly number[];
  states: readonly IssueStatusEntry[];
}): Summary {
  const known = new Set(input.states.map((s) => s.issue));
  const closed = new Set(input.closedIssues ?? []);
  const notStarted = [...new Set(input.openIssues ?? [])]
    .filter((n) => !known.has(n) && !closed.has(n))
    .sort((a, b) => a - b);
  const awaitingInput: IssueStatusEntry[] = [];
  const inProgress: IssueStatusEntry[] = [];
  const completed: IssueStatusEntry[] = [];
  for (const s of input.states) {
    if (closed.has(s.issue)) completed.push({ ...s, closed: true });
    else if (s.archived || s.stage === "done") completed.push(s);
    else if (s.stage === "review-wait" || s.stage === "blocked") awaitingInput.push(s);
    else inProgress.push(s);
  }
  awaitingInput.sort((a, b) => a.issue - b.issue);
  completed.sort((a, b) => a.issue - b.issue);
  inProgress.sort((a, b) => {
    const d = IN_PROGRESS_ORDER.indexOf(a.stage) - IN_PROGRESS_ORDER.indexOf(b.stage);
    return d !== 0 ? d : a.issue - b.issue;
  });
  return { notStarted, awaitingInput, inProgress, completed };
}

export interface WorkingEntry {
  issue: number;
  stage: Stage;
  startedAt: number;
}

export interface StatusInput {
  loopRunning: boolean;
  loopStartedAt: number | null;
  now: number;
  working?: WorkingEntry[];
  issueStates: IssueStatusEntry[];
  /** Labeled open issue numbers from gh.listIssues(); omitted/empty degrades. */
  openIssues?: readonly number[];
  /** Labeled closed issue numbers from gh.listIssues("all"); omitted/empty degrades. */
  closedIssues?: readonly number[];
  mode?: "status" | "startup" | "stop" | "check";
  /** First line for mode "check" (the trigger result). */
  checkResult?: string;
  issueUrl?: (issue: number) => string | null;
}

function underline(label: string): string {
  return "-".repeat(label.length);
}

/** Renders the three top-level groups; empty groups are omitted. */
function renderGroups(
  summary: Summary,
  href: (issue: number) => string,
): string[] {
  const groups: string[][] = [];

  const action: string[] = [];
  if (summary.awaitingInput.length > 0) {
    action.push("awaiting input:");
    for (const e of summary.awaitingInput) action.push(`  ${href(e.issue)}`);
  }
  const completedPr = summary.completed.filter((e) => !e.closed && !e.archived && e.prUrl);
  if (completedPr.length > 0) {
    action.push("Completed, PR needed:");
    for (const e of completedPr) action.push(`  ${href(e.issue)} -- PR (${e.prUrl})`);
  }
  if (action.length > 0) {
    groups.push(["Action needed", underline("Action needed"), ...action]);
  }

  if (summary.inProgress.length > 0) {
    groups.push([
      "In progress",
      underline("In progress"),
      ...summary.inProgress.map((e) => `  ${href(e.issue)} -- ${e.stage}`),
    ]);
  }

  const closed = summary.completed.filter((e) => e.closed);
  if (closed.length > 0) {
    groups.push([
      "Completed",
      underline("Completed"),
      ...closed.map((e) => `  ${href(e.issue)} — closed`),
    ]);
  }

  if (summary.notStarted.length > 0) {
    groups.push([
      "Pending",
      underline("Pending"),
      "not started:",
      ...summary.notStarted.map((n) => `  ${href(n)}`),
    ]);
  }

  const lines: string[] = [];
  for (let idx = 0; idx < groups.length; idx++) {
    if (idx > 0) lines.push("");
    lines.push(...groups[idx]);
  }
  return lines;
}

export function formatStatus(i: StatusInput): string {
  const mode = i.mode ?? "status";
  const href = (issue: number): string => {
    const url = i.issueUrl?.(issue);
    return url ? `#${issue} (${url})` : `#${issue}`;
  };
  const summary = classifyIssues({
    openIssues: i.openIssues,
    closedIssues: i.closedIssues,
    states: i.issueStates,
  });
  const lines: string[] = [];

  if (mode === "check") {
    if (i.checkResult !== undefined) lines.push(i.checkResult);
  } else if (mode === "startup") {
    const active =
      summary.notStarted.length + summary.awaitingInput.length + summary.inProgress.length;
    lines.push(
      active > 0
        ? "The pipeline loop is running."
        : "No issues require work, polling for new work.",
    );
  } else if (i.loopRunning) {
    const since = i.loopStartedAt ?? i.now;
    lines.push(`pipeline loop: running for ${humanDuration(i.now - since)}`);
  } else {
    lines.push("pipeline loop: stopped");
  }

  const working = i.working ?? [];
  if (working.length > 0) {
    const parts = working.map((w) => {
      const agent = STAGE_AGENT[w.stage] ?? "none";
      return `issue ${href(w.issue)} · stage ${w.stage} · agent ${agent} · ${humanDuration(i.now - w.startedAt)}`;
    });
    lines.push(`working: ${parts.join("; ")}`);
  }

  const known = i.issueStates.length > 0 || (i.openIssues?.length ?? 0) > 0 ||
    (i.closedIssues?.length ?? 0) > 0;
  const groups = renderGroups(summary, href);
  if (!known) lines.push("no pipeline-labeled issues found");
  else lines.push(...groups);
  return lines.join("\n");
}
