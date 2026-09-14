from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/merge-on-green/scripts/merge-on-green"


def load_module(name: str, relative: str):
    import importlib.util
    from importlib.machinery import SourceFileLoader
    path = ROOT / relative
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


mog = load_module("merge_on_green", "skills/merge-on-green/scripts/merge-on-green")


def git(repo: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.test",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.test"})


FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
plan_path = os.environ['MOG_FAKE_PLAN']
plan = json.loads(open(plan_path).read())
plan['calls'] = plan.get('calls', 0) + 1
argv = sys.argv[1:]
fail_first = plan.get('fail_first', 0)
if plan.get('fail_mode') and plan['calls'] <= fail_first:
    print(plan['fail_mode'], file=sys.stderr)
    open(plan_path, 'w').write(json.dumps(plan))
    raise SystemExit(1)
open(plan_path, 'w').write(json.dumps(plan))
if '--merge' in argv:
    plan['merged'] = True
    open(plan_path, 'w').write(json.dumps(plan))
    raise SystemExit(0)
view = plan['views'].pop(0) if len(plan['views']) > 1 else plan['views'][0]
open(plan_path, 'w').write(json.dumps(plan))
print(json.dumps({
    'headRefOid': view['head'], 'state': 'MERGED' if plan.get('merged') else view.get('state', 'OPEN'),
    'mergeable': view.get('mergeable', 'MERGEABLE'),
    'mergeStateStatus': view['merge_state'],
    'reviewDecision': view.get('review', 'APPROVED'),
}))
"""


class FakeResponse:
    def __init__(self, payload: bytes, headers: dict | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def forgejo_json(value) -> bytes:
    return json.dumps(value).encode()


PULL = {"state": "open", "merged": False, "mergeable": True, "head": {"sha": "sha1"}}
STATUS_OK = {"status": "success"}
REVIEW_OK = [{"state": "APPROVED"}]


class HelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def git_repo(self, url: str) -> Path:
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "remote", "add", "origin", url)
        return repo

    def test_detects_github_from_remote(self) -> None:
        repo = self.git_repo("git@github.com:foo/bar.git")
        with mock.patch.object(mog, "git", return_value=str(url := "git@github.com:foo/bar.git")):
            self.assertEqual(mog.detect_provider(None, None), "github")
        self.assertTrue(str(repo))

    def test_detects_forgejo_from_remote(self) -> None:
        with mock.patch.object(mog, "git", return_value="https://git.starintel.actor/foo/bar.git"):
            self.assertEqual(mog.detect_provider(None, None), "forgejo")

    def test_unknown_remote_requires_provider(self) -> None:
        with mock.patch.object(mog, "git", return_value="https://gitlab.example/foo/bar.git"):
            with self.assertRaises(mog.SystemExit2):
                mog.detect_provider(None, None)

    def test_github_slug_from_remote(self) -> None:
        with mock.patch.object(mog, "git", return_value="git@github.com:foo/bar.git"):
            self.assertEqual(mog.GithubProvider(None, "gh").slug(), "foo/bar")
            self.assertEqual(mog.GithubProvider("a/b", "gh").slug(), "a/b")


class GithubEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "remote", "add", "origin", "https://github.com/foo/bar.git")
        self.plan = root / "plan.json"
        self.fake = root / "gh"
        self.fake.write_text(FAKE_GH)
        self.fake.chmod(stat.S_IRWXU)
        self.sleeps: list[float] = []

    def run_main(self, *extra: str) -> tuple[int, str]:
        argv = [mog.__name__, "7", "--gh", str(self.fake), "--repo", "foo/bar",
                "--poll-interval", "0.01", "--max-delay", "0.02", *extra]
        err = io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(mog.time, "sleep", side_effect=self.sleeps.append), \
                contextlib.redirect_stderr(err), \
                mock.patch.dict(os.environ, {"MOG_FAKE_PLAN": str(self.plan)}):
            status = mog.main()
        return status, err.getvalue()

    def plan_with(self, *views: dict, **plan: dict) -> None:
        self.plan.write_text(json.dumps({"views": list(views), **plan}))

    @staticmethod
    def view(head: str = "sha1", merge_state: str = "CLEAN", **extra: str) -> dict:
        return {"head": head, "merge_state": merge_state, **extra}

    def test_green_head_is_merged_exactly(self) -> None:
        self.plan_with(self.view())
        status, err = self.run_main()
        self.assertEqual(status, 0, err)
        self.assertIn("merging verified head sha1", err)
        plan = json.loads(self.plan.read_text())
        self.assertTrue(plan["merged"])

    def test_dry_run_never_merges(self) -> None:
        self.plan_with(self.view())
        status, err = self.run_main("--dry-run")
        self.assertEqual(status, 0, err)
        self.assertIn("would be merged", err)
        self.assertNotIn("merging verified", err)

    def test_stale_head_invalidates_green_evidence(self) -> None:
        self.plan_with(self.view("sha1"), self.view("sha2", merge_state="BLOCKED", review="APPROVED"))
        status, err = self.run_main()
        self.assertEqual(status, 4, err)
        self.assertIn("invalidating green evidence", err)
        self.assertIn("not mergeable: failed", err)

    def test_head_kept_changing_gives_up(self) -> None:
        self.plan_with(self.view("sha1"), self.view("sha2", merge_state="PENDING"),
                       self.view("sha3", merge_state="PENDING"))
        status, err = self.run_main("--head-restarts", "1")
        self.assertEqual(status, 4, err)
        self.assertIn("head kept changing", err)

    def test_failed_gate_blocks(self) -> None:
        self.plan_with(self.view(merge_state="UNSTABLE"))
        status, err = self.run_main()
        self.assertEqual(status, 4, err)
        self.assertIn("not mergeable: failed", err)

    def test_conflict_blocks(self) -> None:
        self.plan_with(self.view(merge_state="DIRTY", mergeable="NOT_MERGEABLE"))
        status, err = self.run_main()
        self.assertEqual(status, 4, err)
        self.assertIn("not mergeable: conflict", err)

    def test_review_required_blocks(self) -> None:
        self.plan_with(self.view(merge_state="BLOCKED", review="REVIEW_REQUIRED"))
        status, err = self.run_main()
        self.assertEqual(status, 4, err)
        self.assertIn("not mergeable: review_required", err)

    def test_pending_gate_polls_until_green(self) -> None:
        self.plan_with(self.view(merge_state="PENDING"), self.view())
        status, err = self.run_main()
        self.assertEqual(status, 0, err)
        self.assertGreaterEqual(len(self.sleeps), 1)

    def test_poll_timeout_blocks(self) -> None:
        self.plan_with(self.view(merge_state="PENDING"))
        status, err = self.run_main("--max-wait", "0.001")
        self.assertEqual(status, 4, err)
        self.assertIn("max-wait", err)

    def test_transient_api_failure_recovers(self) -> None:
        self.plan_with(self.view(), fail_mode="network error", fail_first=1)
        status, err = self.run_main()
        self.assertEqual(status, 0, err)
        self.assertIn("transient API failure (1/", err)

    def test_persistent_api_failure_returns_3(self) -> None:
        self.plan_with(self.view(), fail_mode="api down", fail_first=99)
        status, err = self.run_main("--max-retries", "1")
        self.assertEqual(status, 3, err)

    def test_rate_limit_exhaustion_returns_5(self) -> None:
        self.plan_with(self.view(), fail_mode="HTTP 429 rate limit exceeded", fail_first=99)
        status, err = self.run_main("--max-retries", "2")
        self.assertEqual(status, 5, err)

    def test_rate_limit_honors_retry_after_capped(self) -> None:
        self.plan_with(self.view(), fail_mode="rate limit; Retry-After: 900", fail_first=99)
        status, err = self.run_main("--max-retries", "1")
        self.assertEqual(status, 5, err)
        self.assertLessEqual(max(self.sleeps), 0.02)

    def test_already_merged_returns_0(self) -> None:
        self.plan_with(self.view(state="MERGED"))
        status, err = self.run_main()
        self.assertEqual(status, 0, err)
        self.assertIn("already merged", err)


class ForgejoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def provider(self) -> mog.ForgejoProvider:
        with mock.patch.dict(os.environ, {"FORGEJO_TOKEN": "tok"}), \
                mock.patch.object(mog, "git", return_value="https://git.starintel.actor/foo/bar.git"):
            return mog.ForgejoProvider(None, None, timeout=1)

    def respond(self, pull: dict, status: dict | None = None, reviews: list | None = None) -> None:
        def fake_urlopen(request: urllib.request.Request, timeout: float) -> FakeResponse:
            path = request.full_url.rsplit("/api/v1/repos/foo/bar/", 1)[1]
            self.calls.append((request.get_method(), path))
            payloads = {
                "pulls/7": pull,
                f"commits/{pull['head']['sha']}/status": status or STATUS_OK,
                "pulls/7/reviews": reviews if reviews is not None else REVIEW_OK,
                "pulls/7/merge": b"",
            }
            value = payloads[path]
            return FakeResponse(value if isinstance(value, bytes) else forgejo_json(value))

        self.patcher = mock.patch.object(urllib.request, "urlopen", side_effect=fake_urlopen)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_ready_probe_classification(self) -> None:
        self.respond(dict(PULL))
        state = self.provider().probe(7)
        self.assertEqual(mog.classify(state), "ready")
        self.assertEqual(state["head"], "sha1")

    def test_unapproved_review_requires_review(self) -> None:
        self.respond(dict(PULL), reviews=[])
        self.assertEqual(mog.classify(self.provider().probe(7)), "review_required")

    def test_failing_commit_status_blocks(self) -> None:
        self.respond(dict(PULL), status={"status": "failure"})
        self.assertEqual(mog.classify(self.provider().probe(7)), "failed")

    def test_cancelled_gate_counts_as_failure(self) -> None:
        self.respond(dict(PULL), status={"status": "error"})
        self.assertEqual(mog.classify(self.provider().probe(7)), "failed")

    def test_conflict_blocks(self) -> None:
        self.respond({**PULL, "mergeable": False})
        self.assertEqual(mog.classify(self.provider().probe(7)), "conflict")

    def test_closed_without_merge_is_blocked(self) -> None:
        self.respond({**PULL, "state": "closed"})
        self.assertEqual(mog.classify(self.provider().probe(7)), "closed")

    def test_merge_posts_to_provider(self) -> None:
        self.respond(dict(PULL))
        self.provider().merge(7)
        self.assertEqual(self.calls[-1], ("POST", "pulls/7/merge"))

    def test_rate_limit_parses_retry_after(self) -> None:
        provider = self.provider()

        def rate_limited(request: urllib.request.Request, timeout: float) -> FakeResponse:
            raise urllib.error.HTTPError(request.full_url, 429, "slow down", {"Retry-After": "5"}, io.BytesIO())

        with mock.patch.object(urllib.request, "urlopen", side_effect=rate_limited):
            with self.assertRaises(mog.ApiError) as caught:
                provider.probe(7)
        self.assertEqual(caught.exception.retry_after, 5)

    def test_network_unreachable_is_transient(self) -> None:
        provider = self.provider()
        with mock.patch.object(urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("connection refused")):
            with self.assertRaises(mog.ApiError) as caught:
                provider.probe(7)
        self.assertIsNone(caught.exception.retry_after)

    def test_missing_token_is_configuration_error(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(mog, "git", return_value="https://git.starintel.actor/foo/bar.git"):
            with self.assertRaises(mog.SystemExit2):
                mog.ForgejoProvider(None, None, timeout=1)


if __name__ == "__main__":
    unittest.main()
