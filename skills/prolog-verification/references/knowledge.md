# Durable Prolog knowledge

The long-term store uses SWI-Prolog `library(persistency)` through the trusted `scripts/knowledge-store.pl` helper. Agents pass data as argv; they do not generate or consult arbitrary executable Prolog to mutate the database.

## Record model

Each record has:

```text
id, scope, owner, kind, key, value, source, status, created_at, updated_at
```

Scopes:

- `session`: current agent/session knowledge; requires an explicit session id;
- `project`: default, shared across worktrees for the same repository identity;
- `global`: cross-project knowledge; use sparingly.

Applicable recall precedence is `session -> project -> global`. If the same `(kind, key)` exists in more than one applicable tier, the narrower tier wins.

Kinds:

- `memory`: reusable factual/project context;
- `bug`: a known defect that remains relevant until resolved;
- `failure_path`: a known bad approach, precondition, or sequence that should not be repeated;
- `invariant`: a durable rule expected to remain true;
- `decision`: an accepted design/API/behavior decision;
- `workaround`: a temporary safe path around a defect or constraint;
- `warning`: important operational or verification hazard.

Statuses are `active`, `resolved`, and `superseded`. Only active records are projected into `.prolog/knowledge.kb` by default.

## Commands

```text
prolog-verify remember --kind bug --key cache-stale --value "Cache must be invalidated when HEAD changes"
prolog-verify recall --query cache --json
prolog-verify recall --kind failure-path --json
prolog-verify resolve k-<id>
prolog-verify supersede k-<id>
prolog-verify forget k-<id>
prolog-verify context
```

`remember` upserts on `(scope, owner, kind, key)`. Prefer stable semantic keys over timestamps or issue prose.

## What belongs in long-term knowledge

Store facts that save future reasoning or prevent repeated failure: a recurring bug signature, a verified workaround, a repository invariant, a test command specific to the project, a dangerous recovery path, an architectural decision, or a stable dependency relationship.

Do not store transient command noise, whole logs, large source excerpts, speculative diagnoses, secrets, credentials, or personal/sensitive data. Store a compact conclusion and provenance; keep bulky evidence in its authoritative source.

## Proof boundary

Durable knowledge can answer "what have we learned before?" It cannot answer "did the current tree pass?" without fresh current-state evidence. `facts.kb` and machine observations remain the proof boundary. This separation prevents an old memory such as "tests pass" from certifying a changed worktree.
