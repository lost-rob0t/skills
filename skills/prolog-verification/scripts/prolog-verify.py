#!/usr/bin/env python3
"""Create and enforce an on-disk SWI-Prolog verification workspace."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Iterator, Sequence


VERIFY_TEMPLATE = r"""% Task-specific verification for the current worktree.
:- set_prolog_flag(unknown, error).
:- use_module(library(plunit)).
:- use_module(library(time)).
:- ensure_loaded('facts.kb').

current_successful_observation :-
    repo_state(Head, Digest),
    observation(_, _, exit(0), _, Head, Digest).

current_research_evidence :-
    research_required(false).
current_research_evidence :-
    research_required(true),
    repo_state(Head, Digest),
    brave_search(_, _, _, Head, Digest).

base_complete :-
    task(_),
    current_successful_observation,
    current_research_evidence.

% Extend this predicate with task-specific requirements and invariants.
complete :-
    base_complete.

:- begin_tests(workspace_verification).

test(complete) :-
    complete.

:- end_tests(workspace_verification).

main :-
    catch(call_with_time_limit(30, (run_tests, once(complete))),
          Error,
          (print_message(error, Error), fail)),
    !,
    halt(0).
main :-
    halt(1).

:- initialization(main, main).
"""


class VerificationError(RuntimeError):
    """A fail-closed verification error."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atom(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return f"'{escaped}'"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


@contextlib.contextmanager
def facts_lock(prolog_dir: Path) -> Iterator[None]:
    prolog_dir.mkdir(parents=True, exist_ok=True)
    with (prolog_dir / ".facts.lock").open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def discover_root(value: str | None) -> Path:
    start = Path(value or os.getcwd()).expanduser().resolve()
    probe = run_git(start, "rev-parse", "--show-toplevel", check=False)
    if probe.returncode == 0:
        return Path(probe.stdout.decode().strip()).resolve()
    return start


def hash_file(hasher: "hashlib._Hash", root: Path, path: Path) -> None:
    relative = path.relative_to(root).as_posix().encode()
    hasher.update(len(relative).to_bytes(8, "big"))
    hasher.update(relative)
    if path.is_symlink():
        payload = os.readlink(path).encode()
    else:
        payload = path.read_bytes()
    hasher.update(len(payload).to_bytes(8, "big"))
    hasher.update(payload)


def repository_state(root: Path) -> tuple[str, str]:
    head_probe = run_git(root, "rev-parse", "HEAD", check=False)
    if head_probe.returncode == 0:
        head = head_probe.stdout.decode().strip()
        diff = run_git(root, "diff", "--binary", "HEAD", "--", ".", ":(exclude).prolog/**").stdout
        others = run_git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".").stdout
        hasher = hashlib.sha256(diff)
        names = sorted(name for name in others.split(b"\0") if name)
        for raw_name in names:
            relative = Path(os.fsdecode(raw_name))
            if relative.parts and relative.parts[0] == ".prolog":
                continue
            path = root / relative
            if path.exists() or path.is_symlink():
                hash_file(hasher, root, path)
        return head, hasher.hexdigest()

    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() and not path.is_symlink():
            continue
        if relative.parts and relative.parts[0] in {".git", ".prolog"}:
            continue
        hash_file(hasher, root, path)
    return "no-git", hasher.hexdigest()


def paths(root: Path) -> tuple[Path, Path, Path, Path]:
    prolog_dir = root / ".prolog"
    return prolog_dir, prolog_dir / "facts.kb", prolog_dir / "verify.pl", prolog_dir / "result.json"


def ensure_workspace(root: Path) -> tuple[Path, Path, Path, Path]:
    result = paths(root)
    if not result[1].is_file() or not result[2].is_file():
        raise VerificationError("missing .prolog/facts.kb or .prolog/verify.pl; run prolog-verify init")
    return result


def replace_fact(text: str, predicate: str, line: str) -> str:
    matcher = re.compile(rf"^{re.escape(predicate)}\(.*\)\.\n?", re.MULTILINE)
    matches = list(matcher.finditer(text))
    if len(matches) != 1:
        raise VerificationError(f"expected exactly one {predicate}/1-or-more fact")
    return matcher.sub(line + "\n", text, count=1)


def update_state(facts: Path, head: str, digest: str) -> None:
    text = facts.read_text(encoding="utf-8")
    line = f"repo_state({atom(head)}, {atom(digest)})."
    atomic_write(facts, replace_fact(text, "repo_state", line))


