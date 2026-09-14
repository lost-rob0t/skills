from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "skills/opencode-worker/scripts/opencode-worker"
RESOLVER = ROOT / "skills/opencode-worker/scripts/resolve-model"


class OpenCodeWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.log = root / "calls.jsonl"
        self.count = root / "count"
        self.fake = root / "opencode"
        self.fake.write_text("""#!/usr/bin/env python3
import json, os, pathlib, signal, sys, time
log = pathlib.Path(os.environ['FAKE_LOG'])
if sys.argv[1:] == ['models']:
    print(os.environ.get('FAKE_MODELS', 'openai/gpt-6-astra'))
    raise SystemExit(int(os.environ.get('FAKE_MODELS_STATUS', '0')))
with log.open('a') as stream: stream.write(json.dumps(sys.argv[1:]) + '\\n')
count_path = pathlib.Path(os.environ['FAKE_COUNT'])
count = int(count_path.read_text() if count_path.exists() else '0') + 1
count_path.write_text(str(count))
if os.environ.get('FAKE_SLEEP'): time.sleep(float(os.environ['FAKE_SLEEP']))
failures = int(os.environ.get('FAKE_FAILURES', '0'))
if count <= failures:
    print(os.environ.get('FAKE_ERROR', 'HTTP 429 rate limit'), file=sys.stderr)
    raise SystemExit(int(os.environ.get('FAKE_STATUS', '75')))
print((os.environ.get('FAKE_OUTPUT', 'answer')) * int(os.environ.get('FAKE_OUTPUT_REPEAT', '1')))
print('diagnostic', file=sys.stderr)
""", encoding="utf-8")
        self.fake.chmod(stat.S_IRWXU)

    def env(self, **values: str) -> dict[str, str]:
        return {**os.environ, "OPENCODE_BIN": str(self.fake), "FAKE_LOG": str(self.log),
                "FAKE_COUNT": str(self.count), **values}

    def run_worker(self, *args: str, prompt: str = "do work", **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(WORKER), *args], input=prompt, text=True,
                              capture_output=True, env=self.env(**env), check=False)

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_text_mapping_role_metadata_and_options(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--role", "reviewer", "--format", "text",
                               "--agent", "build", "--title", "Review", prompt="do work\n\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        call = self.calls()[0]
        self.assertIn("default", call)
        self.assertNotIn("--role", call)
        self.assertIn("Role: reviewer", call[-1])
        self.assertIn("do work", call[-1])
        self.assertTrue(call[-1].endswith("do work\n\n"))
        self.assertEqual(proc.stdout, "answer\n")
        self.assertIn("diagnostic", proc.stderr)

    def test_json_mapping_and_explicit_model(self) -> None:
        proc = self.run_worker("--model", "vendor/model", "--format", "json",
                        FAKE_MODELS="vendor/model")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("json", self.calls()[0])

    def test_session_attach_directory_and_fork_are_forwarded(self) -> None:
        target = Path(self.tmp.name)
        proc = self.run_worker(
            "--model", "astra-medium", "--dir", str(target), "--session", "ses_123",
            "--fork", "--attach", "http://127.0.0.1:4096", "--variant", "high",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        call = self.calls()[0]
        for value in ("--dir", str(target), "--session", "ses_123", "--fork",
                      "--attach", "http://127.0.0.1:4096", "--variant", "high"):
            self.assertIn(value, call)

    def test_continue_is_forwarded(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--continue")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--continue", self.calls()[0])

    def test_malformed_argument_and_missing_executable(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--bogus")
        self.assertEqual(proc.returncode, 2)
        missing = subprocess.run(
            [str(WORKER), "--model", "astra-medium"], input="work", text=True,
            capture_output=True, env={**os.environ, "OPENCODE_BIN": "/missing/opencode"},
            check=False,
        )
        self.assertEqual(missing.returncode, 127)

    def test_rate_limit_stops_at_max_retries(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--max-retries", "1", "--max-delay", "0",
                               FAKE_FAILURES="3", FAKE_STATUS="75")
        self.assertEqual(proc.returncode, 75)
        self.assertEqual(len(self.calls()), 2)

    def test_resolver_rejects_unavailable_mapping(self) -> None:
        proc = subprocess.run([str(RESOLVER), "astra-medium"], text=True,
                              capture_output=True, env=self.env(FAKE_MODELS="other/model"))
        self.assertEqual(proc.returncode, 3)
        self.assertIn("unavailable", proc.stderr)

    def test_rate_limit_retries_and_bounds_retry_after(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--max-retries", "2", "--max-delay", "0",
                        FAKE_FAILURES="1", FAKE_ERROR="Retry-After: 99; HTTP 429")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(self.calls()), 2)
        self.assertIn("retry 1/2 in 0s", proc.stderr)

    def test_non_rate_failure_preserves_status_without_retry(self) -> None:
        proc = self.run_worker("--model", "astra-medium", FAKE_FAILURES="2",
                        FAKE_ERROR="bad request", FAKE_STATUS="42")
        self.assertEqual(proc.returncode, 42)
        self.assertEqual(len(self.calls()), 1)

    def test_optional_lock_file_runs_worker(self) -> None:
        lock = Path(self.tmp.name) / "worker.lock"
        proc = self.run_worker("--model", "astra-medium", "--lock-file", str(lock))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(lock.exists())

    def test_mutation_rejects_main_worktree_and_sessions(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--mode", "isolated-mutate",
                        "--dir", str(ROOT))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("isolated linked worktree", proc.stderr)
        proc = self.run_worker("--model", "astra-medium", "--mode", "isolated-mutate",
                        "--dir", str(ROOT), "--continue")
        self.assertEqual(proc.returncode, 2)

    def test_empty_prompt_is_rejected_without_launching(self) -> None:
        proc = self.run_worker("--model", "astra-medium", prompt="")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("empty prompt", proc.stderr)
        self.assertFalse(self.log.exists())

    def test_oversized_prompt_is_rejected_with_guidance(self) -> None:
        proc = self.run_worker("--model", "astra-medium", "--max-prompt-bytes", "16",
                               prompt="0123456789")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--max-prompt-bytes", proc.stderr)
        self.assertFalse(self.log.exists())
        default = self.run_worker("--model", "astra-medium", prompt="x" * 131072)
        self.assertEqual(default.returncode, 2)
        self.assertIn("--max-prompt-bytes", default.stderr)
        self.assertFalse(self.log.exists())

    def test_large_allowed_prompt_is_forwarded_intact(self) -> None:
        big = "x" * 100000
        proc = self.run_worker("--model", "astra-medium", prompt=big)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        call = self.calls()[0]
        self.assertTrue(call[-1].endswith(big))
        self.assertIn("Role: worker", call[-1])

    def test_downstream_close_terminates_without_hanging(self) -> None:
        # Whether the producer dies of SIGPIPE depends on the writer's
        # internals (GNU cat 9.x splices through a large internal pipe), so
        # assert only the worker-owned property: prompt consumption plus a
        # closed downstream never hangs the pipeline.
        fake = subprocess.Popen(
            [str(WORKER), "--model", "astra-medium"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            env=self.env(FAKE_SLEEP="0.2", FAKE_OUTPUT="x", FAKE_OUTPUT_REPEAT="200000"),
        )
        assert fake.stdin and fake.stdout
        fake.stdin.write("wait")
        fake.stdin.close()
        head = subprocess.Popen(["head", "-c", "1"], stdin=fake.stdout,
                                stdout=subprocess.DEVNULL)
        fake.stdout.close()
        self.addCleanup(fake.stdout.close)
        self.assertEqual(head.wait(timeout=10), 0)
        self.assertEqual(fake.wait(timeout=15), 141)

    def test_sigterm_is_forwarded_and_returns_143(self) -> None:
        proc = subprocess.Popen([str(WORKER), "--model", "astra-medium"], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                env=self.env(FAKE_SLEEP="10"))
        assert proc.stdin
        proc.stdin.write("wait")
        proc.stdin.close()
        for _ in range(100):
            if self.log.exists(): break
            time.sleep(0.01)
        proc.send_signal(signal.SIGTERM)
        self.assertEqual(proc.wait(timeout=3), 143)
        assert proc.stdout and proc.stderr
        proc.stdout.close()
        proc.stderr.close()


class WorkerConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.span_log = root / "spans.jsonl"
        self.lock = root / "serialize.lock"
        self.fake = root / "opencode"
        self.fake.write_text("""#!/usr/bin/env python3
import json, os, pathlib, sys, time
if sys.argv[1:2] == ['models']:
    print('openai/gpt-6-astra')
    raise SystemExit(0)
span_log = pathlib.Path(os.environ['FAKE_SPAN_LOG'])
prompt = sys.argv[-1]
start = time.monotonic()
span_log.open('a').write(json.dumps([os.getpid(), 'start', start]) + '\\n')
time.sleep(float(os.environ['FAKE_SLEEP']))
end = time.monotonic()
span_log.open('a').write(json.dumps([os.getpid(), 'end', end]) + '\\n')
print('done', prompt is not None)
""", encoding="utf-8")
        self.fake.chmod(stat.S_IRWXU)

    def env(self, **values: str) -> dict[str, str]:
        return {**os.environ, "OPENCODE_BIN": str(self.fake),
                "FAKE_SPAN_LOG": str(self.span_log), "FAKE_LOCK": str(self.lock), **values}

    def run_two(self, *extra: str) -> list[subprocess.CompletedProcess[str]]:
        procs = [subprocess.Popen([str(WORKER), "--model", "astra-medium", *extra],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True,
                                  env=self.env(FAKE_SLEEP="0.5"))
                 for _ in range(2)]
        for proc in procs:
            assert proc.stdin
            proc.stdin.write("work")
            proc.stdin.close()
        for proc in procs:
            proc.wait()
        return procs

    def spans(self) -> list[tuple[int, float, float]]:
        events: dict[int, dict[str, float]] = {}
        for line in self.span_log.read_text().splitlines():
            pid, kind, when = json.loads(line)
            events.setdefault(pid, {})[kind] = when
        return [(pid, span["start"], span["end"]) for pid, span in events.items()]

    def test_same_lock_file_serializes_workers(self) -> None:
        procs = self.run_two("--lock-file", str(self.lock))
        for proc in procs:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        for _ in range(200):
            if len(self.spans()) == 2: break
            time.sleep(0.05)
        spans = sorted(self.spans(), key=lambda span: span[1])
        self.assertEqual(len(spans), 2)
        self.assertGreaterEqual(spans[1][1], spans[0][2] - 0.01)

    def test_without_lock_workers_run_concurrently(self) -> None:
        procs = self.run_two()
        for proc in procs:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        for _ in range(200):
            if len(self.spans()) == 2: break
            time.sleep(0.05)
        spans = self.spans()
        self.assertEqual(len(spans), 2)
        latest_start = max(span[1] for span in spans)
        earliest_end = min(span[2] for span in spans)
        self.assertLess(latest_start, earliest_end)


if __name__ == "__main__":
    unittest.main()
