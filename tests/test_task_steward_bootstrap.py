from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "task_steward_bootstrap",
    ROOT / "skills" / "task-steward-bootstrap" / "scripts" / "bootstrap.py",
)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class TaskStewardBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sources = self.root / "sources"
        for name in bootstrap.SKILL_NAMES:
            skill = self.sources / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_project_agents_installs_both_canonical_links(self) -> None:
        project = self.root / "project"
        project.mkdir()
        results = bootstrap.install(
            "agents",
            "project",
            project_root=project,
            source_root=self.sources,
        )
        self.assertEqual(len(results), 2)
        for name in bootstrap.SKILL_NAMES:
            target = project / ".agents" / "skills" / name
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), (self.sources / name).resolve())

    def test_install_is_idempotent_for_matching_links(self) -> None:
        project = self.root / "project"
        project.mkdir()
        bootstrap.install(
            "opencode",
            "project",
            project_root=project,
            source_root=self.sources,
        )
        results = bootstrap.install(
            "opencode",
            "project",
            project_root=project,
            source_root=self.sources,
        )
        self.assertTrue(all(item.startswith("ok ") for item in results))

    def test_conflicting_target_fails_closed(self) -> None:
        project = self.root / "project"
        target = project / ".agents" / "skills" / "task-steward-worker"
        target.mkdir(parents=True)
        with self.assertRaisesRegex(FileExistsError, "refusing existing path"):
            bootstrap.install(
                "agents",
                "project",
                project_root=project,
                source_root=self.sources,
            )

    def test_agent_zero_global_requires_real_install_root(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --a0-root"):
            bootstrap.install(
                "agent-zero",
                "global",
                source_root=self.sources,
                home=self.root / "home",
            )

    def test_agent_zero_project_uses_a0proj_and_optional_compat_a0(self) -> None:
        project = self.root / "project"
        project.mkdir()
        bootstrap.install(
            "agent-zero",
            "project",
            project_root=project,
            source_root=self.sources,
            compat_a0=True,
        )
        for root in (project / ".a0proj/skills", project / ".a0/skills"):
            for name in bootstrap.SKILL_NAMES:
                self.assertEqual((root / name).resolve(), (self.sources / name).resolve())

    def test_dry_run_makes_no_filesystem_changes(self) -> None:
        project = self.root / "project"
        project.mkdir()
        results = bootstrap.install(
            "agents",
            "project",
            project_root=project,
            source_root=self.sources,
            dry_run=True,
        )
        self.assertTrue(all(item.startswith("would-link ") for item in results))
        self.assertFalse((project / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
