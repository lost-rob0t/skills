---
name: forgejo-skill-edit
description: skills, forgejo, editing, validation, gitflow, pull-request, CI
compatibility: Requires a Git checkout of the skills repository, its validation commands, and the `tea` CLI with a login for `git.starintel.actor`.
---

# Edit and release skills on Forgejo

## Goal

Forgejo (`git.starintel.actor`) variant of `skill-edit`: change reusable
skills at their canonical source, validate the complete catalog, and publish
the change through gated Gitflow-style pull requests on the Forgejo host.

Use this skill when the skills repository remote points at
`git.starintel.actor`. Use `skill-edit` (GitHub CLI) only when the remote
is `github.com`. The `git` skill documents host routing.

## Workflow

1. Locate the canonical skills repository and read its `AGENTS.md`. Edit the
   repository source first. Never make a durable edit in an installed
   OpenCode, Claude, Codex, or other client copy.
2. Keep each skill under `skills/<name>/SKILL.md`; update the canonical flake
   catalog, README catalog, and CI export/package checks when adding a skill.
3. Run the complete validator before committing:

   ```sh
   bash scripts/validate-skills
   git diff --check
   ```

4. Review `git status`, `git diff`, and recent history. Create a fresh
   Gitflow-style branch named `feature/<short-name>`, stage only the intended
   skill and catalog changes, and commit them.
5. Confirm the Forgejo login with `tea login list` (use
   `--login <name>` for `git.starintel.actor`), push the feature branch, and
   open a pull request with `tea pr create`. Record the PR number and URL;
   do not push directly to the default branch.
6. Wait for every required check before merging. On Forgejo, inspect the
   pull request state (`tea pr view <number>`) and the commit status for the
   head SHA through the Forgejo API. Do not merge while checks are pending,
   failing, or stale. Fix failures on the same feature branch and rerun the
   complete validator.
7. Merge only after all required checks are green (`tea pr merge`), then
   delete the remote feature branch.

## Rules

- Treat `skills/<name>/SKILL.md` as the one durable source for each skill.
- Use `skill-portability` to remove usernames, hosts, absolute paths, private
  services, and undeclared machine-specific assumptions before release.
- Validate every skill, not only the package being edited.
- Do not create or maintain an OpenCode-specific customization skill as a
  parallel source; client deployment is an adapter of the canonical package.
- Never commit credentials, tokens, generated caches, or unrelated work.
- Never merge red, pending, or stale CI.
