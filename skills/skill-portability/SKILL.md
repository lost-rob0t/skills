---
name: skill-portability
description: Adapt an author-specific skill to the current user's environment without changing its intended operation. Use when a skill assumes personal dotfiles, repositories, paths, usernames, hosts, MCP registration, private infrastructure, or undeclared dependencies.
compatibility: Agent Skills-compatible coding agent with repository access; git recommended
---

# Skill portability

## Goal

Make a skill reusable by other users while preserving its behavior and keeping `SKILL.md` short.

## Input

- the target skill and its nearby support files;
- repository-level instructions such as `AGENTS.md` and `docs/`;
- the current user's runtime/configuration when it can be inspected.

## Output

A skill whose dependencies and configuration requirements are explicit, whose personal assumptions are removed or narrowly scoped, and whose setup is documented only as deeply as needed.

## Workflow

1. Read the target skill and its local docs/support files.
2. Find author-specific assumptions: repository owners, dotfiles, usernames, hosts, absolute paths, private services, config managers, MCP registrations, and undeclared commands.
3. Classify each assumption as a dependency, configuration detail, workflow rule, or optional owner optimization.
4. Rewrite dependencies as capabilities the skill actually consumes.
5. Replace personal paths/config with discovery, configurable values, or the current user's actual declarative source.
6. If configuration is missing and the user requested setup, inspect the user's environment and configure it when authorized and tooling permits. Do not impose the author's config system.
7. Put non-obvious install/config instructions in nearby docs or `references/`; keep only the required dependency and common path in `SKILL.md`.
8. Preserve useful author-specific behavior only under an explicit compatibility condition.
9. Update repository indexes, exports, and validation when the skill package or catalog changes.
10. Verify the intended operation still works and search the result for stale personal coupling.

## Rewrite rule

Prefer:

```text
Requires a compatible Prolog MCP server exposing the operations used below.
If absent, configure one in the user's agent runtime and document the chosen setup.
```

over:

```text
Use lost-rob0t/dotfiles to get the Prolog MCP server.
```

A personal repository may be an implementation example. It must not become the semantic dependency unless the operation truly requires that repository itself.

## Rules

- Preserve intent; remove coupling.
- Declare only dependencies actually consumed.
- Never leak private infrastructure while generalizing it.
- Never invent package names, config paths, or service details.
- Prefer declarative edits when the user's environment already has a declarative owner.
- Do not turn a short skill into a setup manual; link detail outward.
- Do not overwrite unrelated user configuration.
- Verify generated/runtime behavior after configuration changes.
