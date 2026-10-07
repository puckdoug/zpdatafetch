export interface PrioritizedIssue {
  number: number;
  priority?: string | null;
}

export interface PrioritySnapshot {
  /** Configured options, topmost (highest) first; [] if unknown. */
  order: string[];
  /** Issue number -> selected option name. */
  values: Record<number, string>;
  /** Non-null means the lookup degraded to issue-number ordering. */
  error: string | null;
}

export const STANDARD_PRIORITY = ["Urgent", "High", "Medium", "Low"] as const;

export function priorityRank(
  value: string | null | undefined,
  order: string[],
): number | null {
  const v = typeof value === "string" ? value.trim().toLowerCase() : "";
  if (!v) return null;
  const effective = order.length > 0 ? order : [...STANDARD_PRIORITY];
  const i = effective.findIndex((o) => o.trim().toLowerCase() === v);
  return i === -1 ? null : i;
}

export function orderIssues<T extends PrioritizedIssue>(
  issues: T[],
  order: string[] = [],
): T[] {
  return [...issues].sort((a, b) => {
    const ra = priorityRank(a.priority, order);
    const rb = priorityRank(b.priority, order);
    if (ra === null && rb === null) return a.number - b.number;
    if (ra === null) return 1;
    if (rb === null) return -1;
    if (ra !== rb) return ra - rb;
    return a.number - b.number;
  });
}

/** Attaches snapshot values and orders. null/error snapshot -> ascending number. */
export function selectIssues<T extends { number: number }>(
  issues: T[],
  snapshot: PrioritySnapshot | null | undefined,
): (T & { priority: string | null })[] {
  const values = snapshot?.values ?? {};
  const order = snapshot?.order ?? [];
  return orderIssues(
    issues.map((i) => ({ ...i, priority: values[i.number] ?? null })),
    order,
  );
}

export function parsePriorityJson(raw: string, numbers: number[]): PrioritySnapshot {
  const empty: PrioritySnapshot = { order: [], values: {}, error: null };
  let doc: unknown;
  try {
    doc = JSON.parse(raw);
  } catch {
    return { ...empty, error: "invalid json" };
  }
  const root = doc as {
    data?: { repository?: Record<string, unknown> };
    errors?: { message?: string }[];
  };
  const repo = root.data?.repository;
  if (!repo) return { ...empty, error: root.errors?.[0]?.message ?? "no repository data" };
  const values: Record<number, string> = {};
  let order: string[] = [];
  for (const n of numbers) {
    const node = repo[`i${n}`] as { projectItems?: { nodes?: unknown[] } } | undefined;
    for (const item of (node?.projectItems?.nodes ?? []) as {
      fieldValues?: { nodes?: unknown[] };
    }[]) {
      for (const fv of (item?.fieldValues?.nodes ?? []) as {
        name?: unknown;
        field?: { name?: unknown; options?: unknown };
      }[]) {
        const fieldName = fv?.field?.name;
        if (typeof fieldName !== "string" || fieldName.toLowerCase() !== "priority") continue;
        if (typeof fv.name === "string") values[n] = fv.name;
        if (order.length === 0 && Array.isArray(fv.field?.options)) {
          order = (fv.field.options as { name?: unknown }[])
            .map((o) => o?.name)
            .filter((x): x is string => typeof x === "string");
        }
      }
    }
  }
  return { order, values, error: null };
}
