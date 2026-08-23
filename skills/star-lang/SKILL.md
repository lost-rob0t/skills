---
name: star-lang
description: star-lang, common-lisp, compiler, runtime, actors, manifests, nix
---

# Star-Lang

## Goal

Load, compile, test, or extend Star-Lang source and its Common Lisp actor runtime using the current repository authority.

Requires Git, Nix, and a current `lost-rob0t/star-lang` checkout.

## Input

A `.star` specification, runtime/actor change, or exact Star-Lang operation.

## Output

A loaded manifest, tested Common Lisp runtime change, or executable local actor with evidence from the repository gates.

## Workflow

1. Read the current `lost-rob0t/star-lang` README, conformance ledger, and relevant implementation-slice matrix. Current code outranks older Auto Research prose.
2. Keep Star-Lang implementation in Common Lisp. Generated Python/TypeScript bindings consume portable manifests; they do not implement the language.
3. Parse `.star` only through the closed Star-Lang parser. Do not feed it to the Common Lisp reader.
4. Load a local spec with:

   ```bash
   nix run . -- load <file.star> \
     --runtime-compiler eval \
     --cache <cache-dir> \
     --manifest <loaded-graph.json>
   ```

5. For remote imports, require the exact library name, version, full SHA-256 digest, and explicit `--allow-network`; keep HTTPS and cache verification intact.
6. For actors, use the final `starlang-runtime` local API described in [references/runtime.md](references/runtime.md). Source-level actor lowering, external dispatch, supervision, and remoting remain partly prototype-owned; extend the current authority instead of creating a parallel path.
7. Run focused ASDF tests, then use this skill's `scripts/verify.py --repo <star-lang-checkout>` helper for the canonical `nix run .#tests` plus `nix flake check -L` gate. It refuses to run outside a flake checkout and stops at the first failing stage.

## Rules

- Normalized IR remains runtime-neutral and data-only; transport details belong in adapter manifests or ports.
- Preserve lower-camel-case wire/document fields and deterministic canonical JSON.
- Exact decimal values remain canonical strings; floats must be finite binary64 JSON numbers.
- Do not claim full research conformance while the repository ledger says otherwise.
