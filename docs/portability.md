# Portability

Portable does not mean lowest-common-denominator. It means the skill states what it needs without confusing the author's implementation with the requirement.

## Rewrite model

When a skill contains personal assumptions, classify each one before editing it:

| Assumption | Portable form |
| --- | --- |
| personal repository | required capability plus optional implementation example |
| absolute home path | discovered/configured path |
| username or hostname | runtime value or user configuration |
| personal MCP registration | required MCP capability and setup instructions |
| private service/DNS | abstract service requirement, never leaked infrastructure |
| personal config manager | discover the user's actual config owner |

Preserve the operation. Replace only the coupling.

## Dependency rule

State dependencies at the level the skill actually consumes.

If a skill only calls a Prolog MCP server, its dependency is a compatible Prolog MCP server, not the author's dotfiles repository that happened to register one.

If exact tool names or protocol operations matter, list them. Do not invent a package or installer when the dependency cannot be verified.

## Configuration rule

When a required capability is missing:

1. inspect the current runtime and existing configuration when tools allow it;
2. identify the declarative source that owns that configuration;
3. edit it when the user requested the change and the agent is authorized;
4. otherwise provide the smallest configuration fragment or dependency instructions needed;
5. document non-obvious setup near the skill or in repository docs;
6. verify the resulting capability, not merely the source edit.

Do not silently migrate a user to Nix, Home Manager, a particular dotfiles layout, or any other configuration system.

## Owner compatibility

Author-specific optimizations may remain when they are useful, but they must be explicitly scoped.

Example:

```text
Generic: discover the user's Home Manager target or activation workflow.
Owner compatibility: for the original unseen@desktop setup, preserve its known target.
```

The generic path remains authoritative for everyone else.

## Brevity rule

Do not solve portability by turning every skill into an installation manual.

Keep `SKILL.md` focused on the executable contract. Put longer setup recipes in `references/` or `docs/` and link them from the dependency line.
