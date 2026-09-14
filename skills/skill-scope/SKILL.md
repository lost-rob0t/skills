---
name: skill-scope
description: skills, scope, local, global, discovery, creation
compatibility: Agent Skills-compatible agent with filesystem access
---

# Skill Scope

## Goal

Resolve skill origin and edit ownership without confusing installed global skills
with project-local skills.

## Workflow

1. Run `scripts/skill-scope list --project "$PWD"` to inventory both scopes.
2. Project-local skills are only `.opencode/skills/<name>` and
   `.agents/skills/<name>` beneath the current repository.
3. Global installed skills are runtime views; the editable source is
   `OPENCODE_GLOBAL_SKILLS_CHECKOUT`, falling back to `~/Documents/AI/skills`
   for this owner environment.
4. For creation, require `--scope local|global`. Never infer global merely
   because an installed skill exists.
5. Use `skill-edit` for validation, tests, and publishing after ownership is
   resolved.

## Rules

- Never edit Nix store paths or generated runtime adapters.
- Prefer local scope when a workflow belongs to one project.
- Use global scope only for genuinely reusable workflows or explicit requests.
- Report the origin path with every listed skill.
