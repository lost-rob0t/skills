# Operating the Forgejo Copilot service

Deployment and recovery detail for the `forgejo-copilot` daemon. The
`SKILL.md` contract covers enable/config semantics; this file covers
running it as a service.

## Environment file layout

Keep secrets in one root-readable file, referenced by the unit and never
committed to any repository:

```ini
# /etc/forgejo-copilot/env  (mode 0600, owner root)
FORGEJO_URL=https://git.example.com/api/v1
FORGEJO_TOKEN=<bot-account token>
OPENROUTER_API_KEY=<key or unset>
FALLBACK_LLM_URL=<openai-compatible endpoint or unset>
FALLBACK_LLM_KEY=<key or unset>
BRAVE_API_KEY=<key or unset>
```

`FORGEJO_URL` and `FORGEJO_TOKEN` are the only fail-fast variables; the
model credentials are read at request time and may be omitted when the
tier in use does not need them.

## systemd unit

The daemon polls outbound only. Run it under a dedicated user with a
durable state directory; do not open any inbound port.

```ini
# /etc/systemd/system/forgejo-copilot.service
[Unit]
Description=Forgejo Copilot bot (polling)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=forgejo-copilot
Group=forgejo-copilot
EnvironmentFile=/etc/forgejo-copilot/env
WorkingDirectory=/opt/forgejo-copilot          # the checkout
StateDirectory=forgejo-copilot                 # -> /var/lib/forgejo-copilot
ExecStart=/usr/bin/swipl -s bin/copilot-service.pl -- \
  --forever --repo owner/name --state-dir /var/lib/forgejo-copilot/run
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/forgejo-copilot

[Install]
WantedBy=multi-user.target
```

Repeat `--repo owner/name` once per watched repository — the watch list is
CLI-only (there is no repo environment variable). Adjust paths to the
actual SWI-Prolog binary and checkout location. If the prolog-rlm pack is
not installed system-wide, add it to the unit environment, e.g.
`Environment=SWIPL_PACK_PATH=/opt/prolog-rlm/pack` or
`Environment=PROLOG_RLM_HOME=/opt/prolog-rlm`.

## Lifecycle

```sh
systemctl edit forgejo-copilot && systemctl daemon-reload   # config change
systemctl restart forgejo-copilot                           # apply + resume
journalctl -u forgejo-copilot -f                             # logs
systemctl stop forgejo-copilot                               # drains nothing:
                                                            # state is durable
```

A restart is safe at any time: on start the daemon resumes paused runs
from checkpoints before polling, and one admitted run per
`(repo, pr, sha)` is recorded in the effect ledger, so a crash and
restart neither drops nor duplicates work.

## Cron / CI mode

`--once` resumes paused runs, polls every watched repository one time, and
exits 0 — suitable for a timer or scheduled CI job with the same
environment file. Unknown flags exit 2; a missing environment exits 1
with a message naming the variable.

## State directory

`--state-dir` (default `state/run` in the checkout) holds the cursor, the
effect ledger, and run checkpoints. It is the only writable data the
service needs.

- To replay nothing and re-admit a run, prefer a new mention after a force
  push (a new sha re-admits by design) instead of deleting ledger files.
- Back it up with the host: losing it loses deduplication history, and the
  bot may re-post work it already reported.
- Never hand-edit ledger or checkpoint files; if a run is wedged, stop the
  daemon, capture the state dir, and fix forward in the checkout.

## Troubleshooting

| Symptom | Meaning |
| --- | --- |
| Exit 1 naming an environment variable | Fail-fast gate: set it in the environment file and restart. |
| Exit 2 on start | Unknown CLI flag; check the unit's `ExecStart` against `--help`. |
| No reaction to a mention | Repo not on the watch list, `.copilot` absent or `enabled: false` on the base branch, or the PR's base branch has no `.copilot` (PR-branch copies are ignored). |
| Mention skipped after force push or re-mention | Same `(repo, pr, sha)` already admitted — the ledger is doing its job. |
| Repeated poll errors in the journal | One bad cycle is logged and the loop continues; check `FORGEJO_URL` reachability and token validity from the host. |
| Model failures | The tier chain (primary, alternate, fallback) ended in a visible failure comment; set the missing model credential and re-mention. |
