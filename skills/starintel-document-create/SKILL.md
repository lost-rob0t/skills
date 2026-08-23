---
name: starintel-document-create
description: starintel, documents, relations, schema, validation, local-db
---

# Create StarIntel documents

## Goal

Create or update canonical local StarIntel v0.9.0 documents and relations through repository-owned tooling.

Requires Python 3.11+, Nim, and a current StarIntel Auto-Dig checkout.

## Input

Resolved entities, atomic observations or claims, exact sources, evidence locators, and a target dataset.

## Output

Schema-valid records under `db/<dtype>/<_id>.ndjson` or a validated packet JSONL, plus a green repository gate.

## Workflow

1. Read `AGENTS.md`; the checkout's `starintel_doc/` and generated v0.9.0 schema are authoritative.
2. Inspect the executable registry before drafting:

   ```bash
   python3 scripts/starintel.py types
   python3 scripts/starintel.py schema --dtype <dtype>
   ```

3. Search for an existing stable identity before choosing `_id`.
4. Put common metadata in the canonical envelope and dtype-specific values in `data`.
5. Create one normalized record with the transactional writer:

   ```bash
   python3 scripts/create-db-document.py <dtype> \
     --dataset <dataset> --id <stable-id> --title '<title>' \
     --data @data.json --metadata @metadata.json
   ```

6. For a batch produced outside `db/`, import canonical JSONL with `python3 scripts/starintel.py import records.jsonl`. Current import atomicity is tracked in `lost-rob0t/starintel-gpt-auto-dig#2221`; preflight the complete batch until that issue is resolved.
7. For a relation, resolve both endpoints first, then emit and import a draft:

   ```bash
   python3 scripts/create-db-link.py '<subject>' <predicate> '<object>' \
     --dataset <dataset> --source-id <source-id> --output .work/relation.jsonl
   python3 scripts/starintel.py import .work/relation.jsonl
   ```

8. Run `nimble buildFast` and `bin/validate-for-merge --site`.

## Rules

- Never hand-write normalized DB files or invent fields from examples.
- Separate observations, attributed claims, analysis, events, sources, targets, and relations by dtype.
- Relation endpoints resolve to normalized records unless the schema explicitly represents them as unresolved.
- Use `--replace` only for an intentional correction or newer version of the same identity.
- Validation failure stops the document transaction; do not weaken the schema to admit the record.
