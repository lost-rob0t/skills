import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "prolog-verification" / "scripts" / "prolog-verify.py"


FAKE_SWIPL = r'''#!/usr/bin/env python3
import json
from pathlib import Path
import sys

if "--" not in sys.argv:
    raise SystemExit(0)

args = sys.argv[sys.argv.index("--") + 1:]
db = Path(args[0])
action = args[1]
state_path = Path(str(db) + ".fake.json")
if state_path.exists():
    records = json.loads(state_path.read_text(encoding="utf-8"))
else:
    records = []

def save():
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(records), encoding="utf-8")

def emit(payload):
    print(json.dumps(payload, sort_keys=True))

if action == "put":
    _, _, record_id, scope, owner, kind, key, value, source, status, stamp = args
    existing = next((item for item in records if item["scope"] == scope and item["owner"] == owner and item["kind"] == kind and item["key"] == key), None)
    if existing is not None:
        record_id = existing["id"]
        created_at = existing["created_at"]
        records.remove(existing)
    else:
        created_at = stamp
    record = {
        "id": record_id,
        "scope": scope,
        "owner": owner,
        "kind": kind,
        "key": key,
        "value": value,
        "source": source,
        "status": status,
        "created_at": created_at,
        "updated_at": stamp,
    }
    records.append(record)
    save()
    emit(record)
elif action == "list":
    _, _, scope, owner, kind, query, status = args
    def matches(expected, actual):
        return expected == "*" or expected == actual
    needle = query.lower()
    found = [
        item for item in records
        if matches(scope, item["scope"])
        and matches(owner, item["owner"])
        and matches(kind, item["kind"])
        and matches(status, item["status"])
        and (query == "*" or needle in item["key"].lower() or needle in item["value"].lower())
    ]
    emit({"records": found})
elif action == "applicable":
    _, _, project_owner, session_owner, kind, query, status = args
    def matches(expected, actual):
        return expected == "*" or expected == actual
    needle = query.lower()
    found = [
        item for item in records
        if (
            (item["scope"] == "global" and item["owner"] == "*")
            or (item["scope"] == "project" and item["owner"] == project_owner)
            or (session_owner != "*" and item["scope"] == "session" and item["owner"] == session_owner)
        )
        and matches(kind, item["kind"])
        and matches(status, item["status"])
        and (query == "*" or needle in item["key"].lower() or needle in item["value"].lower())
    ]
    emit({"records": found})
elif action == "status":
    _, _, record_id, new_status, stamp = args
    record = next(item for item in records if item["id"] == record_id)
    record["status"] = new_status
    record["updated_at"] = stamp
    save()
    emit({"id": record_id, "status": new_status, "updated_at": stamp})
elif action == "forget":
    _, _, record_id = args
    records[:] = [item for item in records if item["id"] != record_id]
    save()
    emit({"id": record_id, "deleted": True})
elif action == "health":
    emit({"status": "ok", "records": len(records)})
else:
    raise SystemExit(2)
'''


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
        self.fake_swipl.write_text(FAKE_SWIPL, encoding="utf-8")
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
        env["PROLOG_VERIFY_DB"] = str(self.root / "durable-knowledge.db")
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
        self.assertIn("knowledge_sha256", report)

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

    def test_durable_bug_memory_is_projected_and_resolvable(self):
        self.run_script("init", "--task", "memory", check=True)
        remembered = self.run_script(
            "remember",
            "--kind", "bug",
            "--key", "stale-context-cache",
            "--value", "Cache reuse after HEAD changes produces stale symbolic context.",
        )
        self.assertEqual(remembered.returncode, 0, remembered.stderr)
        record_id = json.loads(remembered.stdout)["id"]

        projection = (self.root / ".prolog" / "knowledge.kb").read_text(encoding="utf-8")
        self.assertIn("long_term_knowledge(", projection)
        self.assertIn("stale-context-cache", projection)

        recalled = self.run_script("recall", "--kind", "bug", "--json")
        self.assertEqual(recalled.returncode, 0, recalled.stderr)
        rows = json.loads(recalled.stdout)
        self.assertEqual([row["id"] for row in rows], [record_id])

        resolved = self.run_script("resolve", record_id)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        projection = (self.root / ".prolog" / "knowledge.kb").read_text(encoding="utf-8")
        self.assertNotIn("stale-context-cache", projection)
        recalled = self.run_script("recall", "--kind", "bug", "--json")
        self.assertEqual(json.loads(recalled.stdout), [])

    def test_project_memory_overrides_global_memory_with_same_key(self):
        global_result = self.run_script(
            "remember", "--scope", "global", "--key", "test-command", "--value", "make test"
        )
        self.assertEqual(global_result.returncode, 0, global_result.stderr)
        project_result = self.run_script(
            "remember", "--scope", "project", "--key", "test-command", "--value", "nix develop -c make test"
        )
        self.assertEqual(project_result.returncode, 0, project_result.stderr)
        recalled = self.run_script("recall", "--query", "test-command", "--json")
        rows = json.loads(recalled.stdout)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["scope"], "project")
        self.assertEqual(rows[0]["value"], "nix develop -c make test")

    def test_memory_commands_work_without_verification_workspace(self):
        remembered = self.run_script(
            "remember",
            "--kind", "failure-path",
            "--key", "force-reset",
            "--value", "Do not force-reset a shared worktree to recover main.",
        )
        self.assertEqual(remembered.returncode, 0, remembered.stderr)
        self.assertFalse((self.root / ".prolog").exists())
        recalled = self.run_script("recall", "--kind", "failure-path", "--json")
        self.assertEqual(len(json.loads(recalled.stdout)), 1)


if __name__ == "__main__":
    unittest.main()
