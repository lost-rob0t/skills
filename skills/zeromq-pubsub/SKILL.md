---
name: zeromq-pubsub
description: zeromq, pubsub, xpub, state-replication, slow-subscriber, lvc
license: CC-BY-SA-3.0
compatibility: Requires a ZeroMQ runtime or binding; XPUB/XSUB options and filtering behavior must be checked for the deployed version.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Pub/Sub

## Goal

Use PUB/SUB for scalable dissemination while making join loss, slow consumers,
recovery, and replicated-state semantics explicit.

## Workflow

1. Decide whether loss is acceptable. If not, define the separate recovery or
   synchronization path before calling the system reliable.
2. Treat a new subscriber as a late joiner that has missed prior messages.
3. Avoid timing sleeps as correctness mechanisms; add an explicit readiness or
   snapshot handshake where startup completeness matters.
4. Give streams publisher identity + sequence or version metadata when gaps
   must be detectable.
5. Pick a slow-subscriber policy: tolerate bounded lag, drop, disconnect/fail
   the subscriber, or resynchronize. Do not let backlog grow without bound.
6. Use XPUB/XSUB or a proxy only when subscription visibility/control is needed.
7. For latest-state topics, consider a last-value cache keyed by topic.
8. For replicated state, take a snapshot while update traffic queues, then
   apply only updates newer than the snapshot generation.
9. Stress late join, restart, subscriber stalls, HWM pressure, gaps, and
   snapshot/update races.

## Rules

- PUB/SUB is dissemination, not an acknowledgment protocol.
- PUSH/PULL and PUB/SUB are not interchangeable: one-of-many differs from
  all-of-many.
- Do not assume publisher-side filtering behavior across versions/transports.
- Put heavy subscriber work behind a fast receive stage and bounded worker
  pipeline when needed.
