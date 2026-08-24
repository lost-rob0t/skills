#!/usr/bin/env python3
"""Discover Home Manager flake targets without guessing or mutating configuration."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path


def conventional_target(user: str | None = None, hostname: str | None = None) -> str | None:
    user = user or os.environ.get("USER")
    hostname = hostname or socket.gethostname().split(".", 1)[0]
    if not user or not hostname:
        return None
    return f"{user}@{hostname}"


def list_targets(repo: Path, *, nix: str = "nix") -> list[str]:
    executable = shutil.which(nix) if "/" not in nix else nix
    if not executable:
        raise RuntimeError(f"{nix} is not available")
    proc = subprocess.run(
        [
            executable,
            "eval",
            "--json",
            ".#homeConfigurations",
            "--apply",
            "builtins.attrNames",
        ],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "failed to evaluate homeConfigurations")
    value = json.loads(proc.stdout)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeError("homeConfigurations did not evaluate to a list of names")
    return sorted(value)


def select_target(targets: list[str], candidate: str | None) -> str | None:
    if candidate and candidate in targets:
        return candidate
    if len(targets) == 1:
        return targets[0]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--nix", default="nix")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    try:
        targets = list_targets(repo, nix=args.nix)
    except (RuntimeError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from None
    candidate = conventional_target()
    selected = select_target(targets, candidate)
    result = {
        "repo": str(repo),
        "candidate": candidate,
        "targets": targets,
        "selected": selected,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return
    if selected:
        print(selected)
        return
    print("no unambiguous Home Manager target")
    for target in targets:
        print(f"- {target}")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
