from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/status-update/scripts/notify.sh"
BASH = shutil.which("bash") or "/bin/bash"


class StatusUpdateNotifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.bin_dir = Path(self._tmp.name) / "bin"
        self.bin_dir.mkdir()

    def fake_backend(self, name: str, exit_code: int = 0) -> Path:
        log = self.bin_dir / f"{name}.log"
        path = self.bin_dir / name
        body = (
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$@\" >> {log}\n"
            f"exit {exit_code}\n"
        )
        path.write_text(body, encoding="utf-8")
        path.chmod(stat.S_IRWXU)
        self.addCleanup(log.unlink, missing_ok=True)
        return path

    def env(self) -> dict:
        return {**os.environ, "PATH": str(self.bin_dir)}

    def run_script(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [BASH, str(SCRIPT), *argv],
            check=False, text=True, capture_output=True,
            env=self.env(),
        )

    def log(self, name: str) -> list[str]:
        path = self.bin_dir / f"{name}.log"
        if not path.exists():
            return []
        return path.read_text(encoding="utf-8").splitlines()

    def test_resolve_prefers_dunstify(self) -> None:
        self.fake_backend("dunstify")
        self.fake_backend("notify-send")
        proc = self.run_script("--resolve")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "dunstify")

    def test_resolve_falls_back_to_notify_send(self) -> None:
        self.fake_backend("notify-send")
        proc = self.run_script("--resolve")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "notify-send")

    def test_resolve_fails_closed_without_backends(self) -> None:
        proc = self.run_script("--resolve")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no notification backend", proc.stderr)
        self.assertIn("none", proc.stdout)

    def test_send_uses_dunst_flags_and_order(self) -> None:
        self.fake_backend("dunstify")
        self.fake_backend("notify-send")
        proc = self.run_script(
            "--title", "Task complete",
            "--message", "PR #42 opened",
            "--urgency", "critical",
            "--timeout", "5000",
            "--app-name", "ci-agent",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            self.log("dunstify"),
            ["-u", "critical", "-t", "5000", "-a", "ci-agent",
             "Task complete", "PR #42 opened"],
        )
        self.assertEqual(self.log("notify-send"), [])

    def test_send_falls_back_when_dunstify_fails(self) -> None:
        self.fake_backend("dunstify", exit_code=1)
        self.fake_backend("notify-send")
        proc = self.run_script("--title", "Backup test")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("libnotify backup", proc.stderr)
        self.assertEqual(self.log("notify-send")[-1], "Backup test")

    def test_send_fails_when_all_backends_fail(self) -> None:
        self.fake_backend("dunstify", exit_code=1)
        self.fake_backend("notify-send", exit_code=1)
        proc = self.run_script("--title", "Total failure")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("backend notify-send failed", proc.stderr)

    def test_dry_run_prints_vector_without_sending(self) -> None:
        self.fake_backend("dunstify")
        proc = self.run_script("--title", "Dry", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("dunstify -u normal -t 10000 -a agent Dry", proc.stdout)
        self.assertEqual(self.log("dunstify"), [])

    def test_usage_errors_fail_closed(self) -> None:
        cases = [
            (),
            ("--message", "no title"),
            ("--title", "x", "--urgency", "yelling"),
            ("--title", "x", "--timeout", "soon"),
            ("--title", "x", "--bogus"),
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                self.fake_backend("dunstify")
                proc = self.run_script(*argv)
                self.assertNotEqual(proc.returncode, 0)
                self.assertEqual(self.log("dunstify"), [])


if __name__ == "__main__":
    unittest.main()