def append_fact(facts: Path, line: str) -> None:
    text = facts.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        text += "\n"
    atomic_write(facts, text + line + "\n")


def init_workspace(root: Path, task: str, force: bool) -> None:
    prolog_dir, facts, verify, _ = paths(root)
    if not force and (facts.exists() or verify.exists()):
        raise VerificationError("verification workspace already exists; refusing to overwrite it")
    head, digest = repository_state(root)
    prolog_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(
        facts,
        "% Ground facts and machine observations for this worktree.\n"
        f"task({atom(task)}).\n"
        f"repo_state({atom(head)}, {atom(digest)}).\n"
        "research_required(false).\n",
    )
    atomic_write(verify, VERIFY_TEMPLATE)


def observe(root: Path, command: Sequence[str]) -> int:
    prolog_dir, facts, _, _ = ensure_workspace(root)
    if not command:
        raise VerificationError("observe requires a command after --")
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        completed = subprocess.run(
            list(command),
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            check=False,
        )
        stdout_file.seek(0)
        stdout = stdout_file.read()
        stderr_file.seek(0)
        stderr = stderr_file.read()
    sys.stdout.buffer.write(stdout)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(stderr)
    sys.stderr.buffer.flush()

    head, digest = repository_state(root)
    output_digest = hashlib.sha256(stdout + b"\0" + stderr).hexdigest()
    stamp = utc_now()
    identity = hashlib.sha256((stamp + "\0" + "\0".join(command)).encode()).hexdigest()[:16]
    argv = "[" + ", ".join(atom(item) for item in command) + "]"
    line = (
        f"observation({atom(identity)}, command({argv}), exit({completed.returncode}), "
        f"{atom(output_digest)}, {atom(head)}, {atom(digest)})."
    )
    with facts_lock(prolog_dir):
        update_state(facts, head, digest)
        append_fact(facts, line)
    return completed.returncode


def set_research(root: Path, required: bool) -> None:
    prolog_dir, facts, _, _ = ensure_workspace(root)
    with facts_lock(prolog_dir):
        text = facts.read_text(encoding="utf-8")
        value = "true" if required else "false"
        atomic_write(facts, replace_fact(text, "research_required", f"research_required({value})."))


def record_brave(root: Path, query: str, result_file: Path) -> None:
    prolog_dir, facts, _, _ = ensure_workspace(root)
    payload = result_file.expanduser().read_bytes()
    if not payload:
        raise VerificationError("Brave result file is empty")
    head, digest = repository_state(root)
    line = (
        f"brave_search({atom(hashlib.sha256(query.encode()).hexdigest())}, "
        f"{atom(hashlib.sha256(payload).hexdigest())}, {atom(utc_now())}, "
        f"{atom(head)}, {atom(digest)})."
    )
    with facts_lock(prolog_dir):
        update_state(facts, head, digest)
        text = facts.read_text(encoding="utf-8")
        atomic_write(facts, replace_fact(text, "research_required", "research_required(true)."))
        append_fact(facts, line)


