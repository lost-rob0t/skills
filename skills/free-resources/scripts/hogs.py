#!/usr/bin/env python3
"""Rank resource-heavy processes and stop user-approved PIDs with safety checks."""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any

PROC = Path("/proc")
JIFFY = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100

DEFAULT_CRITICAL = [
    r"^systemd$",
    r"^init$",
    r"^Xorg$",
    r"^Xwayland$",
    r"^gnome-shell$",
    r"^plasmashell$",
    r"^(qtile|i3|i3bar|sway|hyprland|openbox|xfwm4|mutter)$",
    r"^pipewire(-pulse)?$",
    r"^(pulseaudio|rtkit|dbus-daemon|dbus-broker)$",
    r"^sshd(-session)?$",
    r"^udevd$",
    r"^login$",
    r"^getty$",
    r"^aw-server$",
    r"^(emacs|emacsclient)--daemon$",
]
AGENT_NAMES = {"opencode", "codex", "claude", "a0", "agent-zero"}


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, PermissionError):
        return None


def _boot_time(base: Path) -> int | None:
    stat = _read(base / "stat")
    if not stat:
        return None
    for line in stat.splitlines():
        if line.startswith("btime "):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def classify(comm: str, cmdline: str, patterns: list[re.Pattern[str]]) -> str:
    if any(p.search(comm) for p in patterns):
        return "critical"
    head = cmdline.split()[0].rsplit("/", 1)[-1].lower() if cmdline else ""
    if head in AGENT_NAMES or comm.lower() in AGENT_NAMES:
        return "agent"
    return "normal"


