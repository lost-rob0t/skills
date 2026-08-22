# Multi-agent skill formats

## Canonical source

The repository has one durable source for each reusable skill:

```text
skills/<skill-id>/
  SKILL.md
  scripts/       # optional
  references/    # optional
  assets/        # optional
```

`skills/` is platform-neutral Agent Skills source. Client-specific trees are deployment views or generated adapters. Never hand-maintain separate OpenCode, Claude, Codex, Cursor, Copilot, Agent Zero, or other copies of the same skill body.

The canonical local checkout for editing this repository is `$HOME/skills`. Clone `lost-rob0t/skills` there if it is absent. If `$HOME/skills` already exists and is not the expected checkout, stop rather than replacing it.

## Adapter targets

The verified target matrix is:

| Target | User/global deployment view |
| --- | --- |
| OpenCode | `~/.config/opencode/skills/<skill-id>/` |
| Claude Code | `~/.claude/skills/<skill-id>/` |
| Agent Skills generic | `~/.agents/skills/<skill-id>/` |
| Codex | `~/.codex/skills/<skill-id>/` or `~/.agents/skills/<skill-id>/` |
| Cursor | `~/.cursor/skills/<skill-id>/` or `~/.agents/skills/<skill-id>/` |
| GitHub Copilot | `~/.copilot/skills/<skill-id>/` or `~/.agents/skills/<skill-id>/` |
| Agent Zero | `usr/skills/<skill-id>/` inside the Agent Zero installation |

The flake exports a Home Manager module for each user-global fixed path. Agent Zero is different: `usr/skills` is relative to its installation root, so use `lib.mkAgentZeroHomeManagerModule <install-root>` rather than guessing where Agent Zero lives.

OpenCode, Codex, Cursor, and Copilot can all consume the generic `~/.agents/skills` convention. Prefer that shared adapter when one installed tree should serve several clients. Use a client-native adapter when isolation or client-specific precedence matters. Claude Code still needs its Claude-compatible path for reliable personal discovery.

These targets share the open `SKILL.md` model. When a client needs extra metadata or installation behavior, generate or configure that adapter from the canonical package. Do not fork the instructions merely to satisfy a client path convention.

Additional clients must be added only after verifying their current documented discovery and metadata behavior.

## Existing OpenCode skills

The former `opencode/<skill-id>/` tree is migration input. Every existing OpenCode skill must move into `skills/<skill-id>/` without changing its stable ID unless an explicit rename is justified. The flake may keep compatibility aliases such as `lib.opencodeSkills`, but those aliases must point at the canonical catalog.

## Importing external skill corpora

Backups and agent workspaces are source material, not repository content.

Before committing an imported skill:

1. identify the complete skill package, including scripts, references, and assets;
2. strip target-specific and private operational state;
3. preserve reusable technique, tooling, sequencing, validation, and dependency semantics;
4. replace private literals with generic inputs, discovery, variables, or documented examples;
5. remove credentials, tokens, cookies, private keys, personal identifiers, client names, internal DNS, target IPs/domains, addresses, scan output, session state, and collected evidence;
6. deduplicate against existing canonical skills;
7. validate the final canonical package and its adapter exports.

Raw backups and redaction maps must never be committed, attached to issues or PRs, copied into documentation, or echoed into CI logs. Review/automation output should discuss categories of stripped data rather than reproducing the values.

Security and pentesting skills are allowed to retain reusable defensive/offensive-testing procedures and tool usage. What must not survive an import is the historical target state tied to a real engagement or environment.

## Flake contract

The flake exposes the canonical catalog as `lib.skills`, per-client adapter metadata as `lib.adapters`, fixed target roots as `lib.targets`, and Home Manager modules under `homeManagerModules`.

Client adapters must reference the same source paths. A migration is incomplete if changing one skill requires editing multiple durable copies.
