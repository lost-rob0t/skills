---
name: starintel-ingest
description: starintel, ingest, jsonl, local-db, remote-api, validation
---

# StarIntel ingest

## Goal

Move canonical StarIntel documents into the requested local or remote destination while preserving validation and observable success semantics.

Requires a current Auto-Dig checkout, `starintel-spec-version`, and, for remote operations, the configured maintained StarIntel client.

## Input

One canonical document or JSONL batch, the destination, and replacement or publication intent.

## Output

Local DB records or remote acceptance/persistence receipts, with failures classified precisely.

## Local DB

1. Use `starintel-spec-version` to resolve the active `release_version` from the applicable schema lock/canonical manifest, then run the Auto-Dig repository's `python3 scripts/schema-release.py check`. Validate every input record against that lock-resolved executable schema. Do not infer the active release from a `v0.9.0` filename.
2. Import a batch from outside `db/`:

   ```bash
   python3 scripts/starintel.py import records.jsonl
   ```

3. Use `--replace` only for an intentional update to an existing stable ID.
4. Run `nimble buildFast` and `bin/validate-for-merge --site` after the complete transaction.

## Remote service

Read [references/remote-client-status.md](references/remote-client-status.md) before remote ingest.

1. Locate the current maintained remote CLI selected by the repository decision and inspect its `--help` plus current server capabilities.
2. Validate locally before sending. Send lock-resolved canonical records unchanged; relation ingest uses the same document operation with dtype `relation`.
3. Supply the service URL and bearer credential through the client's supported configuration. Keep credentials out of repository files and output.
4. For batch operations, preserve per-record results and asynchronous job IDs.
5. Treat accepted/queued and persisted as different states. Confirm persistence with the supported lookup operation when the task requires it.
6. Do not automatically retry a mutation whose outcome is unknown; use an idempotency facility only when the selected API advertises one.

## Rules

- `release_version` is the active release; immutable base `schema_version` is a different version dimension.
- Do not replace the maintained client with copied HTTP snippets in another skill.
- Do not claim remote success from local validation, an HTTP connection, or a queued response alone.
- Report exact IDs, counts, job state, server correlation ID, and failed records when the client exposes them.
