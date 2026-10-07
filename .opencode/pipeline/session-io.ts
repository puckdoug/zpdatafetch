import type { PluginInput } from "@opencode-ai/plugin";
import { parseModelRef } from "./model.ts";

type Client = PluginInput["client"];

export function stageError(info: { error?: unknown } | undefined): string | null {
  if (!info) return "no response from the model (session produced no message)";
  const e = (info as { error?: { name?: string; message?: string } }).error;
  if (!e) return null;
  return `${e.name ?? "error"}: ${e.message ?? "unknown"}`;
}

export interface StageRunner {
  runStage(agent: string, prompt: string, model?: string | null, directory?: string): Promise<void>;
}

export function createSessionRunner(client: Client, directory: string): StageRunner {
  return {
    async runStage(agent, prompt, model, target): Promise<void> {
      const cwd = target ?? directory;
      const created = await client.session.create({
        body: { title: `pipeline: ${agent}` },
        query: { directory: cwd },
      });
      const session = created.data;
      if (!session) throw new Error("failed to create pipeline session");
      const body: Parameters<typeof client.session.prompt>[0]["body"] = {
        agent,
        parts: [{ type: "text", text: prompt }],
      };
      const ref = parseModelRef(model);
      if (ref) body.model = ref;
      const result = await client.session.prompt({
        path: { id: session.id },
        body,
        query: { directory: cwd },
      });
      const err = stageError(result.data?.info);
      if (err) throw new Error(`stage ${agent} failed: ${err}`);
    },
  };
}

export interface ModelProbe {
  probe(model?: string | null): Promise<string | null>;
}

/**
 * Sends one minimal prompt to confirm the resolved model can actually respond.
 * Returns null on success, or the error string on failure.
 */
export function createModelProbe(client: Client, directory: string): ModelProbe {
  return {
    async probe(model?: string | null): Promise<string | null> {
      try {
        const created = await client.session.create({
          body: { title: "pipeline: model probe" },
        });
        const session = created.data;
        if (!session) return "failed to create probe session";
        const body: Parameters<typeof client.session.prompt>[0]["body"] = {
          parts: [{ type: "text", text: "Reply with exactly: ok" }],
        };
        const ref = parseModelRef(model);
        if (ref) body.model = ref;
        const result = await client.session.prompt({
          path: { id: session.id },
          body,
          query: { directory },
        });
        return stageError(result.data?.info);
      } catch (err) {
        return String(err);
      }
    },
  };
}