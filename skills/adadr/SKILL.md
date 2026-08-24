---
name: adadr
description: analyze, design, adversarial-review, decision-gate, realize
compatibility: Agent Skills-compatible engineering or research agent with repository access, evidence gathering, and project approval metadata
---

# ADADR

Evidence-driven architecture loop. Analysis may invalidate the inherited request; approval gates may block realization.

## Input

- one bounded problem, research question, defect, or design proposal;
- current repository instructions and authoritative state;
- existing research/design artifacts and approval evidence;
- tests, runtime evidence, specifications, and primary sources as applicable.

## Output

- explicit evidence and unknowns;
- a reviewable design with alternatives and acceptance criteria;
- an approval/decision state;
- implementation only when the required decision gate is satisfied.

## Loop

### A — Analyze

Establish the real problem before proposing architecture. Inspect current code/tests, existing research/design, recent changes, production evidence, relevant specifications, and serious alternatives. Separate verified facts, inference, contradictions, and unknowns. For defects, prefer a deterministic failing regression as primary evidence.

### D — Design

Derive the smallest coherent design from the evidence. Define ownership and state boundaries, invariants, lifecycle, failure/recovery behavior, concurrency and resource bounds, security/authority boundaries, compatibility/migration constraints, acceptance criteria, and exact verification gates. Record rejected alternatives and why they lose.

### A — Adversarial review

Attack the design before coding. Construct counterexamples and inspect race, stale-state, partial-failure, cancellation, restart, security, provenance, compatibility, and operational failure cases. Compare the proposal against existing architecture and current implementation. If the design fails, revise it and repeat this phase; never patch around a disproved design.

### D — Decision gate

Resolve the architecture state using the repository's real governance. Approval, implementation-slot state, and green validation are distinct.

- `APPROVED`: realization may proceed when all other gates pass.
- `REJECTED`: record evidence and return to Analyze if the problem still requires a solution.
- `PENDING` or absent required authority: stop realization; continue only non-conflicting eligible work.
- `SUPERSEDED`: follow the replacement artifact.

Never infer approval from a merge, green CI, an existing file, or model confidence.

### R — Realize

Implement only the approved design, using the repository's required implementation workflow. Keep changes traceable to design acceptance criteria. If implementation evidence disproves the design, stop, preserve the evidence, return to Analyze, and start a new iteration rather than silently drifting architecture.

## Research → design → implementation governance

When a project has separate research and design authority, use this strict progression:

1. research reaches reviewable evidence;
2. required human/operator research approval is recorded;
3. a RAGE worker may derive the design from that approved research;
4. required human/operator design approval is recorded;
5. only then may implementation begin.

A research approval authorizes design work, not implementation. A design approval authorizes realization within the approved scope, not unrelated architecture changes.

## RAGE integration

When invoked by RAGE, ADADR owns the architecture reasoning phases while RAGE owns queue selection, run identity, TDD discipline, exact-head verification, PR/merge handling, and backlog continuation. RAGE must load and follow this skill instead of reproducing a weaker prompt-local ADADR variant.

## Rules

- Repository instructions and current evidence outrank remembered architecture.
- Bug-first/TDD-first repository policy may establish evidence before Analyze; ADADR does not weaken it.
- Do not conceal architecture changes inside implementation patches.
- Do not proceed through a required human approval gate autonomously.
- Prefer canonical project research/design artifacts over issue or PR prose when the repository defines them as authoritative.
