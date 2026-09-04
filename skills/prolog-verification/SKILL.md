---
name: prolog-verification
description: prolog, verification, evidence, invariants, durable-memory, known-bugs, failure-paths, worktrees, brave, hooks
compatibility: Python 3, Git when verifying a repository, and SWI-Prolog for verification and durable knowledge
---

# Prolog verification

## Goal

Use Prolog as both a fail-closed verifier for current work and a durable symbolic knowledge layer that accumulates reusable project/global memory across sessions.

Do not mix the two authorities:

- `.prolog/facts.kb` is current-work evidence tied to the exact HEAD/worktree digest.
- the durable knowledge DB stores historical/reusable memory such as known bugs, failure paths, invariants, decisions, workarounds, and warnings;
- `.prolog/knowledge.kb` is a generated read-only projection of applicable durable knowledge for Prolog reasoning. It is context, not proof that the current tree is correct.

The durable DB defaults to `$XDG_DATA_HOME/prolog-verification/knowledge.db` (normally `~/.local/share/prolog-verification/knowledge.db`). Override it with `PROLOG_VERIFY_DB` when an agent/runtime needs an isolated store.

Use the installed `prolog-verify` command when available. Otherwise run this skill's `scripts/prolog-verify.py` with Python 3.

## Durable knowledge loop

Before repeating investigation or choosing a fix, query what is already known:

```text
prolog-verify recall --query <term> --json
prolog-verify recall --kind bug --json
prolog-verify recall --kind failure-path --json
```

Record reusable knowledge as soon as it is established:

```text
prolog-verify remember --kind bug --key <stable-name> --value <concise-fact>
prolog-verify remember --kind failure-path --key <stable-name> --value <what-failed-and-why>
prolog-verify remember --kind invariant --key <stable-name> --value <must-always-hold>
prolog-verify remember --kind decision --key <stable-name> --value <chosen-contract>
prolog-verify remember --kind workaround --key <stable-name> --value <temporary-safe-path>
prolog-verify remember --kind memory --key <stable-name> --value <reusable-context>
```

Project scope is the default. Use `--scope global` only for knowledge that genuinely applies across repositories. Session scope requires `--session-id`. Project identity is derived from the repository identity rather than the current worktree path, so multiple worktrees share the same project memory.

When a bug/failure is fixed, retain the history but remove it from active context:

```text
prolog-verify resolve <record-id>
```

Use `supersede` when a newer fact replaces an older one. Use `forget` only for incorrect, sensitive, or intentionally deleted knowledge.

Do not store credentials, secrets, raw transcripts, large source dumps, or unverified guesses. Record compact facts with useful provenance. A repeated key within the same scope/kind is an upsert, so update the existing knowledge instead of creating semantic duplicates.

## Verification state

- `.prolog/facts.kb` contains requirements and machine-recorded observations.
- `.prolog/knowledge.kb` contains the generated active durable-knowledge projection.
- `.prolog/verify.pl` derives completion and owns task-specific PlUnit tests.
- `.prolog/result.json` is overwritten by the gate with the checked repository state and result, including the knowledge projection digest.

## Verification workflow

1. Recall durable knowledge relevant to the task before rediscovering known failure modes.
2. Run `prolog-verify init --task <short-task-id>` in the worktree before recording evidence.
3. Run `prolog-verify context` to refresh `.prolog/knowledge.kb` when durable knowledge should participate in task reasoning. `check` refreshes it automatically when a durable DB exists.
4. Add task-specific requirements and derived invariants to the canonical verifier files. Never assert `verified(true)` or equivalent self-certifying facts.
5. Run real tests through `prolog-verify observe -- <command> [args...]`. The helper records the command, exit status, output digest, Git HEAD, and worktree digest.
6. When a failure exposes a reusable bad path, record a concise `failure-path`; when it exposes a product defect, record a `bug`. Do not promote every transient command failure into long-term memory.
7. When external discovery is required, run `prolog-verify brave --query <query>` so the fixed Brave CLI call and its result are recorded together. Use `record-brave` only when a compatible Brave tool already wrote its successful result to a file. Do not mark local-only work as research.
8. Run `prolog-verify check`. Treat a missing, stale, timed-out, exceptional, or non-zero result as failure.
9. Resolve/supersede durable records that the completed work makes obsolete instead of deleting the history.

## Rules

- Current proof must come from current machine observations. Durable memory can constrain or guide verification but cannot impersonate fresh evidence.
- Facts tied to an old HEAD or worktree digest are historical evidence, not current proof.
- Keep claimed requirements, machine observations, durable knowledge, and derived conclusions distinct.
- Missing evidence is unknown, not proof of falsehood.
- Use `library(clpfd)` for integer constraints and `table/1` for recursive relations over cyclic graphs when needed.
- Keep verification pure. Filesystem, shell, and network effects belong in the helper, which projects their results into ground Prolog facts.
- Do not weaken or delete an invariant merely to make the gate pass.
- Keep `.prolog/` local unless the repository explicitly adopts its verifier as maintained project code.

For the fact schema and extension rules, read [references/schema.md](references/schema.md). For durable memory semantics, read [references/knowledge.md](references/knowledge.md).
