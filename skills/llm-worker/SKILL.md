---
name: llm-worker
description: remote-shell, opencode, ssh, project-isolation
compatibility: Unix, OpenSSH, OpenCode
---

# LLM Worker

## Goal

Run agent shell work on a project-isolated remote worker instead of the local
machine.

## Input

Configure `LLM_WORKER_HOST` and `LLM_WORKER_PROJECT`. The remote identity is
`PROJECT@HOST`; its project workspace is `~/repo`.

## Output

Remote stdout/stderr and the remote exit status are preserved by
`scripts/llm-worker-exec`.

## Workflow

```sh
export LLM_WORKER_HOST=worker.example
export LLM_WORKER_PROJECT=my-project
scripts/llm-worker-exec -- 'git status --short'
```

For OpenCode, run `scripts/install-opencode-bash-tool`. It installs a custom
`bash` tool that intentionally shadows OpenCode's built-in bash tool and routes
commands through this skill.

Prefer running OpenCode entirely on the worker when local file-edit tools and
remote shell state would otherwise diverge.

## Rules

- Fail closed when host or project is missing.
- Never infer a remote identity from private infrastructure.
- Keep credentials in SSH agent/config or runtime secret stores, never the skill.
- The project user's home and `~/repo` are owned by that project identity.
- Use `nix-remote-build` for builds that must return Nix outputs locally.
