#!/usr/bin/env python3
"""Produce privacy-preserving workflow suggestions from local history."""

from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


SENSITIVE_RE = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|authinfo|\.env(?:\.|$)|"
    r"id_rsa|private[_-]?key|BEGIN [A-Z ]+ KEY)",
    re.IGNORECASE,
)
SENSITIVE_ARGUMENT_RE = re.compile(
    r"(?:^|\s)(?:-p|--password|--token|--secret|--api[-_]?key)(?:=|\s)",
    re.IGNORECASE,
)
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+!?/:=-]{0,63}$")
EMACS_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
COMMAND_WRAPPERS = {"builtin", "command", "env", "exec", "nice", "sudo", "time"}
EMACS_NOISE = {
    "coding",
    "config",
    "desktop",
    "focus",
    "origin",
    "q",
    "sh",
    "w",
    "wq",
    "yes",
    "no",
}
SHELL_SUGGESTION_EXCLUDE = {"cd", "clear", "echo", "exit", "history", "ls", "pwd"}
EMACS_COMMAND_HINTS = (
    "atomic-chrome",
    "bookmark",
    "browse-url",
    "dslide",
    "envrc",
    "gptel",
    "image-",
    "magit",
    "mara",
    "mcp",
    "org",
    "qtile",
    "update-",
)


def is_sensitive(value: str) -> bool:
    """Return whether a history value should be excluded from analysis."""
    return bool(SENSITIVE_RE.search(value) or SENSITIVE_ARGUMENT_RE.search(value))


def command_family(line: str) -> str | None:
    """Extract only the executable family from one safe shell history line."""
    line = line.strip()
    if not line or line.startswith("#") or is_sensitive(line):
        return None
    segment = re.split(r"\s*(?:&&|\|\||[;|])\s*", line, maxsplit=1)[0]
    try:
        words = shlex.split(segment, comments=False, posix=True)
    except ValueError:
        return None
    while words and (words[0] in COMMAND_WRAPPERS or "=" in words[0].split("/", 1)[0]):
        words.pop(0)
    if not words:
        return None
    executable = Path(words[0]).name.casefold()
    return executable if SAFE_NAME_RE.fullmatch(executable) else None


