---
name: starintel-psych-profiling
description: starintel, psych-behavioral, profiling, dossiers, corpus-analysis, frame-guards
compatibility: Agent Skills-compatible coding agent with StarIntel corpus access and workspace state
---

# StarIntel Psych-Behavioral Profiling

## Goal

Produce psych-behavioral profiles of pseudonymous community members and a
community psychological profile (flame points, infighting axes, unifiers)
from an already-collected public StarIntel corpus — as indexed dossiers
plus a schema-correct dataset analysis doc. Behavioral/thematic reading
only; this is not clinical assessment and never identity work.

## Input

- a ranked source-of-truth analysis doc (e.g. top-users by activity);
- corpus read access through the StarIntel dataset views (couch truth for
  reads; search index may lag);
- watchlist rule hits: retro-scan output and per-user rule aggregation;
- the operation workspace state tree for dossiers, index, and handoff.

## Output

- one markdown dossier per handle under the operation's user-content dir,
  indexed in its users-content org index;
- one `dtype:"analysis"` community-psych doc in the dataset (bulk-written
  via the ingest host's loopback API when the public edge refuses bulk
  POSTs; verified readable via the public API after write).

## Workflow

1. Resolve the ranked handle set from the source-of-truth doc; per-sub
   top-N is usually more defensible than a blended score rank.
2. Extract per-handle corpus docs with one one-pass dataset-view scan
   keyed by handle set (plus a top-posts-per-sub sample for community
   theming). Paginate with the full document id as startkey (view emits
   `[dataset, id]`); startkey is inclusive, so dedup rows by id. A frozen
   scan counter usually means the walker is crossing a different-dtype id
   band, not stalling. Avoid unindexed find queries on large corpora.
3. Compute per-handle objective digests: cadence by month, sub spread,
   engagement (replies received), lexical marker counts, watchlist rule
   overlap, top-content titles, comment style samples.
4. Write dossiers from digests plus spot reads. Template fields:
   collected/contract/role header, observed behavior, analyst notes,
   confidence. State corpus coverage honestly (docs sampled vs rank
   universe); if the sample cannot support a psych reading, record role
   classification only.
5. Classify community roles when the data supports it: resident essayist,
   curator, broadcaster, conversationalist, resonance miner,
   burst-dropout, single-day viral drive-by.
6. Write the community doc: quantified thematic coding of top-post
   samples per sub (keyword families), flame points, infighting axes,
   unifiers, indicator concentration, churn observations. Follow the
   analysis-doc data shape: `data{question, method, scope, findings[],
   conclusions[], confidence (number), counterarguments[], limitations[],
   unresolved[]}`, plus top-level `date_added`/`date_updated`.
7. Index dossiers in the users-content org file, update the operation
   handoff and run journal, and run the workspace verification gate with
   observed invariants (tool compile, frame-guard presence per dossier,
   doc readback).

## Rules

- Frame guards are non-negotiable and go in every dossier: public content
  only; `evidence_frame(username_claim, evidence_not_identity)`; no
  clinical diagnosis language; no deanonymization; no real-world identity
  inference; no contact or intervention; `watchlist_hit,
  triage_not_adjudication` for every indicator statement.
- Behavioral facts (cadence, series patterns, lexical markers) may be
  stated as facts; intent, authenticity, and pathology readings must be
  framed as one reading of sequence, not adjudication.
- Engagement claims cite the rank universe; thematic claims cite sample
  sizes; both go in limitations.
- Indicator-dense handles are monitoring priorities, never targets for
  action beyond the operation's contract.
