from __future__ import annotations

import importlib.util
import os
import subprocess
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


wt = load_module("git_worktrees", "skills/git-worktrees/scripts/worktree.py")


def git(repo: Path, *argv: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *argv],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.test",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.test"},
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {argv} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def init_repo(tmp: str) -> Path:
    repo = Path(tmp) / "my-app"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    (repo / "README").write_text("x", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    return repo


class SlugTests(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(wt.slugify("Feature/Foo"), "Feature-Foo")
        self.assertEqual(wt.slugify("  my  weird!!branch  "), "my-weird-branch")
        with self.assertRaises(wt.WorktreeError):
            wt.slugify("///")

    def test_project_slug(self) -> None:
        self.assertEqual(wt.project_slug(Path("/code/my-app")), "my-app")
        self.assertEqual(wt.project_slug(Path("/code/My.App.git")), "my-app")

    def test_branch_label_strips_origin(self) -> None:
        self.assertEqual(wt.branch_label("origin/feature/foo"), "feature-foo")
        self.assertEqual(wt.branch_label("release-1.2"), "release-1-2")

    def test_worktree_path_layout(self) -> None:
        root = Path("/home/t/git/worktrees")
        repo = Path("/code/my-app")
        self.assertEqual(
            wt.worktree_path(root, repo, wt.branch_label("feature/foo")),
            root / "my-app-feature-foo",
        )

    def test_root_resolution(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GIT_WORKTREE_ROOT", None)
            self.assertEqual(wt.worktree_root(None), Path.home() / "git" / "worktrees")
        with mock.patch.dict(os.environ, {"GIT_WORKTREE_ROOT": "/tmp/wt-root"}):
            self.assertEqual(wt.worktree_root(None), Path("/tmp/wt-root"))
        self.assertEqual(wt.worktree_root("/tmp/other"), Path("/tmp/other"))


class WorktreeCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "trees"
        self.repo = init_repo(self._tmp.name)
        os.chdir(self.repo)
        self.addCleanup(os.chdir, ROOT)

    def run_script(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "skills/git-worktrees/scripts/worktree.py"),
             "--root", str(self.root), *argv],
            cwd=self.repo, check=False, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_add_existing_branch_uses_expected_layout(self) -> None:
        git(self.repo, "branch", "feature/foo")
        proc = self.run_script("add", "feature/foo")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        target = self.root / "my-app-feature-foo"
        self.assertIn(str(target), proc.stdout)
        self.assertEqual(git(target, "branch", "--show-current"), "feature/foo")

    def test_add_creates_missing_branch_with_base(self) -> None:
        proc = self.run_script("add", "topic/x", "--base", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        target = self.root / "my-app-topic-x"
        self.assertEqual(git(target, "branch", "--show-current"), "topic/x")

    def test_add_fails_closed_on_existing_path(self) -> None:
        git(self.repo, "branch", "feature/foo")
        self.root.mkdir(parents=True)
        (self.root / "my-app-feature-foo").mkdir()
        proc = self.run_script("add", "feature/foo")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("refusing to overwrite", proc.stderr)

    def test_add_fails_closed_without_base_for_missing_branch(self) -> None:
        proc = self.run_script("add", "topic/y")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--base", proc.stderr)

    def test_add_fails_closed_when_branch_checked_out(self) -> None:
        proc = self.run_script("add", "main")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("already checked out", proc.stderr)

    def test_add_dry_run_does_not_mutate(self) -> None:
        proc = self.run_script("add", "topic/z", "--base", "main", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("dry-run", proc.stdout)
        self.assertFalse((self.root / "my-app-topic-z").exists())

    def test_remove_by_name_and_refuses_main_and_outside_root(self) -> None:
        self.run_script("add", "topic/r", "--base", "main")
        proc = self.run_script("remove", "my-app-topic-r")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.root / "my-app-topic-r").exists())

        outside = Path(self._tmp.name) / "outside"
        git(self.repo, "worktree", "add", "-b", "outside/x", str(outside))
        proc = self.run_script("remove", str(outside))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("outside the worktree root", proc.stderr)

        unregistered = Path(self._tmp.name) / "unregistered"
        unregistered.mkdir()
        proc = self.run_script("remove", str(unregistered))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("not a registered git worktree", proc.stderr)

        proc = self.run_script("remove", str(self.repo))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("main working tree", proc.stderr)

    def test_list_shows_only_root_worktrees(self) -> None:
        self.run_script("add", "topic/a", "--base", "main")
        proc = self.run_script("list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"{self.root / 'my-app-topic-a'}\ttopic/a", proc.stdout)
        self.assertNotIn(str(self.repo) + "\t", proc.stdout)


if __name__ == "__main__":
    unittest.main()
