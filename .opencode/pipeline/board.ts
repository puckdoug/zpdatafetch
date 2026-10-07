import type { Stage, StatusCategory } from "./state.ts";

export interface StatusOption {
  id: string;
  name: string;
}

/** One project item that carries a single-select `Status` field. */
export interface StatusFieldItem {
  itemId: string;
  projectId: string;
  fieldId: string;
  options: StatusOption[];
}

export interface StatusPlan {
  projectId: string;
  itemId: string;
  fieldId: string;
  optionId: string;
  optionName: string;
}

export interface StatusSnapshot {
  items: StatusFieldItem[];
  error: string | null;
}

/** Accepted option names per category. Order is the preference order. */
export const STATUS_SYNONYMS: Record<StatusCategory, readonly string[]> = {
  ready: ["todo", "to do", "ready", "backlog", "queued", "planned", "next"],
  "in-progress": ["in progress", "inprogress", "doing", "active", "started"],
  "on-hold": ["on hold", "onhold", "blocked", "paused", "waiting"],
  done: ["done", "complete", "completed", "shipped"],
};

/** Board category for a pipeline stage (spec stage→status table). */
export function statusCategory(stage: Stage): StatusCategory {
  switch (stage) {
    case "review":
      return "ready";
    case "review-wait":
    case "blocked":
      return "on-hold";
    case "design":
    case "dev":
    case "quality":
    case "docs":
    case "finalize":
      return "in-progress";
    case "done":
      return "done";
  }
}

/** False when the stage already maps to the recorded category (no-op). */
export function shouldSync(stage: Stage, recorded: StatusCategory | undefined): boolean {
  return recorded !== statusCategory(stage);
}

/** Lowercases and removes spaces, hyphens and underscores. */
export function normalizeStatusName(name: string): string {
  return name.toLowerCase().replace(/[\s_-]+/g, "");
}

/** First option name matching the category, by preference; null if none. */
export function matchStatusOption(
  names: readonly string[],
  category: StatusCategory,
): string | null {
  const wanted = STATUS_SYNONYMS[category].map(normalizeStatusName);
  const normalized = names.map(normalizeStatusName);
  for (const w of wanted) {
    const i = normalized.indexOf(w);
    if (i !== -1) return names[i];
  }
  return null;
}

/** One update per item whose Status options include the category. */
export function planStatusUpdates(
  category: StatusCategory,
  items: readonly StatusFieldItem[],
): StatusPlan[] {
  const plan: StatusPlan[] = [];
  for (const item of items) {
    const name = matchStatusOption(item.options.map((o) => o.name), category);
    if (name === null) continue;
    const option = item.options.find((o) => normalizeStatusName(o.name) === normalizeStatusName(name));
    if (!option) continue;
    plan.push({
      projectId: item.projectId,
      itemId: item.itemId,
      fieldId: item.fieldId,
      optionId: option.id,
      optionName: option.name,
    });
  }
  return plan;
}

/** Parses the project-items read into Status fields; never throws. */
export function parseStatusSnapshot(raw: string): StatusSnapshot {
  let doc: unknown;
  try {
    doc = JSON.parse(raw);
  } catch {
    return { items: [], error: "invalid json" };
  }
  const root = doc as {
    data?: { repository?: { issue?: unknown } };
    errors?: { message?: unknown }[];
  };
  if (Array.isArray(root.errors) && root.errors.length > 0) {
    const message = root.errors[0]?.message;
    return { items: [], error: typeof message === "string" ? message : "graphql error" };
  }
  const issue = root.data?.repository?.issue;
  if (!issue || typeof issue !== "object") return { items: [], error: "no project data" };
  const nodes = (issue as { projectItems?: { nodes?: unknown } }).projectItems?.nodes;
  if (!Array.isArray(nodes)) return { items: [], error: "no project data" };
  const items: StatusFieldItem[] = [];
  for (const node of nodes as {
    id?: unknown;
    project?: { id?: unknown; fields?: { nodes?: unknown } };
  }[]) {
    const itemId = node?.id;
    const projectId = node?.project?.id;
    if (typeof itemId !== "string" || typeof projectId !== "string") continue;
    const fields = node.project?.fields?.nodes;
    if (!Array.isArray(fields)) continue;
    for (const field of fields as {
      id?: unknown;
      name?: unknown;
      options?: unknown;
    }[]) {
      if (typeof field?.name !== "string" || field.name.toLowerCase() !== "status") continue;
      if (typeof field.id !== "string" || !Array.isArray(field.options)) continue;
      const options = (field.options as { id?: unknown; name?: unknown }[])
        .filter((o) => typeof o?.id === "string" && typeof o?.name === "string")
        .map((o) => ({ id: o.id as string, name: o.name as string }));
      if (options.length === 0) continue;
      items.push({ itemId, projectId, fieldId: field.id, options });
    }
  }
  return { items, error: null };
}
