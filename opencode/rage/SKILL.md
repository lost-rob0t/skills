---
name: rage
description: Run an issue-driven RAGE loop: consume the next eligible GitHub issue, record the immutable start commit in an Org work log, research deeply enough to challenge the inherited design, derive architecture from evidence, implement the selected slice, verify the exact candidate head, and merge only when the complete gate passes. If the design is disproven, preserve evidence, discard that implementation attempt, and restart from research/design.
compatibility: OpenCode with git, gh, web research, repository tests, and Org-mode work logs
---

# RAGE

RAGE is a research-to-merge workflow for work that deserves more than "try code, stare at CI, add another conditional." It is issue-driven and evidence-driven.

The repository's GitHub Issues are the work queue. An epic is normally a queue/container. One RAGE iteration consumes one eligible issue unless the repository explicitly defines a different atomic unit.

## 1. Consume the issue queue first

Before creating a design or implementation branch:

1. Read the repository's roadmap/order issue when one exists.
2. Read the relevant epic and all open child issues that can affect ordering.
3. Select the first open issue whose declared dependencies are satisfied, honoring explicit priority and ordering rules.
4. Do not skip regression blockers merely because a later feature is more entertaining.
5. Do not invent a parallel TODO when an issue already owns the work.

Record the consumed issue number in the RAGE work log.

## 2. Mark the immutable starting point

Create an Org-mode log under the target repository:

```text
rage/<work-log>.org
```

Before research, design, or implementation commits, record:

```org
* Run identity
- Consumed issue :: #NNN
- Branch :: =rage/<issue>-<slug>=
- RAGE start commit :: =FULL_40_CHARACTER_SHA=
- Start meaning :: Exact repository commit from which this RAGE run began.
```

The start SHA is immutable evidence. A later rebase, retry, or failed attempt does not rewrite history into something prettier.

The log is append-only except for correcting an immediately discovered factual typo. Failed attempts remain visible.

## 3. Research before architecture

Research must be deep enough to falsify assumptions, not merely collect links supporting the design somebody already wanted.

Inspect at minimum:

- current implementation and tests at the recorded start commit;
- the consumed issue, parent epic, dependency issues, and relevant prior PRs;
- authoritative upstream documentation and specifications;
- library/runtime/platform lifecycle behavior;
- security, resource-bound, concurrency, recovery, and compatibility failure modes;
- production incident reports or mature implementation guidance when available;
- serious architectural alternatives.

Research questions should include:

- What assumptions in the issue are wrong or incomplete?
- What can deadlock, leak, race, wedge, duplicate, reorder, or grow without bound?
- What state belongs to the process, connection, authenticated principal, session, request, turn, or stream?
- What happens across restart, disconnect, timeout, cancellation, partial failure, and stale work?
- Which guarantees come from the transport/library, and which must be implemented at the application layer?
- What would make the proposed architecture fail its acceptance criteria even if the happy path works?

For substantial work, write a dedicated Org research artifact under `rage/` and summarize the decisive findings in the main work log.

## 4. Derive the design from the research

Do not start coding until there is an explicit design.

The design must contain:

- problem boundary and non-goals;
- chosen architecture and ownership boundaries;
- state machine/lifecycle where relevant;
- invariants that tests can enforce;
- rejected alternatives and why they lost;
- threat/failure analysis;
- backpressure/resource limits where relevant;
- migration and compatibility constraints;
- acceptance criteria mapped to tests;
- exact focused and full repository gate.

If implementation discovers a design-level contradiction, update the design and work log before continuing. Architecture changes are not allowed to hide inside a convenient patch.

## 5. Implement one consumed issue

Create focused implementation commits for the selected design.

Respect the target repository's AGENTS.md, dependency ownership, branch policy, test conventions, and architecture boundaries. RAGE does not grant permission to bypass project rules; it merely makes humans write down why they are violating physics before they try.

Do not silently expand the iteration into later child issues. If implementation reveals missing prerequisite work, create or update the appropriate issue and re-evaluate eligibility.

## 6. Evaluate the exact candidate head

Run narrow tests while developing, then the repository's complete required gate at the exact candidate SHA.

Record:

- commands;
- candidate SHA;
- focused test results;
- full local gate results;
- build/package results;
- CI workflow/run and exact SHA;
- any security, fuzz, soak, benchmark, or adversarial gates required by the issue.

A green CI run for an older SHA is stale evidence. It cannot authorize merge.

## 7. Merge or trash the attempt

There are two classes of failure.

### Ordinary implementation defect

Examples: typo, missing import, incorrect assertion, small local bug that does not invalidate the design.

Fix it within the current iteration, rerun the required gates, and record the new exact head.

### Design-invalidating failure

Examples: ownership model cannot satisfy isolation, transport semantics break required reconnect behavior, lifecycle design races under shutdown, resource bounds cannot be enforced without changing the architecture, or testing disproves a core invariant.

When this happens:

1. record the failure and evidence in the Org log;
2. preserve enough commit/PR information to audit the failed attempt;
3. discard the failed implementation attempt rather than polishing it into plausible-looking rubble;
4. start a new numbered RAGE iteration from research/design;
5. implement the new design independently;
6. rerun the complete exact-head gate.

## 8. Merge only when the gate is authoritative

Merge only when:

- the consumed issue's acceptance criteria are satisfied;
- focused tests pass;
- the repository's full required gate passes;
- build/package checks pass where required;
- the current PR head is mergeable;
- required GitHub Actions are green for that exact head.

After merge:

- record the merge SHA in the Org log;
- close or update the consumed issue;
- update parent epic/roadmap state when appropriate;
- only then re-read the issues list and consume the next eligible issue for another iteration.

## 9. Repository-local specialization

If the target repository has its own `skills/rage/SKILL.md`, read it after this generic skill. The local skill may add gates, architecture constraints, issue ordering, or project-specific invariants. It may not weaken the generic exact-head or evidence requirements.

## 10. Minimum Org log shape

```org
#+title: RAGE Work Log - <project> <issue>

* Run identity
- Consumed issue :: #NNN
- RAGE start commit :: =...=

* Iteration 1
** Research
** Design
** Implementation
** Gate
** Outcome

* Iteration 2
... only if iteration 1 was invalidated
```

RAGE is complete when the consumed issue is merged through its real gate, or when the evidence shows the issue itself must be rewritten before implementation can responsibly continue.
