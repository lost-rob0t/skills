# The ØMQ Guide map and modernization notes

## Provenance

This package is an adaptation of *The ØMQ Guide* by Pieter Hintjens and its
contributors, source: https://github.com/booksbyus/zguide, revision
`6752d24b215997aa161e6896941bfd6010d4d3f5`. The Guide text is CC BY-SA 3.0. Its source edition describes
ZeroMQ 3.2, so API-level advice must be checked against the deployed runtime.

## Full-book map

- Preface: ZeroMQ as a message-oriented concurrency fabric; minimalism.
- Chapter 1: socket semantics, REQ/REP, PUB/SUB, pipelines, startup/shutdown.
- Chapter 2: topology, multipart messages, poll/reactors, proxies, threading,
  HWM/backpressure, envelopes.
- Chapter 3: ROUTER/DEALER envelopes, async request/reply, readiness-driven
  load balancing, routing intermediaries.
- Chapter 4: failure classes, retries, heartbeats, idempotency, Majordomo,
  durable requests, brokered and brokerless reliability.
- Chapter 5: PUB/SUB trade-offs, tracing, last-value caches, slow subscribers,
  high-speed subscribers, Clone state replication.
- Chapter 6: contracts, community architecture, Simplicity-Oriented Design,
  minimal problem-driven patches and continuously usable software.
- Chapter 7: MOPED, small written protocols, control/data separation,
  serialization, credit flow control, peer state machines, FileMQ.
- Chapter 8: discovery, presence, Harmony P2P, groups, churn simulation,
  blocked peers, distributed logging and content distribution.
- Postface: production case studies; patterns and contracts matter more than
  any particular language binding.

## Durable lessons

- A ZeroMQ socket is a message endpoint abstraction, not a TCP connection.
- Topology and protocol contracts dominate individual API calls.
- Reliability must name failures and define recovery; it is not automatic.
- High-volume data and low-volume control often need different semantics.
- Readiness and explicit credits are stronger than guessing queue capacity.
- State machines make non-trivial async protocols reviewable and testable.
- Simulate churn, overload, restart, and stale peers before production.

## Modern correction gate

Before using a book technique, check current official libzmq/binding docs.
Modern releases add CURVE/ZAP, heartbeat options, socket monitoring,
ROUTER routing controls, UDP transport, and thread-safe socket families.
Some newer socket families remain draft APIs and can change. Classic sockets
remain non-thread-safe. Never copy the Guide's historical SASL/PLAIN or SHA-1
examples into a security design without a fresh security review.
