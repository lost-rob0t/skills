from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/git/scripts/sync-remotes"
GIT = Path(__file__).resolve().parents[1] / "skills/git/SKILL.md"


def git(repo: Path, *argv: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *argv], check=True, text=True,
                          capture_output=True,
                          env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.test",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.test"})
    return proc.stdout.strip()


def commit(repo: Path, message: str) -> None:
    (repo / f"{message.replace(' ', '-')}.txt").write_text(message, encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", message)


class SyncRemotesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.canonical = root / "canonical.git"
        self.mirror = root / "mirror.git"
        self.work = root / "work"
        for bare in (self.canonical, self.mirror):
            subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True,
                           capture_output=True)
        self.work.mkdir()
        git(self.work, "init", "-b", "main")
        commit(self.work, "base")
        git(self.work, "remote", "add", "origin", f"https://git.starintel.actor/foo/bar.git")
        git(self.work, "remote", "add", "mirror", str(self.mirror))
        # The canonical detection uses URLs; point origin's tracking at the
        # local bare canonical repository by adding a second remote with the
        # Forgejo-like URL remapped through instead-of for hermetic tests.
        git(self.work, "config", f"url.{self.canonical}.insteadOf",
            "https://git.starintel.actor/foo/bar.git")

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(SCRIPT), *args], text=True, capture_output=True,
                              cwd=self.work, check=False)

    def push_all(self, repo: Path, remote: str, *branches: str) -> None:
        for branch in branches:
            git(repo, "push", remote, f"{branch}:{branch}")

    def rows(self, proc: subprocess.CompletedProcess[str]) -> list[list[str]]:
        header, *rest = proc.stdout.strip().splitlines()
        assert header.startswith("branch\t")
        return [line.split("\t") for line in rest]

    def test_same_branch_is_in_sync(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = self.rows(proc)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "main")
        self.assertEqual(rows[0][1], "same")
        self.assertNotEqual(rows[0][2], "")
        self.assertEqual(rows[0][2], rows[0][3])

    def test_ahead_on_canonical(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        commit(self.work, "feature")
        self.push_all(self.work, "origin", "main")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual([row[1] for row in self.rows(proc)], ["ahead-canonical"])

    def test_ahead_on_mirror(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        commit(self.work, "mirror-only")
        self.push_all(self.work, "mirror", "main")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual([row[1] for row in self.rows(proc)], ["ahead-mirror"])

    def test_diverged(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        commit(self.work, "canonical-only")
        self.push_all(self.work, "origin", "main")
        git(self.work, "reset", "--hard", "HEAD~1")
        commit(self.work, "mirror-only")
        self.push_all(self.work, "mirror", "main")
        git(self.work, "reset", "--hard", "HEAD~1")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual([row[1] for row in self.rows(proc)], ["diverged"])

    def test_missing_on_one_side(self) -> None:
        commit(self.work, "topic")
        git(self.work, "branch", "topic")
        self.push_all(self.work, "origin", "main", "topic")
        self.push_all(self.work, "mirror", "main")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        states = {row[0]: row[1] for row in self.rows(proc)}
        self.assertEqual(states["topic"], "missing-on-mirror")

    def test_missing_remote_is_reported(self) -> None:
        git(self.work, "remote", "remove", "mirror")
        proc = self.run_script("--mirror", "mirror")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("missing-remote\tmirror", proc.stdout)

    def test_json_output(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        proc = self.run_script("--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["branch"], "main")
        self.assertEqual(data[0]["state"], "same")
        self.assertNotEqual(data[0]["canonical"], "")
        self.assertEqual(data[0]["canonical"], data[0]["mirror"])

    def test_push_fast_forwards_mirror(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        commit(self.work, "new-work")
        self.push_all(self.work, "origin", "main")
        proc = self.run_script("--push")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("pushing main to mirror", proc.stderr)
        verify = self.run_script()
        self.assertEqual(verify.returncode, 0, verify.stderr)
        self.assertEqual([row[1] for row in self.rows(verify)], ["same"])

    def test_push_refuses_dirty_worktree(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        commit(self.work, "unpushed")
        self.push_all(self.work, "origin", "main")
        (self.work / "dirty.txt").write_text("dirty", encoding="utf-8")
        proc = self.run_script("--push")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("dirty worktree", proc.stderr)
        verify = self.run_script()
        self.assertEqual([row[1] for row in self.rows(verify)], ["ahead-canonical"])

    def test_push_reports_unfixable_divergence(self) -> None:
        self.push_all(self.work, "mirror", "main")
        self.push_all(self.work, "origin", "main")
        commit(self.work, "canonical-only")
        self.push_all(self.work, "origin", "main")
        git(self.work, "reset", "--hard", "HEAD~1")
        commit(self.work, "mirror-only")
        self.push_all(self.work, "mirror", "main")
        proc = self.run_script("--push")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("manual reconciliation", proc.stderr)

    def test_usage_error(self) -> None:
        proc = self.run_script("--bogus")
        self.assertEqual(proc.returncode, 2)


class GitSkillInvariantTests(unittest.TestCase):
    def test_no_duplicate_artifacts_documented(self) -> None:
        text = GIT.read_text(encoding="utf-8")
        self.assertIn("Never duplicate a repository or pull request across hosts", text)

    def test_sync_remotes_documented(self) -> None:
        text = GIT.read_text(encoding="utf-8")
        self.assertIn("sync-remotes", text)


if __name__ == "__main__":
    unittest.main()
