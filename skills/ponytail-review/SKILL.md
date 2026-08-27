---
name: ponytail-review
description: review, over-engineering, yagni, deletion, simplification
license: MIT
metadata:
  author: "Dietrich Gebert / DietrichGebert and Ponytail contributors"
  source: "https://github.com/DietrichGebert/ponytail"
  upstream-version: "4.9.0"
  upstream-revision: "2ed6c52c9d7e5e56942508591085fd45dea277d3"
  provenance: "external-import"
---

# Ponytail Review

> External import of **Ponytail** by Dietrich Gebert and contributors, adapted from upstream v4.9.0 under MIT.

## Goal

Review a diff only for unnecessary complexity. The best outcome is a shorter diff.

## Input

A code diff or changed-file set.

## Output

One finding per line:

`<file>:L<line>: <tag> <what to cut>. <replacement>.`

Tags:

- `delete:` dead code, unused flexibility, speculative features; replace with nothing.
- `stdlib:` hand-rolled behavior the standard library already provides.
- `native:` dependency or code duplicating a platform feature.
- `yagni:` abstraction with one implementation, config nobody sets, or a layer with one caller.
- `shrink:` same behavior in materially less code.

Rank useful findings first. End with `net: -<N> lines possible.` If nothing should be cut: `Lean already. Ship.`

## Rules

- Scope is over-engineering and complexity only.
- Do not report correctness, security, or performance findings as Ponytail findings; route those to normal review.
- Do not apply fixes unless the user separately asks.
- Do not flag the single minimal runnable check required by Ponytail as bloat.
