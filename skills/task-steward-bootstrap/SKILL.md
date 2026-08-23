---
name: task-steward-bootstrap
description: steward, bootstrap, a0, opencode, agents, adapters
compatibility: Agent Skills-compatible agent with filesystem access to install skill adapters safely
---

# Task Steward Bootstrap

## Goal

Install the portable Task Steward worker/bootstrap skills for Agent Zero, OpenCode, or generic Agent Skills clients without creating divergent copies.

## Input

Choose a runtime and scope:

- `agents`: generic Agent Skills; project `.agents/skills`, global `~/.agents/skills`
- `opencode`: project `.opencode/skills`, global `~/.config/opencode/skills`
- `agent-zero`: project `.a0proj/skills`, global `<A0_ROOT>/usr/skills`

Agent Zero global installation requires the real installation root. Never guess it.

## Workflow

1. Locate this canonical skills repository and verify both Task Steward packages exist.
2. Discover the requested project/install root instead of assuming an author's machine layout.
3. Run `scripts/bootstrap.py --dry-run` first.
4. Abort if any target exists and does not already resolve to the same canonical package.
5. Run without `--dry-run` to create only missing adapter links.
6. Configure runtime endpoints/tokens outside git.
7. Validate that the target runtime can discover `task-steward-worker` before dispatching work.

## Examples

```sh
python3 scripts/bootstrap.py --runtime agents --scope project --project-root "$PWD" --dry-run
python3 scripts/bootstrap.py --runtime opencode --scope global
python3 scripts/bootstrap.py --runtime agent-zero --scope global --a0-root /path/to/agent-zero
```

For a project that explicitly requires the legacy/local `.a0/skills` compatibility view, add `--compat-a0` with project scope. This is additive; Agent Zero's project discovery path remains `.a0proj/skills`.

## ChatGPT/operator use

Do not invent a ChatGPT filesystem path. A ChatGPT-style operator can consume the canonical skill contract directly and use the Task Steward HTTP assignment/receipt API. The portable contract is the integration point, not a client-specific duplicate.

## Rules

- Never overwrite, delete, or replace an unrelated skill tree.
- Never commit API tokens, A2A tokens, lease tokens, private endpoints, or generated runtime state.
- Adapter links point to canonical packages; edit the canonical package once.
- Missing runtime/project roots are blockers, not permission to guess paths.
