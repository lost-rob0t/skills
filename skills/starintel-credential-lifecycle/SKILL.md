---
name: starintel-credential-lifecycle
description: starintel, api-keys, scopes, rotation, agent-zero, easypg
---

# StarIntel credential lifecycle

## Goal

Issue or replace narrowly scoped Star Server credentials, store their one-time
values in an encrypted Org file, and deliver a service credential through its
local administration API without losing or exposing key material.

Requires `curl`, `jq`, `ssh`, `emacsclient`, an Emacs daemon with EasyPG access,
an authenticated Star Server administrator path, and the target service's local
API contract.

## Input

Credential owners and principal types, exact capability and resource scopes,
expiry, encrypted Org file and headings, predecessor credential IDs, target SSH
identity, local API URL, and destination secret name such as `STAR_AUTH`.

## Output

Authenticated replacement credentials, encrypted records, masked target API
readback, and revoked predecessors with sanitized lifecycle receipts.

## Workflow

1. Inspect the deployed Star Server authorization vocabulary and credential API.
   Reject unknown scopes. Changing scopes requires a new credential; rotation
   preserves the old scope set.
2. Read existing records from the `.org.gpg` buffer through `emacsclient`.
   Extract only required values into memory; do not decrypt to a plaintext file.
3. Resolve every requested resource dimension explicitly. Target work commonly
   needs `targets:read`, `targets:dispatch`, `targets:lease`, and matching
   `tenant:`, `dataset:`, `actor:`, `target:`, `target-namespace:`, and
   `program:` grants. Do not infer wildcard access from a capability.
4. Authenticate to Star Server through the approved administrator path and
   `POST /auth/credentials`. Parse the identifier from
   `credential.credential_id`; the raw `api_key` is returned only once.
5. Validate owner, principal type, expiry, and exact ordered scopes in each
   response. If a multi-key issuance is partial, revoke unusable new keys.
6. Before revoking predecessors, update the encrypted Org buffer through
   `emacsclient`, save it with EasyPG, and retain predecessor IDs as revoked
   audit references. If save fails, revoke the new keys and stop.
7. Configure the target over SSH using `curl` against its loopback API. For
   Agent Zero, obtain CSRF token plus session cookie with an explicit `Origin`,
   read current settings, preserve all fields, merge the secret, and submit via
   `/api/settings_set`. Keep ephemeral cookie material in memory-backed storage
   and remove it on exit.
8. Confirm target readback contains the secret name with a masked value. Then
   call Star Server `/auth/context` with each new key and compare the complete
   principal and scope set. Exercise representative endpoints in every granted
   tenant and one ungranted tenant; require both allow and deny behavior.
9. Revoke predecessor IDs through the authenticated Star Server API only after
   encrypted storage, delivery, and context checks pass. List credential
   metadata and verify the intended active/revoked states.

## Rules

- Never print bearer keys, administrator material, decrypted buffers, request
  bodies containing secrets, or unmasked settings responses.
- Never use the one-time bootstrap route for routine credential lifecycle work.
- Exclude delete, force-release, credential-administration, principal-management,
  audit, and `admin` capabilities unless the operator explicitly requests them.
- A minted key without durable encrypted storage is unusable and must be revoked.
- A masked target readback proves storage, not authorization; `/auth/context`
  proves authentication and scopes.
