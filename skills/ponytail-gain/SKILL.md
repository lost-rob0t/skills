---
name: ponytail-gain
description: benchmarks, ponytail, metrics, savings, scoreboard
license: MIT
metadata:
  author: "Dietrich Gebert / DietrichGebert and Ponytail contributors"
  source: "https://github.com/DietrichGebert/ponytail"
  upstream-version: "4.9.0"
  upstream-revision: "2ed6c52c9d7e5e56942508591085fd45dea277d3"
  provenance: "external-import"
---

# Ponytail Gain

> External import of **Ponytail** by Dietrich Gebert and contributors, adapted from upstream v4.9.0 under MIT.

## Goal

Show Ponytail's published benchmark impact without pretending it measures the current repository.

## Output

Render this compact scoreboard:

```text
ponytail gain              upstream benchmark median · 5 tasks · 3 models

Lines of code   no-skill  100%
                ponytail    6–20%   down 80–94%
Cost            no-skill  100%
                ponytail   23–53%   down 47–77%
Speed           ponytail   3–6x faster
```

Then point repository-specific follow-up to `ponytail-debt` for counted deferrals and `ponytail-audit` for currently cuttable complexity.

## Rules

- These are upstream benchmark medians, not measurements of the current repository.
- Never invent a per-repo savings number: the unbuilt baseline does not exist.
- One-shot display only; do not change Ponytail mode or repository state.
