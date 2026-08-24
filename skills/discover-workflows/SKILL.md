---
name: discover-workflows
description: discover-workflows, bash-history, emacs-history, activitywatch, dotfiles
compatibility: Requires Python 3 and readable local shell/Emacs history files; ActivityWatch is optional.
---

# Discover Workflows

## Goal

Find repeated local workflows and turn them into concise, user-approved
dotfiles suggestions that reduce typing, navigation, or context switching.

## Workflow

1. Run `scripts/discover_workflows.py` from this skill directory. It reads
   Bash history, Emacs `savehist`/`recentf` data, and local ActivityWatch when
   available. Pass explicit paths when the user's configuration uses another
   history location.
2. Present the ranked suggestions with frequency evidence, the proposed
   dotfiles owner, and the expected benefit. Describe patterns, not raw history
   lines, prompts, URLs, credentials, or private paths.
3. Ask the user which suggestions to implement. Do not edit dotfiles merely
   because a command is frequent; frequency is evidence, not authorization.
4. For approved changes, follow the user's existing dotfiles ownership and
   literate-source rules. Validate the generated/runtime result and report any
   pre-existing failures separately.

## Rules

- Treat all history as sensitive local input. The script skips likely secrets,
  redacts paths, and emits only command families, safe Emacs command names,
  broad project roots, and application categories.
- Prefer a small alias, shell function, Emacs command/keybinding, project
  jump, or Qtile rule only when the repeated pattern is stable enough to name.
- Keep suggestions reversible and specific. Do not install packages, publish
  history, or modify a configuration without explicit user approval.
- If a history source is missing or ActivityWatch is unavailable, say so and
  continue with the sources that are present.
