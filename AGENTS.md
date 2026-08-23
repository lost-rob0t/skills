# AGENTS.md

Canonical instructions for agents editing this repository.

## Contract

Skills are small operational contracts, not essays and not snapshots of the author's machine.

Prefer this semantic shape when it fits:

1. Goal
2. Input
3. Output
4. Rules or workflow

Front matter must identify the skill. The `description` field is selection metadata, not prose: use 2–8 comma-separated keywords only. Keep the body concise, preferably about 80 lines or less. Move detail into `references/`, scripts, or repository docs.

## Canonical source

Every durable skill lives once under `skills/<name>/`.

Do not create independently edited OpenCode, Claude, `.agents`, Agent Zero, or other runtime copies. Client layouts are deployment adapters derived from the canonical package. `$HOME/skills` is the canonical local checkout for this repository.

See `docs/formats.md` for adapter, validation, and import rules.

## Portability

Before adding or editing a skill, scan for author-specific assumptions:

- `lost-rob0t/*` repositories;
- usernames, hostnames, absolute home paths, or machine names;
- private infrastructure or DNS;
- a particular dotfiles/configuration manager;
- MCP server names that only exist because of one personal config;
- commands whose dependencies are not declared.

Convert those assumptions into portable semantics:

- state the required capability, package, service, or protocol;
- document the minimum installation/configuration needed;
- discover the current user's real configuration source instead of assuming the author's;
- when authorized and tooling permits, edit that source declaratively and document what changed;
- keep an author-specific fast path only when it is explicitly scoped as compatibility, never as the universal default;
- use configurable paths, environment variables, runtime discovery, or user-provided values instead of hardcoded personal paths.

Do not expose private infrastructure while making a skill portable.

## Imported corpora

Raw agent backups are never repository content.

Before importing a skill, remove target-specific operational state, credentials, tokens, private keys, client identifiers, personal identifiers, addresses, internal DNS, target hosts, scan output, session state, and collected evidence. Preserve reusable technique, tooling, sequencing, verification, scripts, references, and assets.

Never paste raw private values into issues, PRs, commit messages, documentation, or CI output. Discuss the category of removed information instead.

## Repository changes

For a new skill:

1. create `skills/<name>/SKILL.md` and any support files;
2. add it to the canonical `skills` catalog in `flake.nix`;
3. update `.github/workflows/nix.yml` so CI checks the exported name and package;
4. add or adjust a client adapter only when current client behavior requires it;
5. update README/docs only when the new behavior changes repository semantics or setup;
6. run the narrowest relevant validation, then the full required checks.

Existing `lib.opencodeSkills` and `lib.opencodeSkillNames` are compatibility aliases. They must reference the canonical catalog, not a second source tree.

Do not edit generated installed copies of skills as their durable source.

## Dependencies

Declare only dependencies the skill actually needs. Prefer capabilities over personal implementation details.

Bad:

```text
Use lost-rob0t/dotfiles and its prolog MCP config.
```

Better:

```text
Requires a Prolog MCP server exposing the operations used below. Configure it in the user's agent runtime if absent.
```

If setup is non-trivial, keep the skill contract short and link to `references/` or `docs/`.

## Verification

Run the repository-authoritative manifest gate with `bash scripts/validate-skills`; its Agent Skills specification/reference-validator revision is pinned in `docs/formats.md`.

A change is complete when:

- every canonical skill passes `bash scripts/validate-skills`;
- the skill still performs the intended operation;
- its description is 2–8 comma-separated keywords with no prose;
- personal assumptions are scoped or removed;
- dependencies and configuration are explicit;
- links and paths resolve;
- the canonical flake catalog, compatibility aliases, adapters, and CI agree;
- required checks pass.
