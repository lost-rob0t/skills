---
name: forgejo-repo-bootstrap
description: forgejo, repositories, adard, issues, bootstrap, provenance
compatibility: Requires the `tea` CLI with a login for the Forgejo host (`git.starintel.actor`), repository access, and an explicit ADARD source and target mapping.
---

# StarIntel repository bootstrap on Forgejo

## Goal

Forgejo (`git.starintel.actor`) variant of `starintel-repo-bootstrap`:
create one explicitly approved repository and seed its issue tracker with a
small, traceable set of issues from the project's ADARD source. This skill
does not implement the application or deploy it.

Use this skill when the target host is `git.starintel.actor`. Use
`starintel-repo-bootstrap` (GitHub CLI) when the target is GitHub. The
`git` skill documents host routing.

## Inputs and output

Input must include the target owner/name, purpose, visibility, authoritative
ADARD source repository, and issue or design scope. Output is a minimal
repository plus idempotently created issues that preserve source links,
approval state, dependencies, and acceptance criteria.

## Rules

- Load `adadr` for research/design approval semantics and
  `skill-portability` before retaining any source material.
- Use `tea` for every Forgejo operation (`--login <name>` for
  `git.starintel.actor`).
- Inspect authoritative repositories before creating a target. A missing name
  is not evidence that a new repository is needed.
- Never create duplicates, forks, transfers, licenses, application code, or
  language-specific files during bootstrap.
- Never close or edit ADARD source issues.
- Never treat an open issue, green CI, or repository creation as approval.
- Never infer that a new aggregate repository owns work mapped to an existing
  implementation repository.

## Workflow

1. Read applicable repository instructions and inspect local Git status. Keep
   unrelated changes untouched.
2. Run `tea login list`, list visible repositories with
   `tea repos search`, and inspect same-purpose candidates with
   `tea repo view OWNER/NAME`.
3. Confirm the ADARD source repository and inspect the requested source issue
   or design. Use `tea issue view` for issue metadata and read the linked
   research/design implementation map.
4. Require an explicit source-to-target mapping. If the ADARD material names a
   different authoritative implementation repository, stop and ask rather
   than reassigning it to the new target.
5. Build a dry-run manifest of proposed target issues. Include source URL,
   source state, title, scope, dependencies, and acceptance criteria. Ask for
   confirmation before remote issue creation unless the operator supplied the
   exact issue list and mapping.
6. Immediately before creation, run:

   ```bash
   tea repo view OWNER/NAME
   ```

   If it exists, leave it alone. If it is missing and creation is approved,
   create it with `tea repo create`, `--private` when requested, and the
   supplied description. The README states only purpose, deployment
   ownership, and an established public hostname, if applicable.
7. Before each issue creation, inspect all open and closed target issues for
   its source marker (`tea issue list --state all`). Skip an existing
   marker; do not overwrite a matching title that lacks provenance.
8. Create each approved issue with `tea issue create`. Preserve ADARD status,
   source issue/design URLs, bounded scope, acceptance criteria, dependencies,
   non-goals, and the statement that implementation approval is not inferred.
9. If a source design is `PENDING` or `BLOCKED`, create a tracking issue only
   when explicitly requested and preserve that state. Do not create
   implementation-ready work from it.
10. If repository documentation is requested, update the canonical registry
    in the owning infrastructure repository. Do not change live service
    inventory or deployment configuration as part of bootstrap.

## Issue provenance

Use a stable marker in every seeded issue, for example:

```text
<!-- starintel-adard-source: SOURCE-ISSUE-OR-DESIGN-URL -->
```

Do not copy an entire research packet into an issue. Link the source and
summarize only the target-relevant scope. Do not split one source into several
issues unless the source design explicitly splits it or the operator directs
the split. Use only labels already present in the target repository.

## Verification

Verify target visibility, description, default branch, intended bootstrap
files, issue count, source markers, preserved ADARD states, and unresolved
mappings with `tea repo view`, `tea issue list`, and the Forgejo API. Then
run the target repository's required checks. For the skills repository, run:

```bash
bash scripts/validate-skills
bash scripts/validate-support-scripts
git diff --check
```

Report created and pre-existing repositories, each created or skipped issue
with its source URL, validation results, and that no implementation or
deployment occurred.
