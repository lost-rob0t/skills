# Remote client status

Status verified 2026-08-22. Re-check current repositories and deployed capabilities before use.

## Deployed service

- Owner-compatible internal base URL: `http://ingest.star.intel` through nginx.
- Public edge declared by StarInfra: `http://ingest.starintel.actor`; it returned HTTP 502 during verification and is tracked in `starintel-labs/starintel-infra#16`.
- Internal `/health` returned HTTP 200 with runtime, CouchDB, RabbitMQ, consumer, actor, kernel, and HTTP readiness.
- Internal `/` returned server metadata advertising document spec `0.8.0`.
- Protected routes require `Authorization: Bearer <key>` and return a structured 401 error with a correlation ID when absent.

## Current legacy server behavior

| Operation | Route | Semantics |
| --- | --- | --- |
| health | `GET /health` | readiness, public |
| info | `GET /` | server metadata, public |
| ingest one | `POST /new/document/:dtype` | validates transport shape/dtype, publishes to RabbitMQ; acceptance is not persistence |
| ingest batch | `POST /documents/bulk` | up to 500; small batches inline with partial counts, larger batches may return an async job |
| batch status | `GET /documents/bulk/:job-id` | authenticated job status scoped to the principal |
| get | `GET /document/:id` | reads the configured CouchDB database |
| search | `GET /search` | CouchDB/Clouseau full-text search |

The legacy server does not run strict Auto-Dig v0.9 validation. Server-side v0.9, idempotent batch ingest, and target lifecycle are tracked in `lost-rob0t/starintel-server#59`.

## CLI ownership decision

The operator selected the server-owned path: finish `starintel-gserver-client` and
`star-cli` in `lost-rob0t/starintel-server`. Do not create a separate CLI repository
or add a competing Python transport client to Auto-Dig. The decision record is closed
as `lost-rob0t/starintel-gpt-auto-dig#2220`; implementation is tracked by
`lost-rob0t/starintel-server#108`.

This matches merged Auto Research `STAR-RESEARCH-038`, which rejects another
independently maintained client library. Open server PR #104 implements part of that
direction, but it was not green or merged at the verification date.

Until the server-owned CLI lands, do not publish illustrative remote commands as if
they exist. Inspect the current `star-cli` help and tests, then update examples from
its real tested interface.
