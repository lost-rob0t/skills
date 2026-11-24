---
name: zara-expert
description: expert-systems, packs, diagnosis, prolog, remediation, testing
license: MIT
---

# Skill: zara-expert

## Goal

Use the repository's expert system — `<repo>/.zara/experts/bin/zara-expert` —
before diagnosing covered domain problems by hand, and land every reusable
diagnosis as an authored rule in a pack, never only in chat.

## Input

- A repository with `.zara/experts/` (check for it first; scaffold if absent).
- Symptoms as observed facts (`KEY=VALUE`), optionally fed by the pack's
  `probes.sh`.
- Real command evidence for verification.

## Output

- A diagnosis: hypothesis, next probe to run, verification directive.
- Applied remediation with before/after evidence recorded via
  `confirm`/`refute` (the consultation ledger).
- Green `test` gate for every pack you touch.

## Workflow

1. List packs and run the diagnosis; without `K=V` facts, `diagnose` runs the
   pack's `probes.sh` automatically:

   ```sh
   .zara/experts/bin/zara-expert diagnose [PACK] [K=V...]
   ```

2. Act on the returned `next probe` and `verification` directives. Run the
   real commands; never claim a hypothesis confirmed without observed output.
3. Record the outcome so chains self-assess:

   ```sh
   .zara/experts/bin/zara-expert confirm HYP --note "evidence"
   .zara/experts/bin/zara-expert refute HYP --note "why it was wrong"
   ```

   Refuted chains are flagged suspect in later diagnoses; `chains` lists the
   record.
4. When a covered surface is missing rules, extend that pack's `kb/expert.pl`
   and tests. When no pack fits, scaffold one:

   ```sh
   .zara/experts/bin/zara-expert define NAME KIND
   ```

5. Run the merge gate on every touched pack (model-free, network-free):

   ```sh
   .zara/experts/bin/zara-expert test [PACK]
   ```

## Rules

- Pack interface: `kb/expert.pl` exports `fact/2, observe/2, reset_facts/0,
  hypothesis/1, next_probe/2, verification/2`; optional `probes.sh` emits
  `KEY=VALUE` lines, one per line, read-only, no root required.
- Tests must be model-free and deterministic. plunit `setup()` runs once per
  unit, not per test: call `reset_facts` explicitly at the start of each test.
- Fail closed: rules that claim a healthy/verified state must require the
  evidence facts to be present (usually zero counters), so a crashed probe
  never yields "healthy" by absence.
- Normalize probe vocabulary (e.g. sysfs `power/control=on` means autosuspend
  is disabled) and gate flaps on a fresh window, not boot-wide history.
- Author knowledge as rules and facts in the pack; portability rules of the
  repository apply (no usernames, hosts, or machine-specific paths).
- Never weaken tests or verification rules to make a diagnosis pass.
