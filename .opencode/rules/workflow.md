---
description: Planning, implementation workflow, git usage, and issue handling
globs:
---

# Workflow Rules

## Rules come first
- Read and re-read the rules before every action. Every rule here is mandatory. Do not wait to be reminded.

## Planning before implementation
- Never start implementation until explicitly told to do so. Always iterate over a plan until it is ready, then explicitly agree to implement.
- GitHub issues are the tracker. Work existing issues only — pull them with `gh issue view <N>`; never plan an issue from memory or recreate it locally.
- Write the implementation plan into `./docs/planning/issue_<N>_<slug>.md` and maintain it while making changes.
- Record `GitHub issue: #N` in the plan file header so the local plan and the GitHub issue reference each other.
- Always create a checklist at the top of the implementation plan file and maintain it as you progress.
- If it is ever unclear whether to plan or implement, ask.

## Issue handling
- Never ignore an issue (errors or warnings). Never blame issues as "pre-existing".
- GitHub issues are the source of truth for bugs and feature requests. Never create a GitHub issue from local work; work only issues that already exist.
- New problems found while working are resolved immediately or logged in `./docs/planning/` with a proposed solution, never filed as new GitHub issues.
- Working an issue follows this flow:
  1. Pull it from GitHub: `gh issue view <N>`.
  2. Plan locally: create `./docs/planning/issue_<N>_<slug>.md` with `GitHub issue: #N` in the header and a checklist at the top.
  3. Work the plan locally and keep the checklist current. No GitHub writes while work is in progress.
  4. Complete the issue, and only once the work is actually verified working:
     - `just test` and `just check` pass
     - the change has been exercised end to end against the real system where
       feasible (run the CLI / library path on live data), not only against
       mocks. Mocked tests alone do not prove the feature works.
     - plan file finalized: every checklist item checked and `Status: DONE` in the header
     - post the final update with `gh issue comment <N>`: what changed, validation results, and the deep-dive link to the plan file
- NEVER close a GitHub issue. Closing is the maintainer's action and is done only on explicit request. Do not close, reopen, or otherwise change issue state on your own.
- Do not claim an issue is complete, mark its plan `DONE`, or post a completion update until the implementation is verified. If any doubt remains, say so and keep the issue/plan open.

## Git
- Use git commands to rename (`git mv`), remove (`git rm`), or add (`git add`) to ensure change history is tracked.
- These restrictions apply to YOU (the agent), not the maintainer. Never install hooks, aliases, or other mechanisms that change the maintainer's own git behavior.
- Do not make changes to the git repository. Do not use `git commit`, `merge`, `rebase`, or `push`.
- EXCEPTION: only when the maintainer explicitly asks for commits, and only on the branch they name. Before every commit run `git branch --show-current` and confirm it is the branch they named. If it is not — especially `main` — stop and report instead of committing. The check is your own discipline, not tooling.

## Deployment
- At the end of implementation, always summarize steps required to finish deployment in dev and prod (restart granian, run migrations, etc.).
