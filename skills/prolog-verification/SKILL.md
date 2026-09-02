---
name: prolog-verification
description: prolog, verification, evidence, invariants, worktrees, brave, hooks
compatibility: Python 3, Git when verifying a repository, and SWI-Prolog for the final gate
---

# Prolog verification

## Goal

Verify agent changes against explicit facts and invariants stored under the current worktree's `.prolog/` directory.

## Required state

- `.prolog/facts.kb` contains requirements and machine-recorded observations.
- `.prolog/verify.pl` derives completion and owns task-specific PlUnit tests.
- `.prolog/result.json` is overwritten by the gate with the checked repository state and result.

Use the installed `prolog-verify` command when available. Otherwise run this skill's `scripts/prolog-verify.py` with Python 3.

## Workflow

1. Run `prolog-verify init --task <short-task-id>` in the worktree before recording evidence.
2. Add task-specific requirements and derived invariants to the two canonical files. Never assert `verified(true)` or equivalent self-certifying facts.
3. Run real tests through `prolog-verify observe -- <command> [args...]`. The helper records the command, exit status, output digest, Git HEAD, and worktree digest.
4. When external discovery is required, run `prolog-verify brave --query <query>` so the fixed Brave CLI call and its result are recorded together. Use `record-brave` only when a compatible Brave tool already wrote its successful result to a file. Do not mark local-only work as research.
5. Run `prolog-verify check`. Treat a missing, stale, timed-out, exceptional, or non-zero result as failure.

## Rules

- Facts tied to an old HEAD or worktree digest are historical evidence, not current proof.
- Keep claimed requirements, machine observations, and derived conclusions distinct.
- Missing evidence is unknown, not proof of falsehood.
- Use `library(clpfd)` for integer constraints and `table/1` for recursive relations over cyclic graphs when needed.
- Keep verification pure. Filesystem, shell, and network effects belong in the helper, which projects their results into ground Prolog facts.
- Do not weaken or delete an invariant merely to make the gate pass.
- Keep `.prolog/` local unless the repository explicitly adopts its verifier as maintained project code.

For the fact schema and extension rules, read [references/schema.md](references/schema.md).
