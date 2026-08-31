#!/usr/bin/env python3
"""Manage isolated git worktrees under a shared per-project root."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

DEFAULT_ROOT = Path("~") / "git" / "worktrees"
SEPARATORS = re.compile(r"[^A-Za-z0-9]+")


class WorktreeError(RuntimeError):
    pass


def _git(*argv: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *argv],
        cwd=None if cwd is None else str(cwd),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise WorktreeError(
            proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(argv)} failed"
        )
    return proc


def slugify(value: str) -> str:
    slug = SEPARATORS.sub("-", value.strip()).strip("-")
    if not slug:
        raise WorktreeError(f"cannot derive a directory label from {value!r}")
    return slug


def project_slug(toplevel: Path) -> str:
    name = toplevel.name
    if name.endswith(".git"):
        name = name[: -len(".git")]
    return slugify(name).lower()


def branch_label(branch: str) -> str:
    if branch.startswith("origin/"):
        branch = branch[len("origin/") :]
    return slugify(branch)


def worktree_root(root_override: str | None = None) -> Path:
    raw = root_override or os.environ.get("GIT_WORKTREE_ROOT") or str(DEFAULT_ROOT)
    return Path(raw).expanduser()


def worktree_path(root: Path, toplevel: Path, label: str) -> Path:
    return root / f"{project_slug(toplevel)}-{label}"


def toplevel(cwd: Path | None = None) -> Path:
    proc = _git("rev-parse", "--show-toplevel", cwd=cwd)
    return Path(proc.stdout.strip())


def parse_worktrees(cwd: Path) -> list[dict[str, str]]:
    proc = _git("worktree", "list", "--porcelain", cwd=cwd)
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current = {"worktree": value}
        else:
            current[key] = value
    if current:
        entries.append(current)
    return entries


def main_worktree(cwd: Path) -> Path:
    entries = parse_worktrees(cwd)
    if not entries:
        raise WorktreeError("git reported no worktrees")
    return Path(entries[0]["worktree"])


def checked_out_path(cwd: Path, branch: str) -> Path | None:
    ref = f"refs/heads/{branch}"
    for entry in parse_worktrees(cwd):
        if entry.get("branch") == ref:
            return Path(entry["worktree"])
    return None


def branch_exists(cwd: Path, branch: str) -> bool:
    proc = _git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=cwd, check=False)
    return proc.returncode == 0


def resolve_target(args: argparse.Namespace) -> tuple[Path, Path, str, str]:
    cwd = Path.cwd()
    repo = toplevel(cwd)
    root = worktree_root(args.root)
    if args.pr is not None:
        branch = f"pr/{args.pr}"
        label = f"pr-{args.pr}"
    else:
        branch = args.branch
        label = branch_label(branch)
    return worktree_path(root, repo, label), repo, root, branch


def cmd_add(args: argparse.Namespace) -> None:
    target, repo, root, branch = resolve_target(args)
    if target.exists():
        raise WorktreeError(f"refusing to overwrite existing path: {target}")

    exists = branch_exists(repo, branch)
    if not exists and args.pr is None and args.base is None:
        raise WorktreeError(
            f"branch {branch} does not exist; pass --base REF to create it as a new branch"
        )

    clash = checked_out_path(repo, branch) if exists else None
    if clash is not None:
        raise WorktreeError(f"branch {branch} is already checked out at {clash}")

    if args.pr is not None:
        add_argv = ["fetch", "origin", f"pull/{args.pr}/head:{branch}"]
        worktree_argv = ["worktree", "add", str(target), branch]
    elif exists:
        add_argv = []
        worktree_argv = ["worktree", "add", str(target), branch]
    else:
        add_argv = []
        worktree_argv = ["worktree", "add", "-b", branch, str(target), args.base]

    if args.dry_run:
        for argv in ([add_argv] if add_argv else []) + [worktree_argv]:
            print(f"dry-run: would run: git {' '.join(argv)}")
        print(f"dry-run: worktree path: {target}")
        return

    if add_argv:
        _git(*add_argv, cwd=repo)
    root.mkdir(parents=True, exist_ok=True)
    _git(*worktree_argv, cwd=repo)
    print(target)


def cmd_path(args: argparse.Namespace) -> None:
    target, _, _, _ = resolve_target(args)
    print(target)


def cmd_list(args: argparse.Namespace) -> None:
    repo = toplevel(Path.cwd())
    root = worktree_root(args.root).resolve()
    for entry in parse_worktrees(repo):
        path = Path(entry["worktree"]).resolve()
        if path != root and root not in path.parents:
            continue
        if "branch" in entry:
            branch = entry["branch"].removeprefix("refs/heads/")
        else:
            branch = "(detached)"
        print(f"{path}\t{branch}")


def cmd_remove(args: argparse.Namespace) -> None:
    repo = toplevel(Path.cwd())
    root = worktree_root(args.root)
    raw = Path(args.target).expanduser()
    if raw.is_absolute():
        candidates = [raw]
    else:
        candidates = [Path.cwd() / raw, root / raw]
    resolved = next((c for c in candidates if c.exists()), None)
    if resolved is None:
        raise WorktreeError(f"no such worktree path: {args.target}")
    resolved = resolved.resolve()
    entries = parse_worktrees(repo)
    registered = {Path(entry["worktree"]).resolve() for entry in entries}
    if resolved not in registered:
        raise WorktreeError(f"not a registered git worktree: {resolved}")
    if resolved == Path(entries[0]["worktree"]).resolve():
        raise WorktreeError("refusing to remove the main working tree")
    if resolved != root and root not in resolved.parents:
        raise WorktreeError(f"refusing to remove path outside the worktree root: {resolved}")

    if args.dry_run:
        print(f"dry-run: would run: git worktree remove{' --force' if args.force else ''} {resolved}")
        return

    argv = ["worktree", "remove"]
    if args.force:
        argv.append("--force")
    argv.append(str(resolved))
    _git(*argv, cwd=repo)
    print(f"removed {resolved}")


def cmd_prune(args: argparse.Namespace) -> None:
    repo = toplevel(Path.cwd())
    if args.dry_run:
        print("dry-run: would run: git worktree prune")
        return
    _git("worktree", "prune", "--verbose", cwd=repo)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="worktree root (default: ~/git/worktrees or $GIT_WORKTREE_ROOT)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="create a worktree for a branch or pull request")
    target = add.add_mutually_exclusive_group(required=True)
    target.add_argument("branch", nargs="?", help="branch to check out")
    target.add_argument("--pr", type=int, metavar="N", help="check out pull request N")
    add.add_argument("--base", help="create the branch from REF if it does not exist")
    add.add_argument("--dry-run", action="store_true")
    add.set_defaults(func=cmd_add)

    path_cmd = subparsers.add_parser("path", help="print the worktree path for a branch or PR")
    path_target = path_cmd.add_mutually_exclusive_group(required=True)
    path_target.add_argument("branch", nargs="?")
    path_target.add_argument("--pr", type=int, metavar="N")
    path_cmd.set_defaults(func=cmd_path)

    list_cmd = subparsers.add_parser("list", help="list this project's worktrees under the root")
    list_cmd.set_defaults(func=cmd_list)

    remove = subparsers.add_parser("remove", help="remove a registered worktree")
    remove.add_argument("target", help="worktree directory name, relative, or absolute path")
    remove.add_argument("--force", action="store_true", help="discard dirty or locked worktree state")
    remove.add_argument("--dry-run", action="store_true")
    remove.set_defaults(func=cmd_remove)

    prune = subparsers.add_parser("prune", help="drop stale worktree records")
    prune.add_argument("--dry-run", action="store_true")
    prune.set_defaults(func=cmd_prune)

    args = parser.parse_args()
    try:
        args.func(args)
    except WorktreeError as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
