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
:- ensure_loaded('knowledge.kb').

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

KNOWLEDGE_HEADER = r"""% Generated projection of active durable Prolog knowledge.
% This file is advisory/historical context. It is not current machine proof.
:- dynamic long_term_knowledge/10.

remembered(Key, Value) :-
    long_term_knowledge(_, _, _, memory, Key, Value, _, active, _, _).
known_bug(Key, Value) :-
    long_term_knowledge(_, _, _, bug, Key, Value, _, active, _, _).
known_failure_path(Key, Value) :-
    long_term_knowledge(_, _, _, failure_path, Key, Value, _, active, _, _).
known_invariant(Key, Value) :-
    long_term_knowledge(_, _, _, invariant, Key, Value, _, active, _, _).
known_decision(Key, Value) :-
    long_term_knowledge(_, _, _, decision, Key, Value, _, active, _, _).
known_workaround(Key, Value) :-
    long_term_knowledge(_, _, _, workaround, Key, Value, _, active, _, _).
known_warning(Key, Value) :-
    long_term_knowledge(_, _, _, warning, Key, Value, _, active, _, _).
"""

KNOWLEDGE_KINDS = {
    "memory",
    "bug",
    "failure_path",
    "invariant",
    "decision",
    "workaround",
    "warning",
}
KNOWLEDGE_STATUSES = {"active", "resolved", "superseded"}


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


