---
name: dotfiles-workflow
description: Edit the declarative source that actually owns an agent or system configuration. Use for dotfiles, Nix/Home Manager, MCP registration, providers, permissions, plugins, packages, generated config, or skill deployment. Discover the current user's configuration owner instead of assuming the author's dotfiles.
compatibility: Agent Skills-compatible coding agent with git; Nix/Home Manager only when the user's configuration uses them
---

# Declarative configuration workflow

## Goal

Change configuration at its durable declarative source, verify the generated/runtime behavior, and avoid coupling the user to the author's machine.

## Input

- the requested configuration change;
- the current user's runtime and configuration source;
- the owning repository when configuration is version controlled.

## Ownership

First discover what owns the requested state.

- Edit a user's actual dotfiles/config repository for packages, MCP registration, providers, permissions, plugins, or generated runtime config.
- Edit this skills repository for durable `SKILL.md` content and its support files.
- Treat generated files under `$HOME/.config`, installed skill directories, and similar deployment targets as outputs when another source manages them.

Do not require `lost-rob0t/dotfiles` for another user. State required dependencies, inspect the user's existing setup, and configure that setup when the user requested it and tooling permits. Document non-obvious setup without bloating the skill.

## Workflow

1. Identify the declarative owner and required dependencies.
2. Inspect the real source before editing it; preserve its conventions.
3. If the capability is absent, configure the user's existing system when authorized, otherwise provide the minimum setup required.
4. Protect unrelated local changes.
5. Update the repository's default branch with a fast-forward-only pull when appropriate.
6. Create a fresh feature branch for the coherent change.
7. Edit the declarative source, never only its generated target.
8. Run the narrowest useful validation, then required repository checks.
9. Verify generated/runtime behavior after activation or deployment.
10. Commit, push, and open a PR when the repository workflow uses PRs.
11. Merge only when the current head is mergeable and required checks are green.

## Home Manager

When the user's setup uses Home Manager, discover its flake target or activation workflow.

A conventional target may be tried as:

```sh
hm_host="$(hostname -s 2>/dev/null || hostname 2>/dev/null || true)"
hm_target="${USER:?USER is unset}@${hm_host:?hostname unavailable}"
```

If that target does not exist, stop guessing and inspect the flake/configuration or ask for the actual target. Distinguish target discovery failure from a real evaluation/build failure.

### Owner compatibility

For the original `unseen` environment only:

- `lost-rob0t/dotfiles` at `$HOME/.dotfiles` is the canonical personal configuration source;
- Home Manager target `unseen@desktop` is authoritative and must not be replaced with a hostname guess;
- `lost-rob0t/skills` at `$HOME/skills` is the canonical skill source.

This compatibility path is an optimization for that environment, not a dependency imposed on other users.

## Rules

- Never force-push or rewrite a protected/default branch.
- Never discard unrelated user work.
- Never merge red, queued, pending, or stale CI as though it were green.
- Never hand-edit generated state as the durable fix when a declarative source owns it.
- Never invent a user's config path, manager, flake target, hostname, or dependency.
- Prefer one coherent branch/PR per repository change.