def shell_families(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return counts
    for line in lines:
        family = command_family(line)
        if family:
            counts[family] += 1
    return counts


def shell_sequences(path: Path) -> Counter[str]:
    families = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return Counter()
    for line in lines:
        family = command_family(line)
        if family:
            families.append(family)
    return Counter(
        f"{left} -> {right}"
        for left, right in zip(families, families[1:])
        if left != right
    )


def _decode_emacs_string(raw: str) -> str:
    try:
        return str(ast.literal_eval(raw))
    except (SyntaxError, ValueError):
        return raw[1:-1]


def emacs_command_name(value: str) -> str | None:
    """Keep command-shaped Emacs history values while dropping prompts/paths."""
    value = value.strip()
    if (
        not value
        or value.casefold() in EMACS_NOISE
        or len(value) > 64
        or value[0].isdigit()
        or value.startswith(("/", "~/", "http:", "https:"))
        or ":" in value
        or ("/" in value and not value.startswith("+"))
        or not SAFE_NAME_RE.fullmatch(value)
    ):
        return None
    if value.startswith("+") or "/" in value or "-" in value:
        return value
    return value if value.casefold() in EMACS_COMMAND_HINTS else None


def emacs_commands(paths: list[Path]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in EMACS_STRING_RE.findall(text):
            name = emacs_command_name(_decode_emacs_string(raw))
            if name:
                counts[name] += 1
    return counts


def _safe_root(value: str, home: Path) -> str | None:
    if is_sensitive(value):
        return None
    normalized = value.replace(str(home), "~").replace("$HOME", "~")
    markers = (
        ("/.dotfiles", "~/.dotfiles"),
        ("/Documents/AI", "~/Documents/AI"),
        ("/Documents/Projects", "~/Documents/Projects"),
        ("/Documents/Notes", "~/Documents/Notes"),
        ("/Documents/Emacs", "~/Documents/Emacs"),
        ("/Documents/Admin", "~/Documents/Admin"),
    )
    for marker, label in markers:
        if marker in normalized:
            return label
    return None


def recent_roots(paths: list[Path], home: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in EMACS_STRING_RE.findall(text):
            root = _safe_root(_decode_emacs_string(raw), home)
            if root:
                counts[root] += 1
    return counts


def _activity_category(app: str, title: str) -> str:
    value = f"{app} {title}".casefold()
    if any(token in value for token in ("chatgpt", "openai", "claude", "opencode", "openrouter", "llm", "gptel")):
        return "AI tools"
    if any(token in value for token in ("youtube", "twitch", "netflix", "vlc", "mpv", "feishin", "video")):
        return "video/media"
    if any(token in value for token in ("minecraft", "war thunder", "steam", "terraria", "game")):
        return "games"
    if "emacs" in value:
        return "Emacs"
    if any(token in value for token in ("brave", "firefox", "chrom", "browser")):
        return "browsers"
    if any(token in value for token in ("terminator", "terminal", "xterm", "kitty")):
        return "terminals"
    return "other applications"


def activitywatch_categories(base_url: str | None) -> Counter[str]:
    if not base_url:
        return Counter()
    try:
        with urlopen(f"{base_url.rstrip('/')}/api/0/buckets", timeout=1) as response:
            buckets = json.load(response)
        window_bucket = next(
            (bucket_id for bucket_id, bucket in buckets.items() if bucket.get("type") == "currentwindow"),
            None,
        )
        if not window_bucket:
            return Counter()
        with urlopen(
            f"{base_url.rstrip('/')}/api/0/buckets/{window_bucket}/events?limit=50000",
            timeout=2,
        ) as response:
            events = json.load(response)
    except (OSError, URLError, ValueError, KeyError):
        return Counter()
    counts: Counter[str] = Counter()
    for event in events:
        data = event.get("data", {})
        counts[_activity_category(str(data.get("app", "")), str(data.get("title", "")))] += 1
    return counts


def _top(counter: Counter[str], limit: int = 8) -> list[dict[str, Any]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def build_report(
    bash_history: Path,
    emacs_history: list[Path],
    recentf_history: list[Path],
    activitywatch_url: str | None,
    home: Path | None = None,
) -> dict[str, Any]:
    home = home or Path.home()
    shell = shell_families(bash_history)
    sequences = shell_sequences(bash_history)
    commands = emacs_commands(emacs_history)
    roots = recent_roots(recentf_history, home)
    activity = activitywatch_categories(activitywatch_url)
    suggestions: list[dict[str, Any]] = []

    for family, count in shell.most_common(5):
        if count >= 5 and family not in SHELL_SUGGESTION_EXCLUDE:
            suggestions.append({
                "area": "shell",
                "evidence": f"{family} appeared {count} times",
                "proposal": f"Consider a named dotfiles alias or function for the repeated {family} workflow.",
                "confidence": "medium",
            })
    for sequence, count in sequences.most_common(3):
        if count >= 3:
            suggestions.append({
                "area": "shell sequence",
                "evidence": f"the command-family sequence repeated {count} times",
                "proposal": f"Consider a small wrapper for the repeated {sequence} workflow.",
                "confidence": "high",
            })
    for command, count in commands.most_common(5):
        if count >= 3:
            suggestions.append({
                "area": "Emacs",
                "evidence": f"the Emacs command family {command} appeared {count} times",
                "proposal": f"Consider a leader-key binding or persistent shortcut for {command}.",
                "confidence": "medium",
            })
    for root, count in roots.most_common(5):
        if count >= 5:
            suggestions.append({
                "area": "navigation",
                "evidence": f"the broad workspace {root} appeared {count} times in recent-file history",
                "proposal": f"Consider a project-jump command or directory shortcut for {root}.",
                "confidence": "medium",
            })
    for category, count in activity.most_common(5):
        if category != "other applications" and count >= 10:
            suggestions.append({
                "area": "desktop",
                "evidence": f"ActivityWatch recorded {count} window events in the {category} category",
                "proposal": f"Consider a dedicated launcher, workspace rule, or keybinding for {category} workflows.",
                "confidence": "low",
            })

    return {
        "sources": {
            "bash_history": bash_history.is_file(),
            "emacs_history": any(path.is_file() for path in emacs_history),
            "recentf_history": any(path.is_file() for path in recentf_history),
            "activitywatch": bool(activity),
        },
        "evidence": {
            "shell_command_families": _top(shell),
            "shell_sequences": _top(sequences),
            "emacs_command_families": _top(commands),
            "recent_workspace_roots": _top(roots),
            "activity_categories": _top(activity),
        },
        "suggestions": suggestions[:12],
    }


def render_markdown(report: dict[str, Any]) -> str:
    sources = ", ".join(
        f"{name.replace('_', ' ')}={'yes' if available else 'no'}"
        for name, available in report["sources"].items()
    )
    lines = ["## Workflow discovery", "", f"Sources: {sources}", "", "### Suggestions", ""]
    if not report["suggestions"]:
        lines.append("No repeatable workflow met the suggestion threshold.")
    else:
        for suggestion in report["suggestions"]:
            lines.append(
                f"- **{suggestion['area']} ({suggestion['confidence']})** — "
                f"{suggestion['proposal']} Evidence: {suggestion['evidence']}."
            )
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash-history", type=Path, default=home / ".bash_history")
    parser.add_argument(
        "--emacs-history",
        type=Path,
        action="append",
        default=[home / ".config/emacs/.local/cache/savehist"],
    )
    parser.add_argument(
        "--recentf",
        type=Path,
        action="append",
        default=[home / ".config/emacs/.local/cache/recentf", home / "Documents/Emacs/recentf"],
    )
    parser.add_argument("--activitywatch-url", default="http://127.0.0.1:5600")
    parser.add_argument("--no-activitywatch", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser


def main() -> int:
    args = _parser().parse_args()
    report = build_report(
        args.bash_history,
        args.emacs_history,
        args.recentf,
        None if args.no_activitywatch else args.activitywatch_url,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
