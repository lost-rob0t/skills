---
name: zeromq-guide
description: zeromq, zguide, patterns, architecture, routing, reliability
license: CC-BY-SA-3.0
compatibility: Requires a ZeroMQ runtime or binding; verify its libzmq version and draft-feature support before changing version-sensitive behavior.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Guide

Adapted from *The ØMQ Guide* by Pieter Hintjens and contributors. Read
`references/book-map.md` for scope, provenance, and modern corrections.

## Goal

Apply the Guide's durable distributed-systems patterns without blindly copying
its ZeroMQ 3.2-era APIs, defaults, security advice, or implementation details.

## Input

A ZeroMQ architecture, protocol, bug, or design question plus the actual
binding/runtime and deployment constraints.

## Workflow

1. Identify the installed binding, underlying libzmq version, transports, and
   whether draft APIs are enabled.
2. Classify the problem and use the focused skill:
   - topology/evolution -> `zeromq-design`
   - envelopes/brokers/peer routing -> `zeromq-routing`
   - retries/liveness/recovery -> `zeromq-reliability`
   - PUB/SUB/state replication -> `zeromq-pubsub`
   - wire contracts/state machines/flow control -> `zeromq-protocol`
   - HWM/threading/shutdown/debugging -> `zeromq-operations`
   - authentication/encryption -> `zeromq-security`
3. Draw the smallest end-to-end message flow before adding mechanisms.
4. Write down contracts and named failure modes before implementation.
5. Build one minimal working path, then add one verified failure or feature at
   a time.
6. Trace real message flows and stress failure boundaries before declaring the
   architecture reliable.

## Rules

- Treat patterns as more durable than socket-option spellings.
- Do not assume guide-era examples are safe on current libzmq.
- Prefer explicit protocol state, bounded queues, and observable failure.
- Do not share classic ZeroMQ sockets across application threads.
- Treat modern draft socket families as version-sensitive until verified.
- Use current security mechanisms for untrusted networks.
