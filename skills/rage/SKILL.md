---
name: rage
description: rage, issues, research, design, tdd, verification, ci, merge
compatibility: Agent Skills-compatible coding agent with git, issue/PR access, research tools, tests, and Org-mode work logs
---

# RAGE

Research-to-merge loop for one eligible issue at a time. Evidence outranks the inherited design.

## Queue

1. Read repository instructions, roadmap/order issue, relevant epic, and open dependencies.
2. Select the first eligible issue by declared priority/order; blockers beat entertaining later work.
3. Do not create a parallel TODO when an issue already owns the work.
4. Keep one RAGE iteration scoped to one consumed issue unless repository policy says otherwise.

## Start evidence

Before research or implementation, create/update `rage/<work-log>.org` and record:

```org
* Run identity
- Consumed issue :: #NNN
- Branch :: =rage/<issue>-<slug>=
- RAGE start commit :: =FULL_40_CHARACTER_SHA=
```

The start SHA is immutable. Keep failed iterations and decisive evidence visible.

## Research and design

Research deeply enough to falsify assumptions. Inspect the start-commit implementation/tests, issue/dependencies/prior PRs, authoritative upstream docs/specs, lifecycle/concurrency/security/resource failure modes, and serious alternatives.

Before coding, write an explicit design covering ownership/state boundaries, invariants, failure/recovery behavior, resource bounds, rejected alternatives, compatibility constraints, and acceptance criteria mapped to tests.

If research disproves the requested architecture, update the issue/design instead of coding around the contradiction.

## TDD loop

For each required behavior:

1. write the smallest deterministic test;
2. run it and prove the expected red state;
3. implement the minimum coherent change;
4. rerun to green;
5. refactor only while relevant tests stay green.

Exercise meaningful happy, boundary, failure, lifecycle, concurrency, security, persistence, packaging, and regression paths. Never weaken assertions or manufacture execution-only tests to inflate coverage.

## Exact-head gate

At the candidate SHA, record and run:

- focused tests and important red/green evidence;
- the repository's complete required local gate;
- build/package checks;
- required security/fuzz/soak/benchmark gates;
- GitHub Actions for the exact current PR head.

Old-SHA green CI is stale. Merge only when acceptance criteria, local gates, mergeability, and required exact-head checks are green.

## Failure handling

For ordinary implementation defects, fix within the iteration and rerun the gate.

For design-invalidating failures:

1. record the contradiction and evidence;
2. preserve the failed attempt's commit/PR identity;
3. stop extending that implementation attempt;
4. restart research/design as a new numbered iteration;
5. write replacement tests before replacement implementation;
6. run the complete exact-head gate again.

After merge, record the merge SHA, update/close the consumed issue and parent roadmap state, then re-read the queue before consuming another issue.

## Rules

- Repository `AGENTS.md`, branch policy, permissions, and gates remain authoritative.
- Never merge red, queued, pending, stale, or wrong-head CI.
- Never discard unrelated user work while abandoning a failed attempt.
- Never hide architecture changes inside implementation patches; update design evidence first.
- Prefer a repository-local `skills/rage/SKILL.md` as an additive specialization; it may strengthen, not weaken, these gates.
