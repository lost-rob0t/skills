# Workspace verification schema (task/run v2)

`facts.kb` is the active task's trusted control projection:

```prolog
task(TaskId).
verification_context(TaskId, RunId).
repo_state(Head, WorktreeDigest).
research_required(Boolean).
requirement(Suite, command(ExactArgv)).
claim(Suite, requirement(Suite)).
```

Use `require --id <id> -- <command> [args...]` to add a command requirement
and its symbolic claim. An unrelated passing command cannot satisfy it.
`requirement_status/3` and `claim_status/3` return `verified`, `failed`,
`stale`, `conflict`, or `unknown` plus the observation/output/revision evidence. An
conflicting bindings block completion. An unsupported claim shape returns `unknown` and prevents completion. These
predicates execute no command; they query recorded evidence.

Machine evidence lives in `.prolog/runs/<RunId>/evidence.pl`:

```prolog
machine_observation(Task, Run, Id, command(Argv), exit(Status), OutputDigest, Head, Digest).
machine_brave_search(Task, Run, QueryDigest, ResultDigest, RetrievedAt, Head, Digest).
```

The generated verifier exposes `observation/6` and `brave_search/5` as views
restricted to the active task/run. For a repeated command at the same revision,
only its latest journal entry is eligible. A failed latest command prevents the
base gate from succeeding, even when an unrelated command passed. Older entries
remain in the journal. Captured stdout/stderr bytes are retained in
`observations/<Id>/`; their SHA-256 is over `stdout + NUL + stderr`.

Each init creates a UUID run, including repeat tasks and identical HEADs.
`init --force` archives the old controls before switching, never reuses its
observations, and resets the latest result to unknown. Each check retains its
result, controls and evidence snapshot under `checks/<CheckId>/`. Top-level
`result.json` is a convenience view of the latest operation, not historical
proof or a guarantee about a workspace modified since that check. It includes
task/run and revision/content hashes when checked. `check --task ID --run ID`
lets an automation reject an unexpected active context.

Initialization, check, and observation admission/commit are serialized. A command
that spans a task switch records evidence only in its original run and reports
an error; a command spanning a workspace change records an incomplete observation
and cannot provide current proof. Verification also rechecks workspace state
after SWI exits. All failures return nonzero; reports distinguish `pass`, `fail`,
`stale`, and `unknown`. Missing current observations are unknown.

The worktree digest excludes `.git/` and verifier runtime state (`facts.kb`,
`verify.pl`, `result.json`, `.facts.lock`, `sessions/`, `runs/`). Durable
`.prolog/kb/**` changes require fresh evidence. Git digests cover the binary
diff from HEAD and untracked nonignored files. Ignored build outputs are outside
this proof boundary. `verify.pl` is trusted host policy, recorded by hash and
snapshot; this is not a tamper-proof audit against a malicious local user.

## Migration

Legacy HEAD-only runs are historical evidence. They cannot be attributed to a
task/run automatically. `check` rejects controls without a v2 context. Explicit
`init --force --task ID` archives legacy controls under `runs/legacy-<UUID>/`
and starts empty evidence. Old `run-<HEAD>.pl` files stay untouched. Review and
reapply old task-specific rules using the scoped views; never copy old successful
observations into a new run. No automatic data migration occurs.
