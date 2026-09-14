"""Validate GRILL fixtures plant real defects and the skill demands evidence."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/grill"
SKILL = (ROOT / "skills/grill/SKILL.md").read_text(encoding="utf-8")


class FixtureValidityTests(unittest.TestCase):
    """Each fixture must actually contain the defect it pretends to exercise."""

    def test_race_condition_is_check_then_act(self) -> None:
        text = (FIXTURES / "race.py").read_text(encoding="utf-8")
        self.assertIn('STATE.read_text()', text)
        self.assertIn("claimed", text)
        self.assertNotIn("lock", text.lower().replace("blocks", ""))

    def test_unproved_assumption_is_unvalidated_response(self) -> None:
        text = (FIXTURES / "assumption.py").read_text(encoding="utf-8")
        self.assertIn('["retries"]', text)
        self.assertIn("always returns", text)

    def test_missing_negative_coverages_only_cover_happy_path(self) -> None:
        text = (FIXTURES / "missing_negative_coverage.py").read_text(encoding="utf-8")
        self.assertNotIn("assertRaises", text)
        self.assertNotIn("ValueError", text)

    def test_fake_idempotency_retries_mutation_without_key(self) -> None:
        text = (FIXTURES / "fake_idempotency.py").read_text(encoding="utf-8")
        self.assertIn("idempotent", text)
        self.assertIn("requests.post", text)
        self.assertNotIn("Idempotency-Key", text)

    def test_stale_ci_trusts_badge_and_lacks_rollback(self) -> None:
        text = (FIXTURES / "stale_ci.md").read_text(encoding="utf-8")
        self.assertIn("badge", text)
        self.assertIn("roll back", text.lower())

    def test_unsafe_retry_repeats_mutation_forever(self) -> None:
        text = (FIXTURES / "unsafe_retry.sh").read_text(encoding="utf-8")
        self.assertIn("--push-remote", text)
        self.assertIn("keep retrying", text.lower())

    def test_speculative_abstraction_has_single_consumer(self) -> None:
        text = (FIXTURES / "speculative.py").read_text(encoding="utf-8")
        self.assertIn("ChannelRegistry", text)
        self.assertIn("future channels", text)

    def test_missing_rollback_deletes_previous_release(self) -> None:
        text = (FIXTURES / "missing_rollback.sh").read_text(encoding="utf-8")
        self.assertIn("rm -rf", text)
        self.assertIn("restart", text)


class GrillSkillContractTests(unittest.TestCase):
    """GRILL must demand evidence-backed findings, not rhetorical questions."""

    def test_findings_require_evidence_fields(self) -> None:
        for field in ("claim", "challenge", "evidence", "severity",
                      "counterexample", "proof", "correction"):
            self.assertIn(field, SKILL)

    def test_verdicts_are_explicit(self) -> None:
        for verdict in ("SURVIVED", "FAILED", "CONDITIONALLY SURVIVED"):
            self.assertIn(verdict, SKILL)

    def test_questions_not_findings_rejected(self) -> None:
        self.assertIn("Questions are not findings", SKILL)

    def test_read_only_by_default(self) -> None:
        self.assertIn("read-only", SKILL)

    def test_selected_model_critics_use_worker(self) -> None:
        self.assertIn("opencode-worker", SKILL)

    def test_defect_coverage(self) -> None:
        coverage = {
            "race": "races" in SKILL or "races," in SKILL,
            "partial failure": "partial failure" in SKILL,
            "restart": "restart" in SKILL,
            "malformed input": "malformed input" in SKILL,
            "retries": "retries" in SKILL,
            "rollback": "rollback" in SKILL,
            "observability": "observability" in SKILL,
            "speculative abstraction": "speculative abstractions" in SKILL,
            "authorization": "authorization" in SKILL,
            "migration": "migration" in SKILL,
            "performance": "performance" in SKILL,
            "coupling": "coupling" in SKILL,
        }
        missing = [name for name, ok in coverage.items() if not ok]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
