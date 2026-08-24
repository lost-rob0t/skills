#!/usr/bin/env python3
"""Probe desktop privilege prerequisites without requesting elevation."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from typing import Sequence


def _ok(command: Sequence[str], *, timeout: float = 3.0) -> bool:
    try:
        proc = subprocess.run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def portal_broker() -> str | None:
    busctl = shutil.which("busctl")
    if busctl and _ok([busctl, "--user", "--quiet", "--no-pager", "status", "org.freedesktop.portal.Desktop"]):
        return "xdg-desktop-portal"
    gdbus = shutil.which("gdbus")
    if gdbus and _ok([
        gdbus,
        "call",
        "--session",
        "--dest",
        "org.freedesktop.portal.Desktop",
        "--object-path",
        "/org/freedesktop/portal/desktop",
        "--method",
        "org.freedesktop.DBus.Peer.Ping",
    ]):
        return "xdg-desktop-portal"
    return None


def probe() -> dict[str, object]:
    return {
        "pkexec": shutil.which("pkexec"),
        "portal_broker": portal_broker(),
        "desktop_session": os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION"),
        "display_available": bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")),
        "polkit_agent": "not-generically-probed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = probe()
    ready = bool(result["pkexec"] and result["portal_broker"] and result["display_available"])
    if args.json:
        print(json.dumps({**result, "ready": ready}, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
        print(f"ready: {ready}")
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
