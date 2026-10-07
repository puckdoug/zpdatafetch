import { humanReplySince, type IssueComment } from "./github.ts";
import { requeueState, type PipelineState } from "./state.ts";

export const FOLLOW_UP_NOTE = "follow-up comment; re-queued";

/** Re-queues a done/blocked issue when a human commented after state.updated. */
export function detectFollowUp(
  state: PipelineState,
  comments: IssueComment[],
  now: Date = new Date(),
): PipelineState | null {
  if (state.stage !== "done" && state.stage !== "blocked") return null;
  if (!humanReplySince(comments, state.updated)) return null;
  return requeueState(state.issue, "review", state.startDate, FOLLOW_UP_NOTE, now);
}
