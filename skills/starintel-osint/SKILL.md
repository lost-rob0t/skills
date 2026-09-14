---
name: starintel-osint
description: starintel, osint, research, evidence, provenance, corroboration, sources
---

# StarIntel OSINT

## Goal

Run an extensive, evidence-first OSINT pass that produces traceable source records and canonical-document proposals.

Requires web research and repository access plus a current StarIntel Auto-Dig checkout and `starintel-spec-version`.

## Input

- a bounded research question, target, and time/jurisdiction scope;
- the current Auto-Dig corpus and lock-resolved executable StarIntel schema;
- web, archive, filing, repository, and structured-data research tools.

## Output

A source ledger, identity-resolution notes, supported and conflicting observations, coverage gaps, and candidate StarIntel records with exact provenance.

## Workflow

1. Read the checkout's `AGENTS.md`, use `starintel-spec-version` to resolve the active `release_version`, and run the canonical repository's `python3 scripts/schema-release.py check` before drafting any schema-shaped output. Never treat a `v0.9.0` filename as the current release number.
2. Search the local StarIntel corpus before external research. Preserve matching IDs, paths, relations, and contrary records.
3. Build a query matrix from exact names, aliases, identifiers, domains, addresses, organizations, dates, products, predicates, and jurisdiction-specific terms.
4. Cover the relevant source families in [references/source-playbook.md](references/source-playbook.md); do not stop after ordinary web results.
5. Prefer primary records, then use independent secondary reporting to discover, contextualize, or challenge them.
6. Record each source URL, publisher, title, publication/event date, retrieval time, locator, archive URL when useful, and content hash when bytes are retained.
7. Resolve identity with stable identifiers and discriminators. Keep ambiguous people or organizations separate until evidence joins them.
8. Extract atomic observations and attributed claims. Record the exact source location and which record or relation each item supports.
9. Seek counterevidence and log meaningful negative searches, unavailable records, date ranges, and source families checked.
10. Reconcile conflicts by source authority, directness, date, scope, and version; preserve unresolved conflicts instead of averaging them away.
11. Hand accepted material to the canonical document and relation skills, then record follow-up targets for the next pass.

## Rules

- `release_version` is the active StarIntel release; immutable base `schema_version` is a separate contract dimension.
- A search result, source link, co-occurrence, graph edge, or actor agreement is a lead, not proof.
- Keep observations, attributed claims, analysis, and unresolved hypotheses distinguishable.
- Preserve exact names, identifiers, dates, amounts, quotations, URLs, and uncertainty.
- Never manufacture evidence, citations, retrieval results, negative-search coverage, or corroboration.
- Use only public, lawfully accessible sources and the user's authorized data.
