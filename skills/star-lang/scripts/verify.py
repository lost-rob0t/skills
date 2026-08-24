#!/usr/bin/env python3
"""Run the canonical Star-Lang local verification gate."""
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

COMMANDS = (
    ("nix", "run", ".#tests"),
    ("nix", "flake", "check", "-L"),
)


def validate_repo(repo: Path) -> None:
    if not (repo / "flake.nix").is_file():
        raise RuntimeError(f"not a Star-Lang checkout: missing {repo / 'flake.nix'}")


def run_gate(repo: Path, *, dry_run: bool = False) -> None:
    repo = repo.expanduser().resolve()
    validate_repo(repo)
    for command in COMMANDS:
        print("+", shlex.join(command))
        if dry_run:
            continue
        proc = subprocess.run(command, cwd=repo, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"Star-Lang gate failed at {shlex.join(command)}")


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
