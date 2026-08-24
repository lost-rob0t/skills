#!/usr/bin/env python3
"""Tests for privacy-preserving workflow discovery."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/discover-workflows/scripts/discover_workflows.py"
SPEC = importlib.util.spec_from_file_location("discover_workflows", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DiscoverWorkflowsTests(unittest.TestCase):
    def test_command_family_removes_wrappers_and_skips_secrets(self):
        self.assertEqual(MODULE.command_family("sudo nix flake check"), "nix")
        self.assertIsNone(MODULE.command_family("curl --token=secret https://example.test"))
        self.assertIsNone(MODULE.emacs_command_name("OpenRouter:z-ai/glm-5.2"))
        self.assertIsNone(MODULE.emacs_command_name("2026-08-15_configure-prolog-rlm.org"))

    def test_report_contains_only_safe_aggregates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bash_history = root / "bash_history"
            bash_history.write_text(
                "git status\n" * 5 + "curl --token=secret https://private.example\n",
                encoding="utf-8",
            )
            savehist = root / "savehist"
            savehist.write_text(
                '(setq counsel-M-x-history \'("gptel-mode" "gptel-mode" "private prompt"))\n',
                encoding="utf-8",
            )
            recentf = root / "recentf"
            recentf.write_text(
                '(setq recentf-list \'("~/Documents/Projects/a" "~/Documents/Projects/b"))\n',
                encoding="utf-8",
            )
            report = MODULE.build_report(
                bash_history,
                [savehist],
                [recentf],
                None,
                home=Path("/home/test-user"),
            )
            encoded = json.dumps(report)
            self.assertIn("git", encoded)
            self.assertIn("gptel-mode", encoded)
            self.assertNotIn("private.example", encoded)
            self.assertNotIn("private prompt", encoded)


if __name__ == "__main__":
    unittest.main()
