---
name: skill-edit
description: skills, editing, validation, gitflow, pull-request, CI
compatibility: Requires a Git checkout, the repository's validation commands, and GitHub CLI for pull requests.
---

# Edit and release skills

## Goal

Change reusable skills at their canonical source, validate the complete catalog,
and publish the change through gated Gitflow-style pull requests.

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
5. Push the feature branch and open a pull request with `gh`. Record the PR
   number and URL; do not push directly to the default branch.
6. Wait for every required check:

   ```sh
   gh pr checks <number> --watch
   ```

   Do not merge while checks are pending, failing, or stale. Fix failures on
   the same feature branch and rerun the complete validator.
7. Merge only after all required checks are green, then delete the remote
   feature branch.

## Rules

- Treat `skills/<name>/SKILL.md` as the one durable source for each skill.
- Use `skill-portability` to remove usernames, hosts, absolute paths, private
  services, and undeclared machine-specific assumptions before release.
- Validate every skill, not only the package being edited.
- Do not create or maintain an OpenCode-specific customization skill as a
  parallel source; client deployment is an adapter of the canonical package.
- Never commit credentials, tokens, generated caches, or unrelated work.
- Never merge red, pending, or stale CI.
