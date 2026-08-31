# Extending Star-Lang

Read this reference before changing the compiler, normalized IR, generated
bindings, runtime, or adapter packages.

## Pick the owning extension seam

| Need | Extend here |
| --- | --- |
| New domain vocabulary or schema | A new versioned `.star` specification library |
| Repeated declaration shape | A bounded format-1 source macro |
| New declaration, type, or semantic rule | Closed parser/core surface and compiler pipeline |
| New actor execution behavior | The owning `starlang-runtime` API and tests |
| New transport or external effect | `star-adapter-sdk` plus a concrete port system |
| New wire or generated-language representation | Portable manifest, canonical JSON, and every binding generator |

Use a language implementation change only when a specification library or
macro cannot express the requirement. Transport names and runtime handles do
not belong in normalized IR.

## Respect current ownership

The repository is transitional. `prototype/` remains authoritative for the
parts that have not been extracted; populated `star-*` and `starlang-*` systems
own only the APIs and files actually moved into them. Before editing:

1. inspect the relevant `.asd`, package exports, implementation file, and tests;
2. check the README migration map and implementation-slice records;
3. search for an existing path before adding a package or facade;
4. move ownership only as one acyclic, tested slice without duplicate sources.

Do not infer ownership from a target system's name or empty package skeleton.

## Compiler extension checklist

For a new source form or type, trace the whole observable contract:

```text
UTF-8 bytes
  -> read-star-syntax
  -> locked import resolution
  -> expand-star-syntax
  -> validate-star-core
  -> compile-star-core
  -> normalized data-only IR
```

- Add a failing source-level test first, including the structured error path.
- Keep syntax occurrences, spans, scopes, macro provenance, and source maps
  until lowering; do not turn `.star` into host Lisp data early.
- Update the closed declaration/stage allowlist, semantic validation, compiler
  dispatch, and normalized IR together when the form crosses those boundaries.
- If the value crosses a process or language boundary, update canonical JSON,
  portable manifests, Python and TypeScript bindings, and round-trip fixtures.
- Preserve namespace rules, lower-camel-case wire fields, deterministic order,
  exact decimal strings, and finite-number restrictions.
- Update the conformance ledger only when tests and CI establish the claimed
  research property.

## Runtime and adapter extension checklist

- Reuse the existing runtime registry, bounded mailboxes, serialized dispatch,
  lifecycle, and typed conditions. Do not create a second scheduler or a hidden
  synchronous execution path.
- Native actors execute local handlers. External actor registration is only an
  identity and contract until a concrete adapter supplies dispatch.
- Keep transport, network, process, and provider effects behind adapter ports.
  Capability possession and validation remain explicit at that boundary.
- Preserve actor references, generations, stale-reference rejection, contract
  validation, committed state, and failure results across wrappers.
- Add behavior tests to the owning ASDF system; use deterministic dispatch and
  externally observable state rather than sleeps.

## Verification

Run the narrow owning system while iterating, for example:

```bash
nix develop -c sbcl --non-interactive \
  --eval '(require :asdf)' \
  --eval '(asdf:test-system :starlang-runtime)' \
  --eval '(sb-ext:quit)'
```

Use `:starlang-prototype` when the authoritative code is still prototype-owned.
Then run `scripts/verify.py --repo <star-lang-checkout>`, which
executes the complete prototype/final-system test app and `nix flake check -L`.
