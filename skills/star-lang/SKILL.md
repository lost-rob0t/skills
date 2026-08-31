---
name: star-lang
description: star-lang, language, schemas, compiler, runtime, extensions, common-lisp
---

# Star-Lang

## Goal

Use Star-Lang to define, load, and consume versioned specification libraries,
or extend the language and its Common Lisp runtime through the current
canonical implementation.

Requires Git, Nix, and a current Star-Lang checkout. Use paths discovered from
the user's repository or supplied explicitly; do not assume a personal clone
location.

## Choose the task

- To write or modify `.star`, load a library, resolve imports, or consume its
  compiled graph, read [references/language.md](references/language.md).
- To add reusable schema vocabulary, prefer a new or imported `.star` library.
  Use a declarative format-1 macro only for repeated declaration shapes.
- To change syntax, types, compiler IR, bindings, actor behavior, or adapters,
  read [references/extending.md](references/extending.md).
- For native or external actor operations, also read
  [references/runtime.md](references/runtime.md).

## Workflow

1. Inspect the current README, conformance ledger, representative fixtures,
   owning package exports, and tests. Current executable code outranks older
   design prose.
2. Select the smallest extension layer that fits: library source, declarative
   macro, compiler surface, final runtime system, or adapter port. Do not create
   a parallel parser, compiler, dispatcher, or runtime.
3. For language use, start from a minimal `spec-library`, load it through the
   `starlang` CLI, and inspect the resulting graph before integrating it.
4. For implementation changes, add a focused failing test at the owning
   boundary, implement the smallest coherent change, and update fixtures,
   exports, serialization, bindings, docs, or the conformance ledger when those
   contracts actually change.
5. Run focused ASDF tests, then run this skill's complete gate:

   ```bash
   scripts/verify.py --repo <star-lang-checkout>
   ```

## Rules

- `.star` source always enters through the closed UTF-8 Star-Lang parser, never
  the Common Lisp reader or evaluator.
- Preserve the explicit read -> resolve -> expand -> validate -> compile
  pipeline and keep normalized IR deterministic, data-only, and runtime-neutral.
- Imports use exact versions and full SHA-256 locks. Remote resolution is HTTPS
  only and requires explicit network authorization.
- Source and wire field names are lower camel case. Exact decimals stay strings;
  do not claim unsupported numeric or research-conformance behavior.
- Common Lisp is the implementation language. Generated Python or TypeScript
  bindings consume portable manifests; they do not implement Star-Lang.