def paths(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    prolog_dir = root / ".prolog"
    return (
        prolog_dir,
        prolog_dir / "facts.kb",
        prolog_dir / "verify.pl",
        prolog_dir / "result.json",
        prolog_dir / "knowledge.kb",
    )


def ensure_workspace(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    result = paths(root)
    if not result[1].is_file() or not result[2].is_file():
        raise VerificationError("missing .prolog/facts.kb or .prolog/verify.pl; run prolog-verify init")
    if not result[4].is_file():
        atomic_write(result[4], KNOWLEDGE_HEADER)
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
    prolog_dir, facts, verify, _, knowledge = paths(root)
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
    atomic_write(knowledge, KNOWLEDGE_HEADER)


def observe(root: Path, command: Sequence[str]) -> int:
    prolog_dir, facts, _, _, _ = ensure_workspace(root)
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
    prolog_dir, facts, _, _, _ = ensure_workspace(root)
    with facts_lock(prolog_dir):
        text = facts.read_text(encoding="utf-8")
        value = "true" if required else "false"
        atomic_write(facts, replace_fact(text, "research_required", f"research_required({value})."))


def record_brave_payload(root: Path, query: str, payload: bytes) -> None:
    prolog_dir, facts, _, _, _ = ensure_workspace(root)
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
        record_brave_payload(root, query, completed.stdout)
    return completed.returncode


def write_result(result: Path, payload: dict[str, object]) -> None:
    atomic_write(result, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def canonical_repository_identity(root: Path) -> str:
    probe = run_git(root, "config", "--get", "remote.origin.url", check=False)
    if probe.returncode == 0 and probe.stdout.strip():
        value = probe.stdout.decode().strip()
        uri = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://(?:[^@/]+@)?([^/:]+)(?::[0-9]+)?/(.+)$", value)
        if uri:
            host, path = uri.groups()
            return f"{host.lower()}/{path.removesuffix('.git')}"
        scp = re.match(r"^(?:[^@]+@)?([^:]+):(.+)$", value)
        if scp:
            host, path = scp.groups()
            return f"{host.lower()}/{path.removesuffix('.git')}"
        return value.removesuffix(".git")
    return str(root.resolve())


def project_owner(root: Path) -> str:
    identity = canonical_repository_identity(root)
    return "project-" + hashlib.sha256(identity.encode()).hexdigest()[:24]


def knowledge_db_path() -> Path:
    override = os.environ.get("PROLOG_VERIFY_DB")
    if override:
        return Path(override).expanduser().resolve()
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")).expanduser()
    return (data_home / "prolog-verification" / "knowledge.db").resolve()


def knowledge_store_script() -> Path:
    return Path(__file__).resolve().with_name("knowledge-store.pl")


@contextlib.contextmanager
def knowledge_lock(db: Path) -> Iterator[None]:
    lock_path = db.with_name(db.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield


def run_knowledge_store(root: Path, *args: str) -> dict[str, object]:
    store = knowledge_store_script()
    if not store.is_file():
        raise VerificationError(f"missing durable knowledge helper: {store}")
    db = knowledge_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    swipl = os.environ.get("SWIPL_BIN", "swipl")
    try:
        with knowledge_lock(db):
            completed = subprocess.run(
                [swipl, "-q", "-f", "none", "-s", str(store), "--", str(db), *args],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=15,
            )
    except FileNotFoundError as exc:
        raise VerificationError(f"SWI-Prolog executable not found: {swipl}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VerificationError("durable Prolog knowledge operation exceeded 15 seconds") from exc
    if completed.returncode != 0:
        detail = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        raise VerificationError(f"durable Prolog knowledge operation failed ({completed.returncode})" + ((": " + detail) if detail else ""))
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise VerificationError("durable Prolog knowledge helper returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise VerificationError("durable Prolog knowledge helper returned a non-object")
    if payload.get("status") == "error":
        raise VerificationError(str(payload.get("error") or "durable Prolog knowledge helper failed"))
    return payload


def normalize_kind(value: str) -> str:
    kind = value.strip().lower().replace("-", "_")
    if kind not in KNOWLEDGE_KINDS:
        allowed = ", ".join(sorted(KNOWLEDGE_KINDS))
        raise VerificationError(f"unknown knowledge kind {value!r}; expected one of: {allowed}")
    return kind


def knowledge_owner(root: Path, scope: str, session_id: str | None) -> str:
    if scope == "global":
        return "*"
    if scope == "project":
        return project_owner(root)
    if scope == "session":
        if not session_id:
            raise VerificationError("session-scoped knowledge requires --session-id")
        raw = f"{project_owner(root)}\0{safe_session_id(session_id)}"
        return "session-" + hashlib.sha256(raw.encode()).hexdigest()[:24]
    raise VerificationError(f"unknown knowledge scope: {scope}")


def default_knowledge_source(root: Path) -> str:
    head = run_git(root, "rev-parse", "HEAD", check=False)
    if head.returncode == 0:
        return "git:" + head.stdout.decode().strip()
    return "manual"


def maybe_refresh_knowledge_projection(root: Path, session_id: str | None = None) -> None:
    _, facts, verify, _, _ = paths(root)
    if facts.is_file() and verify.is_file():
        refresh_knowledge_projection(root, session_id=session_id)


def remember_knowledge(
    root: Path,
    scope: str,
    session_id: str | None,
    kind: str,
    key: str,
    value: str,
    source: str | None,
) -> dict[str, object]:
    normalized = normalize_kind(kind)
    owner = knowledge_owner(root, scope, session_id)
    source_value = source or default_knowledge_source(root)
    identity = hashlib.sha256(f"{scope}\0{owner}\0{normalized}\0{key}".encode()).hexdigest()[:24]
    payload = run_knowledge_store(
        root,
        "put",
        "k-" + identity,
        scope,
        owner,
        normalized,
        key,
        value,
        source_value,
        "active",
        utc_now(),
    )
    maybe_refresh_knowledge_projection(root, session_id=session_id)
    return payload


def list_knowledge_exact(
    root: Path,
    scope: str,
    owner: str,
    kind: str | None,
    query: str | None,
    status: str | None,
) -> list[dict[str, object]]:
    payload = run_knowledge_store(
        root,
        "list",
        scope,
        owner,
        normalize_kind(kind) if kind else "*",
        query or "*",
        status or "*",
    )
    records = payload.get("records")
    if not isinstance(records, list):
        raise VerificationError("durable Prolog knowledge helper omitted records")
    return [record for record in records if isinstance(record, dict)]


def recall_knowledge(
    root: Path,
    scope: str,
    session_id: str | None,
    kind: str | None,
    query: str | None,
    status: str | None,
    limit: int | None,
) -> list[dict[str, object]]:
    if status is not None and status not in KNOWLEDGE_STATUSES:
        raise VerificationError(f"unknown knowledge status: {status}")

    rank = {"session": 0, "project": 1, "global": 2}
    if scope == "applicable":
        session_owner = knowledge_owner(root, "session", session_id) if session_id else "*"
        payload = run_knowledge_store(
            root,
            "applicable",
            project_owner(root),
            session_owner,
            normalize_kind(kind) if kind else "*",
            query or "*",
            status or "*",
        )
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            raise VerificationError("durable Prolog knowledge helper omitted records")
        records = [record for record in raw_records if isinstance(record, dict)]
        records.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
        records.sort(key=lambda item: rank.get(str(item.get("scope")), 99))
    elif scope in {"global", "project", "session"}:
        owner = knowledge_owner(root, scope, session_id)
        records = list_knowledge_exact(root, scope, owner, kind, query, status)
        records.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    else:
        raise VerificationError(f"unknown recall scope: {scope}")

    deduped: list[dict[str, object]] = []
    seen: set[tuple[object, object]] = set()
    for record in records:
        dedupe_key = (record.get("kind"), record.get("key"))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(record)

    deduped.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return deduped[:limit] if limit is not None else deduped


def render_knowledge_projection(records: Sequence[dict[str, object]]) -> str:
    lines = [KNOWLEDGE_HEADER.rstrip(), ""]
    for record in records:
        values = [
            str(record.get("id") or ""),
            str(record.get("scope") or ""),
            str(record.get("owner") or ""),
            str(record.get("kind") or ""),
            str(record.get("key") or ""),
            str(record.get("value") or ""),
            str(record.get("source") or ""),
            str(record.get("status") or ""),
            str(record.get("created_at") or ""),
            str(record.get("updated_at") or ""),
        ]
        lines.append("long_term_knowledge(" + ", ".join(atom(value) for value in values) + ").")
    return "\n".join(lines) + "\n"


def refresh_knowledge_projection(root: Path, session_id: str | None = None) -> int:
    _, _, _, _, knowledge = ensure_workspace(root)
    records = recall_knowledge(
        root,
        scope="applicable",
        session_id=session_id,
        kind=None,
        query=None,
        status="active",
        limit=None,
    )
    atomic_write(knowledge, render_knowledge_projection(records))
    return len(records)


def set_knowledge_status(root: Path, record_id: str, status: str, session_id: str | None) -> dict[str, object]:
    if status not in KNOWLEDGE_STATUSES:
        raise VerificationError(f"unknown knowledge status: {status}")
    payload = run_knowledge_store(root, "status", record_id, status, utc_now())
    maybe_refresh_knowledge_projection(root, session_id=session_id)
    return payload


def forget_knowledge(root: Path, record_id: str, session_id: str | None) -> dict[str, object]:
    payload = run_knowledge_store(root, "forget", record_id)
    maybe_refresh_knowledge_projection(root, session_id=session_id)
    return payload


def print_knowledge(records: Sequence[dict[str, object]], as_json: bool) -> None:
    if as_json:
        print(json.dumps(list(records), indent=2, sort_keys=True))
        return
    for record in records:
        print(f"[{record.get('id')}] {record.get('scope')} {record.get('kind')} {record.get('key')}")
        print(f"  {record.get('value')}")
        print(f"  source={record.get('source')} status={record.get('status')} updated={record.get('updated_at')}")


def check_workspace(root: Path) -> tuple[bool, str]:
    prolog_dir, facts, verify, result, knowledge = ensure_workspace(root)
    if knowledge_db_path().exists():
        refresh_knowledge_projection(root)
    elif not knowledge.is_file():
        atomic_write(knowledge, KNOWLEDGE_HEADER)

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
        "knowledge_sha256": hashlib.sha256(knowledge.read_bytes()).hexdigest(),
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
    prolog_dir, _, _, _, _ = paths(root)
    head, digest = repository_state(root)
    session = safe_session_id(payload.get("session_id"))
    if (root / ".prolog" / "facts.kb").is_file() and knowledge_db_path().exists():
        try:
            refresh_knowledge_projection(root, session_id=session)
        except VerificationError:
            pass
    atomic_write(
        prolog_dir / "sessions" / f"{session}.json",
        json.dumps({"head": head, "worktree_digest": digest}, sort_keys=True) + "\n",
    )
    print("{}")


def hook_stop() -> None:
    payload = read_hook_input()
    root = discover_root(str(payload.get("cwd") or os.getcwd()))
    prolog_dir, _, _, _, _ = paths(root)
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

    init = commands.add_parser("init", help="create .prolog/facts.kb, knowledge.kb, and verify.pl")
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

    remember = commands.add_parser("remember", help="upsert durable symbolic memory, bugs, failures, and invariants")
    remember.add_argument("--kind", default="memory")
    remember.add_argument("--key", required=True)
    remember.add_argument("--value", required=True)
    remember.add_argument("--scope", choices=("project", "global", "session"), default="project")
    remember.add_argument("--session-id")
    remember.add_argument("--source")

    recall = commands.add_parser("recall", help="query durable symbolic knowledge")
    recall.add_argument("--kind")
    recall.add_argument("--query")
    recall.add_argument("--scope", choices=("applicable", "project", "global", "session"), default="applicable")
    recall.add_argument("--session-id")
    recall.add_argument("--status", choices=tuple(sorted(KNOWLEDGE_STATUSES)), default="active")
    recall.add_argument("--limit", type=int, default=50)
    recall.add_argument("--json", action="store_true")

    resolve = commands.add_parser("resolve", help="mark a durable knowledge record resolved")
    resolve.add_argument("record_id")
    resolve.add_argument("--session-id")

    supersede = commands.add_parser("supersede", help="mark a durable knowledge record superseded")
    supersede.add_argument("record_id")
    supersede.add_argument("--session-id")

    forget = commands.add_parser("forget", help="delete a durable knowledge record")
    forget.add_argument("record_id")
    forget.add_argument("--session-id")

    context = commands.add_parser("context", help="refresh .prolog/knowledge.kb from applicable durable knowledge")
    context.add_argument("--session-id")

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
        if args.action == "brave":
            return brave_search(
                root,
                args.query,
                args.max_tokens,
                args.max_urls,
                args.max_tokens_per_url,
            )
        if args.action == "remember":
            payload = remember_knowledge(
                root,
                args.scope,
                args.session_id,
                args.kind,
                args.key,
                args.value,
                args.source,
            )
            print(json.dumps(payload, sort_keys=True))
            return 0
        if args.action == "recall":
            if args.limit is not None and args.limit < 1:
                raise VerificationError("--limit must be at least 1")
            records = recall_knowledge(
                root,
                args.scope,
                args.session_id,
                args.kind,
                args.query,
                args.status,
                args.limit,
            )
            print_knowledge(records, args.json)
            return 0
        if args.action == "resolve":
            print(json.dumps(set_knowledge_status(root, args.record_id, "resolved", args.session_id), sort_keys=True))
            return 0
        if args.action == "supersede":
            print(json.dumps(set_knowledge_status(root, args.record_id, "superseded", args.session_id), sort_keys=True))
            return 0
        if args.action == "forget":
            print(json.dumps(forget_knowledge(root, args.record_id, args.session_id), sort_keys=True))
            return 0
        if args.action == "context":
            count = refresh_knowledge_projection(root, session_id=args.session_id)
            print(f"projected {count} durable knowledge records into {root / '.prolog' / 'knowledge.kb'}")
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
