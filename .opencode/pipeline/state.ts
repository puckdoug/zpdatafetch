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

export type StatusCategory = "ready" | "in-progress" | "on-hold" | "done";

export function isStatusCategory(v: unknown): v is StatusCategory {
  return v === "ready" || v === "in-progress" || v === "on-hold" || v === "done";
}

export interface PipelineState {
  issue: number;
  stage: Stage;
  branch: string;
  startDate: string;
  attempts: Record<string, number>;
  updated: string;
  note: string;
  /** Count of human comments seen; used to detect follow-ups after completion. */
  humanComments?: number;
  /** Last board status category applied; absent = not yet applied. */
  boardStatus?: StatusCategory;
  /** Signature of the issue content acknowledged at review; absent = legacy. */
  issueSignature?: string;
  /** Set when a change must restart this issue at the next stage boundary. */
  pendingRestart?: boolean;
}

export function branchName(issue: number): string {
  return `pipeline/gh-${issue}`;
}

export type RetryRequest = { issue: number; stage: Stage } | { error: string };

/** Parses "/pipeline-retry <issue> [stage]" — stage defaults to review. */
export function parseRetryRequest(request: string): RetryRequest {
  const parts = request.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return { error: "usage: /pipeline-retry <issue> [stage] (stage defaults to review)" };
  }
  const issue = Number(parts[0].replace(/^#/, ""));
  if (!Number.isInteger(issue) || issue <= 0) {
    return { error: `invalid issue number "${parts[0]}"` };
  }
  const stage = (parts[1] ?? "review") as Stage;
  if (!STAGES.includes(stage) || stage === "done" || stage === "blocked" || stage === "review-wait") {
    return { error: `invalid stage "${parts[1]}"; use one of review, design, dev, quality, docs, finalize` };
  }
  return { issue, stage };
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
    humanComments: 0,
  };
}

/** Re-queued state, matching /pipeline-retry: attempts reset, startDate kept. */
export function requeueState(
  issue: number,
  stage: Stage,
  startDate: string,
  note: string,
  now: Date = new Date(),
): PipelineState {
  return { ...initialState(issue, now), startDate, stage, note };
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
  const out: PipelineState = {
    issue: v.issue,
    stage: v.stage as Stage,
    branch: typeof v.branch === "string" ? v.branch : branchName(v.issue),
    startDate: typeof v.startDate === "string" ? v.startDate : dateStamp(new Date(updated)),
    attempts: (v.attempts ?? {}) as Record<string, number>,
    updated,
    note: typeof v.note === "string" ? v.note : "",
    humanComments: typeof v.humanComments === "number" ? v.humanComments : 0,
  };
  if (isStatusCategory(v.boardStatus)) out.boardStatus = v.boardStatus;
  if (typeof v.issueSignature === "string") out.issueSignature = v.issueSignature;
  if (v.pendingRestart === true) out.pendingRestart = true;
  return out;
}