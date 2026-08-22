---
name: zara-mcp
description: zara, mcp, stdio, http, tools, resources, prompts, debugging
compatibility: Agent Skills-compatible coding agent with a Zara build that includes native MCP client support
---

# Zara MCP

## Goal

Operate and verify Zara's native MCP client without confusing it with the calling agent's own MCP configuration.

## Workflow

1. Confirm the installed Zara exposes `zara mcp --help` and `zara mcp status`.
2. Inspect before mutating: `list`, `status`, `inspect SERVER`, `tools SERVER`, `resources SERVER`, `prompts SERVER`.
3. Configure the smallest required server through Zara's MCP management surface.
4. Keep credentials in environment variables or an appropriate secret source; never commit or print them.
5. Verify the server reaches a usable state and that expected tools/resources/prompts are discovered.
6. After enable, disable, add, or remove operations, rerun status plus the relevant inspection command.
7. When changing Zara MCP code, run focused tests, the repository gate, and exact-head CI.

## Transports

For stdio, configure an executable plus arguments. Treat the command as code executed with Zara's OS privileges; do not install or run an untrusted server merely because it speaks MCP.

For Streamable HTTP, use Zara's HTTP transport, keep TLS verification enabled, and reference secrets through environment/config indirection rather than embedding credentials in URLs or committed files.

## Configuration

Prefer Zara's managed MCP commands over rewriting unrelated configuration. When direct configuration is required, discover the current Zara config location instead of assuming an author's home path.

Typical operations:

```sh
zara mcp status
zara mcp inspect SERVER
zara mcp tools SERVER
zara mcp resources SERVER
zara mcp prompts SERVER
zara mcp enable SERVER
zara mcp disable SERVER
zara mcp remove SERVER
```

## Invariants

- Zara owns one client/session lifecycle per configured server.
- stdio and Streamable HTTP use the supported MCP transport paths.
- discovered tools enter Zara's existing tool registry; do not create a parallel registry.
- resources remain resources and prompts remain prompts.
- remote tools cannot silently overwrite native Zara tools.
- operation timeouts and cancellation remain bounded.
- failed possibly-effectful calls are not automatically replayed.
- reconnect applies to future operations, not implicit effect replay.
- one failed server must not take down unrelated servers or Zara's UI loop.
- shutdown closes sessions and supervised stdio children.
- secrets stay out of diagnostics and logs.

## Debugging order

1. `zara mcp status`
2. `zara mcp inspect SERVER`
3. inspect tools/resources/prompts
4. inspect Zara's named server lifecycle/error evidence
5. inspect the server process or remote endpoint only after locating the failing boundary

For stdio failures, verify the executable and arguments under Zara's actual user/environment. For HTTP failures, verify endpoint reachability and secret availability without printing the secret.

## Verification

Use the target Zara repository's current focused MCP tests and canonical full gate. For the current Zara tree, prefer:

```sh
nix develop -c bash scripts/test-all.sh
nix flake check
```

Exact-head CI is the final observable merge gate when the repository provides it.

## Rules

- Do not substitute OpenCode, Claude, Codex, or another host's MCP configuration for Zara's client.
- Do not weaken TLS or secret handling to make a server connect.
- Do not replay failed effects.
- Do not claim a server is usable from configuration syntax alone; verify runtime discovery.
