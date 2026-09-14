---
name: grill
description: grill, adversarial-review, evidence, assumptions, failures, tests
compatibility: Agent Skills-compatible read-only reviewer; opencode-worker optional
---

# GRILL

## Goal

Prove a target is not relying on unsupported claims, fake coverage, or unsafe
failure semantics. This is read-only unless repair is explicitly requested.

## Workflow

Inspect the target, implementation, tests, history, CI identity, runtime evidence,
and project invariants. Attack races, partial failure, restart, malformed input,
authorization, retries, rollback, observability, coupling, migration, performance,
and speculative abstractions. Questions are not findings; inspect evidence.

For each important problem report:

`claim | challenge | evidence | severity | counterexample | required proof/test | correction`

When an independent critic uses a selected model/version/variant, invoke it only
through `opencode-worker`. Bound critic count and reconcile disagreements against
repository evidence.

End with `SURVIVED`, `FAILED`, or `CONDITIONALLY SURVIVED`, followed by concrete
reasons and unmet proof obligations.
