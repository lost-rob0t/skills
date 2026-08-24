---
name: activitywatch-productivity
description: activitywatch, productivity, friction, routines, recommendations
compatibility: Requires ActivityWatch data with enough coverage for the requested period and user context for interpretation.
---

# Improve workflows with ActivityWatch

## Goal

Use observed activity patterns to suggest small, reversible changes that reduce
friction and context switching while respecting the user's own priorities.

## Workflow

1. Establish the user's goal: faster project entry, fewer interruptions,
   easier AI/media routing, shorter recovery after context switches, or a
   different outcome they name.
2. Analyze stable patterns across comparable time windows: repeated sequences,
   long setup tails, frequent app switching, idle gaps, and return paths.
3. Separate observation from interpretation. Give each recommendation its
   evidence, expected benefit, confidence, and a cheap way to test it.
4. Prefer one or two changes at a time: a shell function, Emacs binding,
   project jump, Qtile group rule, launcher, or reminder.
5. Re-measure after the user chooses a trial period; do not claim improvement
   from one noisy day.

## Rules

- ActivityWatch is a local behavioral trace, not an objective productivity or
  character measure. Never shame, diagnose, or rank the user.
- Redact raw titles, URLs, prompts, document names, credentials, and private
  paths from reports and committed configuration.
- Do not install packages, change schedules, or edit dotfiles without approval.
- Treat missing watchers, AFK semantics, clock changes, and collection gaps as
  limitations, not evidence of inactivity.
