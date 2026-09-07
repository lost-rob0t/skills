#!/usr/bin/env python3
"""Diagnose CPU, memory, and I/O pressure from /proc and recommend the bottleneck."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PROC = Path("/proc")
JIFFY = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
PAGE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096

SEVERE_PSI = 25.0
PRESSURE_PSI = 10.0
LOAD_RATIO = 1.5
UTIL_RATIO = 0.60
SWAP_RATE = 1.0  # MiB/s
MEM_AVAIL_FLOOR = 0.10


def parse_psi(text: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        kind = parts[0]
        values = {}
        for item in parts[1:]:
            key, _, raw = item.partition("=")
            try:
                values[key] = float(raw)
            except ValueError:
                continue
        out[kind] = values
    return out


def parse_meminfo(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        key, _, raw = line.partition(":")
        fields = raw.split()
        if fields:
            try:
                out[key.strip()] = int(fields[0]) * 1024
            except ValueError:
                continue
    return out


def parse_vmstat(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        key, _, raw = line.partition(" ")
        try:
            out[key] = int(raw.strip())
        except ValueError:
            continue
    return out


def parse_diskstats(text: str) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 14:
            continue
        name = fields[2]
        out[name] = {
            "read_sectors": int(fields[5]),
            "write_sectors": int(fields[9]),
            "io_ticks_ms": int(fields[12]),
        }
    return out


def parse_proc_stat(text: str) -> tuple[int, int]:
    """Return (idle_jiffies, total_jiffies) summed over all CPUs."""
    idle = total = 0
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 5 or not parts[0].startswith("cpu") or parts[0] == "cpu":
            continue
        nums = [int(x) for x in parts[1:] if x.isdigit()]
        if len(nums) < 5:
            continue
        idle += nums[3] + (nums[4] if len(nums) > 4 else 0)
        total += sum(nums)
    return idle, total


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, PermissionError):
        return None


def iter_pids(base: Path) -> list[int]:
    pids = []
    for entry in base.iterdir():
        if entry.name.isdigit():
            pids.append(int(entry.name))
    return sorted(pids)


def process_snapshot(base: Path, pids: list[int]) -> dict[int, dict[str, Any]]:
    procs: dict[int, dict[str, Any]] = {}
    boot = _boot_time(base)
    for pid in pids:
        stat = _read(base / str(pid) / "stat")
        if not stat:
            continue
        try:
            rest = stat[stat.rindex(")") + 2 :].split()
        except ValueError:
            continue
        comm = stat[stat.index("(") + 1 : stat.rindex(")")]
        try:
            utime, stime = int(rest[11]), int(rest[12])
            starttime = int(rest[19])
        except (IndexError, ValueError):
            continue
        info: dict[str, Any] = {
            "comm": comm,
            "utime": utime,
            "stime": stime,
            "rss": 0,
            "swap": 0,
            "io_read": None,
            "io_write": None,
            "age_s": max(0, int(time.time()) - boot - starttime // JIFFY) if boot else None,
        }
        roll = _read(base / str(pid) / "smaps_rollup")
        if roll:
            for line in roll.splitlines():
                key, _, raw = line.partition(":")
                fields = raw.split()
                if fields and key in ("Rss", "Swap"):
                    try:
                        info[key.lower()] = int(fields[0]) * 1024
                    except ValueError:
                        continue
        pio = _read(base / str(pid) / "io")
        if pio:
            values: dict[str, int] = {}
            for line in pio.splitlines():
                key, _, raw = line.partition(":")
                try:
                    values[key.strip()] = int(raw.strip())
                except ValueError:
                    continue
            info["io_read"] = values.get("read_bytes")
            info["io_write"] = values.get("write_bytes")
        try:
            info["uid"] = (base / str(pid)).stat().st_uid
        except OSError:
            info["uid"] = None
        procs[pid] = info
    return procs


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


def ncpu(base: Path) -> int:
    stat = _read(base / "stat")
    if not stat:
        return 1
    return max(1, sum(1 for line in stat.splitlines() if line.startswith("cpu") and line[3:4].isdigit()))


def sample_system(base: Path, interval: float) -> dict[str, Any]:
    pids = iter_pids(base)
    cpu0 = parse_proc_stat(_read(base / "stat") or "")
    disk0 = parse_diskstats(_read(base / "diskstats") or "")
    vm0 = parse_vmstat(_read(base / "vmstat") or "")
    procs0 = process_snapshot(base, pids)
    time.sleep(interval)
    cpu1 = parse_proc_stat(_read(base / "stat") or "")
    disk1 = parse_diskstats(_read(base / "diskstats") or "")
    vm1 = parse_vmstat(_read(base / "vmstat") or "")
    procs1 = process_snapshot(base, iter_pids(base))

    total_delta = max(1, cpu1[1] - cpu0[1])
    idle_delta = cpu1[0] - cpu0[0]
    cpu_busy = max(0.0, min(1.0, 1.0 - idle_delta / total_delta))

    disks: dict[str, dict[str, float]] = {}
    for name, now in disk1.items():
        prev = disk0.get(name)
        if not prev:
            continue
        dt = max(interval, 0.001)
        sectors = 512
        disks[name] = {
            "read_mib_s": (now["read_sectors"] - prev["read_sectors"]) * sectors / dt / 1048576,
            "write_mib_s": (now["write_sectors"] - prev["write_sectors"]) * sectors / dt / 1048576,
            "util": max(0.0, min(1.0, (now["io_ticks_ms"] - prev["io_ticks_ms"]) / 1000 / dt)),
        }

    processes: dict[int, dict[str, Any]] = {}
    for pid, now in procs1.items():
        prev = procs0.get(pid)
        if not prev:
            continue
        cpu_j = (now["utime"] + now["stime"]) - (prev["utime"] + prev["stime"])
        processes[pid] = {
            **now,
            "cpu_pct": max(0.0, cpu_j / JIFFY / interval * 100),
            "io_rate_mib_s": (
                ((now["io_read"] or 0) + (now["io_write"] or 0) - (prev["io_read"] or 0) - (prev["io_write"] or 0))
                / interval
                / 1048576
            )
            if now["io_read"] is not None and prev["io_read"] is not None
            else None,
        }
    return {
        "interval": interval,
        "ncpu": ncpu(base),
        "cpu_busy": cpu_busy,
        "psi": {
            kind: parse_psi(_read(base / "pressure" / kind) or "")
            for kind in ("cpu", "memory", "io")
        },
        "meminfo": parse_meminfo(_read(base / "meminfo") or ""),
        "vmstat": {"now": vm1, "delta": {k: vm1.get(k, 0) - vm0.get(k, 0) for k in ("pswpin", "pswpout")}},
        "disks": disks,
        "processes": processes,
    }


def classify(sample: dict[str, Any]) -> dict[str, Any]:
    ncpu = sample["ncpu"]
    mem = sample["meminfo"]
    total = mem.get("MemTotal", 0)
    avail = mem.get("MemAvailable", 0)
    swap_total = mem.get("SwapTotal", 0)
    swap_free = mem.get("SwapFree", swap_total)
    swap_used_mib = max(0, swap_total - swap_free) / 1048576
    swap_rate = (sample["vmstat"]["delta"].get("pswpin", 0) + sample["vmstat"]["delta"].get("pswpout", 0)) * PAGE / max(sample["interval"], 0.001) / 1048576
    load_text = sample.get("loadavg") or ""

    def psi_some(kind: str) -> float:
        return sample["psi"].get(kind, {}).get("some", {}).get("avg60", 0.0)

    def psi_full(kind: str) -> float:
        return sample["psi"].get(kind, {}).get("full", {}).get("avg60", 0.0)

    procs = [{**p, "pid": pid} for pid, p in sample["processes"].items()]
    top_cpu = sorted(procs, key=lambda p: -p["cpu_pct"])[:5]
    top_mem = sorted(procs, key=lambda p: -(p["rss"] + p["swap"]))[:5]
    top_io = sorted(
        (p for p in procs if p["io_rate_mib_s"]),
        key=lambda p: -(p["io_rate_mib_s"] or 0),
    )[:5]
    worst_disk = max(
        ({"device": k, **v} for k, v in sample["disks"].items()),
        key=lambda d: d["util"],
        default=None,
    )

    evidence: list[str] = []
    scores = {
        "memory": 0.0,
        "io": 0.0,
        "cpu": 0.0,
    }
    if psi_some("memory") >= PRESSURE_PSI:
        scores["memory"] += psi_some("memory")
        evidence.append(f"PSI memory some avg60={psi_some('memory'):.1f}%")
    if psi_full("memory") >= PRESSURE_PSI:
        scores["memory"] += psi_full("memory")
        evidence.append(f"PSI memory full avg60={psi_full('memory'):.1f}%")
    if total and avail / total < MEM_AVAIL_FLOOR:
        scores["memory"] += 10
        evidence.append(f"MemAvailable {avail / 1048576:.0f}MiB is below 10% of {total / 1048576:.0f}MiB")
    if swap_total and swap_used_mib > 0:
        evidence.append(f"swap in use: {swap_used_mib:.0f}MiB of {swap_total / 1048576:.0f}MiB")
    if swap_rate >= SWAP_RATE:
        scores["memory"] += 20
        evidence.append(f"swap moving at {swap_rate:.1f}MiB/s (thrashing)")
    if psi_some("io") >= PRESSURE_PSI:
        scores["io"] += psi_some("io")
        evidence.append(f"PSI io some avg60={psi_some('io'):.1f}%")
    if psi_full("io") >= PRESSURE_PSI:
        scores["io"] += psi_full("io")
        evidence.append(f"PSI io full avg60={psi_full('io'):.1f}%")
    if worst_disk and worst_disk["util"] >= UTIL_RATIO:
        scores["io"] += worst_disk["util"] * 20
        evidence.append(
            f"device {worst_disk['device']} {worst_disk['util'] * 100:.0f}% util "
            f"(r {worst_disk['read_mib_s']:.1f}/w {worst_disk['write_mib_s']:.1f} MiB/s)"
        )
    if psi_some("cpu") >= PRESSURE_PSI:
        scores["cpu"] += psi_some("cpu")
        evidence.append(f"PSI cpu some avg60={psi_some('cpu'):.1f}%")
    if sample["cpu_busy"] >= 0.90:
        scores["cpu"] += 10
        evidence.append(f"CPUs {sample['cpu_busy'] * 100:.0f}% busy across {ncpu} cores")
    try:
        load1 = float((load_text or "0").split()[0])
        if load1 / ncpu >= LOAD_RATIO:
            scores["cpu"] += 10
            evidence.append(f"loadavg 1m {load1:.2f} is {load1 / ncpu:.1f}x core count")
    except (IndexError, ValueError):
        pass

    bottleneck = max(scores, key=lambda k: scores[k]) if scores and max(scores.values()) > 0 else "healthy"
    advice: dict[str, list[str]] = {
        "memory": [
            "Rank processes by RSS+swap (free-resources skill) and stop the hogs after user approval.",
            "Check for leak suspects: processes whose swap far exceeds RSS have been idle-paged out.",
            "Dropping caches hides symptoms, not causes; do not sysctl-tune without approval.",
        ],
        "io": [
            "Rank processes by I/O rate and find the writer before changing kernel settings.",
            "Check Dirty/Writeback in meminfo; a flush storm means a writer, not a disk fault.",
            "For a constantly busy device at low data rates, inspect iostat util and process io accounting.",
        ],
        "cpu": [
            "Rank processes by CPU% and look for spin loops (high CPU, no progress).",
            "A wedged watcher or agent that stopped producing output but burns a core should be restarted.",
            "Use free-resources (with user approval) to stop or renice offenders.",
        ],
        "healthy": [
            "No significant pressure detected in this sample; re-run with a longer interval if symptoms are intermittent.",
        ],
    }
    return {
        "bottleneck": bottleneck,
        "scores": {k: round(v, 1) for k, v in scores.items()},
        "evidence": evidence,
        "advice": advice[bottleneck],
        "top_cpu": top_cpu,
        "top_mem": top_mem,
        "top_io": top_io,
        "swap_used_mib": round(swap_used_mib, 1),
        "swap_rate_mib_s": round(swap_rate, 2),
    }


def _mib(value: int | None) -> str:
    return f"{(value or 0) / 1048576:.0f}M"


def render(sample: dict[str, Any], verdict: dict[str, Any]) -> str:
    lines = []
    mem = sample["meminfo"]
    lines.append(f"CPU: {sample['cpu_busy'] * 100:.0f}% busy on {sample['ncpu']} cores")
    lines.append(
        f"RAM: {_mib(mem.get('MemAvailable', 0))} available of {_mib(mem.get('MemTotal', 0))}"
        f" | swap used {verdict['swap_used_mib']}MiB at {verdict['swap_rate_mib_s']}MiB/s"
    )
    for kind, values in sample["psi"].items():
        some = values.get("some", {}).get("avg60", 0.0)
        full = values.get("full", {}).get("avg60", 0.0)
        lines.append(f"PSI {kind}: some avg60={some:.1f}% full avg60={full:.1f}%")
    for disk, stats in sorted(sample["disks"].items()):
        lines.append(
            f"IO {disk}: r {stats['read_mib_s']:.1f} w {stats['write_mib_s']:.1f} MiB/s util {stats['util'] * 100:.0f}%"
        )
    lines.append("")
    lines.append(f"Verdict: {verdict['bottleneck']}")
    for item in verdict["evidence"]:
        lines.append(f"  - {item}")
    for item in verdict["advice"]:
        lines.append(f"  -> {item}")
    for title, rows, key in (
        ("Top CPU", verdict["top_cpu"], "cpu_pct"),
        ("Top memory (RSS+swap)", verdict["top_mem"], None),
        ("Top I/O", verdict["top_io"], "io_rate_mib_s"),
    ):
        if not rows:
            continue
        lines.append("")
        lines.append(f"{title}:")
        for p in rows:
            extra = f" cpu {p[key]:.0f}%" if key else f" rss {_mib(p['rss'])} swap {_mib(p['swap'])}"
            io = f" io {p['io_rate_mib_s']:.1f}MiB/s" if p.get("io_rate_mib_s") is not None else ""
            lines.append(f"  {p['pid']:>7} {p['comm'][:24]:24}{extra}{io}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=2.0, help="sampling window in seconds")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--proc", type=Path, default=PROC, help="procfs root (for testing)")
    args = parser.parse_args(argv)

    base = args.proc
    if not (base / "stat").exists():
        print(f"error: {base} does not look like a procfs root (Linux required)", file=sys.stderr)
        return 2
    if args.interval <= 0:
        parser.error("--interval must be positive")
    loadavg = _read(base / "loadavg")
    sample = sample_system(base, args.interval)
    sample["loadavg"] = loadavg
    verdict = classify(sample)
    payload = {
        "bottleneck": verdict["bottleneck"],
        "scores": verdict["scores"],
        "evidence": verdict["evidence"],
        "advice": verdict["advice"],
        "cpu_busy": round(sample["cpu_busy"], 3),
        "ncpu": sample["ncpu"],
        "psi": sample["psi"],
        "meminfo_gib": {
            "MemTotal": round(sample["meminfo"].get("MemTotal", 0) / 1073741824, 2),
            "MemAvailable": round(sample["meminfo"].get("MemAvailable", 0) / 1073741824, 2),
            "SwapTotal": round(sample["meminfo"].get("SwapTotal", 0) / 1073741824, 2),
            "SwapFree": round(sample["meminfo"].get("SwapFree", 0) / 1073741824, 2),
        },
        "swap_rate_mib_s": verdict["swap_rate_mib_s"],
        "disks": sample["disks"],
        "top_cpu": verdict["top_cpu"],
        "top_mem": verdict["top_mem"],
        "top_io": verdict["top_io"],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render(sample, verdict))
    return 0 if verdict["bottleneck"] == "healthy" else 1


if __name__ == "__main__":
    sys.exit(main())
