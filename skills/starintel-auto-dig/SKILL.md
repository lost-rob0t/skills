---
name: starintel-auto-dig
description: starintel, auto-dig, osint, recursion, documents, relations, validation
---

# StarIntel Auto-Dig

## Goal

Run one complete evidence-first research loop and leave a validated, traceable next frontier.

Requires web research tools and a current StarIntel Auto-Dig checkout.

## Input

A root target or investigation-target document, research question, dataset, and recursion budget.

## Output

A source ledger, canonical documents and relations, a `research-pass`, a green gate, optional remote receipts, and selected next targets.

## Loop

1. Read the current checkout's `AGENTS.md`, reuse its canonical dataset root, and record the starting commit.
2. Use `starintel-local-search` to find existing records, relations, unresolved targets, conflicts, and prior passes.
3. Use `starintel-osint` for extensive external research and independent corroboration.
4. Resolve identities and split material into exact document dtypes.
5. Use `starintel-document-create` for canonical documents and explicit relations.
6. Add or update a `research-pass` recording the question, method, findings, supporting and counterevidence IDs, unresolved target IDs, agent identity, iteration, start/end times, and coverage gaps.
7. Use this skill's `scripts/verify.py --repo <auto-dig-checkout>` helper for the canonical local `nimble buildFast` plus `bin/validate-for-merge --site` gate. It validates the checkout, logs the exact argument vectors, and stops on the first failed stage.
8. When remote publication is part of the request, use `starintel-ingest` and preserve accepted, queued, failed, and persisted states separately.
9. Generate the next deterministic frontier with the Auto-Dig repository's maintained `python3 scripts/starintel.py select-targets --query '<current subject>' --limit 20 --emit-documents --output recursive-targets.jsonl` operation.
10. Review and import accepted target documents through the canonical batch path, then publish through the repository's branch/PR workflow when requested.

## Rules

- Every conclusion traces to canonical IDs and exact sources; mission plans and selection scores are not evidence.
- Keep actors or research roles independent until synthesis so shared assumptions do not masquerade as corroboration.
- Stop recursion at the declared depth/breadth, satisfied question, exhausted credible leads, or repeated unsupported hypothesis.
- Never describe a failing, skipped, pending, stale, or unrun gate as success.
