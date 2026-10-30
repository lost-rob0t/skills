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
import uuid
from typing import Iterator, Sequence


VERIFY_TEMPLATE = r"""% Task-specific verification for the current worktree.
:- set_prolog_flag(unknown, error).
:- use_module(library(plunit)).
:- use_module(library(time)).
:- use_module(library(lists)).
:- dynamic machine_observation/8, machine_brave_search/7, requirement/2, claim/2.
:- discontiguous machine_observation/8, machine_brave_search/7, requirement/2, claim/2.
:- ensure_loaded('facts.kb').

load_current_run :-
    verification_context(_, Run),
    atomic_list_concat(['runs/', Run, '/evidence.pl'], RunFile),
    ( exists_file(RunFile) -> ensure_loaded(RunFile) ; true ).

:- load_current_run.

% Compatibility views expose only the active task/run, never another journal.
observation(Id, Command, Exit, Output, Head, Digest) :-
    verification_context(Task, Run),
    machine_observation(Task, Run, _, Command, _, _, Head, Digest),
    findall(record(I, E, O),
            machine_observation(Task, Run, I, Command, E, O, Head, Digest),
            Records),
    last(Records, record(Id, Exit, Output)).
brave_search(Query, Result, Time, Head, Digest) :-
    verification_context(Task, Run),
    machine_brave_search(Task, Run, Query, Result, Time, Head, Digest).

current_successful_observation :-
    repo_state(Head, Digest),
    observation(_, _, exit(0), _, Head, Digest).

current_research_evidence :-
    research_required(false).
current_research_evidence :-
    research_required(true),
    repo_state(Head, Digest),
    brave_search(_, _, _, Head, Digest).

% Closed executable bindings. Unsupported claims stay unknown.
requirement_status(Id, Status, Evidence) :-
    requirement_result(Id, Actual, Evidence), Status = Actual.

requirement_result(Id, conflict, none) :-
    requirement(Id, A), requirement(Id, B), A \== B, !.
requirement_result(Id, Status, Evidence) :-
    requirement(Id, command(Argv)),
    !,
    repo_state(Head, Digest),
    ( observation(Observation, command(Argv), exit(Exit), Output, Head, Digest)
    -> ( Exit =:= 0 -> Status = verified ; Status = failed ),
       Evidence = evidence(Observation, Output, Head, Digest)
    ; observation(_, command(Argv), _, _, _, _)
    -> Status = stale, Evidence = none
    ; Status = unknown, Evidence = none ).
requirement_result(_, unknown, none).

claim_status(Id, Status, Evidence) :-
    claim_result(Id, Actual, Evidence), Status = Actual.

claim_result(Id, conflict, none) :-
    claim(Id, A), claim(Id, B), A \== B, !.
claim_result(Id, Status, Evidence) :-
    claim(Id, requirement(Requirement)),
    !, requirement_status(Requirement, Status, Evidence).
claim_result(_, unknown, none).

current_failed_observation :-
    repo_state(Head, Digest),
    observation(_, _, exit(Exit), _, Head, Digest),
    Exit =\= 0.

base_complete :-
    task(_),
    \+ current_failed_observation,
    forall(requirement(Id, _), (requirement_status(Id, RequirementStatus, _), RequirementStatus == verified)),
    forall(claim(Id, _), (claim_status(Id, ClaimStatus, _), ClaimStatus == verified)),
    current_successful_observation,
    current_research_evidence.

% Extend this predicate with task-specific requirements and invariants.
complete :-
    base_complete.

:- begin_tests(workspace_verification).

test(complete) :-
    once(complete).

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


def atomic_write(path: Path, text: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(text.encode("utf-8") if isinstance(text, str) else text)
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


def is_runtime_prolog_path(relative: Path) -> bool:
    if not relative.parts or relative.parts[0] != ".prolog":
        return False
    if len(relative.parts) >= 2 and relative.parts[1] in {"runs", "sessions"}:
        return True
    return relative.as_posix() in {
        ".prolog/facts.kb",
        ".prolog/verify.pl",
        ".prolog/result.json",
        ".prolog/.facts.lock",
    }


def repository_state(root: Path) -> tuple[str, str]:
    head_probe = run_git(root, "rev-parse", "HEAD", check=False)
    if head_probe.returncode == 0:
        head = head_probe.stdout.decode().strip()
        diff = run_git(
            root,
            "diff",
            "--binary",
            "HEAD",
            "--",
            ".",
            ":(exclude).prolog/facts.kb",
            ":(exclude).prolog/verify.pl",
            ":(exclude).prolog/result.json",
            ":(exclude).prolog/.facts.lock",
            ":(exclude).prolog/runs/**",
            ":(exclude).prolog/sessions/**",
        ).stdout
        others = run_git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".").stdout
        hasher = hashlib.sha256(diff)
        names = sorted(name for name in others.split(b"\0") if name)
        for raw_name in names:
            relative = Path(os.fsdecode(raw_name))
            if is_runtime_prolog_path(relative):
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
        if relative.parts and relative.parts[0] == ".git":
            continue
        if is_runtime_prolog_path(relative):
            continue
        hash_file(hasher, root, path)
    return "no-git", hasher.hexdigest()


def paths(root: Path) -> tuple[Path, Path, Path, Path]:
    prolog_dir = root / ".prolog"
    return prolog_dir, prolog_dir / "facts.kb", prolog_dir / "verify.pl", prolog_dir / "result.json"


def context(facts: Path) -> tuple[str, str]:
    text = facts.read_text(encoding="utf-8")
    matches = re.findall(r"^verification_context\('([A-Za-z0-9_.-]+)', '([a-f0-9]{32})'\)\.$", text, re.MULTILINE)
    if len(matches) != 1:
        raise VerificationError("missing or invalid run identity; legacy evidence requires explicit init --force")
    task, run = matches[0]
    if f"task({atom(task)})." not in text.splitlines():
        raise VerificationError("task does not match verification context")
    return task, run


def run_path(prolog_dir: Path, run: str) -> Path:
    return prolog_dir / "runs" / run / "evidence.pl"


def archive_controls(prolog_dir: Path, facts: Path, verify: Path) -> None:
    sources = [path for path in (facts, verify, prolog_dir / "result.json") if path.exists()]
    if not sources:
        return
    try:
        _, run = context(facts)
    except (OSError, VerificationError):
        run = "legacy-" + uuid.uuid4().hex
    destination = prolog_dir / "runs" / run / "controls" / uuid.uuid4().hex
    for source in sources:
        atomic_write(destination / source.name, source.read_bytes())


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


def append_fact(path: Path, line: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    atomic_write(path, text + line + "\n")


def init_workspace(root: Path, task: str, force: bool) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", task):
        raise VerificationError("task must be a portable identifier of 1-128 characters")
    prolog_dir, facts, verify, result = paths(root)
    with facts_lock(prolog_dir):
        if not force and (facts.exists() or verify.exists()):
            raise VerificationError("verification workspace already exists; refusing to overwrite it")
        archive_controls(prolog_dir, facts, verify)
        head, digest = repository_state(root)
        run = uuid.uuid4().hex
        atomic_write(
            facts,
            "% Ground task/control facts. Evidence is isolated by task and run.\n"
            f"task({atom(task)}).\n"
            f"verification_context({atom(task)}, {atom(run)}).\n"
            f"repo_state({atom(head)}, {atom(digest)}).\n"
            "research_required(false).\n",
        )
        atomic_write(verify, VERIFY_TEMPLATE)
        atomic_write(run_path(prolog_dir, run), "% Machine-owned append-only evidence.\n")
        write_result(result, {"task": task, "run": run, "status": "unknown", "reason": "no observations yet"})


def observe(root: Path, command: Sequence[str]) -> int:
    prolog_dir, facts, _, _ = ensure_workspace(root)
    if not command:
        raise VerificationError("observe requires a command after --")
    with facts_lock(prolog_dir):
        task, run = context(facts)
        before = repository_state(root)
        write_result(paths(root)[3], {"task": task, "run": run, "status": "unknown", "reason": "observation in progress"})
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
    identity = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S%f") + "-" + uuid.uuid4().hex
    argv = "[" + ", ".join(atom(item) for item in command) + "]"
    line = (
        f"machine_observation({atom(task)}, {atom(run)}, {atom(identity)}, command({argv}), exit({completed.returncode}), "
        f"{atom(output_digest)}, {atom(head)}, {atom(digest)})."
    )
    with facts_lock(prolog_dir):
        output_dir = run_path(prolog_dir, run).parent / "observations" / identity
        atomic_write(output_dir / "stdout.txt", stdout)
        atomic_write(output_dir / "stderr.txt", stderr)
        if before != (head, digest):
            incomplete = (f"incomplete_observation({atom(task)}, {atom(run)}, {atom(identity)}, "
                          f"command({argv}), exit({completed.returncode}), {atom(output_digest)}, "
                          f"before({atom(before[0])}, {atom(before[1])}), "
                          f"after({atom(head)}, {atom(digest)})).")
            append_fact(run_path(prolog_dir, run), incomplete)
            raise VerificationError("workspace changed during observation; result is not current proof")
        append_fact(run_path(prolog_dir, run), line)
        if context(facts) != (task, run):
            raise VerificationError("active task/run changed during observation; evidence retained in original run")
        update_state(facts, head, digest)
    return completed.returncode


def require_command(root: Path, identity: str, command: Sequence[str]) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", identity) or not command:
        raise VerificationError("require needs a portable --id and exact command after --")
    prolog_dir, facts, _, result = ensure_workspace(root)
    with facts_lock(prolog_dir):
        task, run = context(facts)
        text = facts.read_text(encoding="utf-8")
        prefix = f"requirement({atom(identity)},"
        if any(line.startswith(prefix) for line in text.splitlines()):
            raise VerificationError("requirement already exists; use a new identity or explicit new run")
        argv = "[" + ", ".join(atom(item) for item in command) + "]"
        append_fact(facts, f"requirement({atom(identity)}, command({argv})).")
        append_fact(facts, f"claim({atom(identity)}, requirement({atom(identity)})).")
        write_result(result, {"task": task, "run": run, "status": "unknown", "reason": "requirements changed; check required"})


def set_research(root: Path, required: bool) -> None:
    prolog_dir, facts, _, _ = ensure_workspace(root)
    with facts_lock(prolog_dir):
        text = facts.read_text(encoding="utf-8")
        value = "true" if required else "false"
        atomic_write(facts, replace_fact(text, "research_required", f"research_required({value})."))
        task, run = context(facts)
        write_result(paths(root)[3], {"task": task, "run": run, "status": "unknown", "reason": "research requirements changed"})


def record_brave_payload(root: Path, query: str, payload: bytes,
                         expected: tuple[tuple[str, str], tuple[str, str]] | None = None) -> None:
    prolog_dir, facts, _, _ = ensure_workspace(root)
    if not payload:
        raise VerificationError("Brave result file is empty")
    task, run = context(facts)
    head, digest = repository_state(root)
    line = (
        f"machine_brave_search({atom(task)}, {atom(run)}, {atom(hashlib.sha256(query.encode()).hexdigest())}, "
        f"{atom(hashlib.sha256(payload).hexdigest())}, {atom(utc_now())}, "
        f"{atom(head)}, {atom(digest)})."
    )
    with facts_lock(prolog_dir):
        if context(facts) != (task, run) or (expected is not None and expected != ((task, run), (head, digest))):
            raise VerificationError("active task/run or workspace changed during research")
        update_state(facts, head, digest)
        text = facts.read_text(encoding="utf-8")
        atomic_write(facts, replace_fact(text, "research_required", "research_required(true)."))
        append_fact(run_path(prolog_dir, run), line)
        write_result(paths(root)[3], {"task": task, "run": run, "status": "unknown", "reason": "research observed; check required"})


def record_brave(root: Path, query: str, result_file: Path) -> None:
    record_brave_payload(root, query, result_file.expanduser().read_bytes())


def brave_search(
    root: Path,
    query: str,
    max_tokens: int,
    max_urls: int | None,
    max_tokens_per_url: int | None,
) -> int:
    if not 128 <= max_tokens <= 32768:
        raise VerificationError("--max-tokens must be between 128 and 32768")
    if max_urls is not None and not 1 <= max_urls <= 20:
        raise VerificationError("--max-urls must be between 1 and 20")
    if max_tokens_per_url is not None and not 128 <= max_tokens_per_url <= 8192:
        raise VerificationError("--max-tokens-per-url must be between 128 and 8192")
    prolog_dir, facts, _, _ = ensure_workspace(root)
    with facts_lock(prolog_dir):
        expected = context(facts), repository_state(root)
    binary = os.environ.get("BX_BIN", "bx")
    command = [binary, "context", query, "--max-tokens", str(max_tokens)]
    if max_urls is not None:
        command += ["--max-urls", str(max_urls)]
    if max_tokens_per_url is not None:
        command += ["--max-tokens-per-url", str(max_tokens_per_url)]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=45,
        )
    except FileNotFoundError as exc:
        raise VerificationError(f"Brave Search CLI executable not found: {binary}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VerificationError("Brave Search CLI exceeded 45 seconds") from exc
    sys.stdout.buffer.write(completed.stdout)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(completed.stderr)
    sys.stderr.buffer.flush()
    if completed.returncode == 0:
        record_brave_payload(root, query, completed.stdout, expected)
    return completed.returncode


def write_result(result: Path, payload: dict[str, object]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    run = payload.get("run")
    if run:
        history = result.parent / "runs" / str(run) / "checks" / uuid.uuid4().hex
        atomic_write(history / "result.json", text)
        for name in ("facts.kb", "verify.pl", "runs/" + str(run) + "/evidence.pl"):
            source = result.parent / name
            if source.exists():
                atomic_write(history / Path(name).name, source.read_text(encoding="utf-8"))
    atomic_write(result, text)


def check_workspace(root: Path, task: str | None = None, run: str | None = None) -> tuple[bool, str]:
    with facts_lock(paths(root)[0]):
        return check_locked(root, task, run)


def check_locked(root: Path, expected_task: str | None, expected_run: str | None) -> tuple[bool, str]:
    prolog_dir, facts, verify, result = ensure_workspace(root)
    head, digest = repository_state(root)
    fact_text = facts.read_text(encoding="utf-8")
    task, run = context(facts)
    if (expected_task is not None and expected_task != task) or (expected_run is not None and expected_run != run):
        raise VerificationError("active task/run does not match the requested verification identity")
    current_run = run_path(prolog_dir, run)
    run_text = current_run.read_text(encoding="utf-8") if current_run.is_file() else ""
    expected_state = f"repo_state({atom(head)}, {atom(digest)})."
    state_lines = [line for line in fact_text.splitlines() if line.startswith("repo_state(")]
    error = None
    if state_lines != [expected_state]:
        error = "verification evidence is stale for the current HEAD/worktree digest"
    current_suffix = f", {atom(head)}, {atom(digest)})."
    observations = [
        line for line in run_text.splitlines()
        if line.startswith(f"machine_observation({atom(task)}, {atom(run)},") and ", exit(0)," in line and line.endswith(current_suffix)
    ]
    if error is None and not observations:
        error = "no successful machine observation exists for the current workspace state"
    research_required = "research_required(true)." in fact_text.splitlines()
    brave = [
        line for line in run_text.splitlines()
        if line.startswith(f"machine_brave_search({atom(task)}, {atom(run)},") and line.endswith(current_suffix)
    ]
    if error is None and research_required and not brave:
        error = "external research is required but no current Brave evidence exists"

    base = {
        "task": task,
        "run": run,
        "checked_at": utc_now(),
        "head": head,
        "worktree_digest": digest,
        "facts_sha256": hashlib.sha256(facts.read_bytes()).hexdigest(),
        "verify_sha256": hashlib.sha256(verify.read_bytes()).hexdigest(),
        "run_file": current_run.name,
        "run_sha256": hashlib.sha256(current_run.read_bytes()).hexdigest() if current_run.is_file() else None,
    }
    if error is not None:
        attempted = any(line.startswith(f"machine_observation({atom(task)}, {atom(run)},")
                        and line.endswith(current_suffix) for line in run_text.splitlines())
        status = "stale" if "stale" in error else ("fail" if attempted else "unknown")
        write_result(result, {**base, "status": status, "reason": error})
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
        if (repository_state(root) != (head, digest)
                or facts.read_text(encoding="utf-8") != fact_text
                or hashlib.sha256(verify.read_bytes()).hexdigest() != base["verify_sha256"]
                or hashlib.sha256(current_run.read_bytes()).hexdigest() != base["run_sha256"]):
            write_result(result, {**base, "status": "stale", "reason": "workspace changed during verification"})
            return False, "workspace changed during verification"
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
    search = commands.add_parser("brave", help="run a fixed Brave context search and record its result")
    search.add_argument("--query", required=True)
    search.add_argument("--max-tokens", type=int, default=4096)
    search.add_argument("--max-urls", type=int)
    search.add_argument("--max-tokens-per-url", type=int)
    requirement = commands.add_parser("require", help="bind a requirement and claim to an exact command")
    requirement.add_argument("--id", required=True)
    requirement.add_argument("command", nargs=argparse.REMAINDER)
    check = commands.add_parser("check", help="fail unless current machine evidence and Prolog tests pass")
    check.add_argument("--task", help="expected task identity; fail on mismatch")
    check.add_argument("--run", help="expected run identity; fail on mismatch")
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
        if args.action == "require":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            require_command(root, args.id, command)
            return 0
        if args.action == "set-research":
            set_research(root, args.value == "required")
            return 0
        if args.action == "record-brave":
            record_brave(root, args.query, args.result_file)
            return 0
        if args.action == "brave":
            return brave_search(
                root,
                args.query,
                args.max_tokens,
                args.max_urls,
                args.max_tokens_per_url,
            )
        if args.action == "check":
            passed, reason = check_workspace(root, args.task, args.run)
            stream = sys.stdout if passed else sys.stderr
            print(reason, file=stream)
            return 0 if passed else 1
        raise AssertionError(args.action)
    except (OSError, VerificationError) as exc:
        print(f"prolog-verify: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
