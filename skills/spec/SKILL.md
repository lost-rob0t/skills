---
name: spec
description: spec, specification, planning, requirements, acceptance, verification
---

# Spec

Turn a request into a decision-ready, testable specification. Stop after the spec unless the user separately asks for execution.

## Goal

Produce the smallest spec that makes the work unambiguous enough to execute and verify across software, infrastructure, research, operations, writing, data, or other domains.

## Input

Use the user's request plus the current repository, artifact, environment, instructions, and authoritative sources that materially affect the task.

Do not ask for information that can be discovered. Ask only when a missing decision would materially change the requested outcome and cannot be inferred safely.

## Output

When a writable temporary filesystem exists, write the spec to:

```text
${TMPDIR:-/tmp}/spec/<task-slug>/SPEC.md
```

Create parent directories as needed. Keep scratch notes beside it rather than in chat. If no writable temporary filesystem exists, return the spec directly.

End with the spec path and any genuine unresolved blockers.

## Workflow

1. Read applicable instructions and inspect the current state before designing the future state.
2. Research mutable, niche, or externally defined behavior from authoritative current sources when it can change the spec.
3. Separate observed facts, user requirements, inferred constraints, and unresolved unknowns. Do not present guesses as facts.
4. Define the outcome and explicit non-goals. Preserve the user's requested architecture unless evidence proves it invalid.
5. Define only the interfaces, state, data, dependencies, constraints, failure behavior, security boundaries, or operational behavior relevant to this task.
6. State invariants and acceptance criteria as observable conditions.
7. Map each acceptance criterion to a verification method: test, command, inspection, measurement, review, or evidence check.
8. Define rollout, migration, rollback, or recovery only when the task can alter durable state or production behavior.
9. Remove implementation trivia that does not constrain correctness. Add implementation detail only where compatibility, safety, interoperability, or user intent requires it.
10. Re-read the request and current evidence. Tighten the spec until another capable agent could execute it without rediscovering key decisions.

## Spec shape

Use only sections that carry information. A typical spec is:

```markdown
# <Task>

## Outcome
## Current state
## Requirements
## Non-goals
## Design / behavior
## Invariants
## Failure and recovery
## Acceptance criteria
## Verification
## Rollout / rollback
## Open blockers
```

For research or writing tasks, replace engineering sections with the equivalent scope, evidence, source, structure, quality, and completion constraints.

## Rules

- A spec is a contract, not a transcript, brainstorm, or implementation log.
- Prefer observable behavior over vague adjectives.
- Prefer constraints and invariants over prescribing incidental implementation choices.
- Keep source evidence traceable when research affects a decision.
- Never weaken repository policy, user constraints, safety boundaries, or required gates.
- Do not silently expand scope.
- Do not implement merely because the implementation is obvious; `/spec` terminates at a verified specification.
