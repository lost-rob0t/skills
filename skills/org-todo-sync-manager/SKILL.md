---
name: org-todo-sync-manager
description: org, todo, ideas, rescheduling, github, issues
compatibility: Agent Skills-compatible agent with Org file access, current-time access, and repository issue/PR tools
---

# Org Todo Sync Manager

## Goal

Keep a timeboxed daily plan, an Org idea inbox, and repository feature issues synchronized without turning every idea into urgent work.

## Input

- current local date/time and stop time;
- active daily todo source;
- Org ideas file path;
- configured idea TODO state, such as `IDEA`;
- repository map plus issue/PR/check access.

## Output

- one current timeboxed daily plan;
- durable idea entries in the Org ideas file;
- repo feature issues only for promoted ideas;
- backlinks between promoted Org ideas and repository issues.

## Workflow

1. Read the current daily plan and current repo truth before changing priorities.
2. Re-slice remaining time when an important blocker, red required check, dependency change, or operator instruction makes the plan stale.
3. Capture every new non-urgent project/product idea immediately in the ideas file. Deduplicate by meaning and source before appending.
4. Use the configured TODO keyword as a **state**, never as a tag. For an `IDEA` state, write:
   ```org
   ** IDEA <short title>
   - Captured: YYYY-MM-DD HH:MM <timezone>
   - Source: <reference>
   - Why deferred: <reason>
   - Next proof: <smallest evidence needed>
   - Promoted issue: none
   ```
5. Do not add `SCHEDULED` or `DEADLINE` to an idea until it is promoted into active work. Never invent a same-named Org tag such as `:IDEA:`.
6. On each sync, review unresolved ideas. Keep an item as IDEA while it is vague, duplicate-prone, low-priority, or lacks a known owning repo.
7. Before promotion, search the owning repo's open/closed issues and PRs for duplicates or existing implementation.
8. Promote only when the repo is known, the idea is actionable, the desired behavior is clear, and useful acceptance criteria can be stated.
9. Create a feature issue with problem/context, desired behavior, bounded acceptance criteria, source/provenance, and relevant constraints. Do not promise an implementation design that has not been researched.
10. Backlink the created/existing issue from the Org entry. Preserve the original idea record; change its TODO state only if the user's Org workflow defines a post-promotion state.
11. If an idea becomes important for today, place the resulting concrete work into the daily timed plan rather than scheduling the vague IDEA itself.

## Rules

- Execution work outranks speculative ideas.
- Important unfinished work rolls forward; it is never silently dropped.
- IDEA is a configurable TODO state. Do not convert it into an Org tag.
- One idea may map to an existing issue; do not create duplicates for bookkeeping.
- If repository ownership is ambiguous, keep the item in the idea inbox.
- Respect repository issue templates, contribution rules, labels, and governance.
