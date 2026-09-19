---
name: zeromq-routing
description: zeromq, router, dealer, envelopes, brokers, peer-routing
license: CC-BY-SA-3.0
compatibility: Requires a ZeroMQ runtime or binding; ROUTER option names and modern peer socket alternatives are version-sensitive.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Routing

## Goal

Build addressed asynchronous routing without losing message-envelope,
readiness, or peer-lifecycle semantics.

## Workflow

1. Draw each hop and label which side binds and which connects.
2. Separate routing envelope from application body.
3. If a ROUTER is involved, define the routing identity lifecycle explicitly.
4. Route work only to peers that have declared readiness/capacity.
5. Keep broker logic minimal: routing, liveness, service lookup, and bounded
   state; business logic stays at endpoints.
6. For symmetric peer networks, consider the Guide's Harmony shape:
   one bound inbox plus one connected outbound socket per peer.
7. Require an initial HELLO/READY handshake before accepting stateful traffic.
8. Define what happens to unknown, stale, disconnected, and duplicated peer
   identities.
9. Verify with delayed connect, reconnect, endpoint reuse, peer churn, and
   unroutable-message tests.

## Rules

- Do not treat ROUTER identity as user identity or authorization.
- Avoid sending to a peer before the protocol says it is routable/ready.
- Prefer explicit failure for unroutable sends when the runtime supports it.
- Keep route metadata outside opaque application payloads when intermediaries
  need to forward without understanding the body.
- A blocked peer must not stall unrelated peers.
- Guide-era ROUTER-to-ROUTER limitations are historical; verify current
  routing-ID/probe features before asserting what a modern runtime can do.
