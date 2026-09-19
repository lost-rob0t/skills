# Routing notes

## Request/reply envelopes

The Guide models request/reply as an envelope plus a body. ROUTER exposes peer
routing identities; DEALER removes strict REQ/REP lockstep and allows multiple
outstanding messages. Intermediaries should preserve the body while adding or
removing only the routing information they own.

## Readiness-driven balancing

The durable load-balancing pattern is not “round-robin every known worker”.
Workers announce READY, the broker keeps only available workers in the ready
set, assigns one job, then returns the worker to the ready set after its reply
or next readiness signal. This makes capacity a protocol fact.

## Harmony peer shape

For true peer networks the Guide used:
- one ROUTER inbox bound on each node;
- one DEALER per remote peer, connected outbound;
- a first HELLO carrying return endpoint/identity;
- any valid incoming traffic as evidence of liveness.

The value is the asymmetric implementation of a symmetric abstraction:
outbound sockets can queue while connecting, while one inbound ROUTER gives a
single addressed receive point.

## Modern checks

Current libzmq adds options for mandatory ROUTER routing, routing IDs, probing,
and other connection behavior. Exact names/support vary by version and
binding. Verify them instead of reproducing 3.2-era workarounds.
