# Reliability pattern ladder

## From cheap to expensive

1. **Lazy retry** — one server, deadline, bounded retries, recreate unusable
   strict request state.
2. **Failover pool** — try another server after bounded failure.
3. **Brokered workers** — broker knows ready workers and isolates clients from
   worker churn.
4. **Heartbeat/liveness** — explicit protocol state for peers that can become
   silent while still connected.
5. **Durable request service** — persist request/result state so clients can
   disconnect and later collect outcomes.
6. **Replicated authority** — only when loss of the broker/state authority is a
   required failure to survive.

Each step adds state and new failure modes. Stop as soon as requirements are
met.

## Duplicate-safe requests

A timeout cannot tell whether the peer did nothing, is still working, performed
the side effect but lost the reply, or replied on a path that failed. Stable
request IDs plus server-side dedupe/reply caching are therefore part of the
application contract for safely retried effects.

## Heartbeats

Use negotiated/configured intervals and expiry policy. Avoid synchronized
heartbeat storms. Ordinary valid messages can refresh liveness. Under overload,
late heartbeats can be a symptom rather than the cause; pair liveness with
backpressure/queue observations.
