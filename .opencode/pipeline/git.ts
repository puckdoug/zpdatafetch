import { execFile } from "node:child_process";
import { readFile, writeFile, rename } from "node:fs/promises";
import { isAbsolute, join } from "node:path";
import { promisify } from "node:util";
import {
  addExcludeLine,
  parseWorktreeList,
  worktreeAddArgs,
  type WorktreeEntry,
} from "./worktree.ts";

const run = promisify(execFile);

export type MergeResult =
  | { status: "clean" }
  | { status: "conflicted" }
  | { status: "failed"; error: string };

export interface Git {
  currentBranch(): Promise<string | null>;
  isClean(): Promise<boolean>;
  isTracked(relPath: string): Promise<boolean>;
  gitRun(args: string[]): Promise<void>; // throws on non-zero exit
  renameFile(fromAbs: string, toAbs: string): Promise<void>;
  branchExists(branch: string): Promise<boolean>;
  /** force-deletes a local branch; used to recreate a stale issue branch. */
  deleteBranch(branch: string): Promise<void>;
  worktreeList(): Promise<WorktreeEntry[]>;
  worktreeExists(path: string): Promise<boolean>;
  /** creates `branch` from `defaultBranch` and checks it out at `path`. */
  worktreeAdd(path: string, branch: string, defaultBranch: string): Promise<void>;
  /** non-force removal; throws when the worktree is dirty or absent. */
  worktreeRemove(path: string): Promise<void>;
  /** appends `.worktrees/` to the repo's local exclude; idempotent. */
  excludeWorktrees(): Promise<void>;
  /** Runs `git fetch origin` in the bound directory; throws on failure. */
  fetch(): Promise<void>;
  /** Resolves a ref to a SHA; null when the ref does not exist. */
  revParse(ref: string): Promise<string | null>;
  /** True when `ancestor` is reachable from `descendant`. */
  isAncestor(ancestor: string, descendant: string): Promise<boolean>;
  /** Merges `ref`; never throws on conflict, returns the outcome as a value. */
  merge(ref: string): Promise<MergeResult>;
  /** True when the bound worktree has a conflicted/in-progress merge. */
  hasMergeInProgress(): Promise<boolean>;
}

/**
 * Git access via node child_process (works under Bun at runtime and deno/node
 * in tests). `isClean` ignores untracked files (`-uno`): the pipeline's own
 * untracked planning bookkeeping must not block the archive commit, while
 * tracked modifications and deletions still do.
 */
export function createGit(directory: string): Git {
  async function git(args: string[]): Promise<string> {
    try {
      const { stdout } = await run("git", args, { cwd: directory });
      return stdout;
    } catch (e) {
      const err = e as { stderr?: string; message: string };
      const detail = (err.stderr ?? err.message).trim();
      throw new Error(`git ${args.join(" ")} failed: ${detail}`);
    }
  }

  async function gitNothrow(
    args: string[],
  ): Promise<{ code: number; stdout: string; stderr: string }> {
    try {
      const { stdout } = await run("git", args, { cwd: directory });
      return { code: 0, stdout, stderr: "" };
    } catch (e) {
      const err = e as { code?: number; stdout?: string; stderr?: string };
      return { code: err.code ?? 1, stdout: err.stdout ?? "", stderr: err.stderr ?? "" };
    }
  }

  async function hasMergeInProgress(): Promise<boolean> {
    const { code } = await gitNothrow(["rev-parse", "--verify", "--quiet", "MERGE_HEAD"]);
    if (code === 0) return true;
    const { stdout } = await gitNothrow(["status", "--porcelain"]);
    return stdout.split("\n").some((line) => /^(DD|AU|UD|UA|DU|AA|UU)/.test(line));
  }

  return {
    async currentBranch(): Promise<string | null> {
      const { stdout } = await gitNothrow(["rev-parse", "--abbrev-ref", "HEAD"]);
      const name = stdout.trim();
      return !name || name === "HEAD" ? null : name;
    },
    async isClean(): Promise<boolean> {
      const { stdout } = await gitNothrow(["status", "--porcelain", "-uno"]);
      return stdout.trim() === "";
    },
    async isTracked(relPath: string): Promise<boolean> {
      const { code } = await gitNothrow(["ls-files", "--error-unmatch", "--", relPath]);
      return code === 0;
    },
    async gitRun(args: string[]): Promise<void> {
      await git(args);
    },
    async renameFile(fromAbs: string, toAbs: string): Promise<void> {
      await rename(fromAbs, toAbs);
    },
    async branchExists(branch: string): Promise<boolean> {
      const { code } = await gitNothrow(["show-ref", "--verify", "--quiet", `refs/heads/${branch}`]);
      return code === 0;
    },
    async deleteBranch(branch: string): Promise<void> {
      await git(["branch", "-D", branch]);
    },
    async worktreeList(): Promise<WorktreeEntry[]> {
      const { stdout } = await gitNothrow(["worktree", "list", "--porcelain"]);
      return parseWorktreeList(stdout);
    },
    async worktreeExists(path: string): Promise<boolean> {
      const { stdout } = await gitNothrow(["worktree", "list", "--porcelain"]);
      return parseWorktreeList(stdout).some((w) => w.path === path);
    },
    async worktreeAdd(path, branch, defaultBranch): Promise<void> {
      await git(worktreeAddArgs(path, branch, defaultBranch));
    },
    async worktreeRemove(path: string): Promise<void> {
      await git(["worktree", "remove", path]);
    },
    async excludeWorktrees(): Promise<void> {
      const { stdout } = await gitNothrow(["rev-parse", "--git-path", "info/exclude"]);
      const rel = stdout.trim();
      if (!rel) throw new Error("could not locate git info/exclude");
      const abs = isAbsolute(rel) ? rel : join(directory, rel);
      let current = "";
      try {
        current = await readFile(abs, "utf8");
      } catch {
        /* no exclude file yet */
      }
      const next = addExcludeLine(current);
      if (next.changed) await writeFile(abs, next.content);
    },
    async fetch(): Promise<void> {
      await git(["fetch", "origin"]);
    },
    async revParse(ref: string): Promise<string | null> {
      const { code, stdout } = await gitNothrow(["rev-parse", "--verify", "--quiet", ref]);
      return code === 0 ? stdout.trim() : null;
    },
    async isAncestor(ancestor: string, descendant: string): Promise<boolean> {
      const { code } = await gitNothrow(["merge-base", "--is-ancestor", ancestor, descendant]);
      return code === 0;
    },
    async merge(ref: string): Promise<MergeResult> {
      const { code, stderr } = await gitNothrow(["merge", "--no-edit", ref]);
      if (code === 0) return { status: "clean" };
      if (await hasMergeInProgress()) return { status: "conflicted" };
      return { status: "failed", error: stderr.trim() || `git merge exited ${code}` };
    },
    hasMergeInProgress,
  };
}