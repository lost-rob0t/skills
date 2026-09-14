---
name: opencode-orchestrate
description: orchestration, continuation, status, handoff, safety, verification
compatibility: Agent Skills-compatible coding agent with git and project tools
---

# OpenCode Orchestrate

## Goal

Drive a repository goal through coherent verified slices without repeatedly
replanning or losing session state.

## State Discovery

Read repository instructions, current goal/session, durable Prolog TODO state,
Org plans/handoffs, git branch/worktree/status/log, issue and PR state, focused
test evidence, remote CI, active worker records, blockers, and the last meaningful
completed action. Distinguish facts from inference.

## Lifecycle

`understand -> inspect -> choose slice -> implement -> test -> verify -> finish`

For `continue`, `do`, or `resume`, recover the established objective first and
advance the next unblocked coherent slice. Do not restart planning unless evidence
invalidates it. For `status`, report current action and phase, repository,
worktree, branch, dirt, issue/PR, tests/CI, workers, blockers, and next action.

Persist handoffs as concise Org when a file is warranted: goal, completed work,
branch/worktree, changes, evidence, issues/PRs, blockers, and exact next action.

## Workers And Safety

Use native subtasks only when model identity does not matter. Any selected model,
provider, version, variant, or agent profile MUST use `opencode-worker`. Parallel
mutation requires isolated linked worktrees; otherwise serialize or reject it.
Honor task budgets and stop/panic at safe boundaries without resetting user work.
