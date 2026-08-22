---
name: dotfiles-workflow
description: Use the correct declarative source repository for managed OpenCode and Nix configuration. Dotfiles owns Home Manager, packages, MCP wiring, providers, permissions, plugins, and generated config. lost-rob0t/skills owns SKILL.md content and skill metadata. Work from a fresh default branch, use a feature branch, verify locally, open a PR, poll CI, and merge only when green.
compatibility: OpenCode with git, gh, Nix, and Home Manager
---

# Declarative configuration workflow

Change the repository that actually owns the requested state. Do not edit generated files in `$HOME`, and do not move source content into another repository merely because that repository deploys it.

## Ownership

Use `lost-rob0t/dotfiles` for:

- Nix and Home Manager configuration;
- package definitions and flake wiring;
- OpenCode MCP server registration;
- OpenCode providers, permissions, plugins, and generated configuration;
- deployment or lockfile updates for the skills flake input.

Use `lost-rob0t/skills` for:

- `SKILL.md` content;
- skill descriptions, metadata, instructions, examples, and support files;
- the skills flake's exported skill catalog and Home Manager module.

Treat `$HOME/.config/opencode/opencode.json` and installed paths under `$HOME/.config/opencode/skills` as generated state when Home Manager owns them.

## Repository workflow

For the repository that owns the change:

1. Locate or initialize the canonical checkout.
2. Make sure unrelated local changes will not be overwritten or committed.
3. Fetch and update its default branch with a fast-forward-only pull.
4. Create a fresh `feature/<short-purpose>` branch from that updated branch.
5. Edit the declarative source, never the generated target under `$HOME`.
6. Run the narrowest relevant checks first, then the repository's full required validation.
7. Commit and push the feature branch.
8. Open a pull request against the repository's default branch.
9. Poll the current PR head's CI/check status until every required check completes. Queued or running is not green.
10. If CI fails, inspect the failure, fix the branch, rerun local checks, push, and continue polling the new head.
11. Merge only when the current head is mergeable and all required checks are green. Prefer squash merge unless repository policy says otherwise.
12. Refresh the local default branch after merge.

## Dotfiles changes

The canonical dotfiles checkout is `$HOME/.dotfiles`, with default branch `master`:

```sh
cd "$HOME/.dotfiles"
git fetch origin
git switch master
git pull --ff-only origin master
git switch -c feature/<short-purpose>
```

After editing, rebuild the affected Home Manager profile.

### Home Manager target resolution

Keep the known desktop target for the original workflow. When running as another Unix user, try the conventional `user@hostname` Home Manager target before asking for configuration details:

```sh
if [ "${USER:-}" = "unseen" ]; then
  hm_target='unseen@desktop'
else
  hm_host="$(hostname -s 2>/dev/null || hostname 2>/dev/null || true)"

  if [ -z "${USER:-}" ] || [ -z "$hm_host" ]; then
    echo 'Cannot infer Home Manager user/hostname target.' >&2
    exit 2
  fi

  hm_target="${USER}@${hm_host}"
fi

nix run github:nix-community/home-manager/release-26.05 -- switch --flake ".#${hm_target}"
```

For `$USER=unseen`, preserve `unseen@desktop`; do not replace it with a guessed hostname-derived target.

For any other `$USER`, first try `$USER@$(hostname -s)`. If that target does not exist, the checkout uses a different Home Manager naming convention, or the machine is managed by a different activation workflow, stop guessing and prompt the user to describe their configuration/rebuild workflow and target name. Do not silently fall back to arbitrary flake attributes.

Distinguish target-discovery failure from an actual configuration failure. If the inferred target resolves but evaluation, build, or activation fails because of the change being tested, debug that failure normally instead of asking the user how Home Manager works.

For OpenCode MCP/config changes, verify the generated OpenCode behavior after activation instead of assuming evaluation was sufficient.

## Skill changes

The canonical skills checkout is `$HOME/skills`. If it does not exist, initialize it by cloning the repository there:

```sh
if [ ! -d "$HOME/skills/.git" ]; then
  if [ -e "$HOME/skills" ]; then
    echo "$HOME/skills exists but is not a git checkout" >&2
    exit 1
  fi
  git clone git@github.com:lost-rob0t/skills.git "$HOME/skills"
fi

cd "$HOME/skills"
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c feature/<short-purpose>
```

Edit the relevant `SKILL.md`, support files, or the skills flake in `$HOME/skills`. Validate the skills repository, push the branch, open a PR against `main`, poll CI, and merge only when green.

If the shipped skill revision is pinned by dotfiles, update dotfiles only after the skill PR merges. That second change is deployment metadata or a flake lock/input update. Do not duplicate the skill body in dotfiles.

## Routing examples

```text
add/change MCP server
  -> $HOME/.dotfiles
  -> Nix/Home Manager source
  -> resolve Home Manager target
  -> rebuild + verify
  -> PR + green CI + merge

edit/create SKILL.md
  -> $HOME/skills (clone if absent)
  -> skill source
  -> validate skills flake
  -> PR + green CI + merge
  -> update dotfiles flake input/lock if deployment needs the new revision
  -> resolve Home Manager target
  -> rebuild + verify
  -> PR + green CI + merge
```

## Guardrails

- Never force-push or rewrite `master` or `main`.
- Never merge while CI is red, queued, pending, or stale for an older commit.
- Never discard unrelated local work to make the workflow convenient.
- Never bypass declarative ownership by hand-editing generated OpenCode configuration or installed skill paths.
- Never edit a skill's durable source in dotfiles.
- If `$HOME/skills` exists but is not the expected Git checkout, stop rather than deleting or replacing it.
- If Home Manager target inference fails for a user other than `unseen`, ask for that user's actual workflow instead of guessing repeatedly.
- If a rebuild exposes a pre-existing unrelated failure, distinguish it clearly from failures introduced by the feature branch.
- Prefer one coherent feature branch and PR per repository change.
