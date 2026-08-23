# Star-Lang runtime operations

The final `starlang-runtime` currently owns deterministic local actor creation, registration, bounded mailboxes, serialized state transitions, tell, ask, stop, restart/generation, stale-reference rejection, and shutdown.

## Native actor

Create a runtime with `starlangruntime:make-runtime`, then use `starlangruntime:create-native-actor` with:

- a unique actor name;
- a handler of `(message state runtime)`;
- optional `:service-uri`, `:accepts`, `:produces`, input/output validators, initial state, restart policy, mailbox capacity, and metadata.

The default local service URI is `star://local:localhost:<actor-name>`. A supplied URI must end in the same actor name.

Use `tell` for queued delivery, `ask` for a correlated result, `run-until-idle` for deterministic draining, and `resolve-actor` for name or STAR URI lookup. `invoke-actor` is compatibility syntax over `ask`, not a second execution path.

## External actor

`create-external-actor` registers identity and contract only. Current final local execution raises `actor-external-dispatch-required-error`; concrete remote dispatch, runtime-directory integration, Sento remoting, journal/replay, leases, and fencing remain partly prototype-owned. Do not present registration alone as an operational remote actor.

## Scraper example

`star-scrape:create-scraper-actor` is the current concrete final-system example. It composes a fixture or real HTTP client and HTML adapter, declares `:scrape-plan` to `:scrape-result`, validates both contracts, and registers through `starlangruntime:create-actor`.

## Tests

Use the owning ASDF system tests for the touched boundary, then run:

```bash
nix run .#tests
nix flake check -L
```
