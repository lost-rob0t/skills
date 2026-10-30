# Knowledge and expert integration contract

## Current implementation and ownership

The project KB skill currently composes repository-owned `.prolog/kb/*.pl`
through an explicit loader. Main has no implemented cross-project/global store.
An existing unmerged storage proposal (skills PR #42) must be reconciled before
adding another database. This slice changes verification and demonstrates the
learning contract; it does not deploy a universal expert registry or global KB.

Expert definitions/rules/corpora/tests belong to the configured expert library.
For the originating project, the recorded ownership decision places them in
`dotfiles/.zara/experts/`; reusable Prolog-RLM execution/selection contracts stay
in Prolog-RLM. Repository source observations stay in its Project/source KB,
with generation and parser/xref provenance. Integrate via explicit adapters;
never copy private project facts into a public expert corpus or package.

## Required scope and precedence for the next storage slice

Use explicit identities: `project(ProjectId)`, `shared(StoreId)`, and
`session(SessionId)`. No implicit scan/import of home directories or private
notes. Project queries see only that project plus shared sources explicitly
selected by trusted configuration. Shared rules are reusable policy candidates;
project observations are project-scoped evidence. A shared observation cannot
prove a project task passed. Session overrides must be explicit and ephemeral.

For configurable rules, project-local overrides take precedence over imported
shared defaults by a typed `supersedes` relation. Retain the shadowed rule,
origin and reason. Two competing successors are a conflict, not last-write-wins.
Do not apply this precedence rule to contradictory factual observations: return
the conflict and its evidence. Source truth is invariant under policy overrides.

## Symbolic assertions and lifecycle

Each assertion needs identity, project/scope, typed subject and relation, value,
polarity, evidence references, author/producer, source revision/generation, and
lifecycle. Keep `hypothesis`, `confirmed`, `rejected`, `retracted`, and
`superseded` distinct. Append lifecycle events; do not erase earlier assertions.
A missing observation is `unknown`, never an implicit negation. Opposite current
polarity or incompatible values for a single-valued relation is a contradiction.
A stale observation remains inspectable but cannot prove a current query.

A claim must name its symbolic requirement and evidence query. A proposed action
must name its target symbol/source identity, expected revision/preimage, purpose,
and required evidence. This slice implements exact-command requirements and
`claim_status/3`; source-symbol/action binding requires the existing Project API
adapter and is not represented as complete by these command checks.

## Troubleshooting and accumulation

The required loop is executable: observations -> hypothesis -> diagnostic query
-> selected test -> new evidence -> confirmed/rejected/conflicting/unknown
finding. Persist only findings with concrete evidence and tested rules; future
sessions query those rules before repeating investigations. Preserve unsuccessful
hypotheses and supersession links as history, outside the confirmed rule view.

A promoted expert version needs its input/output contract, typed rules, evidence
IDs and revisions, deterministic tests, explicit project/shared scope, prior
version link, and a promotion decision. A rule that worked on one revision is a
candidate for reuse on another; revalidate it rather than transferring success.
Registration is neither execution authority nor a permission grant.

The executable contract fixture is `tests/fixtures/prolog_kb_troubleshooting.pl`.
`tests/test_prolog_troubleshooting.py` executes the original generated verifier's
borrowing bug, confirms the corrected behavior, queries Prolog for the cause,
promotes a versioned closed record, and reloads it in a fresh SWI process. The
fixture rejects stale evidence, contradictory test observations, hypotheses and
other-project recall. It is an illustrative contract, not a deployed project
expert. It uses no model and no ambient `call/1`/`consult/1` over learned data.

Run it with:

```sh
python3 -m unittest discover -s tests -p 'test_prolog*.py'
```

SWI-Prolog must be installed; absence skips the real Prolog cases and must be
reported as unrun. Existing helper-only tests use a fake SWI executable to test
Python preflight/hook mechanics; those are not Prolog or live-model evidence.

## Prioritized follow-up

1. Reconcile the shared-store proposal with append-only scoped assertions,
   conflict/retraction/supersession queries and explicit import policy.
2. Add an owner-library adapter for persistent expert versions and promotion
   history, consuming project evidence references without copying raw private data.
3. Bind source claims/actions to existing Prolog-RLM Project identities and fresh
   symbol generations; make the task's mandatory requirement set explicit.
4. Add explicit multi-active-task selection/resumption. This slice permits one
   active task/run per worktree; independent worktrees isolate concurrent tasks.
5. Update downstream installed policy text after the helper release is selected.
   Legacy HEAD-only automation must migrate explicitly. No user machine changes
   or production migration are included here.
