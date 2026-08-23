# Current StarIntel actor boundaries

Status verified against current repositories on 2026-08-22.

## Star-Lang local runtime

The `lost-rob0t/star-lang` final systems own local actor references, bounded mailboxes, creation/registration, deterministic tell/ask, state transitions, restart generation, stale-reference checks, and shutdown. `star-scrape` is a concrete final-system actor example.

Source actor lowering, concrete Sento remoting, wire lifecycle extraction, external dispatch, runtime directory, supervision, journal/replay, leases, and fencing are not all final-owned. Read `docs/implementation-slices/ACTOR-RUNTIME-MIGRATION-MATRIX.md` before extending one of those areas.

## StarIntel server plugin

Production server plugins are Common Lisp ASDF systems loaded beside `starintel-gserver`. The maintained public plugin surface currently includes actor registration, the producer agent, publish, remote-target consumer creation, canonical target routing keys, actor-event logging, and actor-start hooks.

`lost-rob0t/starintel-pro-actors` contains the `org-member` plugin example. It registers with the server actor system, consumes target documents, performs its adapter work, publishes normalized records, logs lifecycle events, and uses deterministic IDs for duplicate delivery.

Use this route when the actor must participate in the deployed server's Sento/RabbitMQ lifecycle today. Do not copy its domain logic into Star-Lang merely to obtain actor syntax.

## Auto-Dig records

The Auto-Dig v0.9 schema includes `actor-manifest`, `target`, `investigation-target`, and `research-node` document types. These records capture contracts, scheduling intent, or research plans. Runtime code must still load, register, and execute the actor through one of the boundaries above.
