---
name: starintel-local-search
description: starintel, local-search, jsonl, ndjson, relations, corpus
---

# StarIntel local search

## Goal

Search canonical local DB records and Auto-Dig packets before research, document creation, linking, or remote ingest.

Requires Python 3.11+ and a current StarIntel Auto-Dig checkout.

## Input

A query, identifier, dtype, dataset, predicate, source, or confidence requirement.

## Output

Matching canonical documents with stable IDs and optional repository locations.

## Command

Run from the Auto-Dig repository root:

```bash
python3 scripts/starintel.py search '<terms>' \
  --dtype <dtype> \
  --dataset <dataset-fragment> \
  --predicate <predicate-fragment> \
  --source <source-fragment> \
  --min-confidence 0.8 \
  --with-location
```

Use only the filters needed for the question. Results are JSONL. `--with-location` adds path, line, and surface around each document.

## Workflow

1. Read the checkout's `AGENTS.md` and confirm it is current.
2. Start with exact entity names, StarIntel IDs, external identifiers, source URLs, or predicates.
3. Search without a confidence floor first so contrary or uncertain records remain visible.
4. Narrow with `--dtype`, `--dataset`, `--id`, `--predicate`, or `--source`.
5. Preserve result IDs and locations in downstream notes or document proposals.
6. For link work, use `scripts/search-db-links.py search`, `resolve`, and `neighbors`; those commands prefer normalized DB records and fail on ambiguity.

## Rules

- Search both `db/` and `digs/` unless the task explicitly needs `--db-only` or `--packets-only`.
- Resolve ambiguous names with identifiers and source evidence; never choose a record merely because it ranked first.
- A relation match is evidence that a record asserts an edge, not proof that the edge is true.
