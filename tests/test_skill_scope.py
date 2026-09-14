from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/skill-scope/scripts/skill-scope"


class SkillScopeTests(unittest.TestCase):
    def test_lists_local_and_global_origins_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            global_checkout = root / "global"
            (project / ".opencode/skills/local-one").mkdir(parents=True)
            (project / ".opencode/skills/local-one/SKILL.md").write_text("local")
            (global_checkout / "skills/global-one").mkdir(parents=True)
            (global_checkout / "skills/global-one/SKILL.md").write_text("global")
            result = subprocess.run(
                [str(SCRIPT), "list", "--project", str(project), "--global-checkout", str(global_checkout)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("local\tlocal-one\t", result.stdout)
            self.assertIn("global\tglobal-one\t", result.stdout)

    def test_environment_selects_canonical_global_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "skills-source"
            (checkout / "skills/global-one").mkdir(parents=True)
            (checkout / "skills/global-one/SKILL.md").write_text("global")
            result = subprocess.run(
                [str(SCRIPT), "list"],
                text=True,
                capture_output=True,
                env={**os.environ, "OPENCODE_GLOBAL_SKILLS_CHECKOUT": str(checkout)},
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(checkout), result.stdout)


if __name__ == "__main__":
    unittest.main()
