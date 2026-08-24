---
name: adadr
description: analyze, design, adversarial-review, decision-gate, realize
compatibility: Agent Skills-compatible software engineering agent with repository access, evidence gathering, and project approval metadata
---

# ADADR

Evidence-driven software architecture loop.

## Control-plane discovery gate

Before architecture work, discover the project's canonical location or workflow for research, design, approval state, and implementation promotion. Use repository instructions, project configuration, or current authoritative project state.

Do not invent a new `research/`, `design/`, `adadr/`, or approval directory just to satisfy this skill.

If no canonical location/workflow is defined, or the defined location is not actually used by the project, stop before Analyze and ask the user to choose one mode:

1. **ADADR** — human-gated software design. Research approval and design approval are explicit user gates.
2. **Auto-RAGE** — the coding worker runs the complete ADADR software-design loop itself and records the research, design, review, decision, and verification evidence without stopping for user approval.

Persist the selected mode in durable project instructions/configuration when authorized so future workers do not ask again. Never silently choose Auto-RAGE.

## Loop

### A — Analyze

Establish the real problem before proposing architecture. Inspect current code/tests, existing research/design, recent changes, runtime evidence, relevant specifications, and serious alternatives. Separate verified facts, inference, contradictions, and unknowns. For defects, prefer a deterministic failing regression as primary evidence.

### D — Design

Derive the smallest coherent design from the evidence. Define ownership and state boundaries, invariants, lifecycle, failure/recovery behavior, concurrency and resource bounds, security/authority boundaries, compatibility/migration constraints, acceptance criteria, and exact verification gates. Record rejected alternatives and why they lose.

### A — Adversarial review

Attack the design before coding. Construct counterexamples and inspect race, stale-state, partial-failure, cancellation, restart, security, provenance, compatibility, and operational failure cases. If the design fails, revise it and repeat this phase.

### D — Decision gate

In **ADADR mode**, use the project's real human approval state. Research approval authorizes design work only; design approval authorizes implementation within that scope only. Missing approval blocks implementation.

In **Auto-RAGE mode**, the worker may record its own software-design decision after adversarial review, but it must still produce the explicit decision record before implementation.

Never infer human approval from a merge, green CI, an existing file, or model confidence.

### R — Realize

Implement only the approved/recorded design using the repository's required implementation workflow. Keep changes traceable to design acceptance criteria. If implementation evidence disproves the design, preserve the evidence and return to Analyze rather than silently drifting architecture.

## Human-gated progression

`research -> explicit research approval -> RAGE produces design -> explicit design approval -> implementation`

## Auto-RAGE progression

`research -> design -> adversarial review -> recorded worker decision -> implementation`

## RAGE integration

When invoked by RAGE, ADADR owns control-plane discovery and architecture reasoning. RAGE owns queue selection, run identity, TDD discipline, exact-head verification, pull-request handling, merge gates, and backlog continuation.

## Rules

- Repository instructions and current evidence outrank remembered architecture.
- Bug-first/TDD-first repository policy may establish evidence before Analyze.
- Do not invent an ADADR directory/control plane when none exists.
- Do not silently choose Auto-RAGE.
- Do not hide architecture changes inside implementation patches.
- Prefer canonical project research/design artifacts when the repository defines them as authoritative.
