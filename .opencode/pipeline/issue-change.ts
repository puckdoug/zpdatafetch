import { PIPELINE_MARKER, type IssueComment } from "./github.ts";
import { requeueState, type PipelineState } from "./state.ts";

export interface IssueContent {
  title: string;
  body: string;
  comments: IssueComment[];
}

export const RESTART_NOTE = "issue changed; re-queued at review";

/** Bodies of human comments in order (pipeline-marker comments excluded). */
export function humanCommentBodies(
  comments: IssueComment[],
  marker: string = PIPELINE_MARKER,
): string[] {
  return comments.filter((c) => !c.body.includes(marker)).map((c) => c.body);
}

/** Deterministic signature over the human-editable issue content. */
export function issueSignature(
  content: IssueContent,
  marker: string = PIPELINE_MARKER,
): string {
  return JSON.stringify({
    title: content.title,
    body: content.body,
    comments: humanCommentBodies(content.comments, marker),
  });
}

/** True when a live issue's content differs from the acknowledged baseline. */
export function issueChanged(
  state: PipelineState,
  content: IssueContent,
  marker: string = PIPELINE_MARKER,
): boolean {
  if (state.stage === "done") return false;
  if (typeof state.issueSignature !== "string") return false;
  return issueSignature(content, marker) !== state.issueSignature;
}

/** Re-queued state when a live issue changed; null otherwise. */
export function detectIssueChange(
  state: PipelineState,
  content: IssueContent,
  now: Date = new Date(),
  marker: string = PIPELINE_MARKER,
): PipelineState | null {
  if (!issueChanged(state, content, marker)) return null;
  const requeued = requeueState(state.issue, "review", state.startDate, RESTART_NOTE, now);
  return {
    ...requeued,
    branch: state.branch,
    issueSignature: issueSignature(content, marker),
  };
}

export interface RestartPlan {
  /** Non-active issues to restart immediately. */
  restarts: PipelineState[];
  /** Issue numbers whose restart waits for the stage boundary. */
  pending: number[];
}

/** Orders detected changes into immediate restarts and pending restarts. */
export function planRestarts(
  states: PipelineState[],
  contents: Map<number, IssueContent>,
  active: ReadonlySet<number>,
  now: Date = new Date(),
): RestartPlan {
  const restarts: PipelineState[] = [];
  const pending: number[] = [];
  for (const s of states) {
    if (s.stage === "done") continue;
    const content = contents.get(s.issue);
    if (!content) continue;
    const next = detectIssueChange(s, content, now);
    if (!next) continue;
    if (active.has(s.issue)) pending.push(s.issue);
    else restarts.push(next);
  }
  return { restarts, pending };
}
