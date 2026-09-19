# Security modernization notes

## What is historical

The Guide's SASL discussion and FileMQ PLAIN mechanism were architecture
experiments from the ZeroMQ 3.2 era. Its SHA-1 cache example was for file change
detection, not a modern security recommendation. Do not turn either into a new
security baseline.

## Modern layers

- **Transport security**: current libzmq CURVE can provide encrypted,
  authenticated ZeroMQ transport when configured correctly.
- **Authorization**: ZAP lets an application decide which authenticated peers
  may connect/use a domain.
- **Application E2EE**: needed when a legitimate router/broker/storage server
  must relay data without learning plaintext.

These layers solve different problems and can be combined.

## Key lifecycle checklist

- generate keys on the endpoint that owns them;
- protect private material with OS/runtime secret storage;
- publish fingerprints/public keys through an authenticated enrollment path;
- record principal-to-key binding and generation;
- reject revoked/stale generations;
- rotate without silently trusting a replacement key;
- provide explicit recovery semantics;
- redact key material from telemetry and crash reports.

## Protocol security

Include version negotiation/downgrade policy, message-size limits, replay or
request IDs where needed, authenticated principal binding, and behavior for
malformed or unauthenticated traffic.
