#!/usr/bin/env python3
"""Initialize immutable RAGE start evidence for the current git checkout."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "work"


def render(issue: int, branch: str, start_sha: str) -> str:
    return (
        "* Run identity\n"
        f"- Consumed issue :: #{issue}\n"
        f"- Branch :: ={branch}=\n"
        f"- RAGE start commit :: ={start_sha}=\n"
    )


def init_run(
    repo: Path,
    issue: int,
    slug: str,
    *,
    output: Path | None = None,
    allow_non_rage_branch: bool = False,
    append: bool = False,
    branch: str | None = None,
    start_sha: str | None = None,
) -> Path:
    repo = repo.expanduser().resolve()
    actual_branch = branch or _git(repo, "branch", "--show-current")
    if not actual_branch:
        raise RuntimeError("detached HEAD: RAGE requires a named branch")

    expected = f"rage/{issue}-{slugify(slug)}"
    if actual_branch != expected and not allow_non_rage_branch:
        raise RuntimeError(f"expected branch {expected}, current branch is {actual_branch}")

    sha = start_sha or _git(repo, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        raise RuntimeError(f"expected full 40-character git SHA, got: {sha}")

    target = output or repo / "rage" / f"{issue}-{slugify(slug)}.org"
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = render(issue, actual_branch, sha)

    if target.exists() and not append:
        raise FileExistsError(f"refusing to overwrite existing RAGE log: {target}")
    if append and target.exists():
        with target.open("a", encoding="utf-8") as stream:
            if target.stat().st_size:
                stream.write("\n")
            stream.write(payload)
    else:
        target.write_text(payload, encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", type=int)
    parser.add_argument("slug")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-non-rage-branch", action="store_true")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()
    try:
        target = init_run(
            args.repo,
            args.issue,
            args.slug,
            output=args.output,
            allow_non_rage_branch=args.allow_non_rage_branch,
            append=args.append,
        )
    except (RuntimeError, FileExistsError) as exc:
        raise SystemExit(str(exc)) from None
    print(target)


if __name__ == "__main__":
    main()
