# Using Star-Lang

Read this reference when the task is to write `.star`, extend a specification
library, load it, or consume its compiled graph.

## Start with one library

```lisp
(spec-library "example/contacts@1"
  (:version "1.0.0")

  (scalar contact-id
    (:base string :pattern "^[A-Z0-9]+$"))

  (enum contact-state
    (active inactive))

  (document contact
    (:persistence persistent)
    (contactId contact-id :required)
    (displayName string :required)
    (state contact-state :optional :default active)
    (tags (list string) :optional))

  (predicate knows
    (:source contact :destination contact))

  (message upsert-contact
    (:fields ((contact contact :required)))))
```

Save it as `contacts.star`, then from the Star-Lang checkout run:

```bash
nix run . -- load contacts.star \
  --cache .cache/star-lang/specs \
  --manifest contacts-loader.json
```

The command parses, expands, validates, compiles, and prints the locked library
graph. `--manifest` writes the loader graph; it does not start actors. Use
`nix run . -- --help` for the current CLI surface.

## Core source model

- A file contains exactly one `spec-library` with a string library identity and
  exact string `:version`. A root `:digest` is optional; resolved imports are not.
- Library declarations are `import`, `scalar`, `enum`, `document`, `predicate`,
  and `message`. Declarative format-1 macros may expand to those declarations
  before validation.
- Built-in types are `any`, `boolean`, `decimal`, `integer`, `map`, `reference`,
  `string`, `symbol`, `iso-date`, and `iso-datetime`. Type constructors are
  `(list TYPE)` and `(optional TYPE)`.
- `scalar` refines a base type with supported `:pattern`, `:format`, `:minimum`,
  `:maximum`, or `:scale` constraints. `enum` values are identifiers.
- `document` selects `persistent` or `transient` persistence, may `:extends`
  another document, and adds fields. Fields require exactly one of `:required`
  or `:optional`; only optional fields may have `:default VALUE`.
- `predicate` names typed `:source` and `:destination` document endpoints.
  `message` owns a `:fields` list using the same field syntax as documents.
- Declaration and type names may be kebab case. Document, message, manifest,
  and serialized wire fields must preserve ASCII lower-camel-case spelling.

Use current fixtures as executable examples. Start with the smallest fixture
that contains the feature needed; do not copy a large domain schema as a
template for a small library.

## Import and extend another library

Use a locked local import during development:

```lisp
(import "example/core@1"
  :version "1.2.0"
  :digest "sha256:<64 hexadecimal digits>"
  :path "../core/core.star")
```

Use `:url "https://..."` instead of `:path` for a remote library. Remote
resolution must be explicitly enabled with `--allow-network`; the full digest
is verified before compilation and the cached copy may be reused offline.
Never use an import to mutate or replace declarations from the imported
library. Add a new library and new qualified declarations.

For repeated declaration shapes, a source macro is the language-level extension
point:

```lisp
(macro required-message
  (:format 1
   :context declaration
   :rules (((required-message ?name ?field)
            (message ?name (:fields ((?field string :required))))))))

(required-message ping messageId)
```

Macros are bounded, declarative, hygienic, and declaration-context only. They
must expand to the closed core surface; they cannot call Common Lisp or perform
I/O.

## Consume the compiled graph

The Common Lisp API package `star-lang.api` exposes the supported pipeline and
document operations:

- `load-star`, `load-star-file`, and `load-star-url` load locked graphs;
- `read-star-syntax`, `expand-star-syntax`, `validate-star-core`, and
  `compile-star-core` expose explicit compiler phases;
- `load-star-runtime` optionally installs generated constructors;
- `create-document`, `encode-document`, `decode-document`, and
  `relate-documents` use compiled schemas.

Load the owning ASDF system and use exported API symbols. Do not depend on
unexported prototype internals merely because they are currently visible.
