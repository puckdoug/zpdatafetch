---
description: Planning, implementation workflow, git usage, and issue handling
globs:
---

# Workflow Rules

## Rules come first
- Read and re-read the rules before every action. Every rule here is mandatory. Do not wait to be reminded.

## Planning before implementation
- Never start implementation until explicitly told to do so. Always iterate over a plan until it is ready, then explicitly agree to implement.
- Write implementation plans into `./docs/planning/` and maintain them while making changes.
- Always create a checklist at the top of the implementation plan file and maintain it as you progress.
- If it is ever unclear whether to plan or implement, ask.

## Issue handling
- Never ignore an issue (errors or warnings). Never blame issues as "pre-existing".
- When you identify an issue, either resolve it immediately or log it in `./docs/planning/` and propose a solution.

## Git
- Use git commands to rename (`git mv`), remove (`git rm`), or add (`git add`) to ensure change history is tracked.
- Do not make changes to the git repository. Do not use `git commit`, `merge`, `rebase`, or `push`.

## Deployment
- At the end of implementation, always summarize steps required to finish deployment in dev and prod (restart granian, run migrations, etc.).
