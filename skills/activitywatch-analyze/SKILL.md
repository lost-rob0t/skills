---
name: activitywatch-analyze
description: activitywatch, analysis, time-use, workflow-patterns, privacy
compatibility: Requires a local ActivityWatch server or exported bucket data and Python-capable analysis tools.
---

# Analyze ActivityWatch data

## Goal

Turn ActivityWatch window, AFK, web, and editor buckets into evidence-backed
workflow findings without treating raw activity as a productivity score.

## Workflow

1. Discover available buckets from the local ActivityWatch API or user-provided
   export. Confirm the time range and bucket types before making claims.
2. Normalize app classes, domains, titles, and editor buffers into broad
   categories. Redact credentials, tokens, private URLs, personal prompts,
   document contents, and identifying path segments.
3. Measure time totals, active intervals, transitions, repeated sequences,
   interruption clusters, and missing-data boundaries. Distinguish observed
   duration from event count.
4. Report the evidence, uncertainty, and a short list of workflow changes.
   Compare periods only when collection coverage and bucket semantics match.

## Rules

- Use the local server by default (`http://127.0.0.1:5600`); never upload
  ActivityWatch data or silently query a remote service.
- Do not infer intent, health, employment performance, or moral value from app
  names or idle time. Label interpretations as hypotheses.
- Prefer aggregate categories and counts. Show raw titles or URLs only when the
  user explicitly requests them and they are safe to disclose.
- Suggestions may target aliases, Emacs commands, Qtile rules, project jumps,
  or reminders, but implementation requires user approval.
