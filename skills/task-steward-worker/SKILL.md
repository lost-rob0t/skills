---
name: task-steward-worker
description: steward, rage, leases, fencing, heartbeat, receipts
compatibility: Agent Skills-compatible agent with HTTP access to a Task Steward runtime and repository issue/PR tools
---

# Task Steward Worker

## Goal

Execute one leased Task Steward transaction without choosing global work.

## Input

An assignment must provide `worker`, `project`, `task_ref`, `generation`, `lease_token`, and a receipt endpoint. It may also provide score/provenance fields.

Use `scripts/steward-worker.py claim` when the runtime uses pull assignment rather than pushed dispatch.

## Output

Produce normal repository evidence plus steward receipts: `heartbeat`, `status`, `complete`, `blocked`, or `yield`.

## Workflow

1. Validate that the assignment names this worker and expected project.
2. Load the repository's RAGE/process skill and local instructions.
3. Resolve `task_ref` to the canonical issue/PR; never substitute a different task.
4. Recover a safe existing transaction for that exact task before creating another.
5. Send bounded heartbeat/status receipts during long work.
6. At a real transaction boundary, send exactly one terminal receipt: `complete`, `blocked`, or `yield`.
7. Preserve worker/project/task/generation/lease token exactly in every receipt.
8. If the steward reports stale generation, revocation, or lease mismatch, stop state-changing work immediately.

## Receipt helper

```sh
python3 scripts/steward-worker.py receipt \
  --worker "$WORKER" --project "$PROJECT" --task-ref "$TASK_REF" \
  --generation "$GENERATION" --lease-token "$LEASE_TOKEN" \
  --kind heartbeat --detail 'focused tests running'
```

Set `STEWARD_URL` for the runtime base URL. If the runtime requires authentication, set `STEWARD_API_TOKEN`; the helper sends it as a bearer token without persisting it.

## Rules

- Prolog/steward policy owns scheduling and worker eligibility.
- A lease authorizes only the assigned transaction, never validation or permission bypasses.
- Repository issue/PR state and exact-head CI remain canonical execution evidence.
- Do not commit API tokens, lease tokens, private endpoints, or raw assignment secrets.
- Missing steward connectivity is a blocker; it is not authority to freelance.
