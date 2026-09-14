---
name: starintel-spec-version
description: starintel, schema, versioning, release, lock, conformance
---

# StarIntel spec version

## Goal

Resolve and bump the active StarIntel document release without confusing the
release/profile version with the immutable base schema version or filename.

## Input

A StarIntel checkout containing `schema/starintel-schema.lock.json`, or a local
canonical `starintel-gpt-auto-dig` checkout for release mutation.

## Output

A verified current release/profile/base-schema tuple, or a scripted next-patch
release bump followed by repository conformance checks.

## Workflow

1. **Resolve the lock before reading issue/docs version claims.** Prefer the
   current repository's `schema/starintel-schema.lock.json`. If absent, locate
   the applicable sibling `starintel-doc`/consumer lock; do not guess.
2. Resolve the current version with this skill's helper:

   ```bash
   python3 scripts/starintel_spec_version.py current \
     --lock schema/starintel-schema.lock.json
   ```

   The value to report as the current StarIntel spec/release is
   `release_version`, **not** `schema_version` and not a schema filename.
3. Follow `canonical_repository` + `canonical_commit` from the lock and verify
   the pinned manifest. Lock and manifest `release_version` must match.
4. Before any schema/profile change, inspect the canonical repository's
   repo-owned release tool:

   ```bash
   python3 scripts/schema-release.py current
   python3 scripts/schema-release.py check
   ```

5. Release changes must use the canonical bump script. For the current release
   train the next change is `0.9.2`:

   ```bash
   python3 scripts/schema-release.py bump --to 0.9.2 --dry-run
   python3 scripts/schema-release.py bump --to 0.9.2
   python3 scripts/schema-release.py check
   ```

6. After the canonical release is merged/green, repin consumer locks through
   each repository's existing sync/lock script and run cross-language
   conformance. Do not hand-edit copied schemas or package versions.

## Rules

- Current release/profile is `0.9.1`; the next additive release is `0.9.2`.
  Always trust the live lock/script over this historical sentence after a bump.
- `schema_version = 0.9.0` may remain correct while `release_version = 0.9.1`
  or `0.9.2`; the v0.9.0 filename is the immutable base family.
- Never use stale issue prose, research notes, README text, or memory as version
  authority.
- Never `sed` or search/replace a release bump by hand.
- Never rename the immutable base schema merely to make filenames match the
  release/profile version.
- A new base schema version requires an explicit compatibility/migration
  decision; a patch release does not imply one.
- If the lock, canonical commit, manifest, or bump checker disagree, stop and
  repair the authority chain before changing documents.
