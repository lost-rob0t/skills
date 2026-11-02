---
name: project-resume
description: resume, handoff, prolog, todos, project-kb, session-state
license: MIT
---

# Skill: project-resume

## Goal

Resume a repository session from its durable `.prolog/` state instead of
prose handoff files: the LAST handoff, active TODOs, recent work, and the
knowledge-base summary — printed and enforced by one script.

## Input

The current repository (a git tree containing `.prolog/`), or a path to
one. No arguments means: the working directory's repository.

## Output

The enforced resume view, produced by
`scripts/prolog-resume <repo-path>`:

1. LAST handoff — facts from `.prolog/handoff.pl` (goal, state,
   next_action, blockers, coordinates, written).
2. ACTIVE todos — `todo(Status, Id, Text)` with status `active`/`next`
   from `.prolog/runs/*.pl`.
3. RECENT work — the newest `obs(Id, Text)` entries across run journals.
4. KNOWLEDGE — `.prolog/kb/` module list with fact counts.

Exit codes are the enforcement contract:

- `0` — state found and printed; proceed with `next_action`.
- `2` — no `.prolog/` at all: initialize per the `prolog-project-kb`
  skill (`prolog-verify init`) before resuming.
- `3` — `.prolog/` exists but NO handoff: write `.prolog/handoff.pl`
  (see `prolog-project-kb`) before claiming to resume anything.

A staleness warning is printed (not fatal) when a run journal is newer
than the handoff: the TODOs and observations outrank the handoff's
`next_action` until a fresh handoff is written.

## Rules

- `/resume` MUST run the script and act on its exit code; never
  reconstruct state from memory when the script exits non-zero.
- The handoff is `.prolog/handoff.pl` — flat `handoff(Key, Text)` facts,
  last-write-wins, committed like KB files. Org/Markdown handoff files
  are superseded: do not create new ones for repositories using
  `.prolog/`.
- Selection of what to do next follows TODO state rules from the
  `prolog-project-kb` skill; this skill only restores and verifies view
  state.
