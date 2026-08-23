#!/usr/bin/env python3
"""Fail-closed Task Steward skill adapter installer."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

SKILL_NAMES = ("task-steward-bootstrap", "task-steward-worker")


def canonical_skills_root() -> Path:
    return Path(__file__).resolve().parents[2]


def target_root(
    runtime: str,
    scope: str,
    *,
    project_root: Path | None = None,
    a0_root: Path | None = None,
    home: Path | None = None,
) -> Path:
    home = home or Path.home()
    if scope == "project":
        if project_root is None:
            raise ValueError("project scope requires --project-root")
        project = project_root.expanduser().resolve()
        suffix = {
            "agents": Path(".agents/skills"),
            "opencode": Path(".opencode/skills"),
            "agent-zero": Path(".a0proj/skills"),
        }[runtime]
        return project / suffix

    if runtime == "agents":
        return home / ".agents/skills"
    if runtime == "opencode":
        return home / ".config/opencode/skills"
    if a0_root is None:
        raise ValueError("Agent Zero global scope requires --a0-root")
    return a0_root.expanduser().resolve() / "usr/skills"


def _install_link(source: Path, target: Path, *, dry_run: bool) -> str:
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return f"ok {target} -> {source}"
        raise FileExistsError(f"refusing conflicting symlink: {target}")
    if target.exists():
        raise FileExistsError(f"refusing existing path: {target}")
    if dry_run:
        return f"would-link {target} -> {source}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=True)
    return f"linked {target} -> {source}"


def install(
    runtime: str,
    scope: str,
    *,
    project_root: Path | None = None,
    a0_root: Path | None = None,
    home: Path | None = None,
    source_root: Path | None = None,
    dry_run: bool = False,
    compat_a0: bool = False,
) -> list[str]:
    if runtime not in {"agents", "opencode", "agent-zero"}:
        raise ValueError(f"unsupported runtime: {runtime}")
    if scope not in {"global", "project"}:
        raise ValueError(f"unsupported scope: {scope}")
    if compat_a0 and scope != "project":
        raise ValueError("--compat-a0 is project-scope only")

    sources = (source_root or canonical_skills_root()).resolve()
    missing = [name for name in SKILL_NAMES if not (sources / name / "SKILL.md").is_file()]
    if missing:
        raise FileNotFoundError(f"canonical skills are missing: {', '.join(missing)}")

    roots = [
        target_root(
            runtime,
            scope,
            project_root=project_root,
            a0_root=a0_root,
            home=home,
        )
    ]
    if compat_a0:
        if project_root is None:
            raise ValueError("--compat-a0 requires --project-root")
        roots.append(project_root.expanduser().resolve() / ".a0/skills")

    results: list[str] = []
    for root in roots:
        for name in SKILL_NAMES:
            results.append(_install_link(sources / name, root / name, dry_run=dry_run))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("agents", "opencode", "agent-zero"), required=True)
    parser.add_argument("--scope", choices=("global", "project"), required=True)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--a0-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--compat-a0", action="store_true")
    args = parser.parse_args()

    try:
        results = install(
            args.runtime,
            args.scope,
            project_root=args.project_root,
            a0_root=args.a0_root,
            dry_run=args.dry_run,
            compat_a0=args.compat_a0,
        )
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from None
    print("\n".join(results))


if __name__ == "__main__":
    main()
