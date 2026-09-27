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
  /** Source state file's `updated` (ISO); drives the idle report's last-completed pick. */
  updated?: string;
};

/** True when a should replace b as "last completed": later `updated`; tie or missing → higher issue number. */
function isLaterCompleted(a: IssueStatusEntry, b: IssueStatusEntry): boolean {
  const ta = Date.parse(a.updated ?? "");
  const tb = Date.parse(b.updated ?? "");
  if (Number.isFinite(ta) && Number.isFinite(tb) && ta !== tb) return ta > tb;
  return a.issue > b.issue;
}

export function lastCompletedIssue(
  states: ReadonlyArray<IssueStatusEntry>,
): IssueStatusEntry | null {
  let best: IssueStatusEntry | null = null;
  for (const s of states) {
    if (s.stage !== "done") continue;
    if (best === null || isLaterCompleted(s, best)) best = s;
  }
  return best;
}

export interface StatusInput {
  loopRunning: boolean;
  loopStartedAt: number | null;
  now: number;
  current: { issue: number; stage: Stage; startedAt: number } | null;
  issueStates: IssueStatusEntry[];
  /** "startup" renders the /pipeline-start report; default "status" is unchanged. */
  mode?: "status" | "startup";
}

export function formatStatus(i: StatusInput): string {
  const startup = i.mode === "startup";
  const lines: string[] = [];
  if (startup) {
    lines.push("The pipeline loop is running.");
  } else if (i.loopRunning) {
    const since = i.loopStartedAt ?? i.now;
    lines.push(`pipeline loop: running for ${humanDuration(i.now - since)}`);
  } else {
    lines.push("pipeline loop: stopped");
  }

  if (i.current) {
    const agent = STAGE_AGENT[i.current.stage] ?? "none";
    lines.push(
      `working: issue #${i.current.issue} · stage ${i.current.stage} · agent ${agent} · ${humanDuration(i.now - i.current.startedAt)}`,
    );
    return lines.join("\n");
  }

  const focus =
    i.issueStates.find((s) => s.stage !== "done" && s.stage !== "blocked") ??
    i.issueStates.find((s) => s.stage === "blocked") ??
    i.issueStates.find((s) => s.stage === "done" && !s.archived) ??
    i.issueStates.find((s) => s.stage === "done");

  if (startup && focus?.stage === "done") {
    const last = lastCompletedIssue(i.issueStates) ?? focus;
    return `No issues require work, polling for new work.\nLast completed issue #${last.issue}`;
  }

  if (!focus) {
    lines.push(startup ? "waiting for input" : "no pipeline-labeled issues found");
    return lines.join("\n");
  }

  switch (focus.stage) {
    case "review-wait":
      lines.push(`waiting for input: issue #${focus.issue} (review asked questions on the issue)`);
      break;
    case "blocked":
      lines.push(`failed/blocked: issue #${focus.issue} (see the note in its state file)`);
      break;
    case "done":
      if (focus.archived) {
        lines.push(`archived: issue #${focus.issue} (planning docs in docs/done)`);
      } else {
        lines.push(`completed: issue #${focus.issue}`);
      }
      break;
    default:
      lines.push(
        startup
          ? `working: issue #${focus.issue} · stage ${focus.stage} · agent ${STAGE_AGENT[focus.stage] ?? "none"} · ${humanDuration(0)}`
          : `idle at issue #${focus.issue} · stage ${focus.stage}`,
      );
  }
  return lines.join("\n");
}
export function mergeStartupStates(
  issues: ReadonlyArray<{ number: number }>,
  planningStates: ReadonlyArray<IssueStatusEntry>,
  doneStates: ReadonlyArray<IssueStatusEntry>,
): IssueStatusEntry[] {
  const planningByIssue = new Map(planningStates.map((s) => [s.issue, s]));
  const doneByIssue = new Map<number, IssueStatusEntry>();
  for (const s of doneStates) {
    const prev = doneByIssue.get(s.issue);
    if (!prev || isLaterCompleted(s, prev)) doneByIssue.set(s.issue, s);
  }
  const merged: IssueStatusEntry[] = issues
    .map((it) => {
      const local = planningByIssue.get(it.number);
      return local
        ? {
            issue: it.number,
            stage: local.stage,
            ...(local.updated !== undefined ? { updated: local.updated } : {}),
          }
        : { issue: it.number, stage: "review" as Stage };
    })
    .sort((a, b) => a.issue - b.issue);
  const listed = new Set(merged.map((s) => s.issue));
  for (const [issue, s] of [...planningByIssue, ...doneByIssue].sort((a, b) => a[0] - b[0])) {
    if (listed.has(issue)) continue;
    merged.push(s);
    listed.add(issue);
  }
  return merged;
}
