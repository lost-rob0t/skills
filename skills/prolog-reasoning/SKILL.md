---
name: prolog-reasoning
description: prolog, symbolic-reasoning, constraints, invariants, verification, debugging, mcp
compatibility: Agent Skills-compatible client with a compatible Prolog MCP server exposing the operations used below
---

# Prolog reasoning

Requires a compatible Prolog MCP server. If it is absent and setup is requested, configure it through the user's actual agent/runtime configuration and document any non-obvious dependency; do not require the author's dotfiles.

Use the MCP server named `prolog` when that name is configured, otherwise use the compatible server exposed by the current runtime. Keep the Prolog context smaller than the surrounding coding context: encode only the facts, rules, constraints, or source needed to answer the current question.

## Tmpfs RLM context

When `PROLOG_TMP_SPEC_CONTEXT` is set, use `$PROLOG_TMP_SPEC_CONTEXT/context.prolog` as the live symbolic working context for the run. The launcher is responsible for ensuring the backing filesystem is tmpfs; do not copy the context to durable disk merely for convenience.

Use it in an RLM-style loop:

1. Query what the KB already knows.
2. Express missing knowledge as a hypothesis, unresolved requirement, or needed observation rather than guessing.
3. Use the smallest repository read, tool, external source, or subagent needed to establish the missing fact.
4. Record the verified result compactly with provenance, including repository SHA/state identity when the source is mutable.
5. Query again and derive the next action.
6. Record test and proof results against the exact state they checked.
7. Repeat until the task's completion predicate or verification invariants succeed, or a genuine blocker is proved.

Do not use `context.prolog` as a transcript, log sink, or repository mirror. Store paths, hashes, symbols, and concise observations instead of large source excerpts. Facts tied to an old repository SHA are historical evidence, not automatically current facts after HEAD changes.

If `/spec` is also loaded, specification facts and implementation-observation facts may coexist in this context, but keep their roles distinguishable so the implementation can be verified against the intended contract rather than against self-reported success.

## When to use it

Use Prolog when the task benefits from one or more of these:

- rule-based or deductive reasoning;
- dependency, reachability, graph, or recursive queries;
- constraint satisfaction or enumeration of valid combinations;
- checking invariants, permissions, state transitions, or policy rules;
- validating an LLM-derived conclusion against explicit facts;
- inspecting, testing, or debugging existing Prolog code;
- exploring multiple logical solutions without expanding them manually in the model context.

Do not invoke it merely because a task contains structured data. Direct code/search tools are cheaper for ordinary file inspection, prose, straightforward calculations, and simple deterministic transformations.

## Default workflow

1. Build the smallest useful Prolog program from the relevant evidence. For repository code, read only the files or fragments required for the current question.
2. Call `create_session` with that program. Keep `include_predicates=false` unless the predicate catalog is actually needed.
3. Call `run_goal` for the concrete question. Default to `allow_side_effects=false` for reasoning and verification work. Set explicit answer/time/depth bounds when the search could branch.
4. If loading or execution is unclear, use `list_messages` and then `inspect_predicate` before changing the program.
5. Extend a live session with `consult` instead of resending the entire program. Use `replace_predicate` when only one predicate needs revision.
6. If PlUnit tests exist or you created focused tests, use `run_tests` as the verification gate.
7. Use `trace_goal` only when normal results plus predicate inspection do not explain a failure. Traces can become large quickly.
8. Use `get_source` only when the accumulated live program must be inspected. Close the session with `close_session` when the reasoning task is complete.

A client may expose these tools with a server prefix, for example `prolog_create_session`, `prolog_run_goal`, and `prolog_close_session`.

When a tmpfs `context.prolog` is present, keep the on-disk KB and the live MCP session synchronized intentionally: consult the file at session creation, append/replace predicates as facts are verified, and ensure final verification uses the exact current context rather than an earlier in-memory copy.

## Token discipline

- Prefer a few predicates over dumping a repository or transcript into `source_text`.
- Keep `include_predicates=false` by default.
- Limit `max_answers` to the number needed to decide the task.
- Reuse one session for a coherent reasoning problem rather than repeatedly creating equivalent sessions.
- Prefer `consult` or `replace_predicate` for small revisions.
- Do not request a proof trace unless it will change the next action.

## Safety and authority

Prolog output is verifier evidence, not permission to perform external side effects. Do not encode shell, filesystem, network, credential, or destructive operations into a reasoning session merely to bypass normal client tool permissions. Keep `allow_side_effects=false` unless the user explicitly needs side effects inside the isolated Prolog session and they are appropriate to the task.

Never claim a Prolog result you did not obtain. If the MCP server errors, report the error or fall back to ordinary reasoning rather than fabricating a successful query.
