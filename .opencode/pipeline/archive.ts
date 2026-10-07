import type { PipelineState } from "./state.ts";

export const PLANNING_DIR = "docs/planning";
export const DONE_DIR = "docs/done";

export interface ArchiveCandidate {
  issue: number;
  branch: string;
  files: string[]; // basenames inside PLANNING_DIR, sorted, includes the state file
}

/**
 * Archive when the work is finished: `done` with a merged PR, or the issue is
 * closed on GitHub (dead/closed issues must not sit in planning forever).
 */
export function selectArchiveCandidates(
  files: string[],
  states: PipelineState[],
  mergedBranches: ReadonlySet<string>,
  closedIssues: ReadonlySet<number> = new Set<number>(),
): ArchiveCandidate[] {
  return states
    .filter(
      (s) =>
        (s.stage === "done" && mergedBranches.has(s.branch)) ||
        closedIssues.has(s.issue),
    )
    .sort((a, b) => a.issue - b.issue)
    .map((s) => ({
      issue: s.issue,
      branch: s.branch,
      files: files
        .filter((f) => new RegExp(`^\\d{8}-gh${s.issue}-`).test(f))
        .sort(),
    }))
    .filter((c) => c.files.length > 0);
}

export interface PlannedMove {
  file: string; // basename inside PLANNING_DIR
  dest: string; // basename inside DONE_DIR (collision-resolved by avoidCollision)
  tracked: boolean;
}

export type RollbackStep =
  | { kind: "git"; args: string[] }
  | { kind: "rename"; from: string; to: string };

/**
 * Numbers every archived file so copies sort sequentially: first archive is
 * `<stem>-0<ext>`, next free number after that. A legacy unsuffixed base file
 * (`<stem><ext>` already in `existing`) counts as slot 0, so the first
 * addition to a legacy set is `-1`.
 */
export function avoidCollision(file: string, existing: Iterable<string>): string {
  const taken = new Set(existing);
  const dot = file.lastIndexOf(".");
  const stem = dot > 0 ? file.slice(0, dot) : file;
  const ext = dot > 0 ? file.slice(dot) : "";
  let n = taken.has(file) ? 1 : 0;
  while (taken.has(`${stem}-${n}${ext}`)) n++;
  return `${stem}-${n}${ext}`;
}

export function planRollback(moves: PlannedMove[], committed: boolean): RollbackStep[] {
  const steps: RollbackStep[] = [
    committed
      ? { kind: "git", args: ["reset", "-q", "HEAD~1"] }
      : { kind: "git", args: ["reset", "-q"] },
    { kind: "git", args: ["checkout", "-q", "--", PLANNING_DIR] },
  ];
  for (const m of moves) {
    steps.push({ kind: "rename", from: `${DONE_DIR}/${m.dest}`, to: `${PLANNING_DIR}/${m.file}` });
  }
  return steps;
}
