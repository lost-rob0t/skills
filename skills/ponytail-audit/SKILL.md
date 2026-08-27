---
name: ponytail-audit
description: audit, over-engineering, yagni, deletion, simplification
license: MIT
metadata:
  author: "Dietrich Gebert / DietrichGebert and Ponytail contributors"
  source: "https://github.com/DietrichGebert/ponytail"
  upstream-version: "4.9.0"
  upstream-revision: "2ed6c52c9d7e5e56942508591085fd45dea277d3"
  provenance: "external-import"
---

# Ponytail Audit

> External import of **Ponytail** by Dietrich Gebert and contributors, adapted from upstream v4.9.0 under MIT.

## Goal

Run the Ponytail over-engineering review across an entire repository.

## Input

A repository tree and enough source/dependency context to inspect real usage.

## Output

Rank findings by biggest useful cut:

`<tag> <what to cut>. <replacement>. [path]`

Use the same tags as `ponytail-review`: `delete`, `stdlib`, `native`, `yagni`, `shrink`.

End with `net: -<N> lines, -<M> deps possible.` If nothing should be cut: `Lean already. Ship.`

## Workflow

Hunt for dependencies the platform already replaces, single-implementation interfaces, factories with one product, wrappers that only delegate, dead flags/config, speculative layers, needless one-export files, and hand-rolled standard-library behavior.

## Rules

- Repo-wide audit only; one-shot.
- Scope is over-engineering and complexity. Correctness, security, and performance belong in normal review.
- Report findings; do not mutate the repository unless the user separately asks.
