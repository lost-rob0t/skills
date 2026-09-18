---
name: literate-engineering
description: org, literate-programming, technical-writing, code-review
compatibility: Org source projects with deterministic tangling or compilation
---

# Literate engineering

## Goal

Make human-readable Org the implementation authority while keeping generated source reproducible, reviewed, and useful to normal compilers and editors.

## Input

- a feature, fix, or migration that changes executable source;
- the repository's Org reader/tangler or compiler;
- the generated targets and authoritative tests.

## Output

Produce canonical Org source, exact generated files, test evidence, and independent review evidence.

## Workflow

1. Put the explanation and executable source blocks in the canonical Org file.
2. Give every build block an explicit relative `:tangle` target. Keep examples inert with no target or `:tangle no`.
3. Write the problem and invariant before the block that implements them.
4. Tangle/compile the Org source. Never hand-edit generated output.
5. Run focused tests and the repository's required gates.
6. Have a different parent/supervisor review prose and generated code together.
7. Send the surviving revision to a harsh nihilist reviewer.
8. Canonicalize only after `ACCEPT_ORG_SOURCE`.
9. If the project has a teaching/book lane, hand off the accepted source only after required coverage is complete.

## Writing voice

Use **Literate Engineering Voice**:

- prefer active voice and strong verbs;
- use specific nouns and one main idea per sentence;
- explain this system, not generic programming;
- keep rationale beside the code it justifies;
- document public forms, predicates, messages, effects, capabilities, configuration fields, and failure behavior;
- remove throat-clearing, marketing adjectives, fake enthusiasm, generic conclusions, and prose that only restates syntax;
- distinguish observed facts, deterministic inference, LLM candidates, and external effects.

See `references/style.md` for the research basis.

## Parent critic

The parent reviewer must not be the author.

Reject prose/code drift, hidden generated behavior, needless abstractions, authority widening, undocumented public behavior, stale generated files, and tests that do not prove the documented contract.

Terminal result: `PARENT_ACCEPT(...)` or `PARENT_REJECT(...)`.

## Harsh nihilist

Assume every abstraction, sentence, dependency, and generated layer is unnecessary until justified.

Try to replace new machinery with an existing fact, rule, actor message, parser, effect boundary, capability, or runtime primitive.

Reject speculative generality, duplicate registries, fake compatibility, undocumented authority, unproven prose, and LLM text treated as truth.

Be harsh about the work, never the person.

Terminal result: `ACCEPT_ORG_SOURCE` or `REJECT_ORG_SOURCE(<specific blockers>)`.

A rejection requires a source change and a fresh parent review before another nihilist pass.

## Rules

- Org is canonical; generated files are artifacts.
- Generated behavior absent from Org is a defect.
- Tangling/compilation must be deterministic and path-confined.
- Documentation-only blocks never execute merely because they look like code.
- Do not let a model-authored block gain ambient shell, filesystem, network, or repository authority.
- Preserve provenance for model-assisted source and claims.
- Book/tutorial prose is downstream and never becomes implementation authority.
