---
name: prolog-project-kb
description: prolog, memory, todo, debugging, tools, knowledge
compatibility: SWI-Prolog and Git for repository work
---

# Prolog project KB

## Goal

Make repository work accumulate reusable symbolic knowledge while keeping per-run churn out of Git.

## State

Use `.prolog/kb/` for durable tracked knowledge and `.prolog/runs/<RunId>/` for task/run-local execution state. `prolog-verify init --task <id>` creates the run and writes its identity to `.prolog/facts.kb`.

The durable KB must be composed from many focused Prolog files. Do not impose a fixed ontology such as `tools.pl` or `debugging.pl`. Inspect the existing KB, discover the structure that best fits the project, and evolve/refactor it when needed. Keep one obvious loader such as `.prolog/kb/index.pl` so agents can consult the whole KB.

Run files are append/update execution journals, not durable project knowledge. Keep `.prolog/runs/` untracked with a local ignore mechanism when possible so TODO updates and observations do not dirty the repository.

## Handoffs

The LAST handoff lives in `.prolog/handoff.pl` as flat facts, one file per
repository, last-write-wins, committed like KB files (survives worktree
and session changes):

```prolog
handoff(goal, 'what this lane/repo is driving toward').
handoff(state, 'verified current state, facts not inference').
handoff(written, 'ISO-8601 timestamp').
handoff(next_action, 'the exact next step').
handoff(blockers, 'what blocks and what unblocks it').
handoff(coordinates, 'repos/hosts/branches/urls that matter').
```

Writing a handoff OVERWRITES the previous one — that is the point: the
resume view shows only the last handoff. Org/Markdown handoff files are
superseded for repositories using `.prolog/`; do not create new ones.
The `project-resume` skill and its `prolog-resume` script consume this
file (exit 3 when absent) together with run-journal TODOs, newest
observations, and the KB summary.

## Workflow

1. Before substantive work, consult the durable KB and the active task/run journal if present.
2. Represent the work as Prolog TODO state. Select an actionable TODO and mark it active before doing it.
3. Update the run file immediately when TODO state, blockers, dependencies, or observations change. Add newly discovered work instead of silently carrying it in model context.
4. Verify work with the repository's real checks and `prolog-verification` when file changes are involved. Mark TODOs done only after evidence exists.
5. Troubleshoot by querying Prolog over typed observations, candidate hypotheses and diagnostic requirements. Execute the selected tests, then query whether each finding is confirmed, rejected, conflicting, stale or unknown. Do not substitute a prose diagnosis for these queries.
6. Promote reusable verified discoveries into the durable KB: architecture, tool capabilities, useful scripts and commands, failure modes, root causes, fixes, invariants, dependencies, and recurring workflows.
7. Put promoted knowledge into the most appropriate existing KB file. Create or reorganize files when the current structure no longer models the project well.

## Rules

- No substantive work without current Prolog TODO state.
- No stale TODO state after a meaningful work transition.
- Prefer relations and reusable predicates over prose blobs.
- Preserve provenance or verification links when practical; do not promote guesses as facts.
- Do not turn the durable KB into a command log. Raw observations belong in the active run journal.
- Do not collapse the KB into one giant file; structure is project knowledge too.
- Query first, work, verify, then persist what future agents should know.

For scope, promotion, lifecycle and expert integration contracts, read [references/knowledge-contract.md](references/knowledge-contract.md).
