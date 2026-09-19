---
name: zeromq-design
description: zeromq, architecture, moped, topology, contracts, simplicity
license: CC-BY-SA-3.0
compatibility: Requires a ZeroMQ runtime or binding and enough deployment context to identify transports, peers, scale, and failure requirements.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Design

Adapted from the Guide's SOD/MOPED architecture method.

## Goal

Grow a ZeroMQ system from a minimal end-to-end path instead of designing a
large speculative messaging framework up front.

## Input

A real user/system problem, participating components, required message flows,
scale targets, and failures that actually matter.

## Workflow

1. State the concrete problem and the economic/operational reason to solve it.
2. Draw only the essential components and arrows for one end-to-end path.
3. Define two contract surfaces before implementation:
   - application-facing API;
   - peer-to-peer wire protocol.
4. Record measurable constraints: latency, throughput, ordering, durability,
   availability, memory, and security.
5. Implement the smallest end-to-end solution that proves the topology.
6. Exercise it as a user; turn the next observed problem into one small patch.
7. Repeat while keeping the system runnable and the contracts explicit.
8. Split components only when an observed pressure justifies the new concept.

## Selection rules

- Stable service with many dynamic clients: stable side usually binds; dynamic
  sides usually connect.
- One-of-many work distribution: PUSH/PULL or DEALER/ROUTER depending on
  reply/routing needs.
- All-of-many ephemeral broadcast: PUB/SUB, accepting its loss model.
- Addressed asynchronous peers: ROUTER/DEALER or a modern verified equivalent.
- Stateful protocol: model peer state explicitly rather than hiding it in
  callback order.
- Large payload stream: design bounded credit/backpressure before optimizing.

## Rules

- Prefer removing concepts over adding options.
- Do not expose implementation state as a public protocol.
- Do not optimize serialization before measuring the actual hot data flow.
- Do not add HA, discovery, persistence, or federation until a named failure
  or use case demands it.
- Re-check current libzmq docs before selecting draft or version-sensitive APIs.
