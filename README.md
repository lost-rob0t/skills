# skills

Reusable agent skills as small operational contracts.

This repository is the source for skills that can be installed into different agent runtimes without requiring the author's workstation, dotfiles, usernames, hosts, or private infrastructure.

## Semantics

A skill should describe the smallest repeatable procedure that changes an agent's behavior.

- Keep `SKILL.md` short. Prefer roughly 80 lines or less when the task allows it.
- Keep front-matter `description` extremely short: 2–8 comma-separated keywords, no prose.
- Describe capabilities and dependencies, not one person's machine layout.
- Put deterministic work in scripts beside the skill.
- Put long explanations, examples, and integration notes in `references/` or `docs/`.
- Do not duplicate policy between skills. Compose or link instead.
- Preserve the user's existing configuration model rather than forcing the author's.

See [`docs/semantics.md`](docs/semantics.md), [`docs/portability.md`](docs/portability.md), and [`docs/formats.md`](docs/formats.md).

## Layout

```text
skills/<skill>/SKILL.md    canonical platform-neutral skill contract
docs/                      repository-wide semantics and conventions
AGENTS.md                   canonical contributor/agent rules
flake.nix                   canonical catalog plus client deployment adapters
```

Client-specific paths are deployment views. Do not maintain separate editable copies for OpenCode, Claude, Codex, Cursor, Copilot, Agent Zero, or another compatible runtime.

## Skills

- `activitywatch-analyze` - activitywatch, analysis, time-use, workflow-patterns, privacy.
- `activitywatch-group` - activitywatch, window-groups, qtile, clustering, routing.
- `activitywatch-productivity` - activitywatch, productivity, friction, routines, recommendations.
- `activitywatch-visualize` - activitywatch, visualization, timelines, heatmaps, privacy.
- `discover-workflows` - discover repeated Bash, Emacs, and ActivityWatch workflows for dotfiles suggestions.
- `dotfiles-workflow` - dotfiles, declarative-config, nix, home-manager, mcp.
- `forgejo-repo-bootstrap` - forgejo, repositories, adard, issues, bootstrap, provenance.
- `forgejo-skill-edit` - skills, forgejo, editing, validation, gitflow, pull-request, CI.
- `git` - git, forgejo, github, hosting, remote, fallback, pr, issues.
- `git-worktrees` - git, worktrees, parallel-work, branch-isolation, pr-review, cleanup.
- `impeccable` - design, frontend, ui, ux, audit, polish, accessibility, impeccable. External integration of `pbakaus/impeccable` (Apache-2.0).
- `prolog-reasoning` - prolog, symbolic-reasoning, constraints, verification, mcp.
- `qtile-confirm` - qtile, screenshots, vision, visual-regression, bar-layout.
- `qtile-debug` - qtile, diagnostics, logs, IPC, crash-analysis.
- `qtile-edit` - qtile, literate-config, tangle, configuration, tests.
- `qtile-reload` - qtile, reload, IPC, validation, runtime-verification.
- `rage` - rage, issues, research, design, tdd, verification, ci, merge.
- `skill-edit` - skills, editing, validation, gitflow, pull-request, CI.
- `skill-portability` - portability, dependencies, configuration, redaction, adapters.
- `star-lang` - star-lang, common-lisp, compiler, runtime, actors, manifests, nix.
- `starintel-actor-create` - starintel, actors, star-lang, sento, plugins, manifests, testing.
- `starintel-auto-dig` - starintel, auto-dig, osint, recursion, documents, relations, validation.
- `starintel-document-create` - starintel, documents, relations, schema, validation, local-db.
- `starintel-ingest` - starintel, ingest, jsonl, local-db, remote-api, validation.
- `starintel-local-search` - starintel, local-search, jsonl, ndjson, relations, corpus.
- `starintel-osint` - starintel, osint, research, evidence, provenance, corroboration, sources.
- `starintel-repo-bootstrap` - github, repositories, adard, issues, bootstrap, provenance.
- `status-update` - notify-send, dunst, libnotify, desktop-notifications, status, task-completion.
- `sudo` - sudo, privilege-escalation, desktop-portals, xdg-desktop-portal, polkit, authentication.
- `task-steward-bootstrap` - steward, bootstrap, a0, opencode, agents, adapters.
- `task-steward-worker` - steward, rage, leases, fencing, heartbeat, receipts.
- `youtube-context` - youtube, transcripts, yt-dlp, whisper, video-context.
- `zara-mcp` - zara, mcp, stdio, http, tools, resources, prompts, debugging.

## Portable dependencies

A skill may require Git, Nix, Home Manager, an MCP server, a program, or another capability. State that requirement directly.

Do not make `lost-rob0t/dotfiles`, `$HOME/.dotfiles`, a specific username, hostname, or private service a universal dependency. If an author-specific setup is useful, keep it as a narrowly scoped compatibility path and document the generic requirement first.

When configuration is needed, discover the user's actual configuration source. If the agent is authorized and has the tools, it may edit that source and document the change. Otherwise, provide the minimum configuration the user must add.

## Import privacy and attribution

External agent backups are source material only. Strip target-specific operational data, credentials, private infrastructure, client identifiers, addresses, scan output, session state, and collected evidence before committing an imported skill. Preserve reusable procedures, tooling, validation logic, scripts, references, and assets.

Externally authored skills remain externally authored after import or adaptation. Preserve the upstream project/source URL, author or organization attribution, license, and a version/tag/revision when available. Put provenance in `SKILL.md` metadata and make attribution visible in the skill or a linked reference; do not imply the repository maintainer created upstream work.

Raw backups and redaction maps do not belong in this repository, issues, PRs, or CI logs.

## Flake and adapters

The flake exports the canonical catalog as `lib.skills` and `lib.skillNames`. Existing consumers may continue using the compatibility aliases `lib.opencodeSkills` and `lib.opencodeSkillNames`.

Per-client outputs cover OpenCode, Claude Code, generic Agent Skills, Codex, Cursor, GitHub Copilot, and Agent Zero. Fixed user-global clients have Home Manager modules under `homeManagerModules`; Agent Zero uses `lib.mkAgentZeroHomeManagerModule` because its `usr/skills` path is relative to the installation root.

```sh
nix flake metadata
nix eval --json .#lib.skillNames
nix eval --json .#lib.targets
nix eval --json .#lib.adapters
```

New skills must be added to the canonical catalog in `flake.nix` and to CI validation in `.github/workflows/nix.yml`.
