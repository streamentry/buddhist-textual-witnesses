import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_promotion_core as core


class ReviewPromotionTests(unittest.TestCase):
    def setUp(self):
        self.case_id = "case:test"
        self.alignment = {
            "alignment_id": "mw:test",
            "work_id": "DN 14",
            "status": "model_reviewed",
            "relation_type": "parallel_passage",
            "scope": "test_scope",
            "members": [
                {
                    "member_id": "pli",
                    "language": "pli",
                    "witness_id": "DN 14",
                    "source_unit_ids": ["DN 14#p1"],
                    "coverage": "full",
                },
                {
                    "member_id": "san",
                    "language": "san",
                    "witness_id": "SF 36",
                    "source_unit_ids": ["SF 36#p1"],
                    "coverage": "full",
                },
            ],
            "variants": [],
            "review": {
                "status": "reviewed",
                "reviewer_type": "model",
                "reviewer": "model",
                "decision": "accepted",
                "confidence": "high",
            },
        }
        self.alignments = {"mw:test": self.alignment}
        self.indexes = {
            "pli": {
                "DN 14#p1": {
                    "unit_id": "DN 14#p1",
                    "language": "pli",
                    "work_id": "DN 14",
                    "text": "Evaṃ me sutaṃ",
                    "source": {"project": "Bilara", "revision": "aaa", "root_path": "dn14.json"},
                }
            },
            "lzh": {},
            "san": {
                "SF 36#p1": {
                    "unit_id": "SF 36#p1",
                    "language": "san",
                    "witness_id": "SF 36",
                    "edition_text": "evaṃ <supplied>mayā</supplied> śrutam",
                    "source": {"project": "Bilara", "revision": "aaa", "root_path": "sf36.json"},
                }
            },
        }

    def review(self):
        return {
            "review_schema_version": 2,
            "review_id": "review:alice:mw-test:1",
            "case_study_id": self.case_id,
            "alignment_id": "mw:test",
            "reviewer": {
                "reviewer_type": "human",
                "name": "Alice",
                "reviewer_id": "orcid:0000-0000-0000-0001",
                "affiliation": None,
                "identifier": "0000-0000-0000-0001",
            },
            "decision": "accepted",
            "assessments": {
                "source_units": "agree",
                "relation_type": "agree",
                "variant_notes": "agree",
                "editorial_handling": "agree",
            },
            "reviewed_at": "2026-10-05T14:00:00Z",
            "notes": "checked",
            "proposed_changes": None,
            "evidence": core.evidence_for_alignment(self.alignment, self.indexes),
        }

    def promotion(self, review):
        return {
            "promotion_schema_version": 1,
            "promotion_id": "promotion:mw-test:1",
            "case_study_id": self.case_id,
            "alignment_id": "mw:test",
            "review_id": review["review_id"],
            "review_digest": core.review_digest(review),
            "evidence_digest": core.evidence_digest(review),
            "decision": "established",
            "promoter": {
                "actor_type": "human",
                "name": "Maintainer",
                "actor_id": "github:maintainer",
            },
            "promoted_at": "2026-10-05T15:00:00Z",
            "policy_version": core.PROMOTION_POLICY_VERSION,
            "notes": "explicit promotion",
        }

    def test_fresh_human_review_is_eligible(self):
        review = self.review()
        errors, fresh, reasons = core.validate_review_record(
            review, self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(errors, [])
        self.assertTrue(fresh)
        self.assertEqual(reasons, [])
        self.assertTrue(core.review_is_promotion_eligible(review, fresh))

    def test_source_drift_makes_review_stale_not_invalid_history(self):
        review = self.review()
        drifted = copy.deepcopy(self.indexes)
        drifted["pli"]["DN 14#p1"]["text"] = "changed"
        errors, fresh, reasons = core.validate_review_record(
            review, self.case_id, self.alignments, drifted
        )
        self.assertEqual(errors, [])
        self.assertFalse(fresh)
        self.assertIn("source_unit_evidence_changed", reasons)
        self.assertFalse(core.review_is_promotion_eligible(review, fresh))

    def test_accepted_requires_all_assessments_agree(self):
        review = self.review()
        review["assessments"]["variant_notes"] = "uncertain"
        errors, _, _ = core.validate_review_record(
            review, self.case_id, self.alignments, self.indexes
        )
        self.assertTrue(any("all assessments=agree" in error for error in errors))

    def test_model_review_cannot_enter_human_review_layer(self):
        review = self.review()
        review["reviewer"]["reviewer_type"] = "model"
        errors, fresh, _ = core.validate_review_record(
            review, self.case_id, self.alignments, self.indexes
        )
        self.assertTrue(any("reviewer_type must be human" in error for error in errors))
        self.assertFalse(core.review_is_promotion_eligible(review, fresh))

    def test_promotion_binds_exact_review(self):
        review = self.review()
        promotion = self.promotion(review)
        errors, fresh = core.validate_promotion_record(
            promotion,
            self.case_id,
            self.alignments,
            {review["review_id"]: review},
            self.indexes,
            require_current_fresh=True,
        )
        self.assertEqual(errors, [])
        self.assertTrue(fresh)

        edited = copy.deepcopy(review)
        edited["notes"] = "silently changed"
        errors, _ = core.validate_promotion_record(
            promotion,
            self.case_id,
            self.alignments,
            {edited["review_id"]: edited},
            self.indexes,
        )
        self.assertTrue(any("review_digest" in error for error in errors))

    def test_rejected_review_can_never_be_promoted(self):
        review = self.review()
        review["decision"] = "rejected"
        promotion = self.promotion(review)
        errors, _ = core.validate_promotion_record(
            promotion,
            self.case_id,
            self.alignments,
            {review["review_id"]: review},
            self.indexes,
        )
        self.assertTrue(any("not an accepted human review" in error for error in errors))

    def test_derived_established_requires_explicit_promotion(self):
        review = self.review()
        state = core.derived_alignment_status(
            "mw:test", [review], [], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(state["derived_status"], "promotion_required")

        promotion = self.promotion(review)
        state = core.derived_alignment_status(
            "mw:test", [review], [promotion], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(state["derived_status"], "established")

    def test_review_revisions_must_explicitly_supersede_latest(self):
        first = self.review()
        second = copy.deepcopy(first)
        second["review_id"] = "review:alice:mw-test:2"
        second["reviewed_at"] = "2026-10-05T16:00:00Z"
        errors = core.validate_review_lineage([first, second])
        self.assertTrue(any("must supersede latest review" in error for error in errors))

        second["supersedes_review_id"] = first["review_id"]
        self.assertEqual(core.validate_review_lineage([first, second]), [])
        self.assertEqual(core.active_review_ids([first, second]), {second["review_id"]})

    def test_superseded_promoted_review_requires_new_promotion(self):
        first = self.review()
        promotion = self.promotion(first)
        second = copy.deepcopy(first)
        second["review_id"] = "review:alice:mw-test:2"
        second["reviewed_at"] = "2026-10-05T16:00:00Z"
        second["supersedes_review_id"] = first["review_id"]

        state = core.derived_alignment_status(
            "mw:test",
            [first, second],
            [promotion],
            self.case_id,
            self.alignments,
            self.indexes,
        )
        self.assertEqual(state["derived_status"], "promotion_required")
        self.assertIn(first["review_id"], state["superseded_review_ids"])

    def test_source_drift_demotes_current_derived_state_to_review_stale(self):
        review = self.review()
        promotion = self.promotion(review)
        drifted = copy.deepcopy(self.indexes)
        drifted["san"]["SF 36#p1"]["source"]["revision"] = "bbb"
        state = core.derived_alignment_status(
            "mw:test", [review], [promotion], self.case_id, self.alignments, drifted
        )
        self.assertEqual(state["derived_status"], "review_stale")


if __name__ == "__main__":
    unittest.main()
