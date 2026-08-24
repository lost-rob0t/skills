---
name: activitywatch-group
description: activitywatch, window-groups, qtile, clustering, routing
compatibility: Requires ActivityWatch window data and, when changing routing, the user's actual window-manager configuration source.
---

# Build ActivityWatch workflow groups

## Goal

Discover stable groups of applications, windows, domains, and editor contexts
that can become useful workspace, launcher, or reporting categories.

## Workflow

1. Inspect repeated app/title/domain patterns and their co-occurrence over
   time. Use a bounded sample and mark sparse or ambiguous patterns.
2. Propose group names with explicit membership rules, exclusions, and
   precedence. Prefer WM_CLASS/app identity first and title/domain matching
   only where it is stable.
3. Check collisions: AI, messenger, games, media, browser, editor, and
   project rules must have a documented precedence instead of competing
   catch-all regexes.
4. Present the proposed groups for approval. If accepted, edit the canonical
   Qtile/literate source or other owning dotfiles source, regenerate outputs,
   run tests, and verify the live behavior.

## Rules

- Do not move windows, create groups, or edit dotfiles during discovery alone.
- Keep raw titles, URLs, prompts, and path names out of committed rules.
- Prefer narrow rules with negative examples over broad words such as `chat`,
  `work`, or `video` that create false positives.
- Preserve existing group labels, ownership, and event-loop responsiveness.
