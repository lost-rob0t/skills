---
name: opencode-yolo
description: opencode, yolo, auto-approve, tmpfs, prolog, spec, rlm, starintel
compatibility: Linux with OpenCode and a writable tmpfs such as /dev/shm or XDG_RUNTIME_DIR
---

# OpenCode YOLO + Prolog tmpfs context

Use this skill when an autonomous OpenCode session should keep specification and Prolog-RLM working context in memory rather than the repository.

The canonical launcher is `scripts/opencode-yolo`. It uses OpenCode's supported `--auto` flag while accepting `--yolo` as a wrapper alias. Explicit OpenCode `deny` rules still win; this wrapper does not bypass them.

## Context contract

The launcher starts in `${OPENCODE_WORKSPACE:-$HOME/Documents/Projects/starintelV4}` and exposes this project-visible path:

```text
./prolog-tmp-spec-context/
```

Its backing directory MUST live on a verified `tmpfs`. The launcher prefers `OPENCODE_TMPFS_ROOT`, then `XDG_RUNTIME_DIR`, then `/dev/shm`, and fails closed when none is a writable tmpfs.

During the session it exports:

- `PROLOG_TMP_SPEC_CONTEXT` — project-visible context path;
- `PROLOG_TMP_SPEC_CONTEXT_REAL` — real tmpfs backing path;
- `STARINTEL_V4_ROOT` — selected workspace root;
- `STARINTEL_SPEC_PROMPT` — `spec.prompt.org` when present;
- `TMPDIR` — a session-local tmp directory inside the same tmpfs.

`context.prolog` is created at the context root before OpenCode starts. Treat it as the live symbolic state for the run: requirements, verified observations with provenance, hypotheses, decisions, todo/completed state, test evidence, and verification results. Keep it compact; source trees, logs, patches, and transcripts remain outside the KB and are referenced by path/SHA when needed.

The context is ephemeral by default and is removed when OpenCode exits. Set `OPENCODE_KEEP_PROLOG_CONTEXT=1` only when the user explicitly wants post-run inspection; it still remains on tmpfs and is not durable across reboot.

## StarIntel bootstrap

When `spec.prompt.org` exists in the workspace, the launcher supplies a short initial OpenCode prompt requiring the agent to:

1. read `spec.prompt.org` first;
2. load `/spec`, `prolog-reasoning`, and applicable `starintel*` skills;
3. use `context.prolog` in a Prolog-RLM loop: query -> identify missing fact -> inspect/tool/subagent -> assert verified fact with provenance -> query again;
4. write scratch specifications and symbolic context only under `PROLOG_TMP_SPEC_CONTEXT`;
5. keep durable implementation and source-repository changes in the normal workspace/repositories, not in the tmpfs context.

If no `spec.prompt.org` exists, the tmpfs and skill contract still apply.

## Invocation

From the skill directory:

```sh
./scripts/opencode-yolo --yolo
```

or launch a different workspace:

```sh
OPENCODE_WORKSPACE="$HOME/Documents/Projects/starintelV4" ./scripts/opencode-yolo --yolo
```

All unrecognized arguments are forwarded to OpenCode. The wrapper removes its own `--yolo` alias and invokes OpenCode with `--auto` exactly once.

## Rules

- Never silently fall back from tmpfs to disk.
- Never overwrite an existing real `prolog-tmp-spec-context` directory or unrelated symlink in the workspace.
- A stale broken context symlink created by an earlier session may be removed.
- Do not persist `context.prolog` into git unless the user explicitly asks to promote selected facts into a durable specification.
- Prolog verification is evidence, not a permission bypass.
- Explicit OpenCode denies remain authoritative even in YOLO/auto mode.
