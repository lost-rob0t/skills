# AGENTS.md

Canonical instructions for agents editing this repository.

## Contract

Skills are small operational contracts, not essays and not snapshots of the author's machine.

Prefer this semantic shape when it fits:

1. Goal
2. Input
3. Output
4. Rules or workflow

Front matter must identify the skill and explain when it should be selected. Keep the body concise, preferably about 80 lines or less. Move detail into `references/`, scripts, or repository docs.

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

## Repository changes

For a new OpenCode skill:

1. create `opencode/<name>/SKILL.md`;
2. add it to `opencodeSkills` in `flake.nix`;
3. update `.github/workflows/nix.yml` so CI checks the exported name and file;
4. update README/docs only when the new behavior changes repository semantics or setup;
5. run the narrowest relevant validation, then the full required checks.

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

A change is complete when:

- the skill still performs the intended operation;
- personal assumptions are scoped or removed;
- dependencies and configuration are explicit;
- links and paths resolve;
- the flake catalog and CI agree;
- required checks pass.
