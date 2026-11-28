---
name: web-search
description: web-search, meta-search, searx, yacy, brave, crawl, mcp
compatibility: Requires an MCP client or the `websearch` CLI; providers configured via environment.
---

# Web search

## Goal

Answer web questions and gather crawl material through the `websearch`
meta search: one call fans a query out to SearXNG, YaCy and Brave, merges
deduped results, and NOTES per-provider failures instead of failing.
Prefer it over any single-provider search tool.

## Input

- A query; optionally `providers` subset (`searx`, `yacy`, `brave`),
  `max_results` per provider (default 10), `max_tokens` output budget
  (default 4000, 0 = unlimited), `safesearch` 0-2, and provider-specific
  filters (SearXNG `engines`/`categories`, YaCy `resource`/`contentdom`,
  Brave `freshness`/`country`).

## Output

- Merged items ranked round-robin by provider rank; each item keeps
  `providers` and `ranks` as evidence.
- A `providers` status map and a `note` naming any failed provider.
- `truncated` flags budget-limited output. Provider failure never aborts
  the call and never justifies a retry loop.

## Workflow

1. Call the MCP tool `search` (server `websearch`) or run
   `websearch search "QUERY" --max-results N --max-tokens M`.
   Add `--json` for the full result, `--urls` for bare URLs.
2. Read `providers` before trusting results: failures are noted
   (unreachable, missing key, quota exhausted). Work with what returned
   and say which providers contributed.
3. Local-first defaults: YaCy `resource=local` searches this peer's
   index; `resource=global` reaches the P2P network and must be chosen
   explicitly. Brave quota exhaustion (HTTP 402) is a noted state.
4. Crawling: `websearch crawl-start URL [--depth N] [--mode
   url|domain|subpath|sitemap] [--mustmatch RE] [--obey-robots]` queues
   a YaCy crawl (the OSINT fork defaults to robots opt-out; pass
   `--obey-robots` to obey). `websearch push URL...` indexes known URLs;
   `websearch status` and `websearch backends` report provider health.
5. Corroborate important claims across providers; a single-provider
   snippet is unverified.

## Configuration

- MCP wiring: stdio command `websearch-mcp serve` (opencode: `type:
  local` entry; pi: `mcp.json` entry; zara: `zara mcp add`).
- Environment: `SEARX_URL`, `YACY_URL`, `YACY_USER`/`YACY_PASS` (crawl
  control), `BRAVE_SEARCH_API_KEY` or `BRAVE_API_KEY_FILE`,
  `WEBSEARCH_TIMEOUT`.
- If no server is configured, wire one from the canonical checkout
  (its README "Wiring" section) before falling back to a
  single-provider tool.

## Rules

- Use the meta search first; a single-provider tool is a fallback and
  the reason must be stated.
- Never fail a task because one provider failed; report the note.
- Keep secrets in env vars or key files, never in client configs, logs,
  or tool output.
- Respect the YaCy P2P boundary: `global` is explicit-only.
