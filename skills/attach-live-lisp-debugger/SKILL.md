---
name: attach-live-lisp-debugger
description: common-lisp, sbcl, slynk, swank, debugger, backtrace
compatibility: Requires Python 3.10+, Linux procfs, and an existing authorized same-user IPv4-loopback Slynk endpoint. Swank requires independent protocol validation.
---
# Attach a live Lisp debugger

## Establish scope before connecting

Resolve the host, environment, application, PID, executable, start time and exact existing debugger endpoint from service configuration and OS process/socket ownership. Ask when ambiguous. Use the user's selected execution environment and its authorized access path. A request to create this skill is not permission to attach to a service.

Treat the debugger as arbitrary code execution capability. Even connecting can install global debugger hooks; a nominally read-only thread listing updates debugger bookkeeping. Explain and obtain scoped attachment approval, including impact on latency and condition handling. Do not attach to production or another user's process by assumption. Never create or expand persistent debug access, public listeners, tunnels, credentials, OS permissions or security settings as an attachment workaround. Never use ptrace, signal injection, `/proc` memory writes or denied network workarounds.

Use an already authorized loopback endpoint. Inspect the installed Slynk/Swank source/version before use; do not assume they are interchangeable. Read [references/protocol.md](references/protocol.md) for tested RPCs, limits and connection side effects. Confirm disconnect consequences before starting, especially if a condition will be suspended on the client connection.

## Inspect live state

Prefer a version-matched existing SLY/SLIME client when available. For a Linux IPv4-loopback endpoint, the bundled standard-library Python helper verifies the listener belongs to the same-user PID, checks executable/start time and verifies the protocol's PID before requesting any application diagnostics:

```sh
python3 scripts/inspect_lisp.py --pid PID --port PORT --protocol slynk \
  --authorized-attach --disconnect-approved --watch-seconds 10
```

Run relative to this skill's directory. Flags record already obtained scope; they never grant authorization. The helper sends only connection-info, list-threads and debugger-info-for-emacs. It cannot evaluate arbitrary forms, invoke restarts, interrupt threads or livepatch code. Default evidence suppresses all server strings. `--include-details` exposes bounded names/condition text/frame arguments locally; use it only when needed, review every string and manually remove secrets/private payloads before sharing. Pattern redaction alone is insufficient.

A connection with no `:debug` event does not prove no condition exists anywhere. Existing debugger clients may own other suspended conditions. Never fabricate a backtrace from logs or from a different worker. Use an observed debug thread and level for condition/restart/frame inspection. The helper queries the live debugger for up to 20 frames after receiving its event, with a hard maximum of 50 per RPC. Preserve restart names and indices as observations, not choices.

If an unbroken thread's stack is needed, first obtain separate explicit permission to interrupt that exact thread. Interruption can alter application timing. Use the installed client's supported thread-debug command only after validating its implementation. Never send an arbitrary eval to simulate inspection.

## Changes and safe exit

Before evaluating a user form, compiling/redefining code, changing a binding, invoking any restart, stepping, resuming, aborting or interrupting, obtain explicit scoped approval naming the PID/thread/condition, exact action, expected impact and rollback when applicable. Listing a restart is not approval to select it. Do not replay stale restart indices after condition level changes. The helper intentionally has no mutation escape hatch; use a separately approved, version-matched client action.

Disconnect only the connection you created. Do not stop the debugger server, close someone else's session, kill application threads or select ABORT merely to tidy up. Disconnect may unwind or strand a suspended condition depending on implementation; describe the verified behavior and require approval if application state can change. If the owner wants to keep interactive control, use an existing persistent SLY/SLIME session rather than this bounded helper. Recheck the same PID/start time and approved health check after detaching; report uncertainty or failures immediately.

Report identity, endpoint and protocol, observed thread/condition, bounded relevant frames/restarts, evidence redactions, actions actually taken and post-detach state. Separate observations from hypotheses.

## Unsupported and missing-debugger paths

If no debugger endpoint exists, say live attachment is unavailable through this workflow. Propose a separately approved development restart with a loopback debugger; never inject a server into the process or enable it persistently. Do not install dependencies without authorization. Port/authentication mismatch, inaccessible socket ownership, unsupported protocol, oversized/malformed replies or denied actions are stop conditions, not reasons to bypass checks.

For JVM-hosted Lisp, distinguish ABCL/Slynk from Java/JDWP; do not treat a Java PID as SBCL. For ECL embedded in another runtime, do not invoke Lisp across foreign threads or inject debugger hooks without that host's documented safe lifecycle/thread bridge. The bundled helper is tested on SBCL/Slynk only; Swank selection requires compatible installed source and a disposable validation first.
