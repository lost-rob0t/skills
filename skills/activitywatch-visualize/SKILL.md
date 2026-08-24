---
name: activitywatch-visualize
description: activitywatch, visualization, timelines, heatmaps, privacy
compatibility: Requires a local ActivityWatch server or exported bucket data and a chart-capable visualization tool.
---

# Visualize ActivityWatch data

## Goal

Create clear, privacy-safe views that make recurring work patterns and
friction easier to inspect.

## Workflow

1. Confirm the bucket sources, date range, timezone, and collection gaps.
2. Choose the smallest useful visual: hourly heatmap, daily stacked time,
   app/category share, transition graph, workflow timeline, or before/after
   comparison.
3. Aggregate before rendering. Use broad app, project, or workflow groups;
   remove raw titles, URLs, prompts, and file paths unless explicitly needed.
4. Annotate charts with units, sample coverage, and uncertainty. Explain what
   the visual shows and what it cannot establish.
5. End with concrete candidate improvements for the user's dotfiles or
   workflow, keeping implementation separate from visualization.

## Rules

- Read local ActivityWatch data through `127.0.0.1`; do not send it to a
  hosted charting service.
- Never use a decorative chart when a short table answers the question better.
- Do not present app time as productivity, focus, or wellbeing without the
  user's own interpretation and corroborating context.
- Preserve reproducibility: record the bucket names, filters, aggregation,
  and time range used for each visualization.
