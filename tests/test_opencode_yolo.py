from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "skills/opencode-yolo/scripts/opencode-yolo"


def load_spec_init():
    path = ROOT / "skills/spec/scripts/init-spec.py"
    spec = importlib.util.spec_from_file_location("spec_init_tmpfs", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["spec_init_tmpfs"] = module
    spec.loader.exec_module(module)
    return module


class OpenCodeYoloTests(unittest.TestCase):
    def test_spec_prefers_prolog_tmp_context(self) -> None:
        module = load_spec_init()
        with tempfile.TemporaryDirectory() as tmp:
            context = Path(tmp) / "context"
            context.mkdir()
            with mock.patch.dict(os.environ, {"PROLOG_TMP_SPEC_CONTEXT": str(context)}, clear=False):
                target = module.init_spec("V4 Runtime")
            self.assertEqual(target, context / "spec" / "v4-runtime" / "SPEC.md")

    def test_launcher_uses_tmpfs_auto_and_cleans_context(self) -> None:
        shm = Path("/dev/shm")
        if not shm.is_dir() or not os.access(shm, os.W_OK):
            self.skipTest("/dev/shm is unavailable")
        fs_type = subprocess.run(
            ["stat", "-f", "-c", "%T", str(shm)],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        if fs_type != "tmpfs":
            self.skipTest("/dev/shm is not tmpfs")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "starintelV4"
            workspace.mkdir()
            (workspace / "spec.prompt.org").write_text("* Test spec\n", encoding="utf-8")
            capture = root / "capture.txt"
            fake = root / "opencode"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "test -f \"$PROLOG_TMP_SPEC_CONTEXT/context.prolog\"\n"
                "test -L \"$STARINTEL_V4_ROOT/prolog-tmp-spec-context\"\n"
                "{\n"
                "  printf 'ARGS:%s\\n' \"$*\"\n"
                "  printf 'CTX:%s\\n' \"$PROLOG_TMP_SPEC_CONTEXT\"\n"
                "  printf 'REAL:%s\\n' \"$PROLOG_TMP_SPEC_CONTEXT_REAL\"\n"
                "  printf 'FS:%s\\n' \"$(stat -f -c '%T' \"$PROLOG_TMP_SPEC_CONTEXT_REAL\")\"\n"
                "  printf 'SPEC:%s\\n' \"${STARINTEL_SPEC_PROMPT:-}\"\n"
                "} >\"$CAPTURE\"\n",
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env.update(
                {
                    "OPENCODE_BIN": str(fake),
                    "OPENCODE_WORKSPACE": str(workspace),
                    "OPENCODE_TMPFS_ROOT": str(shm),
                    "CAPTURE": str(capture),
                }
            )
            subprocess.run(
                ["bash", str(LAUNCHER), "--yolo", "--model", "test/model"],
                cwd=ROOT,
                env=env,
                check=True,
                text=True,
                capture_output=True,
            )

            values = {}
            for line in capture.read_text(encoding="utf-8").splitlines():
                key, value = line.split(":", 1)
                values[key] = value

            self.assertIn("--auto", values["ARGS"])
            self.assertNotIn("--yolo", values["ARGS"])
            self.assertIn("--prompt", values["ARGS"])
            self.assertIn("--model test/model", values["ARGS"])
            self.assertEqual(values["FS"], "tmpfs")
            self.assertEqual(values["CTX"], str(workspace / "prolog-tmp-spec-context"))
            self.assertEqual(values["SPEC"], str(workspace / "spec.prompt.org"))
            self.assertFalse((workspace / "prolog-tmp-spec-context").exists())
            self.assertFalse(Path(values["REAL"]).exists())


if __name__ == "__main__":
    unittest.main()
