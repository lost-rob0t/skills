# Skill semantics

## Unit of design

A skill is one narrow, reusable operation an agent can select and execute.

It should answer four questions with minimal ceremony:

- **Goal** - what behavior changes?
- **Input** - what context, files, tools, or user values are required?
- **Output** - what concrete state or result is produced?
- **Rules** - what procedure and invariants constrain execution?

Not every `SKILL.md` needs those headings literally, but the information should be obvious.

## Progressive disclosure

Keep selection metadata and the common path in `SKILL.md`.

Move material outward when it is not needed on every invocation:

```text
SKILL.md      selection + operational contract
scripts/      deterministic transformations or checks
references/   detailed integration notes and examples
docs/         repository-wide semantics and policy
```

The agent should not pay token cost for a manual when it only needs a procedure.

## Composition

Prefer multiple narrow skills over one giant skill.

A skill may depend on another capability, but it should not copy that capability's full instructions. Name the dependency and link to its canonical contract when possible.

## Configuration semantics

Represent configuration by intent and ownership:

```text
required capability -> discover current owner -> edit declarative source -> verify generated behavior
```

Do not encode one author's path or repository as the meaning of the capability.

For example, "configure an MCP server" is the semantic operation. Editing `lost-rob0t/dotfiles` is only one implementation of that operation for one environment.

## Scripts

Use scripts when the same deterministic transformation would otherwise be repeatedly re-described or reimplemented by the model.

Scripts belong beside the skill that owns them. They should have explicit inputs, fail loudly, and avoid hidden user-specific state.

## Brevity

Default to the smallest contract that is still executable. Roughly 80 lines for `SKILL.md` is a useful pressure, not a reason to omit required safety, dependencies, or verification.
