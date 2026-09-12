---
name: starintel-wearos-release
description: starintel, wearos, android, release, apk, github, nix, tagging
compatibility: Requires git, Nix, GitHub CLI authentication for lost-rob0t/starintel-wearos, and permission to push tags and inspect GitHub Actions/releases.
---

# StarIntel Wear OS release

## Goal

Cut reproducible tagged releases of `lost-rob0t/starintel-wearos` and publish
all installable application APKs through the repository's Release workflow.
The workflow is the publication authority; do not upload hand-built APKs to a
GitHub release.

A release publishes the phone companion, Wear application, watch face, a
checksum file, a release manifest, and a ZIP containing the APK set.

## Rules

- Release only from an exact, clean `main` HEAD that matches `origin/main`.
- Use semantic release tags in the form `vMAJOR.MINOR.PATCH[-suffix]`.
- Keep `versionName` synchronized across `phone-app`, `wear-app`, and
  `watchface`; omit the leading `v` from `versionName`.
- Keep the three Android `versionCode` values synchronized and increment them
  for each new installable release.
- Never move, overwrite, or recreate an existing release tag.
- Never publish artifacts built outside the tagged source revision.
- A prerelease suffix such as `-alpha`, `-beta`, or `-rc.1` must produce a
  GitHub prerelease.
- Do not bypass failing tests, Nix evaluation, watch-face contract checks,
  round-screen bounds checks, or phone/Wear signer-parity validation.
- The current shared signing key is debug-only. Do not represent an alpha APK
  as production-signed or suitable for Play Store publication.

## Release preparation

1. Read repository instructions and inspect current PRs and CI.
2. Confirm the intended version and verify that neither the Git tag nor GitHub
   release already exists.
3. Update all three Android modules to the requested `versionName` and one
   synchronized, monotonically increasing `versionCode`.
4. Run the normal repository CI before merging the version/release-preparation
   change to `main`.
5. Do not tag a PR branch. Merge first, then refresh local `main` from origin.

For `v0.1.1-alpha`, the expected source versions are:

```text
phone-app/build.gradle.kts  versionCode = 2  versionName = "0.1.1-alpha"
wear-app/build.gradle.kts   versionCode = 2  versionName = "0.1.1-alpha"
watchface/build.gradle.kts  versionCode = 2  versionName = "0.1.1-alpha"
```

## Cut the release

From a clean checkout of `main`:

```bash
git switch main
git pull --ff-only origin main
scripts/release.sh v0.1.1-alpha
```

`scripts/release.sh` verifies exact-main state, source version consistency,
Nix evaluation, Android unit tests, watch-face slot/theme/round-bound checks,
all three Nix-built APKs, and companion signer parity. It then creates and
pushes an annotated tag. Pushing the tag triggers `.github/workflows/release.yml`.

Useful bounded variants:

```bash
scripts/release.sh v0.1.1-alpha --dry-run
scripts/release.sh v0.1.1-alpha --skip-local-checks
scripts/release.sh v0.1.1-alpha --no-wait
```

Use `--skip-local-checks` only when the exact main commit has already passed the
same required checks and the operator wants to avoid a duplicate local build;
release CI still reruns the gates before publication.

## CI publication contract

The Release workflow checks out the tag itself, not floating `main`, and must:

1. validate the tag format and module `versionName` values;
2. evaluate the pinned Nix flake;
3. run phone and Wear unit tests;
4. run watch-face slot, theme, and round-screen geometry checks;
5. build phone, Wear, and watch-face APKs through `nix run .#build-all`;
6. verify phone/Wear signer parity;
7. create versioned APK filenames plus `SHA256SUMS` and
   `RELEASE-MANIFEST.txt`;
8. preserve the complete bundle as a GitHub Actions artifact; and
9. create or idempotently refill the matching GitHub release.

Expected release assets for `v0.1.1-alpha` include:

```text
starintel-phone-v0.1.1-alpha.apk
starintel-wear-v0.1.1-alpha.apk
starintel-watchface-v0.1.1-alpha.apk
starintel-wearos-v0.1.1-alpha-apks.zip
SHA256SUMS
RELEASE-MANIFEST.txt
```

## Verification

After tagging, inspect the Release workflow and do not report success until the
exact tag run is green and the GitHub release exists. Verify each expected
asset is non-empty and that the release is marked prerelease when the version
contains a suffix. Compare the published tag target with the intended main
commit. Report the tag, commit SHA, workflow conclusion, release URL, published
asset names, and any gate that failed.
