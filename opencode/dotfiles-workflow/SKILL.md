---
name: dotfiles-workflow
description: Use the user's dotfiles repository as the source of truth for OpenCode, Home Manager, Nix, desktop, and other managed configuration changes. Pull the latest dotfiles, work on a feature branch, rebuild and verify locally, open a PR, poll CI, and merge only when green. Never edit generated or Home Manager-owned files in place when their source lives in dotfiles.
compatibility: OpenCode with git, gh, Nix, and Home Manager
---

# Dotfiles workflow

For configuration that is owned by `lost-rob0t/dotfiles`, change the repository rather than editing the generated file in `$HOME` directly.

This includes OpenCode configuration managed by Home Manager. Treat `~/.config/opencode/opencode.json` as generated state when dotfiles owns it.

## Required workflow

1. Locate the dotfiles checkout, normally `~/.dotfiles`.
2. Make sure there are no unrelated local changes that would be overwritten or accidentally committed.
3. Fetch and update the default branch before starting work:

   ```sh
   cd ~/.dotfiles
   git fetch origin
   git switch master
   git pull --ff-only origin master
   ```

4. Create a fresh feature branch from the updated `master`:

   ```sh
   git switch -c feature/<short-purpose>
   ```

5. Edit the declarative source in dotfiles. Do not patch generated files under `$HOME` when Home Manager, Nix, Stow, or a literate source owns them.
6. Run the narrowest relevant checks first, then rebuild the affected Home Manager profile. For the desktop profile:

   ```sh
   nix run github:nix-community/home-manager/release-26.05 -- switch --flake '.#unseen@desktop'
   ```

7. Verify the resulting behavior after the rebuild. For OpenCode MCP changes, inspect the generated OpenCode configuration and run the relevant OpenCode MCP/status command rather than assuming Home Manager activation was sufficient.
8. Commit and push the feature branch.
9. Open a pull request against `master` with a concise description of the change and validation performed.
10. Poll the PR's CI/check status until all required checks complete. Do not treat queued or running checks as green.
11. If CI fails, inspect the failing job, fix the feature branch, rebuild/retest locally, push, and continue polling the new checks.
12. Merge only when the current PR head is mergeable and all required CI checks are green. Prefer squash merge unless the repository's current policy says otherwise.
13. After merge, update the local `master` with `git pull --ff-only origin master` so subsequent work starts from the shipped state.

## Guardrails

- Never force-push or rewrite `master`.
- Never merge while CI is red, queued, pending, or stale for an older commit.
- Never discard unrelated local work to make the workflow convenient.
- Never bypass the declarative source by hand-editing a Home Manager-managed target file.
- If a rebuild exposes a pre-existing unrelated failure, distinguish it clearly from failures introduced by the feature branch.
- Prefer one coherent feature branch and PR per configuration change.

## OpenCode configuration

When asked to add or change OpenCode MCP servers, skills, providers, permissions, plugins, or other configuration that dotfiles manages:

```text
request
  -> pull fresh dotfiles/master
  -> feature branch
  -> edit Nix/Home Manager source
  -> rebuild affected profile
  -> verify generated OpenCode behavior
  -> push + PR
  -> poll CI
  -> fix until green
  -> merge
```

Do not directly edit `~/.config/opencode/opencode.json` as the durable solution. The next Home Manager activation would replace it anyway, because apparently configuration files also enjoy reincarnation.
