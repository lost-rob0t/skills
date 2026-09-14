---
name: worker-orchestration
description: workers, routing, delegation, fleet, budgets, concurrency
compatibility: Unix shell and the canonical opencode-worker skill
---

# Worker Orchestration

## Goal

Route and compose bounded child OpenCode workers through one Unix abstraction.

## Workflow

1. Determine task, role, mutation authority, budget, and required independence.
2. Resolve logical models through `opencode-worker-resolve-model`; never derive
   model IDs from prose labels.
3. Pipe complete prompts into `opencode-worker` and consume stdout as the result.
4. Keep diagnostics and usage metadata on stderr. Do not parse terminal escapes.
5. Bound concurrency, retries, elapsed delay, iterations, and total budget.
6. Use isolated linked worktrees for mutating lanes. Read-only lanes may share a
   checkout; never run parallel mutation in one worktree.
7. Reconcile independent results in the parent and verify claims against source.

Use independent models or perspectives for high-value review when budget permits.
Server attachment is optional optimization; standalone operation remains correct.
