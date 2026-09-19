# Protocol design notes

## Small specification shape

A useful protocol document contains:
- name, version, maturity, authorship and license;
- goals and non-goals;
- peer roles and connection topology;
- normative terminology;
- formal message grammar such as ABNF or an equivalent typed schema;
- field/frame encoding and limits;
- state-machine transitions;
- errors, timeout/cancellation, retry and replay behavior;
- security considerations;
- compatibility and extension rules;
- interoperability fixtures.

## Control versus data

The Guide calls this “Cheap or Nasty”. Keep the idea, not the old tooling:
control traffic changes often and is low volume, so optimize it for clarity and
extensibility. Bulk data repeats at high volume, so optimize only the measured
hot path and keep its contract intentionally stable.

## Credit flow control

Receiver grants N messages or bytes of credit. Sender emits no more than the
available credit. Receiver replenishes credit when it has actually freed enough
capacity. This bounds end-to-end in-flight data without guessing internal
ZeroMQ/TCP queue depth.

## State machines

Represent each peer with explicit state + accepted events + actions + next
state. Unknown events have an intentional policy. State is generation-fenced
across reconnect so late traffic cannot mutate a new session.
