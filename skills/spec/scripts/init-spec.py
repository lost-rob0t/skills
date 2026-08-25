#!/usr/bin/env python3
"""Create the deterministic scratch location used by the spec skill."""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

SECTIONS = (
    "Outcome",
    "Current state",
    "Requirements",
    "Non-goals",
    "Design / behavior",
    "Invariants",
    "Failure and recovery",
    "Acceptance criteria",
    "Verification",
    "Rollout / rollback",
    "Open blockers",
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "task"


def render(title: str) -> str:
    lines = [f"# {title}", ""]
    for section in SECTIONS:
        lines.extend((f"## {section}", ""))
    return "\n".join(lines).rstrip() + "\n"


def default_root() -> Path:
    prolog_context = os.environ.get("PROLOG_TMP_SPEC_CONTEXT")
    if prolog_context:
        return Path(prolog_context).expanduser().resolve() / "spec"
    return Path(os.environ.get("TMPDIR", "/tmp")) / "spec"


def init_spec(
    task: str,
    *,
    title: str | None = None,
    root: Path | None = None,
    force: bool = False,
) -> Path:
    base = root or default_root()
    target = base.expanduser().resolve() / slugify(task) / "SPEC.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing spec: {target}")
    target.write_text(render(title or task.strip() or "Task"), encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="task name used for the directory slug")
    parser.add_argument("--title", help="document title; defaults to task")
    parser.add_argument("--root", type=Path, help="override the default scratch spec root")
    parser.add_argument("--force", action="store_true", help="replace an existing SPEC.md")
    args = parser.parse_args()
    try:
        target = init_spec(args.task, title=args.title, root=args.root, force=args.force)
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from None
    print(target)


if __name__ == "__main__":
    main()
