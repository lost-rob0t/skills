---
name: rage
description: rage, issues, adadr, tdd, verification, ci, merge
compatibility: Agent Skills-compatible coding agent with git, issue/PR access, research tools, tests, and Org-mode work logs; requires the canonical adadr skill
---

# RAGE

Research-to-merge loop for one eligible issue at a time. Evidence outranks the inherited design. Load and follow the canonical `adadr` skill for architecture reasoning; do not replace it with a prompt-local approximation.

## Queue

1. Read repository instructions, roadmap/order issue, relevant epic, and open dependencies.
2. Select the first eligible issue by declared priority/order; blockers beat entertaining later work.
3. Do not create a parallel TODO when an issue already owns the work.
4. Keep one RAGE iteration scoped to one consumed issue unless repository policy says otherwise.

## Start evidence

Before research or implementation, enter the intended `rage/<issue>-<slug>` branch and initialize the run log with this skill's `scripts/init-run.py <issue> <slug> --repo <checkout>` helper. It records the actual full HEAD SHA and branch, refuses branch mismatches, and refuses to overwrite an existing run log unless an append is explicitly requested.

The resulting evidence is:

```org
* Run identity
- Consumed issue :: #NNN
- Branch :: =rage/<issue>-<slug>=
- RAGE start commit :: =FULL_40_CHARACTER_SHA=
```

The start SHA is immutable. Keep failed iterations and decisive evidence visible.

## ADADR architecture loop

Load `adadr` after queue selection/start evidence and before architecture or implementation work.

First execute ADADR's control-plane discovery gate. If the project has no defined/used research-design approval location or workflow, stop this issue and ask the user to choose **ADADR** or **Auto-RAGE**. Do not invent a directory and do not silently choose a mode.

- **ADADR**: `research -> explicit research approval -> RAGE produces design -> explicit design approval -> implementation`.
- **Auto-RAGE**: RAGE still performs the complete Analyze -> Design -> Adversarial review -> Decision -> Realize loop, but records its own software-design decision rather than waiting for human approval.

When a project already defines and uses a human-gated control plane, use ADADR mode without asking again. When a durable project instruction already selects Auto-RAGE, use that mode without asking again.

Research approval does not authorize implementation. Missing design approval in ADADR mode blocks code but must not idle unrelated eligible backlog work.

If research or implementation evidence disproves the architecture, return through ADADR rather than coding around the contradiction.

## TDD loop

For every defect or required behavior, establish the smallest deterministic test as early as repository policy permits. For bug-first repositories this regression is the entry evidence for ADADR.

1. write the smallest deterministic test;
2. run it and prove the expected red state;
3. after the ADADR decision gate authorizes realization, implement the minimum coherent change;
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

For ordinary implementation defects, fix within the approved/recorded design and rerun the gate.

For design-invalidating failures:

1. record the contradiction and evidence;
2. preserve the failed attempt's commit/PR identity;
3. stop extending that implementation attempt;
4. restart the canonical ADADR loop as a new numbered iteration;
5. write replacement tests before replacement implementation;
6. obtain any approval required by the selected mode;
7. run the complete exact-head gate again.

After merge, record the merge SHA, update/close the consumed issue and parent roadmap state, then re-read the queue before consuming another issue.

## Rules

- Repository `AGENTS.md`, branch policy, permissions, and gates remain authoritative.
- The canonical `adadr` skill is mandatory for RAGE architecture reasoning.
- Never invent an ADADR control-plane directory merely because one is missing.
- Never silently choose Auto-RAGE.
- Never autonomously cross an explicit research or design approval gate in ADADR mode.
- Never merge red, queued, pending, stale, or wrong-head CI.
- Never discard unrelated user work while abandoning a failed attempt.
- Never hide architecture changes inside implementation patches; update canonical design evidence first.
- Prefer a repository-local `skills/rage/SKILL.md` or `skills/adadr/SKILL.md` as an additive specialization; it may strengthen, not weaken, these gates.
