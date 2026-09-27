import type { PluginInput } from "@opencode-ai/plugin";

type Client = PluginInput["client"];

export function stageError(info: { error?: unknown } | undefined): string | null {
  if (!info) return "no response from stage session";
  const e = (info as { error?: { name?: string; message?: string } }).error;
  if (!e) return null;
  return `${e.name ?? "error"}: ${e.message ?? "unknown"}`;
}

export interface StageRunner {
  runStage(agent: string, prompt: string): Promise<void>;
}

export function createSessionRunner(client: Client, directory: string): StageRunner {
  return {
    async runStage(agent: string, prompt: string): Promise<void> {
      const created = await client.session.create({
        body: { title: `pipeline: ${agent}` },
      });
      const session = created.data;
      if (!session) throw new Error("failed to create pipeline session");
      const result = await client.session.prompt({
        path: { id: session.id },
        body: {
          agent,
          parts: [{ type: "text", text: prompt }],
        },
        query: { directory },
      });
      const err = stageError(result.data?.info);
      if (err) throw new Error(`stage ${agent} failed: ${err}`);
    },
  };
}