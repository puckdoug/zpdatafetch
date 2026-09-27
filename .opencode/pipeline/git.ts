import type { PluginInput } from "@opencode-ai/plugin";
import { rename } from "node:fs/promises";

type Shell = PluginInput["$"];

export interface Git {
  currentBranch(): Promise<string | null>;
  isClean(): Promise<boolean>;
  isTracked(relPath: string): Promise<boolean>;
  gitRun(args: string[]): Promise<void>; // throws on non-zero exit
  renameFile(fromAbs: string, toAbs: string): Promise<void>;
}

export function createGit($: Shell, directory: string): Git {
  return {
    async currentBranch(): Promise<string | null> {
      const out = await $`git rev-parse --abbrev-ref HEAD`.cwd(directory).nothrow().text();
      const name = out.trim();
      return !name || name === "HEAD" ? null : name;
    },
    async isClean(): Promise<boolean> {
      const out = await $`git status --porcelain`.cwd(directory).nothrow().text();
      return out.trim() === "";
    },
    async isTracked(relPath: string): Promise<boolean> {
      const r = await $`git ls-files --error-unmatch -- ${relPath}`.cwd(directory).nothrow();
      return r.exitCode === 0;
    },
    async gitRun(args: string[]): Promise<void> {
      await $`git ${args}`.cwd(directory).quiet(); // Bun shell throws on non-zero exit
    },
    async renameFile(fromAbs: string, toAbs: string): Promise<void> {
      await rename(fromAbs, toAbs);
    },
  };
}
