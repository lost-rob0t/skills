---
name: forgejo-copilot
description: forgejo, copilot, bot, enable, daemon, service
compatibility: A `forgejo-copilot` checkout (SWI-Prolog daemon) with the prolog-rlm pack importable via `SWIPL_PACK_PATH` or `PROLOG_RLM_HOME`, a reachable Forgejo REST API, a bot-account API token, and credentials for the model tiers in use.
---

# Forgejo Copilot service

## Goal

Enable and operate `@copilot`: a polling SWI-Prolog service that watches a
Forgejo instance and executes tasks mentioned on issues and pull requests
(plan, branch, implement, test, push, open a PR, reply). Opt-in is per
repository; the service holds no inbound network surface.

## Input

- a `forgejo-copilot` checkout with SWI-Prolog and the prolog-rlm pack
  importable (`SWIPL_PACK_PATH` or `PROLOG_RLM_HOME`);
- `FORGEJO_URL` (base URL of the Forgejo API, e.g.
  `https://git.example.com/api/v1`) and `FORGEJO_TOKEN` (bot account) in
  the environment; model credentials (`OPENROUTER_API_KEY`,
  `FALLBACK_LLM_URL`/`FALLBACK_LLM_KEY`, `BRAVE_API_KEY`) are optional and
  read at request time;
- the `owner/name` repositories the bot may act on.

## Output

A running daemon (or one `--once` cycle) and, per enabled repository, an
opt-in `.copilot` file on its base branch. Nothing else on the host
changes.

## Enable a repository

The `.copilot` file at the repository root on the **base branch HEAD** is
authoritative: PR events read it from the PR base branch, issue events read
it from the daemon's `--config-branch` (default: the repository's default
branch), and task runs branch from that same branch. A `.copilot` inside a
PR branch never self-enables the bot.

```yaml
enabled: true     # default true when the file is present; false opts out
model: fast       # fast | strong (default fast)
tasks: true       # execute @copilot task mentions (default true)
auto: false       # auto-review opened PRs (default true)
```

To enable or reconfigure, commit the file to the base branch — only the
landed base-branch copy counts. To disable, set `enabled: false` or remove
the file. The repository must also be on the daemon's watch list and
readable by the bot account. Enabled repositories get `@copilot <task>` on
issues/PRs, `/review` on a PR, and `/ask <question>`.

## Run the service

```sh
FORGEJO_URL=https://git.example.com/api/v1 FORGEJO_TOKEN=… \
  swipl -s bin/copilot-service.pl -- \
    --forever                      # or --once for a single cron/CI cycle
    --repo owner/name [--repo …]   # required, repeatable; none given exits 1
    [--state-dir DIR]              # default state/run — durable, keep it
    [--poll-seconds 30]
    [--config-branch BRANCH]       # issue-event config and task base
```

The daemon fails fast (exit 1) when `FORGEJO_URL`/`FORGEJO_TOKEN` are
missing or empty or no repository is given; `--help` exits 0 and unknown
flags exit 2. On start it resumes paused runs from the durable checkpoints
in the state dir before polling, and every poll cycle is
catch-and-continue. See `references/operating.md` for a hardened systemd
unit, an environment-file layout, and state recovery.

## Rules

- Secrets live only in the environment (or an `EnvironmentFile`); never in
  `.copilot`, logs, or committed files.
- Never wipe the state dir to fix a stuck run: the effect ledger
  deduplicates posts per `(repo, pr, sha)` and wiping can double-post.
- Keep the service polling-only: no inbound ports, no webhook listener.
- The bot pushes only to `copilot/*` branches and never approves or merges
  its own PRs; keep that human gate intact.
- Enable a repository only with its owner's approval; a `.copilot` on an
  unwatched repository does nothing.

## Verification

```sh
swipl -q -s bin/copilot-service.pl -- --help    # exit 0
env -u FORGEJO_URL swipl -q -s bin/copilot-service.pl -- --once --repo o/r
                                                # exit 1 = fail-fast gate works
swipl -q -s bin/copilot-demo.pl                 # credential-free pipeline smoke
```

In the checkout the full gates are `swipl -q -s test/run_tests.pl` and
`swipl -q -s verify/verify.pl`. On the Forgejo side, confirm one mention
produces exactly one admitted run and one PR under `copilot/`.
