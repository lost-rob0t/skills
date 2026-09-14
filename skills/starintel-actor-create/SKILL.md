---
name: starintel-actor-create
description: starintel, actors, star-lang, sento, plugins, manifests, testing
---

# Create a StarIntel actor

## Goal

Create an actor in the runtime that actually owns the requested execution boundary.

Requires current `lost-rob0t/star-lang` and StarIntel server repositories plus `starintel-spec-version` when the actor consumes or emits StarIntel documents/manifests.

## Input

The actor's purpose, inputs, outputs, effects, deployment target, state/lifecycle requirements, and failure semantics.

## Output

An executable actor plus contract tests, registration/startup wiring, and a matching manifest or canonical record when required.

## Choose the runtime

1. Use final `starlang-runtime` for deterministic local Common Lisp actors.
2. Use a `starintel-server` Common Lisp plugin actor when it must run inside the production Sento actor system or consume the current RabbitMQ target flow.
3. Use `create-external-actor` only to register an external boundary; current final Star-Lang does not yet dispatch it.
4. An Auto-Dig `actor-manifest` document describes an actor. It does not instantiate or deploy one.

Read [references/runtime-boundaries.md](references/runtime-boundaries.md) for the current implementation split.

## Workflow

1. Inspect the current runtime's repository instructions, exported packages, tests, and one maintained actor with the same deployment model.
2. Before defining any StarIntel document, message field derived from the document contract, or `actor-manifest`, use `starintel-spec-version` to resolve the consumer lock's active `release_version` and verify the pinned canonical manifest. Never derive the release from a `v0.9.0` schema filename.
3. Define one stable name and canonical `star://<domain>:<address>:<actor>` URI whose actor component matches the name.
4. Define accepted and produced message contracts, validators, mailbox capacity, state ownership, restart policy, capabilities, and effect ports.
5. Keep network, process, storage, and broker effects behind explicit adapters; keep message/state transitions deterministic.
6. Implement one canonical handler and registration path. Remove obsolete duplicate paths encountered in scope.
7. Add tests for registration, happy path, invalid input/output, mailbox bounds, state rollback, handler failure, restart/generation, shutdown, and the real adapter boundary used.
8. Wire startup only through the runtime's maintained hook or composition root.
9. Run focused ASDF tests and the complete owning repository gate.

## Rules

- `release_version` is the active StarIntel release; immutable base `schema_version` is a separate dimension.
- Do not call a manifest, package shell, or registered external reference an executing actor.
- Do not add a second parser, dispatcher, mailbox, or transport path beside the current authority.
- Stable actor identity and runtime instance/generation are different values.
- Document actual supported behavior; keep prototype-only or unavailable operations explicit.