def snapshot(base: Path, interval: float, critical: list[re.Pattern[str]]) -> list[dict[str, Any]]:
    boot = _boot_time(base)
    pids = [int(e.name) for e in base.iterdir() if e.name.isdigit()]

    def cpu_of(pid: int) -> tuple[int, str, int, int, str | None]:
        stat = _read(base / str(pid) / "stat") or ""
        comm, utime, stime = "?", 0, 0
        cmdline = ""
        try:
            comm = stat[stat.index("(") + 1 : stat.rindex(")")]
            rest = stat[stat.rindex(")") + 2 :].split()
            utime, stime = int(rest[11]), int(rest[12])
        except (ValueError, IndexError):
            pass
        raw = _read(base / str(pid) / "cmdline")
        if raw:
            cmdline = raw.replace("\x00", " ").strip()
        uid = None
        try:
            uid = (base / str(pid)).stat().st_uid
        except OSError:
            pass
        return utime + stime, comm, 0, uid or -1, cmdline

    first = {pid: cpu_of(pid) for pid in pids}
    time.sleep(interval)
    rows: list[dict[str, Any]] = []
    now_t = int(time.time())
    for pid in pids:
        try:
            cpu_now, comm, _, uid, cmdline = cpu_of(pid)
        except OSError:
            continue
        prev = first.get(pid)
        if not prev:
            continue  # exited mid-sample
        cpu_pct = max(0.0, (cpu_now - prev[0]) / JIFFY / interval * 100)
        rss = swap = 0
        roll = _read(base / str(pid) / "smaps_rollup")
        if roll:
            for line in roll.splitlines():
                key, _, raw = line.partition(":")
                fields = raw.split()
                if fields and key in ("Rss", "Swap"):
                    try:
                        if key == "Rss":
                            rss = int(fields[0]) * 1024
                        else:
                            swap = int(fields[0]) * 1024
                    except ValueError:
                        continue
        io_read = io_write = None
        pio = _read(base / str(pid) / "io")
        if pio:
            for line in pio.splitlines():
                key, _, raw = line.partition(":")
                try:
                    if key.strip() == "read_bytes":
                        io_read = int(raw.strip())
                    elif key.strip() == "write_bytes":
                        io_write = int(raw.strip())
                except ValueError:
                    continue
        stat = _read(base / str(pid) / "stat") or ""
        age_s = None
        try:
            starttime = int(stat[stat.rindex(")") + 2 :].split()[19])
            if boot:
                age_s = max(0, now_t - boot - starttime // JIFFY)
        except (ValueError, IndexError):
            pass
        rows.append(
            {
                "pid": pid,
                "comm": comm,
                "uid": uid,
                "age_s": age_s,
                "cpu_pct": round(cpu_pct, 1),
                "rss": rss,
                "swap": swap,
                "io_read": io_read,
                "io_write": io_write,
                "kind": classify(comm, cmdline, critical),
                "cmdline": cmdline[:120],
            }
        )
    return rows


def _fmt_age(seconds: int | None) -> str:
    if seconds is None:
        return "?"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h{seconds % 3600 // 60:02d}m"
    return f"{seconds // 86400}d{seconds % 86400 // 3600:02d}h"


def render(rows: list[dict[str, Any]], sort_key: str) -> str:
    rank = {
        "mem": lambda r: -(r["rss"] + r["swap"]),
        "cpu": lambda r: -r["cpu_pct"],
        "io": lambda r: -((r["io_read"] or 0) + (r["io_write"] or 0)),
    }[sort_key]
    lines = [
        f"{'PID':>7}  {'USER':<8}{'AGE':>7}  {'CPU%':>5}  {'RSS':>7}{'SWAP':>7}  {'IO(TOT)':>9}  {'KIND':<8}COMM"
    ]
    for r in sorted(rows, key=rank)[:20]:
        user = "?"
        try:
            import pwd

            user = pwd.getpwuid(r["uid"]).pw_name if r["uid"] is not None else "?"
        except (ImportError, KeyError):
            pass
        io_total = (r["io_read"] or 0) + (r["io_write"] or 0)
        lines.append(
            f"{r['pid']:>7}  {user:<8}{_fmt_age(r['age_s']):>7}  {r['cpu_pct']:>5.1f}  "
            f"{r['rss'] / 1048576:>6.0f}M{r['swap'] / 1048576:>6.0f}M  {io_total / 1048576:>7.0f}M  "
            f"{r['kind']:<8}{r['comm'][:24]}"
        )
    return "\n".join(lines)


def load_critical(extra: Path | None) -> list[re.Pattern[str]]:
    patterns = [re.compile(p) for p in DEFAULT_CRITICAL]
    if extra:
        for line in extra.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(re.compile(line))
    return patterns


def kill_pids(
    base: Path,
    pids: list[int],
    sig: int,
    critical: list[re.Pattern[str]],
    *,
    timeout: float,
) -> tuple[list[str], int]:
    """Signal approved PIDs only; fail closed on critical, missing, or foreign processes."""
    errors: list[str] = []
    survivors = 0
    for pid in pids:
        proc_dir = base / str(pid)
        stat = _read(proc_dir / "stat")
        if not stat:
            errors.append(f"pid {pid}: no such process")
            survivors += 1
            continue
        try:
            comm = stat[stat.index("(") + 1 : stat.rindex(")")]
        except ValueError:
            comm = "?"
        if any(p.search(comm) for p in critical):
            errors.append(f"pid {pid} ({comm}): session-critical, refusing")
            survivors += 1
            continue
        if pid in (1, os.getpid(), os.getpgrp()):
            errors.append(f"pid {pid}: refusing to kill self or init")
            survivors += 1
            continue
        try:
            target_uid = proc_dir.stat().st_uid
        except OSError as exc:
            errors.append(f"pid {pid}: stat failed ({exc})")
            survivors += 1
            continue
        if os.geteuid() != 0 and target_uid != os.geteuid():
            errors.append(f"pid {pid} ({comm}): owned by uid {target_uid}, not yours; refusing")
            survivors += 1
            continue
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            errors.append(f"pid {pid} ({comm}): signal refused ({exc})")
            survivors += 1
            continue
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not (base / str(pid)).exists():
                break
            time.sleep(0.2)
        if (base / str(pid)).exists():
            errors.append(f"pid {pid} ({comm}): still alive after signal {sig!r}")
            survivors += 1
        else:
            print(f"stopped pid {pid} ({comm})")
    return errors, survivors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plist = sub.add_parser("list", help="rank processes by resource use (read-only)")
    plist.add_argument("--sort", choices=("mem", "cpu", "io"), default="mem")
    plist.add_argument("--interval", type=float, default=2.0)
    plist.add_argument("--json", action="store_true")
    plist.add_argument("--critical", type=Path, default=None, help="extra critical comm regexes, one per line")

    pkill = sub.add_parser("kill", help="stop explicitly approved PIDs after safety checks")
    pkill.add_argument("--pid", type=int, action="append", required=True)
    pkill.add_argument("--signal", default="TERM", choices=("TERM", "KILL"))
    pkill.add_argument("--timeout", type=float, default=5.0)
    pkill.add_argument("--yes", action="store_true", help="required confirmation flag")
    pkill.add_argument("--dry-run", action="store_true")
    pkill.add_argument("--critical", type=Path, default=None)

    args = parser.parse_args(argv)
    base = PROC
    if not (base / "stat").exists():
        print(f"error: {base} does not look like procfs (Linux required)", file=sys.stderr)
        return 2

    if args.command == "list":
        rows = snapshot(base, max(args.interval, 0.1), load_critical(args.critical))
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print(render(rows, args.sort))
        return 0

    if not args.yes:
        parser.error("kill requires explicit --yes (and per-PID user approval before this call)")
    errors, survivors = kill_pids(
        base,
        args.pid,
        signal.SIGKILL if args.signal == "KILL" else signal.SIGTERM,
        load_critical(args.critical),
        timeout=args.timeout,
    )
    for err in errors:
        print(err, file=sys.stderr)
    return 0 if survivors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
