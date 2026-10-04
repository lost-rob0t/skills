# Protocol and project notes

## Verified sources

- OpenCode skill discovery and frontmatter: https://opencode.ai/docs/skills/ (checked 2026-10-04). Project discovery uses `.opencode/skills/attach-live-lisp-debugger/SKILL.md`; global discovery uses `~/.config/opencode/skills/attach-live-lisp-debugger/SKILL.md`. Name must match the containing directory. No permission config changes are necessary merely to package this skill.
- SLY source: https://github.com/joaotavora/sly/tree/master/slynk . Always consult the version actually loaded by the target.
- SLIME source: https://github.com/slime/slime . Validate Swank independently; it is not the Slynk test target.

Discover the application's debugger startup configuration and actual runtime listener; a configured port is not proof that the server is running or attachment is authorized.

## Wire and API

SLY's `slynk-rpc.lisp` uses six ASCII hexadecimal length bytes followed by a UTF-8 S-expression payload. Length counts encoded bytes. Treat returned forms as untrusted data; never evaluate them. The Python subset reader supports lists, strings, symbols and integers and fails on unsupported reader constructs. It caps each frame at 256 KiB, nesting at 64, RPC unsolicited events and session events at 100, watch time at 60 seconds, and absolute frame/RPC deadlines. A frame may not extend the watch deadline. A reply format error closes this connection; it does not authorize fallback eval.

For Slynk from the available `sly-20260101-git` distribution, verified in `slynk.lisp`:

- `(slynk:connection-info)` returns a property list containing `:pid`, implementation and protocol `:version`.
- `(slynk:list-threads)` returns attribute labels followed by thread rows. It updates Slynk's thread-browser bookkeeping; it is not perfectly state-free.
- `(:debug THREAD LEVEL CONDITION RESTARTS FRAMES CONTINUATIONS)` identifies an active debugger context delivered to this connection.
- `(slynk:debugger-info-for-emacs 0 20)` on that exact THREAD returns condition description/type, restart descriptions, frames and continuation IDs. It requires an active debugger dynamic context.
- Request envelope: `(:emacs-rex (slynk:connection-info) "CL-USER" t ID)`; reply `(:return (:ok RESULT) ID)`. Use an integer observed thread ID in place of `t` for debugger inspection. Correlate request IDs and preserve unsolicited events. Discard already-returned contexts and fail if a debug return or replacement debug event arrives during inspection. Event level and queried state are not an atomic snapshot; label the level as event-observed, never guaranteed current.

Connection side effects matter: Slynk's default `*global-debugger*` is true, and its new-connection hook installs a global debugger hook. Do not change this setting on an existing service without separate approval. The disposable fixture disables it before opening its own listener and binds its own synthetic worker hook explicitly.

## Evidence and exit limits

Backtrace formatting can run object printers and expose arguments; no inspection is guaranteed free of application interaction. Keep frames bounded, avoid locals/object graphs by default, and do not persist raw protocol frames containing secrets. The helper is not a general Lisp client or security boundary against a hostile same-user process. PID/start-time/socket checks reduce accidental cross-attachment, not OS-level races or malicious endpoints.

The helper closes only its TCP connection and does not send a restart. That transport-only disconnect is not a guarantee a suspended application thread remains unchanged. Establish expected behavior before using its `--disconnect-approved` flag. A disposable fixture can be terminated by its owning test harness; that is not a production cleanup strategy.
