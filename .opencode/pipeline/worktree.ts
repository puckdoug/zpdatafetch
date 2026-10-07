import { join, sep } from "node:path";

export const WORKTREES_DIR = ".worktrees";
export const WORKTREES_EXCLUDE = ".worktrees/";

/** Absolute worktree path for an issue: <repoRoot>/.worktrees/gh-<n>. */
export function worktreePath(repoRoot: string, issue: number): string {
  return join(repoRoot, WORKTREES_DIR, `gh-${issue}`);
}

/** Args for `git worktree add`: always create `branch` from `defaultBranch`. */
export function worktreeAddArgs(path: string, branch: string, defaultBranch: string): string[] {
  return ["worktree", "add", "-b", branch, path, defaultBranch];
}

export interface WorktreePlan {
  /** Delete the stale local issue branch so it is recreated at the default head. */
  deleteBranch: boolean;
  /** Return the main tree to the default branch before adding the worktree. */
  returnToDefault: boolean;
}

/**
 * Preparation for a missing worktree whose branch may be stale (spec §2):
 * recreate an existing branch from the default head, and move a legacy main
 * tree off the issue branch first.
 */
export function worktreePlan(
  branch: string,
  branchExists: boolean,
  mainBranch: string | null,
): WorktreePlan {
  return { deleteBranch: branchExists, returnToDefault: mainBranch === branch };
}

/**
 * True when the worktree branch is behind or diverged from the upstream default
 * branch and must merge it. `upstreamIsAncestor` is the result of asking git
 * whether `origin/<default>` is an ancestor of the branch head.
 */
export function needsSync(upstreamIsAncestor: boolean): boolean {
  return !upstreamIsAncestor;
}

export interface WorktreeEntry {
  path: string;
  branch: string | null;
}

/** Parses `git worktree list --porcelain` (blocks separated by blank lines). */
export function parseWorktreeList(porcelain: string): WorktreeEntry[] {
  const entries: WorktreeEntry[] = [];
  let path: string | null = null;
  let branch: string | null = null;
  const flush = (): void => {
    if (path !== null) entries.push({ path, branch });
    path = null;
    branch = null;
  };
  for (const line of porcelain.split("\n")) {
    if (line === "") {
      flush();
      continue;
    }
    if (line.startsWith("worktree ")) path = line.slice("worktree ".length);
    else if (line.startsWith("branch ")) {
      const ref = line.slice("branch ".length);
      branch = ref.startsWith("refs/heads/") ? ref.slice("refs/heads/".length) : ref;
    }
  }
  flush();
  return entries;
}

/** Issue number for a worktree path under <repoRoot>/.worktrees, else null. */
export function worktreeIssue(repoRoot: string, path: string): number | null {
  const prefix = join(repoRoot, WORKTREES_DIR) + sep;
  if (!path.startsWith(prefix)) return null;
  const m = /^gh-(\d+)$/.exec(path.slice(prefix.length));
  return m ? Number(m[1]) : null;
}

/** Worktree issue numbers with no state file in planning (run archived). */
export function staleWorktrees(
  worktreeIssues: readonly number[],
  knownIssues: ReadonlySet<number>,
): number[] {
  return worktreeIssues.filter((n) => !knownIssues.has(n)).sort((a, b) => a - b);
}

/** Appends an exclude line once; idempotent. */
export function addExcludeLine(
  content: string,
  line: string = WORKTREES_EXCLUDE,
): { content: string; changed: boolean } {
  const present = content
    .split("\n")
    .map((l) => l.trim())
    .includes(line);
  if (present) return { content, changed: false };
  const base = content.length === 0 || content.endsWith("\n") ? content : `${content}\n`;
  return { content: `${base}${line}\n`, changed: true };
}
