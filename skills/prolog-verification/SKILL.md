---
name: prolog-verification
description: prolog, verification, evidence, invariants, worktrees, brave, hooks
compatibility: Python 3, Git when verifying a repository, and SWI-Prolog for the final gate
---

# Prolog verification

## Goal

Verify agent changes against explicit facts and invariants stored under the current worktree's `.prolog/` directory.

## Required state

- `.prolog/facts.kb` contains task/control facts and current repository state.
- `.prolog/runs/<RunId>/evidence.pl` contains machine observations bound to task, run, HEAD and worktree digest.
- `.prolog/verify.pl` derives completion and owns task-specific PlUnit tests.
- `.prolog/result.json` is the latest view; immutable check snapshots and prior controls remain under `.prolog/runs/<RunId>/`.

Use the installed `prolog-verify` command when available. Otherwise run this skill's `scripts/prolog-verify.py` with Python 3.

## Workflow

1. Run `prolog-verify init --task <short-task-id>` in the worktree before recording evidence.
2. Bind each material claim to an executable requirement with `prolog-verify require --id <requirement> -- <command> [args...]`; add derived invariants to `verify.pl`. Never assert `verified(true)` or equivalent self-certifying facts.
3. Run real tests through `prolog-verify observe -- <command> [args...]`. The helper records the command, exit status, output digest, Git HEAD, and worktree digest in the active run journal.
4. When external discovery is required, run `prolog-verify brave --query <query>` so the fixed Brave CLI call and its result are recorded in the same run file. Use `record-brave` only when a compatible Brave tool already wrote its successful result to a file. Do not mark local-only work as research.
5. Run `prolog-verify check --task <short-task-id>` (and `--run <RunId>` when automating). Treat a missing, stale, timed-out, exceptional, or non-zero result as failure.

## Isolated verifier for huge non-git roots

`init`, `observe`, and `check` digest the whole work tree. In a git worktree that is cheap. Outside Git the walk skips vendored directories and stops at a 256 MiB cap on hashed bytes, failing closed instead of emitting a digest it cannot bound. For a large non-git root, run the verifier against a small dedicated work dir (for example `/tmp/opencode/<task>/`) and record that evidence path in the owning journal.

## Journal floors

After appending to a shared or hand-edited journal, gate it with this skill's `scripts/check-journal.pl`:

```sh
swipl scripts/check-journal.pl -- /abs/path/to/journal.pl [floors.pl]
```

Floors come from `.prolog/checks/floors.pl` when the journal lives under `.prolog/runs/<Run>/`, else `<journal-dir>/floors.pl`, else an explicit argument or `CHECK_JOURNAL_FLOORS`. Declare `min_clauses(<name>/<arity>, <min>).` and `required_entry(<template>).`. SWI-Prolog recovers past syntax-corrupted terms while loading, so predicate existence proves nothing; clause counts prove no region was silently skipped. Exit codes: 0 pass, 1 floor or entry failure, 2 usage or uncaught load error.

## Rules

- `init --force` starts a new isolated run and archives earlier controls; it never authorizes reuse of earlier evidence. Legacy HEAD-only state needs explicit reinitialization.
- Facts tied to an old HEAD or worktree digest are historical evidence, not current proof.
- Keep claimed requirements, machine observations, and derived conclusions distinct.
- `.prolog/runs/`, sessions, verifier control files, and result output are runtime state and are excluded from the worktree digest.
- Durable `.prolog/kb/**` project knowledge is not runtime state: changes there must affect the digest and require fresh verification evidence.
- Missing evidence is unknown, not proof of falsehood.
- Use `library(clpfd)` for integer constraints and `table/1` for recursive relations over cyclic graphs when needed.
- Keep verification pure. Filesystem, shell, and network effects belong in the helper, which projects their results into ground Prolog facts.
- Do not weaken or delete an invariant merely to make the gate pass.
- Fixed defects worth remembering: the verify template once resolved `facts.kb` and the run journal against the process CWD (the journal was silently skipped from any other directory), and the no-git digest once hashed an unbounded tree (a large workspace drove `init` past four minutes and 15 GiB RSS). State now resolves against `verify.pl` itself and the walk is skip-listed, capped, and fail-closed.

For the fact schema and extension rules, read [references/schema.md](references/schema.md).
