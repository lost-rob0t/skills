---
name: opencode-worker
description: opencode, worker, models, retries, isolation, automation
compatibility: Unix, Bash 4+, OpenCode 1.18.29+, Python 3 for model resolution
---

# OpenCode Worker

## Goal

Run OpenCode as a bounded Unix worker while preserving stream and exit-status semantics.

## Input

Pipe the complete prompt to `scripts/opencode-worker`. Select a logical model with
`--model`; `astra-medium` resolves through `config/models.tsv`. Use `--role` for
prompt metadata, not as an OpenCode CLI option.

## Output

Successful model output is written to stdout. Worker and OpenCode diagnostics go
to stderr. The final OpenCode status, or a signal-derived status, is preserved.
`--format text` maps to OpenCode `default`; `--format json` maps to `json`.

## Workflow

```sh
printf '%s\n' 'Review the current change.' |
  scripts/opencode-worker --model astra-medium --role reviewer --dir "$PWD"
```

Use `--mode isolated-mutate --dir <linked-worktree>` for tasks allowed to modify
files. Read-only mode injects a no-mutation instruction. Shared/main-worktree
mutation is rejected. Use `--lock-file <path>` to serialize workers sharing an
external resource.

## Rules

- Set finite `--max-retries` and `--max-delay`; defaults are 3 and 60 seconds.
- Retries apply only to recognizable rate-limit failures and honor bounded
  `Retry-After` values when observable.
- Forward only documented OpenCode options. Never emulate unsupported flags.
- Do not use `--continue` or `--session` for mutating work; use a fresh isolated
  worktree instead.
- Treat JSON mode as raw OpenCode JSON events, not a synthesized envelope.
- Empty prompts and prompts at or above `--max-prompt-bytes` (default 131072)
  are rejected before any model call; Linux caps one process argument near that
  size, so split large tasks instead of raising the limit.

See `references/contract.md` for options and model-map details.
