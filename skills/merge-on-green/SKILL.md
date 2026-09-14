---
name: merge-on-green
description: merge, ci, github, forgejo, exact-head, polling, safety
compatibility: Git repository with gh or Forgejo API access (FORGEJO_TOKEN)
---

# Merge On Green

## Goal

Merge only the exact pull-request head whose required gates and reviews
were verified.

## Workflow

Run `scripts/merge-on-green <pr-number>` from a checkout of the
repository. The provider is detected from the origin remote:
`github.com` uses the `gh` CLI, `git.starintel.actor` uses the Forgejo
REST API with `FORGEJO_TOKEN`. Override detection with `--provider
github|forgejo` and pass `--repo owner/name` when the remote is
ambiguous.

The helper records the PR head SHA, polls gate state with bounded
exponential backoff, and honors `Retry-After`. Pending, cancelled,
failed, conflicting, draft, closed, missing-review, and rate-limited
states are reported and bounded; it never busy-loops.

## Exact-head invariant

Immediately before merging it re-probes the head. If the head differs
from the validated head, all green evidence is invalidated and
validation restarts for the new SHA. The merged commit is always the
verified commit.

## Rules

- Never equate an old-SHA green result with current green.
- Never duplicate a PR across providers.
- Exit codes: 0 merged, 2 configuration, 3 provider failure,
  4 blocked/timeout/head churn, 5 rate-limited beyond budget.
- Use `--dry-run` to verify eligibility without merging.
- On timeout or ambiguity, stop without merging and report the blocker.
