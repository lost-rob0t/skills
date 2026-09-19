# Pub/Sub patterns from the Guide

## Espresso

Capture traffic through a proxy/observation path to understand subscriptions,
unsubscriptions, and published data. Modern socket monitoring can complement,
not replace, application-message tracing.

## Last-value cache

A programmable XPUB/XSUB intermediary can retain the last value per topic and
send it when a matching subscription appears. This solves freshness for
latest-state topics, not arbitrary replay history.

## Suicidal Snail

If stale data is dangerous, a subscriber should detect unacceptable lag or
sequence gaps and fail/resynchronize loudly instead of silently processing
old state.

## Black Box

Keep the SUB receive path tiny. Shard/filter quickly, then hand expensive work
to worker threads/processes using an internal message pipeline. Scale only when
measurement shows the receive/processing stage is saturated.

## Clone

For shared state:
1. subscribe to updates;
2. request a snapshot through a request/reply path;
3. let updates queue while snapshot arrives;
4. snapshot carries a generation/sequence;
5. discard queued updates not newer than that generation;
6. apply later updates in canonical order.

Add subtrees, TTLs, conflict policy, and HA only as required.