def write_result(result: Path, payload: dict[str, object]) -> None:
    atomic_write(result, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def check_workspace(root: Path) -> tuple[bool, str]:
    prolog_dir, facts, verify, result = ensure_workspace(root)
    head, digest = repository_state(root)
    fact_text = facts.read_text(encoding="utf-8")
    expected_state = f"repo_state({atom(head)}, {atom(digest)})."
    state_lines = [line for line in fact_text.splitlines() if line.startswith("repo_state(")]
    error = None
    if state_lines != [expected_state]:
        error = "verification evidence is stale for the current HEAD/worktree digest"
    current_suffix = f", {atom(head)}, {atom(digest)})."
    observations = [
        line for line in fact_text.splitlines()
        if line.startswith("observation(") and ", exit(0)," in line and line.endswith(current_suffix)
    ]
    if error is None and not observations:
        error = "no successful machine observation exists for the current workspace state"
    research_required = "research_required(true)." in fact_text.splitlines()
    brave = [
        line for line in fact_text.splitlines()
        if line.startswith("brave_search(") and line.endswith(current_suffix)
    ]
    if error is None and research_required and not brave:
        error = "external research is required but no current Brave evidence exists"

    base = {
        "checked_at": utc_now(),
        "head": head,
        "worktree_digest": digest,
        "facts_sha256": hashlib.sha256(facts.read_bytes()).hexdigest(),
        "verify_sha256": hashlib.sha256(verify.read_bytes()).hexdigest(),
    }
    if error is not None:
        write_result(result, {**base, "status": "fail", "reason": error})
        return False, error

    swipl = os.environ.get("SWIPL_BIN", "swipl")
    try:
        completed = subprocess.run(
            [swipl, "-q", "-f", "none", "-s", verify.name],
            cwd=prolog_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=45,
        )
        reason = "verification passed" if completed.returncode == 0 else f"SWI-Prolog exited {completed.returncode}"
        write_result(
            result,
            {
                **base,
                "status": "pass" if completed.returncode == 0 else "fail",
                "reason": reason,
                "swipl_exit": completed.returncode,
                "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
            },
        )
        detail = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        return completed.returncode == 0, reason + (("\n" + detail) if detail else "")
    except FileNotFoundError:
        reason = f"SWI-Prolog executable not found: {swipl}"
    except subprocess.TimeoutExpired:
        reason = "SWI-Prolog verification exceeded 45 seconds"
    write_result(result, {**base, "status": "fail", "reason": reason})
    return False, reason


def safe_session_id(value: object) -> str:
    candidate = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", candidate)[:128]


def read_hook_input() -> dict[str, object]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"invalid hook JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise VerificationError("hook input must be a JSON object")
    return payload


def hook_session_start() -> None:
    payload = read_hook_input()
    root = discover_root(str(payload.get("cwd") or os.getcwd()))
    prolog_dir, _, _, _ = paths(root)
    head, digest = repository_state(root)
    session = safe_session_id(payload.get("session_id"))
    atomic_write(
        prolog_dir / "sessions" / f"{session}.json",
        json.dumps({"head": head, "worktree_digest": digest}, sort_keys=True) + "\n",
    )
    print("{}")


def hook_stop() -> None:
    payload = read_hook_input()
    root = discover_root(str(payload.get("cwd") or os.getcwd()))
    prolog_dir, _, _, _ = paths(root)
    session = safe_session_id(payload.get("session_id"))
    baseline_path = prolog_dir / "sessions" / f"{session}.json"
    if not baseline_path.is_file():
        print("{}")
        return
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    head, digest = repository_state(root)
    if baseline == {"head": head, "worktree_digest": digest}:
        print("{}")
        return
    try:
        passed, reason = check_workspace(root)
    except VerificationError as exc:
        passed, reason = False, str(exc)
    if passed:
        print("{}")
        return
    print(json.dumps({"decision": "block", "reason": f"Prolog verification gate failed: {reason}"}))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prolog-verify")
    parser.add_argument("--work-dir", help="worktree or directory to verify; defaults to the current Git root")
    commands = parser.add_subparsers(dest="action", required=True)
    init = commands.add_parser("init", help="create .prolog/facts.kb and .prolog/verify.pl")
    init.add_argument("--task", required=True)
    init.add_argument("--force", action="store_true")
    observe_parser = commands.add_parser("observe", help="run an argv and record its real result")
    observe_parser.add_argument("command", nargs=argparse.REMAINDER)
    research = commands.add_parser("set-research", help="set whether current work requires Brave evidence")
    research.add_argument("value", choices=("required", "not-required"))
    brave = commands.add_parser("record-brave", help="record a successful Brave result file")
    brave.add_argument("--query", required=True)
    brave.add_argument("--result-file", required=True, type=Path)
    commands.add_parser("check", help="fail unless current machine evidence and Prolog tests pass")
    commands.add_parser("hook-session-start", help=argparse.SUPPRESS)
    commands.add_parser("hook-stop", help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "hook-session-start":
            hook_session_start()
            return 0
        if args.action == "hook-stop":
            hook_stop()
            return 0
        root = discover_root(args.work_dir)
        if args.action == "init":
            init_workspace(root, args.task, args.force)
            print(f"initialized {root / '.prolog'}")
            return 0
        if args.action == "observe":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            return observe(root, command)
        if args.action == "set-research":
            set_research(root, args.value == "required")
            return 0
        if args.action == "record-brave":
            record_brave(root, args.query, args.result_file)
            return 0
        if args.action == "check":
            passed, reason = check_workspace(root)
            stream = sys.stdout if passed else sys.stderr
            print(reason, file=stream)
            return 0 if passed else 1
        raise AssertionError(args.action)
    except (OSError, VerificationError) as exc:
        print(f"prolog-verify: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
