from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from review_evidence import alignment_evidence_digest  # noqa: E402
from validate_promotions import validate_promotions  # noqa: E402


class PromotionProtocolTests(unittest.TestCase):
    def setUp(self):
        self.case_id = "case:test"
        self.alignment = {
            "alignment_id": "a:1",
            "work_id": "T",
            "relation_type": "parallel_passage",
            "scope": "test",
            "members": [{
                "member_id": "x",
                "language": "pli",
                "witness_id": "W",
                "source_unit_ids": ["W#1"],
                "coverage": "full",
                "notes": "",
            }],
            "variants": [],
        }
        self.case = {
            "case_study_id": self.case_id,
            "alignments": [self.alignment],
        }
        self.sources = {
            "W#1": {
                "unit_id": "W#1",
                "language": "pli",
                "text": "alpha",
                "source": {"project": "fixture", "revision": "r1", "path": "x"},
            }
        }
        self.digest = alignment_evidence_digest(
            self.case_id, self.alignment, self.sources
        )
        self.review = {
            "review_id": "review:human:1",
            "case_study_id": self.case_id,
            "alignment_id": "a:1",
            "reviewer": {"reviewer_type": "human", "name": "Reviewer"},
            "decision": "accepted",
            "evidence_snapshot": {"digest": self.digest},
        }
        self.promotion = {
            "promotion_id": "promotion:1",
            "case_study_id": self.case_id,
            "alignment_id": "a:1",
            "review_ids": ["review:human:1"],
            "target_status": "established",
            "promoted_by": {"actor_type": "human", "name": "Editor"},
            "promoted_on": "2026-10-06",
            "evidence_digest": self.digest,
            "policy_version": "human-review-promotion-v1",
        }

    def docs(self):
        return (
            {"reviews": [self.review]},
            {
                "case_study_id": self.case_id,
                "policy_version": "human-review-promotion-v1",
                "promotions": [self.promotion],
            },
        )

    def test_valid_explicit_promotion_derives_established(self):
        reviews, promotions = self.docs()
        errors, summary = validate_promotions(
            self.case, reviews, promotions, self.sources
        )
        self.assertEqual(errors, [])
        self.assertEqual(summary["established_alignment_ids"], ["a:1"])
        self.assertTrue(summary["derived_state_only"])
        self.assertFalse(summary["case_study_mutated"])

    def test_model_review_cannot_promote(self):
        reviews, promotions = self.docs()
        reviews["reviews"][0]["reviewer"]["reviewer_type"] = "model"
        errors, _ = validate_promotions(
            self.case, reviews, promotions, self.sources
        )
        self.assertTrue(any("not human" in e for e in errors))

    def test_nonaccepted_review_cannot_promote(self):
        reviews, promotions = self.docs()
        reviews["reviews"][0]["decision"] = "needs_work"
        errors, _ = validate_promotions(
            self.case, reviews, promotions, self.sources
        )
        self.assertTrue(any("not accepted" in e for e in errors))

    def test_source_drift_invalidates_review_and_promotion(self):
        reviews, promotions = self.docs()
        changed_sources = {
            "W#1": {
                **self.sources["W#1"],
                "text": "beta",
                "source": {"project": "fixture", "revision": "r2", "path": "x"},
            }
        }
        errors, summary = validate_promotions(
            self.case, reviews, promotions, changed_sources
        )
        self.assertGreaterEqual(
            sum("stale" in e for e in errors), 2
        )
        self.assertEqual(summary["established_count"], 0)

    def test_no_promotion_means_zero_established(self):
        reviews = {"reviews": [self.review]}
        promotions = {
            "case_study_id": self.case_id,
            "policy_version": "human-review-promotion-v1",
            "promotions": [],
        }
        errors, summary = validate_promotions(
            self.case, reviews, promotions, self.sources
        )
        self.assertEqual(errors, [])
        self.assertEqual(summary["established_count"], 0)


if __name__ == "__main__":
    unittest.main()
