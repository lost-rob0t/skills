# Worker contract

`opencode-worker` reads stdin to EOF before launching `opencode run`. It accepts
`--model`, `--variant`, `--agent`, `--dir`, `--session`, `--continue`, `--fork`,
`--attach`, `--title`, `--role`, `--format text|json`, `--max-retries`,
`--max-delay`, `--max-prompt-bytes`, `--lock-file`, and
`--mode readonly|isolated-mutate`.

Logical models are tab-separated rows in `config/models.tsv`:

```text
logical-name<TAB>provider/model<TAB>optional-variant
```

The resolver probes `opencode models` and fails if the mapped ID is unavailable.
An explicit provider/model ID may also be supplied and is probed the same way.
`OPENCODE_BIN` and `OPENCODE_WORKER_MODEL_CONFIG` support testing and deployment.

The prompt is forwarded as a single `opencode run` argument, and Linux rejects
any single argument near 128 KiB (`MAX_ARG_STRLEN`). A prompt that is empty or
at or above `--max-prompt-bytes` (default 131072) is rejected with exit 2 before
any model call; the limit can only be lowered, since raising it fails at exec
time. Split large tasks into smaller prompts.

Retries recognize exit failures containing HTTP 429, `rate limit`, or
`too many requests`. `Retry-After` integer seconds are preferred; otherwise the
delay doubles from one second. Every delay is capped by `--max-delay`.
