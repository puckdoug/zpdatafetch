import type { PipelineState, Stage } from "./state.ts";

/** Stages where an issue cannot make progress without external input. */
export function isParked(stage: Stage): boolean {
  return stage === "review-wait" || stage === "blocked" || stage === "done";
}

/** Stages whose execution uses the issue worktree; the rest run in the main tree. */
export function isCodeStage(stage: Stage): boolean {
  return stage === "dev" || stage === "quality" || stage === "docs" || stage === "finalize";
}

/** Outcome of processing one issue in a tick. */
export interface IssueRun {
  /** True when the issue could not make progress this tick. */
  skipped: boolean;
  /** Stage the issue ended at; null when skipped. */
  final: Stage | null;
}

export interface ScanResult<T> {
  worked: T[];
  skipped: T[];
  /** True when a worked issue did not park, so later issues were left alone. */
  stopped: boolean;
}

/** One priority-ordered issue considered for a slot this tick. */
export interface CandidateIssue {
  number: number;
  /** True when the issue cannot make progress without external input. */
  parked: boolean;
}

/**
 * Issues to start this tick: at most `cap - running.size`, never an
 * already-running or parked issue, in the given priority order.
 */
export function selectStarts<T extends CandidateIssue>(
  ordered: readonly T[],
  running: ReadonlySet<number>,
  cap: number,
): T[] {
  const starts: T[] = [];
  let free = Math.max(0, cap - running.size);
  if (free === 0) return starts;
  for (const c of ordered) {
    if (free === 0) break;
    if (c.parked || running.has(c.number)) continue;
    starts.push(c);
    free--;
  }
  return starts;
}

export interface CandidateInput {
  number: number;
  /** Known state stage; null when the issue has no state file yet. */
  stage: Stage | null;
  /** review-wait only: a human replied after the state's `updated` time. */
  hasHumanReply?: boolean;
  /** done/blocked only: a human commented after the state's `updated` time. */
  hasFollowUp?: boolean;
}

export type CandidateAction = "start" | "resume" | "park";

/** Pure parked/resume decision, matching today's scan semantics. */
export function candidateAction(input: CandidateInput): CandidateAction {
  const stage = input.stage;
  if (stage === null) return "start";
  if (stage === "review-wait") return input.hasHumanReply ? "resume" : "park";
  if (stage === "done" || stage === "blocked") return input.hasFollowUp ? "resume" : "park";
  return "start";
}

/** Candidate for the scheduler; a resumed issue takes a slot. */
export function toCandidate(input: CandidateInput): CandidateIssue {
  return { number: input.number, parked: candidateAction(input) === "park" };
}

/** Candidate states: planning entries win; archived done entries fill the gaps. */
export function candidateStates(
  planning: ReadonlyMap<number, PipelineState>,
  done: ReadonlyMap<number, PipelineState>,
): Map<number, PipelineState> {
  const merged = new Map(planning);
  for (const [issue, s] of done) if (!merged.has(issue)) merged.set(issue, s);
  return merged;
}

/**
 * One tick's scan over priority-ordered issues. Works at most one issue at a
 * time: skips parked issues, works the first non-parked issue, and only moves
 * on when that issue parked. Stops before starting a second issue if a worked
 * issue is still active.
 */
export async function scanIssues<T>(
  issues: T[],
  run: (issue: T) => Promise<IssueRun>,
): Promise<ScanResult<T>> {
  const worked: T[] = [];
  const skipped: T[] = [];
  for (const issue of issues) {
    const r = await run(issue);
    if (r.skipped) {
      skipped.push(issue);
      continue;
    }
    worked.push(issue);
    if (r.final === null || !isParked(r.final)) return { worked, skipped, stopped: true };
  }
  return { worked, skipped, stopped: false };
}
