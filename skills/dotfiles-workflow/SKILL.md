---
name: dotfiles-workflow
description: dotfiles, declarative-config, nix, home-manager, mcp, skill-updates, plugins
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
6. Create a fresh Gitflow-style `feature/<short-name>` branch for the coherent change.
7. Edit the declarative source, never only its generated target.
8. Run the narrowest useful validation, then all required repository checks.
9. Verify generated/runtime behavior after activation or deployment.
10. Review `git status`, `git diff`, and recent history; commit only intended changes.
11. Push the feature branch and open a pull request with `gh`; do not push directly to the default branch.
12. Wait for every required check with `gh pr checks <number> --watch`. Fix failures on the same branch and rerun validation.
13. Merge only after all required checks are green, then delete the remote feature branch.

## Home Manager

When the user's setup uses Home Manager, discover its flake target or activation workflow. Use this skill's `scripts/discover-home-manager.py --repo <configuration-root>` helper when the flake exports `homeConfigurations`. It evaluates the real exported names, accepts the conventional `USER@hostname` target only when it actually exists, and accepts a lone exported target without inventing a hostname-derived name.

If discovery is ambiguous or evaluation fails, stop guessing and inspect the flake/configuration or ask for the actual target. Distinguish target discovery failure from a real evaluation/build failure.

### Owner compatibility

For the original `unseen` environment only:

- `lost-rob0t/dotfiles` at `$HOME/.dotfiles` is the canonical personal configuration source;
- Home Manager target `unseen@flake` is authoritative and must not be replaced with a hostname guess;
- `lost-rob0t/skills` at `$HOME/skills` is the canonical skill source.

This compatibility path is an optimization for that environment, not a dependency imposed on other users.

## Skill updates

When asked to update, sync, or refresh agent skills that a flake input provides, the durable operation is one loop: update the owning flake input, run the flake's validation gate, publish the lockfile change, and re-activate the local configuration. Follow the repository's own publishing policy for the lockfile commit. Never hand-edit the installed skill directories; the lockfile plus activation is the update path.

### Owner compatibility

For the original `unseen` environment, `skill-sync` (from `lost-rob0t/dotfiles`, deployed on `$PATH` by Home Manager) performs this loop in one step:

```sh
skill-sync --dry-run    # print the plan without changing anything
skill-sync              # update skills input, gate on checks, publish, activate
```

It refuses dirty lockfiles and non-default branches, gates on flake checks before publishing, short-circuits when the input is already current, and supports `--input`, `--branch`, `--configuration`, `--no-push`, and `--no-activate`. Prefer `skill-sync` there instead of running `nix flake update` and `home-manager switch` separately.

## Rules

- Never force-push or rewrite a protected/default branch.
- Never discard unrelated user work.
- Never merge red, queued, pending, or stale CI as though it were green.
- Never hand-edit generated state as the durable fix when a declarative source owns it.
- Never invent a user's config path, manager, flake target, hostname, or dependency.
- Prefer one coherent branch/PR per repository change.
