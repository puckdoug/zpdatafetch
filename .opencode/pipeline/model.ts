export interface ModelRef {
  providerID: string;
  modelID: string;
}

/** Splits "provider/model" at the first slash; model ids may contain further slashes. */
export function parseModelRef(ref: string | null | undefined): ModelRef | null {
  if (typeof ref !== "string") return null;
  const trimmed = ref.trim();
  const i = trimmed.indexOf("/");
  if (i <= 0 || i === trimmed.length - 1) return null;
  return { providerID: trimmed.slice(0, i), modelID: trimmed.slice(i + 1) };
}

/** Resolution order: PIPELINE_MODEL env var, then pipeline.config.json, then null (workspace default). */
export function resolveModel(
  env: string | null | undefined,
  config: string | null | undefined,
): string | null {
  const e = typeof env === "string" ? env.trim() : "";
  if (e) return e;
  const c = typeof config === "string" ? config.trim() : "";
  if (c) return c;
  return null;
}

export function unreachableModelMessage(ref: string | null, error: string): string {
  const label = ref ?? "workspace default model";
  return [
    `model ${label} is unreachable.`,
    `  error: ${error}`,
    "  fix: run /pipeline-pin-model provider/model to pin a working model,",
    "       or export PIPELINE_MODEL=provider/model in the environment.",
  ].join("\n");
}

export interface CatalogModel {
  providerID: string;
  providerName?: string;
  id: string;
  name?: string;
}

export interface ModelCatalog {
  models: CatalogModel[];
}

export type MatchResult =
  | { ok: true; ref: string }
  | { ok: false; error: string; suggestions: string[] };

function tokens(s: string): string[] {
  return s
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length >= 2);
}

/**
 * Resolves a user-supplied model reference against the configured models.
 * Accepts an exact `provider/model` id case-insensitively, or a loose search
 * ("openrouter", "auto router") matched against ids and display names. A
 * unique best match wins; ties return the candidate list to choose from.
 * With no catalog, a full `provider/model` ref passes through unchanged.
 */
export function matchModelRef(input: string, catalog: ModelCatalog, limit = 15): MatchResult {
  const raw = input.trim();
  if (raw === "") return { ok: false, error: "no model given", suggestions: [] };

  if (catalog.models.length === 0) {
    if (parseModelRef(raw)) return { ok: true, ref: raw };
    return { ok: false, error: `model "${raw}" needs a provider prefix (provider/model)`, suggestions: [] };
  }

  const candidates = catalog.models.map((m) => ({
    ref: `${m.providerID}/${m.id}`,
    haystack: [m.providerID, m.providerName ?? "", m.id, m.name ?? ""].join(" ").toLowerCase(),
  }));

  const lc = raw.toLowerCase();
  const exact = candidates.find((c) => c.ref.toLowerCase() === lc);
  if (exact) return { ok: true, ref: exact.ref };

  const want = tokens(raw);
  const scored = candidates
    .map((c) => ({ ref: c.ref, score: want.filter((t) => c.haystack.includes(t)).length }))
    .filter((c) => c.score > 0)
    .sort((a, b) => b.score - a.score || a.ref.localeCompare(b.ref));

  if (scored.length === 0) return { ok: false, error: `no model matches "${raw}"`, suggestions: [] };

  const top = scored.filter((c) => c.score === scored[0].score);
  if (top.length === 1) return { ok: true, ref: top[0].ref };

  const shown = top.slice(0, limit).map((c) => c.ref);
  const extra = top.length - shown.length;
  return {
    ok: false,
    error: `"${raw}" matches ${top.length} models${extra > 0 ? ` (showing ${shown.length})` : ""}; pick one`,
    suggestions: shown,
  };
}

export type PinArg = { ok: true; query: string | null } | { ok: false; error: string };

/** Interprets /pipeline-pin-model's argument: "" or "default" clears the pin. */
export function normalizePinArg(raw: string): PinArg {
  const t = raw.trim();
  if (t === "" || t.toLowerCase() === "default") return { ok: true, query: null };
  return { ok: true, query: t };
}
