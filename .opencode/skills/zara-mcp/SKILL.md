---
name: zara-mcp
description: Configure, inspect, verify, and troubleshoot Zara's native Model Context Protocol client, including stdio and Streamable HTTP servers, tools, resources, prompts, lifecycle, and secret-safe configuration. Use when working on Zara MCP setup or validating an MCP server through Zara; do not substitute OpenCode's own MCP configuration for Zara's client.
license: MIT
compatibility: OpenCode with a Zara build that includes native MCP client support
metadata:
  opencode/slash: "true"
---

# Zara MCP

Use this skill when the task is specifically about **Zara acting as an MCP client/host** for external Model Context Protocol servers.

Do not confuse this with configuring OpenCode itself as an MCP client. Zara owns the MCP sessions and exposes discovered capabilities to Zara's normal agent tool registry.

## Start with the runtime

Confirm the installed Zara build exposes the MCP management surface:

```sh
zara mcp --help
zara mcp status
```

If `zara mcp` is missing, update/fix the Zara build. Do not create a second ad-hoc MCP client inside the OpenCode task just to work around a stale Zara install.

## Inspect before changing configuration

Prefer discovery before mutation:

```sh
zara mcp list
zara mcp status
zara mcp inspect SERVER
zara mcp tools SERVER
zara mcp resources SERVER
zara mcp prompts SERVER
```

Use the returned server state, negotiated protocol/capabilities, and discovered names as the source of truth.

## Add a stdio server

For a local MCP process:

```sh
zara mcp add filesystem \
  --transport stdio \
  --command npx \
  --arg=-y \
  --arg=@modelcontextprotocol/server-filesystem \
  --arg=/home/user/Documents
```

Then verify it:

```sh
zara mcp status
zara mcp inspect filesystem
zara mcp tools filesystem
```

A stdio `command` executes with Zara's OS user privileges. Do not add or run an untrusted command merely because it claims to be an MCP server.

## Add a Streamable HTTP server

Use Zara's `http` transport for MCP Streamable HTTP:

```sh
export RESEARCH_MCP_TOKEN='...'

zara mcp add research \
  --transport http \
  --url https://example.com/mcp \
  --header 'Authorization=Bearer ${RESEARCH_MCP_TOKEN}'
```

Keep credentials in environment variables or another appropriate secret source. Do not hard-code tokens in skill files, repository files, command transcripts intended for commit, or URLs.

Zara rejects credentials embedded in HTTP URLs. TLS verification should remain enabled.

## Configuration files

Zara reads MCP settings from its normal configuration and from the managed companion file:

```text
~/.config/zarathushtra/config.toml
~/.config/zarathushtra/mcp.toml
```

A normal configuration can include:

```toml
[mcp]
connect_timeout = 10
request_timeout = 60
refresh_interval = 30

[mcp.servers.filesystem]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/Documents"]

[mcp.servers.research]
transport = "http"
url = "https://example.com/mcp"
headers = { Authorization = "Bearer ${RESEARCH_MCP_TOKEN}" }
```

Prefer `zara mcp add/enable/disable/remove` when managing the companion file rather than rewriting unrelated Zara configuration.

## Enable, disable, remove

```sh
zara mcp disable SERVER
zara mcp enable SERVER
zara mcp remove SERVER
```

After any change, run `zara mcp status` and the relevant inspection command. Do not infer that configuration syntax alone proves the server is usable.

## Capability identities

Zara keeps a stable internal MCP tool identity equivalent to:

```text
mcp.<server>.<remote-tool>
```

Model-visible LangChain tool names are sanitized into forms equivalent to:

```text
mcp__<server>__<remote-tool>
```

Do not assume a remote tool can overwrite a native Zara tool. Name collisions should remain explicit and deterministic.

MCP **resources** remain resources and MCP **prompts** remain prompts. Do not flatten everything into fake tools when diagnosing or extending the integration.

## Runtime behavior to preserve

When editing or reviewing Zara MCP code, preserve these invariants:

- one owned client/session lifecycle per configured server;
- stdio and Streamable HTTP use the official MCP Python SDK transport paths;
- discovered tools enter Zara's existing LangChain tool registry rather than a second registry;
- resources and prompts retain their MCP identity;
- timeouts and cancellation are bounded per operation;
- a failed possibly-effectful tool call is **not automatically replayed**;
- reconnect is for future operations only;
- one failed MCP server must not take down unrelated servers or Zara's UI loop;
- shutdown closes MCP sessions and supervised stdio children cleanly;
- configured header/environment secrets stay out of diagnostics and logs.

## Debugging order

Use this order instead of guessing:

1. `zara mcp status`
2. `zara mcp inspect SERVER`
3. `zara mcp tools SERVER`
4. `zara mcp resources SERVER`
5. `zara mcp prompts SERVER`
6. inspect Zara logs for the named server lifecycle/operation
7. inspect the server process or remote endpoint only after Zara-side evidence identifies the failing boundary

Typical lifecycle states include `configured`, `starting`, `initializing`, `ready`, `failed`, `stopping`, and `stopped`.

For a stdio failure, verify the executable and arguments under the same environment/user Zara runs with. For HTTP, verify the endpoint and secret environment are available without printing the secret.

## Verification when changing Zara MCP

Do not accept skipped MCP tests as success. The supported Nix environment should contain MCP Python SDK major version 2 and execute the real MCP tests.

At minimum run the repository's focused MCP tests plus the canonical project gates available in the checkout. The full Zara gate is authoritative:

```sh
nix develop -c bash scripts/test-all.sh
nix flake check
```

When GitHub Actions exists for the branch/PR, exact-head CI is the final observable oracle.

## Boundary

This skill is an operator/developer procedure for **using Zara's MCP client**. It does not authorize:

- implementing an unrelated MCP stack in OpenCode;
- silently installing arbitrary stdio servers;
- weakening TLS or secret handling;
- replaying failed effects;
- bypassing Zara's ordinary tool/runtime boundaries.
