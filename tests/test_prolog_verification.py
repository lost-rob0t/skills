import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "prolog-verification" / "scripts" / "prolog-verify.py"


class PrologVerificationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"], check=True)
        (self.root / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "base"], check=True)
        self.fake_swipl = self.root / "fake-swipl"
        self.fake_swipl.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.fake_swipl.chmod(0o755)
        self.fake_bx = self.root / "fake-bx"
        self.fake_bx.write_text(
            "#!/bin/sh\nprintf '{\"results\":[{\"url\":\"https://example.invalid\"}]}\\n'\n",
            encoding="utf-8",
        )
        self.fake_bx.chmod(0o755)

    def tearDown(self):
        self.temporary.cleanup()

    def run_script(self, *args, input_payload=None, check=False):
        env = os.environ.copy()
        env["SWIPL_BIN"] = str(self.fake_swipl)
        env["BX_BIN"] = str(self.fake_bx)
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--work-dir", str(self.root), *args],
            input=json.dumps(input_payload) if input_payload is not None else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=check,
        )

    def initialize_and_observe(self):
        self.run_script("init", "--task", "test-task", check=True)
        result = self.run_script("observe", "--", sys.executable, "-c", "print('green')")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_observe_and_check_current_state(self):
        self.initialize_and_observe()
        facts = (self.root / ".prolog" / "facts.kb").read_text(encoding="utf-8")
        self.assertIn("observation(", facts)
        self.assertIn("exit(0)", facts)
        result = self.run_script("check")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root / ".prolog" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass")

    def test_check_rejects_stale_evidence_before_swipl(self):
        self.initialize_and_observe()
        (self.root / "tracked.txt").write_text("changed after evidence\n", encoding="utf-8")
        result = self.run_script("check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale", result.stderr)
        report = json.loads((self.root / ".prolog" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "fail")

    def test_failed_observation_is_recorded_and_fails(self):
        self.run_script("init", "--task", "failure", check=True)
        result = self.run_script("observe", "--", sys.executable, "-c", "raise SystemExit(7)")
        self.assertEqual(result.returncode, 7)
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 1)
        self.assertIn("no successful machine observation", checked.stderr)

    def test_brave_command_records_current_research_evidence(self):
        self.initialize_and_observe()
        result = self.run_script("brave", "--query", "prolog verification")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("example.invalid", result.stdout)
        facts = (self.root / ".prolog" / "facts.kb").read_text(encoding="utf-8")
        self.assertIn("research_required(true).", facts)
        self.assertIn("brave_search(", facts)
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_stop_hook_blocks_only_after_session_change(self):
        hook = {"session_id": "session-1", "cwd": str(self.root)}
        start = self.run_script("hook-session-start", input_payload=hook)
        self.assertEqual(json.loads(start.stdout), {})
        unchanged = self.run_script("hook-stop", input_payload=hook)
        self.assertEqual(json.loads(unchanged.stdout), {})
        (self.root / "tracked.txt").write_text("agent edit\n", encoding="utf-8")
        changed = self.run_script("hook-stop", input_payload=hook)
        self.assertEqual(json.loads(changed.stdout)["decision"], "block")


if __name__ == "__main__":
    unittest.main()
