---
name: node-red-starintel
description: node-red, starintel, prolog-rlm, hackmode, palettes, flows, examples, deploy
---

# Node-RED StarIntel palettes

## Goal

Operate and extend the StarIntel Node-RED palette family:
`starintel-labs/node-red-starintel`, `starintel-labs/node-red-prolog-rlm`,
`starintel-labs/node-red-hackmode`. Checkouts live in
`~/Documents/Projects/node-red-*` on their default branches; work happens in
`~/git/worktrees/<repo>-<slug>` worktrees.

## Running stack

- Node-RED runs as a systemd **user** service from the dotfiles home-manager
  module (`node-red.enable`, exported as `homeManagerModules.nodeRed`):
  `systemctl --user status node-red`, editor at `http://127.0.0.1:1880`,
  userDir `~/.node-red`, flows file `~/.node-red/flows.json`.
- Install local palettes: `cd ~/.node-red && npm install ~/Documents/Projects/node-red-{starintel,prolog-rlm,hackmode}`
  then `systemctl --user restart node-red`.
- Verify registration: `curl -s localhost:1880/nodes | grep -o 'red-module:[a-z0-9-]*'`.
- The real starintel-server stack: `cd ~/starintel/starintel-server && nix build .#star-server-image .#couchdb-image .#clouseau-image .#rabbitmq-image && nix run .#load-images && docker compose up -d`; API on `127.0.0.1:5000` (auth mode api-key in compose; secrets in `./secrets/`).

## Node surfaces

- starintel: `starintel-server` (config), `starintel-documents` (CRUD/search/by-X), `starintel-actors` (manifest discovery/dispatch/publish), `starintel-target` (canonical target docs -> `POST /new/target/:actor`), `starintel-pro-actors` (17-actor catalog from pro-actors manifests.py), `starintel-filter` (rule engine), `starintel-operations` (dtype operation lifecycle), `starintel-input`/`starintel-emit` (canonical doc flow), `starintel-flow-manager` (admin API: agents reconfigure node-red), `starintel-ui` (data pages at `/starintel-ui/<path>`), `message2org` (messages -> Org), `starintel-rlm` (agentic: dataset context -> prolog-rlm loop).
- prolog-rlm: `prolog-rlm-runtime` (provider presets incl. **llm.starintel.actor** — qwen3-8b, key from `STARINTEL_LLM_API_KEY` env only), `rlm`, `rlm-direct`.
- hackmode: `hackmode-runtime` (**source=auto** clones the monorepo into XDG data; no manual checkouts), `hackmode` (eval), `hackmode-tool` (per-tool family; ASDF system + `{{payload}}`/`{{args}}` template).

## Verification

```sh
cd ~/Documents/Projects/node-red-<repo> && node --test   # deterministic, offline
nix flake check
```

Live lane (prolog-rlm): `RLM_E2E=1 RLM_HOME=~/Documents/Projects/prolog-rlm node --test`.

## Extension recipes

- New starintel node: `node scripts/generate-node.js my-node "My label" --server` (scaffold + registration), then implement + test.
- New hackmode tool node: `node scripts/generate-tool-node.js <asdf-system> '<form template>' "<label>"` — the Kali/nix coverage slices stamp nodes this way.
- Regenerate examples: `python3 scripts/gen-examples.py` (starintel). Examples live in each repo's `examples/` and appear in the editor under Import > Examples.
- Catalog refresh after pro-actors changes: exec `ACTOR_MANIFESTS` from
  `~/starintel/starintel-pro-actors/python/src/starintel_pro_actors/manifests.py`
  (stub `pika`) into `lib/pro-actor-catalog.json`.

## Invariants

- Credentials only as env-var names; never in argv, flows, or logs.
- Subprocesses via execFile argv arrays; hard timeouts kill children.
- starintel-server is LAN-only; strict v0.9 document fields (base 0.9.0, release 0.9.1 per schema lock).
- Design mode is Auto-RAGE, recorded per repo in AGENTS.md; keep rage/ run logs and docs/research records current.
