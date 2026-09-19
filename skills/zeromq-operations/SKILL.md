---
name: zeromq-operations
description: zeromq, debugging, backpressure, threading, monitoring, shutdown
license: CC-BY-SA-3.0
compatibility: Requires access to the deployed ZeroMQ runtime/binding, logs, and enough test control to simulate peers and failures.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Operations

## Goal

Debug and operate ZeroMQ systems by observing message flow, queue pressure,
peer state, and lifecycle transitions instead of guessing from connection state.

## Workflow

1. Reproduce with the smallest topology and log protocol-level send/receive
   events with monotonic timestamps, peer IDs, generations, and message IDs.
2. Check startup ordering/handshake before blaming message loss.
3. Check subscription filters and routing identities.
4. Check HWM, send/receive timeouts, EAGAIN/drop behavior, and application
   processing rate; never treat configured HWM as an exact network queue size.
5. Confirm one application thread owns each classic ZeroMQ socket.
6. Make shutdown explicit: stop producers, drain/cancel intentionally, close
   sockets with chosen linger semantics, then terminate context.
7. Use socket monitoring for transport lifecycle and application traces for
   protocol semantics.
8. Randomize churn tests: connect, disconnect, restart, endpoint reuse, delay,
   malformed messages, slow peers, and process death.
9. Run many isolated peer actors in one test process when practical.
10. Turn every rare assertion/race into a deterministic regression test.

## Rules

- Assertions express invariants in tests/internal code; they are not user-facing
  error handling.
- A single blocked peer must not block the whole routing loop.
- Bound queues, retries, timers, message sizes, and per-peer state.
- Prefer message passing between threads over shared mutable socket state.
- Verify whether a chosen modern socket type is thread-safe and stable/draft in
  the deployed runtime before relying on it.
