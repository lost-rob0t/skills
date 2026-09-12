---
name: starintel-code-coordinator
description: starintel, coding, coordinator, sol, glm, integration
---

# StarIntel Code Coordinator

## Goal

Implement one approved StarIntel vertical slice using GPT-5.6 Sol as the
coordinator and bounded GLM workers for bulk implementation.

The coordinator owns architecture, semantics, integration, review, tests, and
the final branch/PR. GLM workers own only explicitly delegated packets.

## Input

- a `starintel-code-critic` report;
- the user's request and current project context;
- the latest target-repository default branch.

## Workflow

1. Verify the critic report against the live repository and reproduce the
   relevant baseline tests. Correct factual drift without expanding the slice.
2. Create a fresh branch/worktree for the slice.
3. Turn the critic task DAG into `PARALLEL GLM`, `SEQUENTIAL GLM`,
   `SOL INTEGRATION`, and `SOL REVIEW` work.
4. Give every GLM worker an exact goal, allowed files/modules, prohibited scope,
   required tests, commands, dependencies, and completion condition. Require it
   to inspect existing code and commit its finished packet.
5. After every worker result, Sol reviews the actual diff for semantics,
   duplication, architecture leakage, error handling, regression risk, and
   scope creep. Never trust a worker's test claim without rerunning the gate.
6. Integrate in dependency order. When implementations disagree, use project
   conventions plus the critic's semantic contract; choose one canonical path
   and remove redundant alternatives.
7. Run focused tests plus adversarial and real end-to-end tests through the
   actual input-to-runtime path whenever technically applicable.
8. Remove debug code, dead abstractions, generated junk, and accidental scope.
   Update docs/fixtures/exports only when the slice changed those contracts.
9. Run a final Sol review asking whether the capability is reachable, semantics
   are deterministic, errors are useful, tests prove behavior, and anything is
   overengineered.
10. Push one PR for the slice. Merge only when required checks are green and the
    exact head is mergeable; otherwise leave it open with the exact blocker.

## GLM Boundary

GLM may implement bounded code, tests, fixtures, and required documentation.
GLM must not independently redefine architecture, public APIs, language
semantics, verification gates, or broaden the requested slice. Escalate those
decisions to Sol.

## Final Report

Return: slice, branch, PR, GLM workers used, commits, capability now working,
end-to-end proof, tests, Sol review findings, deferred work, merge status, and
the recommended next slice.

## Rule

SOL THINKS. SOL COORDINATES. GLM BUILDS. SOL CRITICIZES. TESTS DECIDE.
