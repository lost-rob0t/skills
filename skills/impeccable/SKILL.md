---
name: impeccable
description: design, frontend, ui, ux, audit, polish, accessibility, impeccable
license: Apache-2.0
compatibility: Requires Node.js/npm with npx and network access for upstream Impeccable installation or updates.
metadata:
  author: "Paul Bakaus / pbakaus and Impeccable contributors"
  source: "https://github.com/pbakaus/impeccable"
  upstream-version: "4.1.1"
  upstream-revision: "c3a30086bc395ea2197fbe287dc59c18969aaeb6"
  provenance: "external-import"
---

# Impeccable

> External upstream integration. This repository did not create Impeccable. The original project is `pbakaus/impeccable`; retain its attribution and Apache-2.0 license when copying or adapting this skill.

## Goal

Use the upstream Impeccable design language and command set for frontend design, critique, audit, refinement, accessibility, responsive behavior, typography, layout, motion, and production polish.

## Input

- a frontend project or UI target;
- the requested Impeccable operation, such as `init`, `shape`, `critique`, `audit`, `polish`, `harden`, `adapt`, or `optimize`;
- the current agent harness/provider when project-local installation is required.

## Output

Return the requested design result or code change using the upstream Impeccable workflow. Report any project files created or changed by Impeccable setup separately from the UI work.

## Workflow

1. Read [references/upstream.md](references/upstream.md) for the pinned source, supported providers, install/update commands, and provenance.
2. Prefer an existing project-local Impeccable installation when present. Do not replace or duplicate it with a hand-maintained client-specific copy.
3. If the user asks to enable Impeccable for a project, detect the active supported provider and run the maintained upstream installer from the project root: `npx impeccable install --providers=<provider> --scope=project`.
4. Reload the harness when its discovery model requires it, then use the upstream `impeccable` skill and its command routing as the authority for design work.
5. Start new projects with `impeccable init` so product and design context are durable. For existing projects, preserve the incumbent visual system unless the user explicitly requests a redesign.
6. For updates, use `npx impeccable update` rather than copying generated provider trees by hand.

## Rules

- The upstream Impeccable package and CLI own Impeccable-specific behavior. Do not fork its generated `.agents`, `.claude`, `.codex`, `.cursor`, `.opencode`, or other provider trees into this repository.
- Do not silently install or update Impeccable as a side effect of an unrelated task. Project-local installation is a repository mutation and requires user intent.
- Preserve user-specified brand, product, accessibility, framework, and platform constraints.
- Keep verification bounded: inspect, batch fixes, confirm once when practical, then stop rather than entering an open-ended polish loop.
- When refreshing this integration, update the upstream version/revision metadata and attribution together.
