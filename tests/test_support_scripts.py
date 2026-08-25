from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
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


spec_init = load_module("spec_init", "skills/spec/scripts/init-spec.py")
rage_init = load_module("rage_init", "skills/rage/scripts/init-run.py")
portability = load_module("portability_audit", "skills/skill-portability/scripts/audit.py")
hm = load_module("hm_discover", "skills/dotfiles-workflow/scripts/discover-home-manager.py")
autodig = load_module("autodig_verify", "skills/starintel-auto-dig/scripts/verify.py")
starlang = load_module("starlang_verify", "skills/star-lang/scripts/verify.py")
zara = load_module("zara_doctor", "skills/zara-mcp/scripts/doctor.py")


class SupportScriptTests(unittest.TestCase):
    def test_spec_init_slug_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = spec_init.init_spec("My Weird / Task", root=root)
            self.assertEqual(target, root / "my-weird-task" / "SPEC.md")
            self.assertIn("## Acceptance criteria", target.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                spec_init.init_spec("My Weird / Task", root=root)

    def test_spec_prefers_prolog_tmp_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            context = Path(tmp) / "context"
            context.mkdir()
            with mock.patch.dict(os.environ, {"PROLOG_TMP_SPEC_CONTEXT": str(context)}, clear=False):
                target = spec_init.init_spec("V4 Runtime")
            self.assertEqual(target, context / "spec" / "v4-runtime" / "SPEC.md")

    def test_rage_init_renders_exact_start_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sha = "a" * 40
            target = rage_init.init_run(
                repo,
                42,
                "Fix Hangs",
                branch="rage/42-fix-hangs",
                start_sha=sha,
            )
            text = target.read_text(encoding="utf-8")
            self.assertIn("Consumed issue :: #42", text)
            self.assertIn("Branch :: =rage/42-fix-hangs=", text)
            self.assertIn(f"RAGE start commit :: ={sha}=", text)

    def test_rage_init_rejects_wrong_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "expected branch"):
                rage_init.init_run(
                    Path(tmp),
                    42,
                    "Fix Hangs",
                    branch="main",
                    start_sha="a" * 40,
                )

    def test_portability_audit_reports_categories_without_content(self) -> None:
        categories = portability.scan_line(
            "repo=/home/alice/work host=box.internal ip=10.1.2.3 owner/repo",
            literals=["owner/repo"],
        )
        self.assertEqual(
            categories,
            {"absolute-home-path", "private-hostname", "private-ip", "literal:owner/repo"},
        )

    def test_home_manager_target_selection(self) -> None:
        self.assertEqual(hm.select_target(["alice@laptop"], "alice@laptop"), "alice@laptop")
        self.assertEqual(hm.select_target(["special"], "alice@laptop"), "special")
        self.assertIsNone(hm.select_target(["a", "b"], "alice@laptop"))

    def test_gate_scripts_fail_closed_outside_expected_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "not an Auto-Dig checkout"):
                autodig.validate_repo(Path(tmp))
            with self.assertRaisesRegex(RuntimeError, "not a Star-Lang checkout"):
                starlang.validate_repo(Path(tmp))

    def test_zara_doctor_redacts_common_secret_shapes(self) -> None:
        text = (
            "Authorization: Bearer abc123\n"
            "https://user:pass@example.test/x?token=secret&ok=1"
        )
        redacted = zara.redact(text)
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("user:pass", redacted)
        self.assertNotIn("token=secret", redacted)
        self.assertIn("<redacted>", redacted)

    def test_zara_doctor_builds_read_only_checks(self) -> None:
        actions = [argv[2] if len(argv) > 2 else argv[-1] for argv in zara.commands("zara", "srv")]
        self.assertEqual(actions, ["--help", "status", "inspect", "tools", "resources", "prompts"])


if __name__ == "__main__":
    unittest.main()
