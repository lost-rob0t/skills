# Workspace verification schema

`facts.kb` is the task/control projection for the current workspace:

```prolog
task(TaskId).
repo_state(Head, WorktreeDigest).
research_required(Boolean).
```

Machine evidence is stored separately in `.prolog/runs/run-<HEAD>.pl`:

```prolog
observation(Id, command(Argv), exit(Status), OutputDigest, Head, WorktreeDigest).
brave_search(QueryDigest, ResultDigest, RetrievedAt, Head, WorktreeDigest).
```

The helper owns machine-evidence predicates. Agents may add task-specific predicates such as `requirement/2` or `supports/2`, but must not hand-write successful command or Brave evidence.

`verify.pl` loads `facts.kb` and the run file for the current `repo_state/2`, defines a semideterministic `complete/0`, and runs focused PlUnit tests. A useful extension pattern is:

```prolog
requirement_satisfied(Requirement) :-
    requirement(Requirement, _),
    supports(Observation, Requirement),
    observation(Observation, _, exit(0), _, Head, Digest),
    repo_state(Head, Digest).

complete :-
    base_complete,
    forall(requirement(Requirement, _),
           once(requirement_satisfied(Requirement))).
```

Do not infer that an unobserved condition is false. Represent an unresolved condition explicitly or make `complete/0` fail until evidence exists.

The worktree digest excludes `.git/` plus verifier runtime state (`facts.kb`, `verify.pl`, `result.json`, `.facts.lock`, `sessions/`, and `runs/`). It deliberately includes durable `.prolog/kb/**` files, so changing project knowledge requires fresh evidence. In Git repositories the digest covers the binary diff from `HEAD` plus untracked, non-ignored files outside those runtime paths.
