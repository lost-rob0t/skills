import json
import shutil
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "prolog-verification" / "scripts" / "prolog-verify.py"
CHECK_JOURNAL = ROOT / "skills" / "prolog-verification" / "scripts" / "check-journal.pl"


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

    def head(self):
        return subprocess.check_output(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"],
            text=True,
        ).strip()

    def run_file(self):
        facts = (self.root / ".prolog" / "facts.kb").read_text()
        import re
        run = re.search(r"verification_context\('[^']+', '([a-f0-9]{32})'\)", facts)[1]
        return self.root / ".prolog" / "runs" / run / "evidence.pl"

    def initialize_and_observe(self):
        self.run_script("init", "--task", "test-task", check=True)
        result = self.run_script("observe", "--", sys.executable, "-c", "print('green')")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_observe_and_check_current_state(self):
        self.initialize_and_observe()
        facts = (self.root / ".prolog" / "facts.kb").read_text(encoding="utf-8")
        run = self.run_file().read_text(encoding="utf-8")
        self.assertNotIn("observation(", facts)
        self.assertIn("machine_observation(", run)
        self.assertIn("exit(0)", run)
        result = self.run_script("check")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root / ".prolog" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["run_file"], self.run_file().name)

    def test_check_rejects_stale_evidence_before_swipl(self):
        self.initialize_and_observe()
        (self.root / "tracked.txt").write_text("changed after evidence\n", encoding="utf-8")
        result = self.run_script("check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale", result.stderr)
        report = json.loads((self.root / ".prolog" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "stale")

    def test_failed_observation_is_recorded_and_fails(self):
        self.run_script("init", "--task", "failure", check=True)
        result = self.run_script("observe", "--", sys.executable, "-c", "raise SystemExit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertIn("exit(7)", self.run_file().read_text(encoding="utf-8"))
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 1)
        self.assertIn("no successful machine observation", checked.stderr)

    def test_brave_command_records_current_research_evidence(self):
        self.initialize_and_observe()
        result = self.run_script("brave", "--query", "prolog verification")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("example.invalid", result.stdout)
        facts = (self.root / ".prolog" / "facts.kb").read_text(encoding="utf-8")
        run = self.run_file().read_text(encoding="utf-8")
        self.assertIn("research_required(true).", facts)
        self.assertIn("brave_search(", run)
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_run_file_churn_does_not_stale_evidence(self):
        self.initialize_and_observe()
        with self.run_file().open("a", encoding="utf-8") as handle:
            handle.write("todo(example, active).\n")
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_durable_kb_change_stales_evidence(self):
        self.initialize_and_observe()
        kb = self.root / ".prolog" / "kb"
        kb.mkdir(parents=True)
        (kb / "knowledge.pl").write_text("tool(swipl).\n", encoding="utf-8")
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 1)
        self.assertIn("stale", checked.stderr)

    def test_task_switch_cannot_borrow_evidence_and_preserves_history(self):
        self.initialize_and_observe()
        self.run_script("check", check=True)
        old_run = self.run_file()
        original = old_run.read_bytes()
        checks = list((old_run.parent / "checks").glob("*/result.json"))
        self.run_script("init", "--task", "other-task", "--force", check=True)
        self.assertNotEqual(old_run, self.run_file())
        self.assertEqual(old_run.read_bytes(), original)
        checked = self.run_script("check")
        self.assertEqual(checked.returncode, 1, checked.stderr)
        report = json.loads((self.root / ".prolog/result.json").read_text())
        self.assertEqual(report["task"], "other-task")
        self.assertEqual(report["status"], "unknown")
        self.assertTrue(all(path.exists() for path in checks))
        self.assertTrue(list((old_run.parent / "controls").glob("*/verify.pl")))

    def test_same_task_new_run_needs_fresh_evidence(self):
        self.initialize_and_observe()
        old_run = self.run_file()
        self.run_script("init", "--task", "test-task", "--force", check=True)
        self.assertNotEqual(old_run, self.run_file())
        self.assertEqual(self.run_script("check").returncode, 1)

    def test_each_check_retains_its_result_and_controls(self):
        self.initialize_and_observe()
        self.run_script("check", check=True)
        before = set(self.run_file().parent.glob("checks/*/result.json"))
        (self.root / "tracked.txt").write_text("edited\n")
        self.run_script("check")
        after = set(self.run_file().parent.glob("checks/*/result.json"))
        self.assertEqual(len(after - before), 1)
        self.assertTrue(any(json.loads(p.read_text())["status"] == "pass" for p in before))
        for report in after:
            self.assertTrue((report.parent / "verify.pl").exists())

    def test_task_switch_during_observation_cannot_write_into_new_task(self):
        self.run_script("init", "--task", "first", check=True)
        old_run = self.run_file()
        command = [sys.executable, str(SCRIPT), "--work-dir", str(self.root),
                   "init", "--task", "second", "--force"]
        observed = self.run_script("observe", "--", *command)
        self.assertEqual(observed.returncode, 2, observed.stderr)
        self.assertIn("active task/run changed", observed.stderr)
        self.assertIn("machine_observation('first'", old_run.read_text())
        self.assertNotIn("machine_observation(", self.run_file().read_text())
        self.assertEqual(self.run_script("check").returncode, 1)

    def test_observation_spanning_revision_change_is_not_proof(self):
        self.run_script("init", "--task", "changing", check=True)
        result = self.run_script("observe", "--", sys.executable, "-c",
                                 "from pathlib import Path; Path('tracked.txt').write_text('changed')")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("workspace changed", result.stderr)
        self.assertNotIn("machine_observation(", self.run_file().read_text())

    def test_legacy_control_files_fail_closed(self):
        self.initialize_and_observe()
        facts = self.root / ".prolog/facts.kb"
        facts.write_text("task('legacy').\nrepo_state('head', 'digest').\n")
        result = self.run_script("check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("legacy evidence", result.stderr)

    @unittest.skipUnless(shutil.which("swipl"), "real SWI-Prolog required")
    def test_symbolic_claim_requires_exact_command_and_latest_outcome(self):
        self.fake_swipl = Path(shutil.which("swipl"))
        self.run_script("init", "--task", "symbolic", check=True)
        # A command can change its outcome without changing the project revision.
        flag = Path(self.temporary.name).parent / (self.root.name + "-flag")
        command = [sys.executable, "-c", f"from pathlib import Path; raise SystemExit(7 if Path({str(flag)!r}).exists() else 0)"]
        self.addCleanup(lambda: flag.unlink(missing_ok=True))
        self.run_script("require", "--id", "suite", "--", *command, check=True)
        self.run_script("observe", "--", sys.executable, "-c", "print('unrelated')", check=True)
        self.assertEqual(self.run_script("check").returncode, 1)
        self.run_script("observe", "--", *command, check=True)
        self.run_script("check", check=True)
        flag.touch()
        self.assertEqual(self.run_script("observe", "--", *command).returncode, 7)
        self.assertEqual(self.run_script("check").returncode, 1)
        flag.unlink()
        self.run_script("observe", "--", *command, check=True)
        self.run_script("check", check=True)

    @unittest.skipUnless(shutil.which("swipl"), "real SWI-Prolog required")
    def test_unknown_and_conflicting_symbolic_bindings_block_completion(self):
        self.fake_swipl = Path(shutil.which("swipl"))
        self.initialize_and_observe()
        facts = self.root / ".prolog/facts.kb"
        original = facts.read_text()
        for bindings in ["claim(unsupported, prose('trust me')).\n",
                         "requirement(same, command([a])).\nrequirement(same, command([b])).\n",
                         "claim(same, requirement(a)).\nclaim(same, requirement(b)).\n"]:
            facts.write_text(original + bindings)
            checked = self.run_script("check")
            self.assertEqual(checked.returncode, 1, checked.stderr)

    def test_check_rejects_unexpected_task_or_run(self):
        self.initialize_and_observe()
        for option, identity in [("--task", "another"), ("--run", "another")]:
            result = self.run_script("check", option, identity)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("requested verification identity", result.stderr)

    def test_changed_policy_during_check_is_stale(self):
        self.fake_swipl.write_text("#!/bin/sh\nprintf '\\n%% changed\\n' >> verify.pl\nexit 0\n")
        self.initialize_and_observe()
        result = self.run_script("check")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("changed during verification", result.stderr)

    def test_unique_observations_retain_raw_output(self):
        self.run_script("init", "--task", "outputs", check=True)
        command = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([255,0,1]))"]
        # Binary output is exercised without the test helper's text decoding.
        for _ in range(2):
            result = subprocess.run([sys.executable, str(SCRIPT), "--work-dir", str(self.root),
                                     "observe", "--", *command], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        outputs = list(self.run_file().parent.glob("observations/*/stdout.txt"))
        self.assertEqual(len(outputs), 2)
        self.assertTrue(all(path.read_bytes() == bytes([255,0,1]) for path in outputs))

    def test_stop_hook_blocks_only_after_session_change(self):
        hook = {"session_id": "session-1", "cwd": str(self.root)}
        start = self.run_script("hook-session-start", input_payload=hook)
        self.assertEqual(json.loads(start.stdout), {})
        unchanged = self.run_script("hook-stop", input_payload=hook)
        self.assertEqual(json.loads(unchanged.stdout), {})
        (self.root / "tracked.txt").write_text("agent edit\n", encoding="utf-8")
        changed = self.run_script("hook-stop", input_payload=hook)
        self.assertEqual(json.loads(changed.stdout)["decision"], "block")

    def make_nongit_root(self):
        directory = tempfile.TemporaryDirectory(prefix="prolog-verify-nongit-")
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    @staticmethod
    def sparse_file(path, size):
        with path.open("wb") as handle:
            handle.truncate(size)

    def test_nongit_init_skips_vendored_directories(self):
        root = self.make_nongit_root()
        for junk in ("node_modules/pkg/bundle.js", ".venv/lib/libpython.so", "__pycache__/x.pyc"):
            path = root / junk
            path.parent.mkdir(parents=True, exist_ok=True)
            self.sparse_file(path, 96 * 1024 * 1024)
        (root / "note.txt").write_text("real content\n", encoding="utf-8")
        started = time.monotonic()
        result = self.run_script("--work-dir", str(root), "init", "--task", "nongit-skip", check=True)
        self.assertLess(time.monotonic() - started, 10)
        facts = (root / ".prolog/facts.kb").read_text(encoding="utf-8")
        self.assertIn("repo_state('no-git',", facts)

    def test_nongit_init_fails_closed_when_hash_budget_exceeded(self):
        root = self.make_nongit_root()
        junk = root / "node_modules/pkg/bundle.js"
        junk.parent.mkdir(parents=True)
        self.sparse_file(junk, 96 * 1024 * 1024)
        self.sparse_file(root / "big-core-dump.bin", 260 * 1024 * 1024)
        started = time.monotonic()
        result = self.run_script("--work-dir", str(root), "init", "--task", "nongit-bound")
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertLess(elapsed, 10)
        self.assertIn("256 MiB digest budget", result.stderr)
        self.assertIn("big-core-dump.bin", result.stderr)
        self.assertIn("use a git worktree or an isolated verifier dir under e.g. /tmp/opencode/<task>/", result.stderr)

    @unittest.skipUnless(shutil.which("swipl"), "real SWI-Prolog required")
    def test_template_loads_state_from_foreign_cwd(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("prolog_verify_module", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        prolog_dir = self.root / ".prolog"
        run = "a" * 32
        prolog_dir.mkdir(parents=True, exist_ok=True)
        (prolog_dir / "facts.kb").write_text(
            "task('cwdtest').\n"
            f"verification_context('cwdtest', '{run}').\n"
            "repo_state('nohead', 'nodigest').\n"
            "research_required(false).\n",
            encoding="utf-8",
        )
        (prolog_dir / "verify.pl").write_text(module.VERIFY_TEMPLATE, encoding="utf-8")
        run_dir = prolog_dir / "runs" / run
        run_dir.mkdir(parents=True)
        (run_dir / "evidence.pl").write_text(
            f"machine_observation('cwdtest', '{run}', 'obs-1', command(['true']), exit(0), "
            "'out', 'nohead', 'nodigest').\n",
            encoding="utf-8",
        )
        # Completion requires facts.kb and the run journal, so exiting 0 from a
        # foreign CWD proves the template resolves state next to verify.pl.
        with tempfile.TemporaryDirectory() as foreign:
            completed = subprocess.run(
                [shutil.which("swipl"), "-q", "-f", "none", "-s", str(prolog_dir / "verify.pl")],
                cwd=foreign,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertNotIn("existence_error", completed.stderr)
        self.assertNotIn("Unknown procedure", completed.stderr)

    @unittest.skipUnless(shutil.which("swipl"), "real SWI-Prolog required")
    def test_check_journal_passes_clean_journal_with_floors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = "b" * 32
            journal = root / ".prolog" / "runs" / run / "evidence.pl"
            entries = [
                f"machine_observation('t', '{run}', 'obs-{n}', command(['run']), exit(0), 'x', 'h', 'd')"
                for n in range(3)
            ]
            journal.parent.mkdir(parents=True)
            journal.write_text("".join(entry + ".\n" for entry in entries), encoding="utf-8")
            floors = root / "floors.pl"
            floors.write_text(
                "min_clauses(machine_observation/8, 3).\n"
                "required_entry(machine_observation(_, _, _, _, exit(0), _, _, _)).\n",
                encoding="utf-8",
            )
            foreign = root / "foreign"
            foreign.mkdir()
            completed = subprocess.run(
                [shutil.which("swipl"), "-q", "-f", "none", str(CHECK_JOURNAL),
                 "--", str(journal), str(floors)],
                cwd=foreign,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("floors satisfied", completed.stdout)

    @unittest.skipUnless(shutil.which("swipl"), "real SWI-Prolog required")
    def test_check_journal_rejects_truncated_final_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = root / "journal.pl"
            entries = [
                f"machine_observation('t', 'r', 'obs-{n}', command(['run']), exit(0), 'x', 'h', 'd')"
                for n in range(4)
            ]
            # The final entry loses its terminating period: SWI recovers, keeps
            # the first three clauses, and silently drops the fourth.
            journal.write_text("".join(entry + ".\n" for entry in entries[:-1]) + entries[-1] + "\n",
                               encoding="utf-8")
            floors = root / "floors.pl"
            floors.write_text("min_clauses(machine_observation/8, 4).\n", encoding="utf-8")
            completed = subprocess.run(
                [shutil.which("swipl"), "-q", "-f", "none", str(CHECK_JOURNAL),
                 "--", str(journal), str(floors)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("has 3 clauses, floor is 4", completed.stderr)


if __name__ == "__main__":
    unittest.main()
