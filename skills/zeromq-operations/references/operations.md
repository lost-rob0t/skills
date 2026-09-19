# Operations checklist

## Missing-message triage

Check in this order:
1. Was the receiver ready/subscribed before correctness depended on delivery?
2. Did the sender address a known current routing identity?
3. Did filters remove the message?
4. Did HWM/backpressure cause drop, EAGAIN, or blocking?
5. Did shutdown/linger discard queued work?
6. Was traffic from an old peer/session generation accepted or ignored?
7. Did endpoint reuse connect a stale peer to a new process?
8. Is the application loop itself slower than incoming traffic?

## Thread ownership

The Guide's durable rule for classic sockets is one owning application thread
per socket. Share the context; communicate between actors/threads with
messages. Modern libzmq has some thread-safe socket families, but availability
and draft status are runtime-specific.

## Observability

Use two layers:
- socket monitor: connect/listen/accept/disconnect/handshake transport events;
- application trace: protocol command, request ID, peer ID, generation, queue or
  credit state, and outcome.

Never put secret payloads or keys in routine traces.

## Churn simulation

Randomly start/stop many peers, inject latency and backpressure, reuse ports,
interrupt handshakes, and force reconnects. Preserve a reproducible random seed
when a failure appears.
