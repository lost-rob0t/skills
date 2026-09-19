---
name: zeromq-security
description: zeromq, security, curve, zap, authentication, encryption
license: CC-BY-SA-3.0
compatibility: Requires a current ZeroMQ runtime/binding with the security mechanisms used by the deployment; verify CURVE/ZAP support directly.
metadata:
  author: Pieter Hintjens and zguide contributors
  source: https://github.com/booksbyus/zguide
  upstream-version: The ØMQ Guide, ZeroMQ 3.2 edition
  upstream-revision: 6752d24b215997aa161e6896941bfd6010d4d3f5
  upstream-license: CC-BY-SA-3.0
  provenance: external-adaptation
---

# ZeroMQ Security

## Goal

Secure ZeroMQ transports and application messages using current mechanisms
without inheriting the Guide's historical SASL/PLAIN examples as modern advice.

## Workflow

1. Write the threat model: passive observer, active MITM, unauthorized client,
   compromised broker/server, stolen device key, replay, and metadata leakage.
2. Separate identities:
   - transport/routing identity;
   - authenticated principal;
   - application/user/device identity.
3. For untrusted TCP networks, prefer current CURVE transport encryption and
   authentication with ZAP authorization where supported.
4. Pin or otherwise authenticate server/public keys; fail closed on unexpected
   key changes.
5. Keep private keys out of source, config committed to Git, logs, diagnostics,
   screenshots, and message metadata.
6. Define rotation, revocation, enrollment, recovery, and stale-key behavior.
7. If intermediaries must not read payloads, add application-layer E2EE above
   ZeroMQ transport security; brokers then route opaque ciphertext.
8. Bind authorization to the authenticated principal, never a caller-controlled
   display name or ROUTER routing ID.
9. Test wrong keys, unknown/revoked principals, replay, tampering, restart,
   rotation races, and diagnostic redaction.

## Rules

- PLAIN-style password authentication is not confidentiality.
- Do not use obsolete digest choices from Guide examples for security.
- Encryption does not solve replay, authorization, or application idempotency.
- Authenticate protocol metadata needed to prevent substitution/downgrade.
- Treat security mechanism availability and option names as runtime-specific.
