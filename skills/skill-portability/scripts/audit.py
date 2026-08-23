#!/usr/bin/env python3
"""Report portable-skill coupling without echoing matched secret-like content."""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {
    ".md", ".txt", ".org", ".py", ".sh", ".bash", ".zsh", ".fish", ".el",
    ".lisp", ".cl", ".scm", ".pro", ".pl", ".nix", ".toml", ".yaml", ".yml",
    ".json", ".ini", ".conf",
}
HOME_RE = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/")
HOST_RE = re.compile(r"\b(?:[A-Za-z0-9-]+\.)+(?:internal|lan|local)\b", re.IGNORECASE)
IP_RE = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: str


def _private_ip(text: str) -> bool:
    for match in IP_RE.finditer(text):
        try:
            address = ipaddress.ip_address(match.group(0))
        except ValueError:
            continue
        if address.is_private and not address.is_loopback:
            return True
    return False


def scan_line(line: str, *, literals: Iterable[str] = ()) -> set[str]:
    categories: set[str] = set()
    if HOME_RE.search(line):
        categories.add("absolute-home-path")
    if HOST_RE.search(line):
        categories.add("private-hostname")
    if _private_ip(line):
        categories.add("private-ip")
    for literal in literals:
        if literal and literal in line:
            categories.add(f"literal:{literal}")
    return categories


def iter_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        path = path.expanduser()
        if path.is_file():
            yield path
            continue
        if not path.is_dir():
            continue
        for child in sorted(path.rglob("*")):
            if not child.is_file() or ".git" in child.parts:
                continue
            if child.suffix.lower() in TEXT_SUFFIXES or child.name == "SKILL.md":
                yield child


def audit(paths: Iterable[Path], *, literals: Iterable[str] = ()) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_text_files(paths):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for category in sorted(scan_line(line, literals=literals)):
                findings.append(Finding(str(path), number, category))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(__file__).resolve().parents[1]])
    parser.add_argument("--literal", action="append", default=[], help="additional exact author/user/host literal to report")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args()

    findings = audit(args.paths, literals=args.literal)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    else:
        for item in findings:
            print(f"{item.path}:{item.line}: {item.category}")
        print(f"{len(findings)} finding(s)")
    if findings and args.fail_on_findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
