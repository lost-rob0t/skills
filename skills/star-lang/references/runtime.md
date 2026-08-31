# Using and extending the actor runtime

Read this reference for local actor execution, external actor contracts, or
changes to `starlang-runtime`.

## Minimal native actor

Load the `starlang-runtime` ASDF system, then use its exported package:

```lisp
(let ((runtime (starlangruntime:make-runtime)))
  (starlangruntime:create-native-actor
   runtime
   "echo"
   (lambda (message state actor-runtime)
     (declare (ignore actor-runtime))
     (values message state))
   :mailbox-capacity 16)
  (unwind-protect
       (starlangruntime:ask runtime "echo" "hello")
    (starlangruntime:shutdown-runtime runtime)))
```

The handler receives `(message state runtime)` and may return `(values result
new-state)`. Use `tell` for queued delivery, `ask` for a correlated result,
`dispatch-next` or `run-until-idle` for deterministic draining, and
`resolve-actor` for name or STAR URI lookup. `invoke-actor` is compatibility
syntax over `ask`, not another execution path.

Add `:accepts`, `:produces`, input/output validators, `:initial-state`, restart
policy, mailbox capacity, service URI, and metadata only when the actor's
contract needs them. A supplied local service URI must end in the actor name.

## External actors

`create-external-actor` registers identity and contract only. Local dispatch to
one raises `actor-external-dispatch-required-error` until a concrete adapter
owns the route. Do not present registration as remote execution or bypass the
adapter boundary with an ambient network call.

The current concrete final-system composition example is
`star-scrape:create-scraper-actor`: it declares input/output contracts, composes
HTTP and HTML adapters, and registers through the same runtime actor path.

## Extending runtime behavior

- Extend exported definitions and the existing registry/mailbox/dispatch path.
- Preserve FIFO delivery, bounded-mailbox results, serialized state commits,
  restart generations, stale-reference rejection, shutdown, and typed failures.
- A failed handler or output contract must not commit proposed actor state.
- Put remote transport in an adapter port and retain explicit external-dispatch
  failure when no adapter is present.
- Add tests to `starlang-runtime/tests/` for final-system behavior. If the
  behavior is still prototype-owned, change and test that authority instead of
  duplicating it.

Run the focused owning ASDF tests, then the skill's complete verification gate.
