#!/usr/bin/env python3
"""Run the canonical local Auto-Dig verification gate without shell reconstruction."""
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

COMMANDS = (
    ("nimble", "buildFast"),
    ("bin/validate-for-merge", "--site"),
)


def validate_repo(repo: Path) -> None:
    if not (repo / "bin" / "validate-for-merge").is_file():
        raise RuntimeError(f"not an Auto-Dig checkout: missing {repo / 'bin/validate-for-merge'}")


def run_gate(repo: Path, *, dry_run: bool = False) -> None:
    repo = repo.expanduser().resolve()
    validate_repo(repo)
    for command in COMMANDS:
        print("+", shlex.join(command))
        if dry_run:
            continue
        proc = subprocess.run(command, cwd=repo, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"{command[0]} gate failed with exit status {proc.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        run_gate(args.repo, dry_run=args.dry_run)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
