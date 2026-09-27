import { tool, type Plugin } from "@opencode-ai/plugin";
import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import {
  initialState,
  parseState,
  parseStateFilename,
  serializeState,
  stateFilename,
  type PipelineState,
} from "../pipeline/state.ts";
import {
  checklistComplete,
  findIssueArtifact,
  hasOpenDeficiency,
} from "../pipeline/artifacts.ts";
import { nextStage, STAGE_AGENT, type Facts } from "../pipeline/transitions.ts";
import { createGh, humanReplySince } from "../pipeline/github.ts";
import { createSessionRunner } from "../pipeline/session-io.ts";
import {
  formatStatus,
  mergeStartupStates,
  type IssueStatusEntry,
} from "../pipeline/status.ts";
import { createGit, type Git } from "../pipeline/git.ts";
import {
  DONE_DIR,
  PLANNING_DIR,
  avoidCollision,
  planRollback,
  selectArchiveCandidates,
  type ArchiveCandidate,
  type PlannedMove,
  type RollbackStep,
} from "../pipeline/archive.ts";

const LABEL = "pipeline";
const INTERVAL_MS = 5 * 60 * 1000;

export const PipelinePlugin: Plugin = async ({ client, $, directory }) => {
  const gh = createGh($, LABEL);
  const runner = createSessionRunner(client, directory);
  const git: Git = createGit($, directory);
  let timer: ReturnType<typeof setInterval> | null = null;
  let started = false;
  let running = false;
  let loopStartedAt: number | null = null;
  let current: { issue: number; stage: PipelineState["stage"]; startedAt: number } | null = null;

  async function log(
    level: "debug" | "info" | "warn" | "error",
    message: string,
    extra?: Record<string, unknown>,
  ): Promise<void> {
    try {
      await client.app.log({ body: { service: "pipeline", level, message, extra } });
    } catch {
      /* logging must never break a tick */
    }
  }

  async function listPlanning(): Promise<string[]> {
    try {
      return await readdir(join(directory, PLANNING_DIR));
    } catch {
      return [];
    }
  }

  async function listDone(): Promise<string[]> {
    try {
      return await readdir(join(directory, DONE_DIR));
    } catch {
      return [];
    }
  }

  async function readStateFile(dir: string, name: string): Promise<PipelineState | null> {
    try {
      const raw = await readFile(join(directory, dir, name), "utf8");
      return parseState(raw);
    } catch {
      return null;
    }
  }

  async function writeState(s: PipelineState): Promise<void> {
    await mkdir(join(directory, PLANNING_DIR), { recursive: true });
    const name = stateFilename(s.startDate, s.issue);
    await writeFile(join(directory, PLANNING_DIR, name), serializeState(s));
  }

  async function gatherFacts(s: PipelineState): Promise<Facts> {
    const files = await listPlanning();
    const spec = findIssueArtifact(files, s.issue, "spec");
    const design = findIssueArtifact(files, s.issue, "design");
    let designBody = "";
    if (design) {
      designBody = await readFile(join(directory, PLANNING_DIR, design), "utf8");
    }
    let humanReply = false;
    if (s.stage === "review-wait") {
      const comments = await gh.comments(s.issue);
      humanReply = humanReplySince(comments, s.updated);
    }
    let hasPR = false;
    if (s.stage === "finalize") {
      hasPR = await gh.prExists(s.branch);
    }
    return {
      hasSpec: spec !== null,
      hasDesign: design !== null,
      hasOpenDeficiency: designBody ? hasOpenDeficiency(designBody) : false,
      checklistComplete: designBody ? checklistComplete(designBody) : false,
      humanReply,
      qualityCycles: s.attempts.quality ?? 0,
      hasPR,
    };
  }

  async function advance(s: PipelineState): Promise<PipelineState> {
    const facts = await gatherFacts(s);
    const next = nextStage(s.stage, facts);
    const updated: PipelineState = {
      ...s,
      stage: next,
      updated: new Date().toISOString(),
      attempts: { ...s.attempts },
    };
    if (s.stage === "quality" && next === "design") {
      updated.attempts.quality = (s.attempts.quality ?? 0) + 1;
    }
    await writeState(updated);
    return updated;
  }

  async function runStageAgent(s: PipelineState): Promise<void> {
    const agent = STAGE_AGENT[s.stage];
    if (!agent) return;
    await gh.comment(s.issue, `Pipeline: entering ${s.stage}. Branch: ${s.branch}`);
    await runner.runStage(
      agent,
      `Process issue #${s.issue}. Stage: ${s.stage}.`,
    );
  }

  async function runStageAgentWithRetry(s: PipelineState): Promise<void> {
    try {
      await runStageAgent(s);
    } catch (err) {
      await gh.comment(
        s.issue,
        `Pipeline: stage ${s.stage} failed (${String(err)}); retrying once.`,
      );
      await runStageAgent(s);
    }
  }

  async function tickOnce(): Promise<void> {
    if (!started) return;
    await processOpenIssue();
    await archiveDoneIssues();
  }

  async function processOpenIssue(): Promise<void> {
    const issues = (await gh.listIssues()).sort((a, b) => a.number - b.number);
    for (const issue of issues) {
      const files = await listPlanning();
      let state: PipelineState | null = null;
      for (const f of files) {
        const parsed = parseStateFilename(f);
        if (parsed && parsed.issue === issue.number) {
          state = await readStateFile(PLANNING_DIR, f);
          if (state) break;
        }
      }
      if (!state) {
        state = initialState(issue.number);
        await writeState(state);
      }
      if (state.stage === "done" || state.stage === "blocked") continue;

      try {
        let s = state;
        while (started) {
          const agent = STAGE_AGENT[s.stage];
          if (agent) {
            current = { issue: s.issue, stage: s.stage, startedAt: Date.now() };
            await runStageAgentWithRetry(s);
            current = null;
          }
          const advanced = await advance(s);
          if (advanced.stage === s.stage) break;
          s = advanced;
        }
      } catch (err) {
        const failed: PipelineState = {
          ...state,
          stage: "blocked",
          updated: new Date().toISOString(),
          note: String(err),
        };
        await writeState(failed);
        await gh.comment(issue.number, `Pipeline blocked: ${String(err)}`);
      }
      return;
    }
  }

  async function archiveDoneIssues(): Promise<void> {
    const files = await listPlanning();
    const stateFiles = files.filter((f) => parseStateFilename(f));
    const states = (await Promise.all(stateFiles.map((f) => readStateFile(PLANNING_DIR, f))))
      .filter((s): s is PipelineState => s !== null);
    const mergedBranches = new Set<string>();
    for (const s of states.filter((s) => s.stage === "done")) {
      if (await gh.prMerged(s.branch)) mergedBranches.add(s.branch);
      else await log("debug", `gh#${s.issue}: PR ${s.branch} not merged yet; recheck next tick`);
    }
    const candidates = selectArchiveCandidates(files, states, mergedBranches);
    for (const c of candidates) {
      try {
        await archiveOne(c);
        await log("info", `archived gh#${c.issue}: ${c.files.length} files moved to docs/done`);
      } catch (err) {
        await log("warn", `archive gh#${c.issue} skipped, will retry next tick: ${String(err)}`);
      }
    }
  }

  async function archiveOne(c: ArchiveCandidate): Promise<void> {
    const prev = await git.currentBranch();
    if (!(await git.isClean())) {
      throw new Error("working tree not clean; retrying next tick");
    }
    const def = await gh.defaultBranch();
    if (prev !== def) await git.gitRun(["checkout", def]);
    try {
      await git.gitRun(["pull", "--ff-only"]);
      await mkdir(join(directory, DONE_DIR), { recursive: true });
      const taken = new Set(await listDone());
      const moves: PlannedMove[] = [];
      for (const f of c.files) {
        const dest = avoidCollision(f, taken);
        taken.add(dest);
        moves.push({ file: f, dest, tracked: await git.isTracked(`${PLANNING_DIR}/${f}`) });
      }
      let committed = false;
      try {
        for (const m of moves) await applyMove(m);
        await git.gitRun(["commit", "-m", `docs: archive gh#${c.issue} planning docs`]);
        committed = true;
        await git.gitRun(["push", "origin", def]);
      } catch (err) {
        await runRollback(planRollback(moves, committed));
        throw err;
      }
    } finally {
      await restore(prev);
    }
  }

  async function applyMove(m: PlannedMove): Promise<void> {
    if (m.tracked) {
      await git.gitRun(["mv", `${PLANNING_DIR}/${m.file}`, `${DONE_DIR}/${m.dest}`]);
    } else {
      await git.renameFile(join(directory, PLANNING_DIR, m.file), join(directory, DONE_DIR, m.dest));
      await git.gitRun(["add", "-f", `${DONE_DIR}/${m.dest}`]);
    }
  }

  async function runRollback(steps: RollbackStep[]): Promise<void> {
    for (const s of steps) {
      try {
        if (s.kind === "git") await git.gitRun(s.args);
        else await git.renameFile(join(directory, s.from), join(directory, s.to));
      } catch (err) {
        await log("error", `archive rollback step failed: ${JSON.stringify(s)}: ${String(err)}`);
      }
    }
  }

  async function restore(branch: string | null): Promise<void> {
    if (!branch) return;
    try {
      await git.gitRun(["checkout", branch]);
    } catch (err) {
      await log("warn", `could not restore branch ${branch} after archive: ${String(err)}`);
    }
  }

  function triggerTick(): string {
    if (running) return "check skipped: an issue or stage is already in progress";
    running = true;
    tickOnce()
      .catch(() => {})
      .finally(() => {
        running = false;
      });
    return "immediate check triggered";
  }

  function start(): void {
    if (started) return;
    started = true;
    loopStartedAt = Date.now();
    timer = setInterval(() => {
      if (running) return;
      running = true;
      tickOnce()
        .catch(() => {})
        .finally(() => {
          running = false;
        });
    }, INTERVAL_MS);
    triggerTick();
  }

  function stop(): void {
    started = false;
    loopStartedAt = null;
    current = null;
    if (timer) clearInterval(timer);
    timer = null;
  }

  async function startupIssueStates(): Promise<IssueStatusEntry[]> {
    const planningStates: IssueStatusEntry[] = [];
    const doneStates: IssueStatusEntry[] = [];
    for (const f of await listPlanning()) {
      if (!parseStateFilename(f)) continue;
      const st = await readStateFile(PLANNING_DIR, f);
      if (st) planningStates.push({ issue: st.issue, stage: st.stage, updated: st.updated });
    }
    const seen = new Set(planningStates.map((s) => s.issue));
    for (const f of await listDone()) {
      const parsed = parseStateFilename(f);
      if (!parsed || seen.has(parsed.issue)) continue;
      const st = await readStateFile(DONE_DIR, f);
      if (st) {
        doneStates.push({ issue: st.issue, stage: st.stage, archived: true, updated: st.updated });
      }
    }
    let issues: { number: number }[] = [];
    try {
      issues = await gh.listIssues();
    } catch (err) {
      await log(
        "warn",
        `startup status: gh.listIssues failed; reporting local state only: ${String(err)}`,
      );
    }
    return mergeStartupStates(issues, planningStates, doneStates);
  }

  return {
    tool: {
      pipeline_start: tool({
        description:
          "Start the pipeline loop: poll pipeline-labeled issues until OpenCode exits.",
        args: {},
        async execute() {
          start();
          const issueStates = await startupIssueStates();
          return formatStatus({
            loopRunning: true,
            loopStartedAt,
            now: Date.now(),
            current,
            issueStates,
            mode: "startup",
          });
        },
      }),
      pipeline_stop: tool({
        description:
          "Stop the pipeline loop after any in-flight stage finishes. No further stages are scheduled.",
        args: {},
        async execute() {
          stop();
          return "pipeline loop stopped";
        },
      }),
      pipeline_check: tool({
        description:
          "Trigger an immediate check of GitHub issues without waiting for the 5-minute polling interval.",
        args: {},
        async execute() {
          if (!started) {
            return "pipeline loop is stopped; start it first with /pipeline-start";
          }
          return triggerTick();
        },
      }),
      pipeline_status: tool({
        description:
          "Report pipeline status: whether the loop is running and for how long, the agent currently working, and the state of pipeline-labeled issues (waiting for input, completed, archived, or failed).",
        args: {},
        async execute() {
          const issueStates: { issue: number; stage: PipelineState["stage"]; archived?: boolean }[] =
            [];
          for (const f of await listPlanning()) {
            if (!parseStateFilename(f)) continue;
            const st = await readStateFile(PLANNING_DIR, f);
            if (st) issueStates.push({ issue: st.issue, stage: st.stage });
          }
          const seen = new Set(issueStates.map((s) => s.issue));
          for (const f of await listDone()) {
            const parsed = parseStateFilename(f);
            if (!parsed || seen.has(parsed.issue)) continue;
            const st = await readStateFile(DONE_DIR, f);
            if (st) issueStates.push({ issue: st.issue, stage: st.stage, archived: true });
          }
          return formatStatus({
            loopRunning: started,
            loopStartedAt,
            now: Date.now(),
            current,
            issueStates,
          });
        },
      }),
    },
  };
};

export default PipelinePlugin;