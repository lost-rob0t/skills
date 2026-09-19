# Design patterns distilled from zguide

## Problem-first loop

The Guide's Simplicity-Oriented Design and MOPED methods converge on one
workflow: find a real problem, draw a small topology, define contracts, make a
minimal end-to-end implementation, test it, then solve one observed problem at
a time. The design is allowed to evolve; the contracts make that evolution
safe.

## Questions before choosing sockets

- Is the flow one-to-one, one-of-many, or all-of-many?
- Is it request/reply, streaming, event broadcast, or replicated state?
- Does the sender need to address a particular peer?
- Can messages be lost during join/reconnect?
- Who owns ordering and deduplication?
- What happens if the receiver is slower forever, not just briefly?
- Which peer has a stable endpoint?
- Is a broker a useful reliability boundary or an unnecessary dependency?

## Architecture smells

- One socket type is being forced to carry unrelated control and bulk-data
  semantics.
- The protocol depends on exact queue depth or timing sleeps.
- A component cannot restart without every other component restarting.
- The design contains concepts with no current use case.
- Wire fields mirror internal objects instead of a simpler public abstraction.
- Reliability is described as “ZeroMQ reconnects” instead of named failure and
  recovery semantics.
