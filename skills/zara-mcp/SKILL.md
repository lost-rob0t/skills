---
name: zara-mcp
description: zara, mcp, stdio, http, tools, resources, prompts, debugging
compatibility: Agent Skills-compatible coding agent with a Zara build that includes native MCP client support
---

# Zara MCP

Operate and verify Zara's native MCP client without confusing it with the calling agent's own MCP configuration.

## Workflow

1. Run this skill's read-only `scripts/doctor.py [SERVER]` helper. Without a server it checks `zara mcp --help` and status; with a server it also checks inspect, tools, resources, and prompts. It does not mutate configuration and redacts common bearer/URL/query secret shapes if diagnostic output is requested.
2. Inspect before mutation: `list`, `status`, `inspect SERVER`, `tools SERVER`, `resources SERVER`, `prompts SERVER`.
3. Configure the smallest required server through Zara's MCP surface.
4. Keep credentials in environment variables or an appropriate secret source; never commit or print them.
5. Verify the server becomes usable and expected capabilities are discovered.
6. After add/enable/disable/remove, rerun the doctor plus relevant inspection.
7. For code changes, run focused tests, the repository gate, and exact-head CI.

## Transports

For stdio, configure an executable plus arguments. Treat it as code executed with Zara's OS privileges; do not run untrusted servers merely because they speak MCP.

For Streamable HTTP, use Zara's HTTP transport, keep TLS verification enabled, and reference secrets indirectly rather than embedding credentials in URLs or committed files.

## Configuration

Prefer Zara's managed MCP commands over rewriting unrelated configuration. If direct configuration is required, discover the active Zara config instead of assuming an author's path.

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

- one owned client/session lifecycle per configured server;
- supported stdio and Streamable HTTP transport paths;
- discovered tools enter Zara's existing registry;
- resources stay resources and prompts stay prompts;
- remote tools cannot silently overwrite native tools;
- bounded timeouts and cancellation;
- failed possibly-effectful calls are not automatically replayed;
- reconnect applies only to future operations;
- one failed server cannot take down unrelated servers or the UI loop;
- shutdown closes sessions and supervised stdio children;
- secrets stay out of diagnostics and logs.

## Debugging

1. run `scripts/doctor.py [SERVER]`;
2. inspect Zara's lifecycle/error evidence;
3. inspect the server process or endpoint after locating the failing boundary.

For stdio, verify executable/arguments under Zara's actual user and environment. For HTTP, verify reachability and secret availability without printing the secret.

## Verification

Use the target Zara repository's focused MCP tests and canonical full gate. For the current Zara tree:

```sh
nix develop -c bash scripts/test-all.sh
nix flake check
```

Exact-head CI is authoritative when provided.

## Rules

- Do not substitute another host's MCP configuration for Zara's client.
- Do not weaken TLS or secret handling.
- Do not replay failed effects.
- Do not claim success from configuration syntax alone; verify runtime discovery.
