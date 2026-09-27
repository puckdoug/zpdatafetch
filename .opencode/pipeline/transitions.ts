import type { Stage } from "./state.ts";

export interface Facts {
  hasSpec: boolean;
  hasDesign: boolean;
  hasOpenDeficiency: boolean;
  checklistComplete: boolean;
  humanReply: boolean;
  qualityCycles: number;
  hasPR: boolean;
}

export const QUALITY_CYCLE_CAP = 3;

export function nextStage(
  current: Stage,
  f: Facts,
  cap: number = QUALITY_CYCLE_CAP,
): Stage {
  switch (current) {
    case "review":
      return f.hasSpec ? "design" : "review-wait";
    case "review-wait":
      return f.humanReply ? "review" : "review-wait";
    case "design":
      return f.hasDesign && !f.hasOpenDeficiency ? "dev" : "design";
    case "dev":
      return f.checklistComplete ? "quality" : "dev";
    case "quality":
      if (!f.hasOpenDeficiency) return "docs";
      return f.qualityCycles >= cap ? "blocked" : "design";
    case "docs":
      return "finalize";
    case "finalize":
      return f.hasPR ? "done" : "finalize";
    default:
      return current;
  }
}

export const STAGE_AGENT: Record<Stage, string | null> = {
  review: "pipeline-review",
  "review-wait": null,
  design: "pipeline-design",
  dev: "pipeline-dev",
  quality: "pipeline-quality",
  docs: "pipeline-docs",
  finalize: "pipeline-finalize",
  done: null,
  blocked: null,
};