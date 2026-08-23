#!/usr/bin/env python3
"""Verify Zara MCP discovery surfaces without mutating server configuration."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass

TOKEN_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+\S+"),
    re.compile(r"(?i)([?&](?:token|api[_-]?key|secret)=)[^&\s]+"),
    re.compile(r"(?i)(https?://)[^/@:\s]+:[^/@\s]+@"),
)


@dataclass(frozen=True)
class Check:
    argv: tuple[str, ...]
    returncode: int
    output: str


def redact(text: str) -> str:
    text = TOKEN_PATTERNS[0].sub("Bearer <redacted>", text)
    text = TOKEN_PATTERNS[1].sub(r"\1<redacted>", text)
    text = TOKEN_PATTERNS[2].sub(r"\1<redacted>@", text)
    return text


def commands(binary: str, server: str | None = None) -> list[tuple[str, ...]]:
    result = [
        (binary, "mcp", "--help"),
        (binary, "mcp", "status"),
    ]
    if server:
        result.extend(
            (binary, "mcp", action, server)
            for action in ("inspect", "tools", "resources", "prompts")
        )
    return result


def run_checks(
    binary: str = "zara",
    server: str | None = None,
    *,
    timeout: float = 15.0,
) -> list[Check]:
    executable = shutil.which(binary) if "/" not in binary else binary
    if not executable:
        raise RuntimeError(f"{binary} is not available")
    checks: list[Check] = []
    for argv in commands(executable, server):
        try:
            proc = subprocess.run(
                argv,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
            checks.append(Check(argv, proc.returncode, redact(proc.stdout)))
        except subprocess.TimeoutExpired as exc:
            output = redact((exc.stdout or "") if isinstance(exc.stdout, str) else "")
            checks.append(Check(argv, 124, output))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("server", nargs="?")
    parser.add_argument("--binary", default="zara")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--show-output", action="store_true")
    args = parser.parse_args()

    try:
        checks = run_checks(args.binary, args.server, timeout=args.timeout)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None

    failed = False
    for check in checks:
        status = "ok" if check.returncode == 0 else f"fail({check.returncode})"
        print(f"{status}: {' '.join(check.argv)}")
        if args.show_output and check.output.strip():
            print(check.output.rstrip())
        failed |= check.returncode != 0
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
