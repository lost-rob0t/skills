# skills

Reusable agent skills as small operational contracts.

This repository is the source for skills that can be installed into different agent runtimes without requiring the author's workstation, dotfiles, usernames, hosts, or private infrastructure.

## Semantics

A skill should describe the smallest repeatable procedure that changes an agent's behavior.

- Keep `SKILL.md` short. Prefer roughly 80 lines or less when the task allows it.
- Describe capabilities and dependencies, not one person's machine layout.
- Put deterministic work in scripts beside the skill.
- Put long explanations, examples, and integration notes in `references/` or `docs/`.
- Do not duplicate policy between skills. Compose or link instead.
- Preserve the user's existing configuration model rather than forcing the author's.

See [`docs/semantics.md`](docs/semantics.md) and [`docs/portability.md`](docs/portability.md).

## Layout

```text
opencode/<skill>/SKILL.md   skill contract
docs/                       repository-wide semantics and conventions
AGENTS.md                   canonical contributor/agent rules
flake.nix                   exported OpenCode skill catalog
```

## Skills

- `dotfiles-workflow` - declarative config ownership and safe repository workflow.
- `prolog-reasoning` - bounded Prolog MCP reasoning and verification.
- `skill-portability` - adapt author-specific skills to the current user's environment.

## Portable dependencies

A skill may require Git, Nix, Home Manager, an MCP server, a program, or another capability. State that requirement directly.

Do not make `lost-rob0t/dotfiles`, `$HOME/.dotfiles`, a specific username, hostname, or private service a universal dependency. If an author-specific setup is useful, keep it as a narrowly scoped compatibility path and document the generic requirement first.

When configuration is needed, discover the user's actual configuration source. If the agent is authorized and has the tools, it may edit that source and document the change. Otherwise, provide the minimum configuration the user must add.

## Validation

The flake exports the OpenCode skill catalog. CI checks that every exported skill exists.

```sh
nix flake metadata
nix eval --json .#lib.opencodeSkillNames
```

New skills must be added to `flake.nix` and the CI package list in `.github/workflows/nix.yml`.
