---
name: prolog-project-kb
description: prolog, memory, todo, debugging, tools, knowledge
compatibility: SWI-Prolog and Git for repository work
---

# Prolog project KB

## Goal

Make repository work accumulate reusable symbolic knowledge while keeping per-run churn out of Git.

## State

Use `.prolog/kb/` for durable tracked knowledge and `.prolog/runs/run-<HEAD>.pl` for the current HEAD's local execution state.

The durable KB must be composed from many focused Prolog files. Do not impose a fixed ontology such as `tools.pl` or `debugging.pl`. Inspect the existing KB, discover the structure that best fits the project, and evolve/refactor it when needed. Keep one obvious loader such as `.prolog/kb/index.pl` so agents can consult the whole KB.

Run files are append/update execution journals, not durable project knowledge. Keep `.prolog/runs/` untracked with a local ignore mechanism when possible so TODO updates and observations do not dirty the repository.

## Workflow

1. Before substantive work, consult the durable KB and the current `run-<HEAD>.pl` if present.
2. Represent the work as Prolog TODO state. Select an actionable TODO and mark it active before doing it.
3. Update the run file immediately when TODO state, blockers, dependencies, or observations change. Add newly discovered work instead of silently carrying it in model context.
4. Verify work with the repository's real checks and `prolog-verification` when file changes are involved. Mark TODOs done only after evidence exists.
5. Promote reusable verified discoveries into the durable KB: architecture, tool capabilities, useful scripts and commands, failure modes, root causes, fixes, invariants, dependencies, and recurring workflows.
6. Put promoted knowledge into the most appropriate existing KB file. Create or reorganize files when the current structure no longer models the project well.

## Rules

- No substantive work without current Prolog TODO state.
- No stale TODO state after a meaningful work transition.
- Prefer relations and reusable predicates over prose blobs.
- Preserve provenance or verification links when practical; do not promote guesses as facts.
- Do not turn the durable KB into a command log. Raw observations belong in `run-<HEAD>.pl`.
- Do not collapse the KB into one giant file; structure is project knowledge too.
- Query first, work, verify, then persist what future agents should know.
