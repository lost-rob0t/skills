from __future__ import annotations

import importlib.util
import os
import signal
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


diagnose = load_module("debug_diagnose", "skills/debug-system/scripts/diagnose.py")
hogs = load_module("free_hogs", "skills/free-resources/scripts/hogs.py")

PSI_TEXT = "some avg10=1.00 avg60=12.00 avg300=5.00 total=0\nfull avg10=0.00 avg60=3.00 avg300=1.00 total=0\n"
PSI_ZERO = "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
MEMINFO_TEXT = textwrap.dedent(
    """\
    MemTotal: 32000000 kB
    MemAvailable: 1000000 kB
    SwapTotal: 8000000 kB
    SwapFree: 4000000 kB
    """
)
MEMINFO_HEALTHY = textwrap.dedent(
    """\
    MemTotal: 32000000 kB
    MemAvailable: 20000000 kB
    SwapTotal: 8000000 kB
    SwapFree: 8000000 kB
    """
)
STAT_A = "cpu0 1 2 3 900 0 0 0 0 0\ncpu1 1 2 3 900 0 0 0 0 0\nbtime 1000000000\nintr 0\n"
STAT_B = "cpu0 1 2 3 1000 0 0 0 0 0\ncpu1 1 2 3 1000 0 0 0 0 0\nbtime 1000000000\nintr 0\n"
DISKSTATS_A = "   8       0 sda 100 0 200 10 50 0 100 20 0 30 40 0 0 0 0 0 0 0\n"
DISKSTATS_B = "   8       0 sda 100 0 400 10 50 0 300 20 0 900 940 0 0 0 0 0 0 0\n"
VMSTAT_A = "pswpin 100\npswpout 200\n"
VMSTAT_B = "pswpin 600\npswpout 700\n"


def _stat(comm: str = "sleeper", utime: int = 0, stime: int = 0, starttime: int = 1000) -> str:
    fields = ["0"] * 44
    fields[0] = "1234"
    fields[1] = comm
    fields[11] = str(utime)
    fields[12] = str(stime)
    fields[19] = str(starttime)
    return f"1234 ({comm}) S 1 1 1 0 -1 0 0 0 0 0 {' '.join(fields[10:])}\n"


class FakeProc:
    def __init__(self, root: Path):
        self.root = root
        (root / "pressure").mkdir(parents=True)
        (root / "1").mkdir()
        (root / "stat").write_text(STAT_A)
        (root / "loadavg").write_text("0.10 0.10 0.10 1/100 1\n")
        (root / "meminfo").write_text(MEMINFO_HEALTHY)
        (root / "vmstat").write_text(VMSTAT_A)
        (root / "diskstats").write_text(DISKSTATS_A)
        for kind in ("cpu", "memory", "io"):
            (root / "pressure" / kind).write_text(PSI_ZERO)
        (root / "1" / "stat").write_text(_stat())
        (root / "1" / "cmdline").write_text("sleep\x001\x00")
        (root / "1" / "smaps_rollup").write_text("Rss:      1000 kB\nSwap:       500 kB\n")

    def advance(self) -> None:
        (self.root / "stat").write_text(STAT_B)
        (self.root / "vmstat").write_text(VMSTAT_B)
        (self.root / "diskstats").write_text(DISKSTATS_B)
        (self.root / "1" / "stat").write_text(_stat(utime=50, stime=50))


class DiagnoseTests(unittest.TestCase):
    def test_parse_psi_and_meminfo(self) -> None:
        psi = diagnose.parse_psi(PSI_TEXT)
        self.assertEqual(psi["some"]["avg60"], 12.0)
        self.assertEqual(psi["full"]["avg60"], 3.0)
        mem = diagnose.parse_meminfo(MEMINFO_TEXT)
        self.assertEqual(mem["MemTotal"], 32000000 * 1024)
        self.assertEqual(mem["SwapFree"], 4000000 * 1024)

    def test_proc_stat_idle_total(self) -> None:
        idle, total = diagnose.parse_proc_stat(STAT_A)
        self.assertEqual(total, 2 * 906)
        self.assertEqual(idle, 2 * 900)

    def test_classify_flags_memory_pressure(self) -> None:
        sample = {
            "interval": 1.0,
            "ncpu": 4,
            "cpu_busy": 0.1,
            "psi": {
                "cpu": diagnose.parse_psi(PSI_ZERO),
                "memory": diagnose.parse_psi(PSI_TEXT),
                "io": diagnose.parse_psi(PSI_ZERO),
            },
            "meminfo": diagnose.parse_meminfo(MEMINFO_TEXT),
            "vmstat": {"now": {}, "delta": {"pswpin": 100, "pswpout": 100}},
            "disks": {},
            "processes": {},
        }
        verdict = diagnose.classify(sample)
        self.assertEqual(verdict["bottleneck"], "memory")
        self.assertTrue(any("PSI memory" in line for line in verdict["evidence"]))
        self.assertTrue(any("swap" in line for line in verdict["evidence"]))

    def test_classify_healthy_without_pressure(self) -> None:
        sample = {
            "interval": 1.0,
            "ncpu": 4,
            "cpu_busy": 0.1,
            "psi": {k: diagnose.parse_psi(PSI_ZERO) for k in ("cpu", "memory", "io")},
            "meminfo": diagnose.parse_meminfo(MEMINFO_HEALTHY),
            "vmstat": {"now": {}, "delta": {"pswpin": 0, "pswpout": 0}},
            "disks": {},
            "processes": {},
        }
        self.assertEqual(diagnose.classify(sample)["bottleneck"], "healthy")

    def test_sample_system_on_fake_proc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeProc(Path(tmp))
            with mock.patch.object(diagnose.time, "sleep", lambda *_: fake.advance()):
                sample = diagnose.sample_system(Path(tmp), 1.0)
            self.assertEqual(sample["ncpu"], 2)
            self.assertEqual(sample["cpu_busy"], 0.0)
            self.assertIn(1, sample["processes"])
            self.assertEqual(sample["processes"][1]["rss"], 1000 * 1024)
            self.assertIn("sda", sample["disks"])
            self.assertEqual(sample["vmstat"]["delta"]["pswpin"], 500)


