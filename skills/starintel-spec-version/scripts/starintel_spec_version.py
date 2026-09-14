#!/usr/bin/env python3
"""Resolve StarIntel release/schema identity from a repository lock.

This helper is intentionally read-only.  Mutating a canonical release belongs to
that repository's own bump script (currently scripts/schema-release.py in the
canonical schema repository).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_LOCK_FIELDS = (
    "release_version",
    "schema_version",
    "canonical_repository",
    "canonical_commit",
    "schema_path",
    "expansion_path",
    "manifest_path",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def validate_lock(lock: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_LOCK_FIELDS if not lock.get(field)]
    if missing:
        raise RuntimeError(f"StarIntel schema lock is missing: {', '.join(missing)}")
    return lock


def resolve_lock(path: Path) -> dict[str, Any]:
    return validate_lock(load_json(path))


def verify_local_canonical(lock: dict[str, Any], canonical_root: Path) -> dict[str, Any]:
    manifest_path = canonical_root / str(lock["manifest_path"])
    if not manifest_path.is_file():
        raise RuntimeError(f"canonical manifest is missing: {manifest_path}")
    manifest = load_json(manifest_path)

    if manifest.get("release_version") != lock["release_version"]:
        raise RuntimeError(
            "canonical manifest release_version disagrees with consumer lock: "
            f"{manifest.get('release_version')!r} != {lock['release_version']!r}"
        )
    if manifest.get("schema_version") != lock["schema_version"]:
        raise RuntimeError(
            "canonical manifest schema_version disagrees with consumer lock: "
            f"{manifest.get('schema_version')!r} != {lock['schema_version']!r}"
        )

    try:
        head = subprocess.run(
            ["git", "-C", str(canonical_root), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"cannot resolve canonical checkout HEAD: {canonical_root}") from exc

    pinned = str(lock["canonical_commit"])
    if head != pinned:
        raise RuntimeError(
            "canonical checkout HEAD does not match the consumer lock; "
            f"HEAD={head} lock={pinned}. Check out the pinned commit or intentionally repin the lock."
        )
    return manifest


def state(lock: dict[str, Any]) -> dict[str, str]:
    return {
        "release_version": str(lock["release_version"]),
        "schema_version": str(lock["schema_version"]),
        "canonical_repository": str(lock["canonical_repository"]),
        "canonical_commit": str(lock["canonical_commit"]),
        "schema_path": str(lock["schema_path"]),
        "expansion_path": str(lock["expansion_path"]),
        "manifest_path": str(lock["manifest_path"]),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Resolve the active StarIntel release from a schema lock."
    )
    result.add_argument(
        "command",
        choices=("current", "check"),
        help="current prints lock state; check also verifies a local canonical checkout when provided",
    )
    result.add_argument(
        "--lock",
        type=Path,
        default=Path("schema/starintel-schema.lock.json"),
        help="consumer schema lock (default: schema/starintel-schema.lock.json)",
    )
    result.add_argument(
        "--canonical-root",
        type=Path,
        help="optional local canonical checkout; must be exactly the commit pinned by the lock",
    )
    result.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return result


def main() -> int:
    args = parser().parse_args()
    lock = resolve_lock(args.lock.resolve())
    if args.command == "check" and args.canonical_root is not None:
        verify_local_canonical(lock, args.canonical_root.resolve())

    resolved = state(lock)
    if args.json:
        print(json.dumps(resolved, sort_keys=True))
    else:
        print(
            f"release={resolved['release_version']} "
            f"base_schema={resolved['schema_version']} "
            f"canonical={resolved['canonical_repository']}@{resolved['canonical_commit']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
