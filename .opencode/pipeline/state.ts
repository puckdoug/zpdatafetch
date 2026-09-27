export type Stage =
  | "review"
  | "review-wait"
  | "design"
  | "dev"
  | "quality"
  | "docs"
  | "finalize"
  | "done"
  | "blocked";

export const STAGES: readonly Stage[] = [
  "review",
  "review-wait",
  "design",
  "dev",
  "quality",
  "docs",
  "finalize",
  "done",
  "blocked",
];

export interface PipelineState {
  issue: number;
  stage: Stage;
  branch: string;
  startDate: string;
  attempts: Record<string, number>;
  updated: string;
  note: string;
}

export function branchName(issue: number): string {
  return `pipeline/gh-${issue}`;
}

export function initialState(issue: number, now: Date = new Date()): PipelineState {
  return {
    issue,
    stage: "review",
    branch: branchName(issue),
    startDate: dateStamp(now),
    attempts: {},
    updated: now.toISOString(),
    note: "",
  };
}

export function dateStamp(now: Date = new Date()): string {
  const y = now.getUTCFullYear();
  const m = String(now.getUTCMonth() + 1).padStart(2, "0");
  const d = String(now.getUTCDate()).padStart(2, "0");
  return `${y}${m}${d}`;
}

export function stateFilename(startDate: string, issue: number): string {
  return `${startDate}-gh${issue}-state.json`;
}

export function parseStateFilename(
  name: string,
): { startDate: string; issue: number } | null {
  const m = /^(\d{8})-gh(\d+)-state(?:-\d+)?\.json$/.exec(name);
  if (!m) return null;
  return { startDate: m[1], issue: Number(m[2]) };
}

export function serializeState(s: PipelineState): string {
  return JSON.stringify(s, null, 2) + "\n";
}

export function parseState(raw: string): PipelineState {
  const v = JSON.parse(raw) as Partial<PipelineState>;
  if (typeof v.issue !== "number" || !STAGES.includes(v.stage as Stage)) {
    throw new Error("invalid pipeline state");
  }
  const updated = typeof v.updated === "string" ? v.updated : new Date(0).toISOString();
  return {
    issue: v.issue,
    stage: v.stage as Stage,
    branch: typeof v.branch === "string" ? v.branch : branchName(v.issue),
    startDate: typeof v.startDate === "string" ? v.startDate : dateStamp(new Date(updated)),
    attempts: (v.attempts ?? {}) as Record<string, number>,
    updated,
    note: typeof v.note === "string" ? v.note : "",
  };
}