class HogsTests(unittest.TestCase):
    def test_list_ranks_and_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeProc(Path(tmp))
            proc2 = Path(tmp) / "2"
            proc2.mkdir()
            (proc2 / "stat").write_text(_stat("opencode"))
            (proc2 / "cmdline").write_text("/usr/bin/opencode\x00run\x00")
            (proc2 / "smaps_rollup").write_text("Rss:      900000 kB\nSwap:       100 kB\n")

            def fake_sleep(seconds: float) -> None:
                fake.advance()
                (proc2 / "stat").write_text(_stat("opencode", utime=250, stime=250))

            with mock.patch.object(hogs.time, "sleep", fake_sleep):
                rows = hogs.snapshot(Path(tmp), 1.0, hogs.load_critical(None))
        kinds = {row["comm"]: row["kind"] for row in rows}
        self.assertEqual(kinds["sleeper"], "normal")
        self.assertEqual(kinds["opencode"], "agent")
        by_comm = {row["comm"]: row for row in rows}
        self.assertGreater(by_comm["opencode"]["cpu_pct"], by_comm["sleeper"]["cpu_pct"])
        self.assertEqual(by_comm["sleeper"]["swap"], 500 * 1024)
        self.assertEqual(by_comm["opencode"]["swap"], 100 * 1024)

    def test_kill_requires_yes(self) -> None:
        with self.assertRaises(SystemExit):
            hogs.main(["kill", "--pid", "1"])

    def test_kill_refuses_critical_and_foreign(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            FakeProc(Path(tmp))
            proc2 = Path(tmp) / "2"
            proc2.mkdir()
            (proc2 / "stat").write_text(_stat("qtile"))
            os.chown(proc2, os.geteuid(), os.getegid())
            errors, survivors = hogs.kill_pids(
                Path(tmp),
                [1, 2, 999],
                signal.SIGTERM,
                hogs.load_critical(None),
                timeout=0.2,
            )
            self.assertEqual(survivors, 3)
            self.assertTrue(any("init" in e for e in errors))
            self.assertTrue(any("session-critical" in e for e in errors))
            self.assertTrue(any("no such process" in e for e in errors))
            self.assertTrue((proc2 / "stat").exists())

    def test_kill_refuses_foreign_uid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            FakeProc(Path(tmp))
            proc2 = Path(tmp) / "2"
            proc2.mkdir()
            (proc2 / "stat").write_text(_stat("victim"))
            foreign = os.geteuid() + 1 if os.geteuid() != 0 else 1
            with mock.patch.object(hogs.os, "geteuid", lambda: foreign):
                errors, survivors = hogs.kill_pids(
                    Path(tmp), [2], signal.SIGTERM, hogs.load_critical(None), timeout=0.2
                )
            self.assertEqual(survivors, 1)
            self.assertTrue(any("not yours" in e for e in errors))
            self.assertTrue((proc2 / "stat").exists())

    def test_kill_stops_owned_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            FakeProc(Path(tmp))
            proc2 = Path(tmp) / "2"
            proc2.mkdir()
            (proc2 / "stat").write_text(_stat("victim"))
            os.chown(proc2, os.geteuid(), os.getegid())
            signaled: list[tuple[int, int]] = []
            target = proc2

            def fake_kill(pid: int, sig: int) -> None:
                signaled.append((pid, sig))

            def fake_exists(path: Path) -> bool:
                return not (path == target and signaled)

            with mock.patch.object(hogs.os, "kill", fake_kill), mock.patch.object(
                hogs.Path, "exists", fake_exists
            ):
                errors, survivors = hogs.kill_pids(
                    Path(tmp), [2], signal.SIGTERM, hogs.load_critical(None), timeout=0.2
                )
            self.assertEqual(errors, [])
            self.assertEqual(survivors, 0)
            self.assertEqual(signaled, [(2, signal.SIGTERM)])


if __name__ == "__main__":
    unittest.main()
