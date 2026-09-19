---
name: zeromq-reliability
description: zeromq, reliability, retries, heartbeats, idempotency, recovery
license: CC-BY-SA-3.0
compatibility: Requires a ZeroMQ runtime or binding and an explicit failure model for the application.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Reliability

## Goal

Choose the least-complex recovery mechanism that handles the failures the
application actually needs to survive.

## Workflow

1. Enumerate failures separately: process crash, restart, busy loop, overload,
   link loss, partition, duplicate request, stale reply, broker loss, and
   storage loss.
2. Classify each operation as idempotent or non-idempotent.
3. Give retried non-idempotent work a stable request ID and a dedupe/reply
   policy before enabling automatic retries.
4. Bound every wait with a deadline or cancellation path.
5. Start with simple timeout + retry/failover; add heartbeats only when they
   detect a failure faster or more accurately than ordinary traffic.
6. Count any valid peer traffic as liveness when the protocol permits it.
7. Use reconnect backoff and jitter; do not spin on a dead endpoint.
8. Recreate strict-state sockets after protocol state becomes unusable.
9. Persist requests/results only when disconnected or durable execution is a
   requirement.
10. Test crash points before receive, during work, after side effect, before
    reply, and during reconnect.

## Rules

- Reconnect is transport behavior, not application-level exactly-once delivery.
- Never retry a side effect blindly.
- Sequence or generation-fence stale replies and state updates.
- Prefer a small pool/failover set over elaborate HA unless requirements demand
  consensus-level behavior.
- Treat Binary Star and other guide-era HA examples as teaching patterns, not
  substitutes for modern consensus when split-brain safety is required.
