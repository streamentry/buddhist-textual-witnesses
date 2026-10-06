import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_promotion_core as core

SPEC = importlib.util.spec_from_file_location(
    "record_human_review", ROOT / "scripts" / "record_human_review.py"
)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


class RecordHumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.case_id = "case:test"
        self.alignment = {
            "alignment_id": "mw:test",
            "work_id": "DN 14",
            "status": "model_reviewed",
            "relation_type": "parallel_passage",
            "relation_member_ids": ["pli", "san"],
            "scope": "opening",
            "members": [
                {
                    "member_id": "pli",
                    "language": "pli",
                    "witness_id": "DN 14",
                    "source_unit_ids": ["DN 14#p1"],
                    "coverage": "full",
                    "editorial_features": [],
                },
                {
                    "member_id": "san",
                    "language": "san",
                    "witness_id": "SF 36",
                    "source_unit_ids": ["SF 36#p1"],
                    "coverage": "full",
                    "editorial_features": ["supplied"],
                },
            ],
            "variants": [],
            "review": {
                "status": "reviewed",
                "reviewer_type": "model",
                "reviewer": "model",
                "decision": "accepted",
                "confidence": "high",
                "notes": "model review",
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
                    "source": {"project": "Bilara", "revision": "aaa"},
                }
            },
            "lzh": {},
            "san": {
                "SF 36#p1": {
                    "unit_id": "SF 36#p1",
                    "language": "san",
                    "witness_id": "SF 36",
                    "edition_text": "evaṃ <supplied>mayā</supplied> śrutam",
                    "source": {"project": "Bilara", "revision": "aaa"},
                }
            },
        }
        self.ledger = {
            "version": 2,
            "case_study_id": self.case_id,
            "promotion_policy": "test",
            "reviews": [],
        }

    def review(self, rid="review:alice:1"):
        return {
            "review_schema_version": 2,
            "review_id": rid,
            "case_study_id": self.case_id,
            "alignment_id": "mw:test",
            "supersedes_review_id": None,
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
            "reviewed_at": "2026-10-06T10:00:00Z",
            "notes": "Reviewed directly against the displayed sources.",
            "proposed_changes": None,
            "evidence": core.evidence_for_alignment(self.alignment, self.indexes),
        }

    def test_valid_review_is_prepared_without_mutating_input_ledger(self):
        review = self.review()
        updated, summaries, errors = mod.prepare_review_append(
            self.ledger, [review], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(errors, [])
        self.assertEqual(self.ledger["reviews"], [])
        self.assertEqual(len(updated["reviews"]), 1)
        self.assertTrue(summaries[0]["promotion_eligible"])

    def test_model_authored_review_is_rejected(self):
        review = self.review()
        review["reviewer"]["reviewer_type"] = "model"
        updated, _, errors = mod.prepare_review_append(
            self.ledger, [review], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(updated["reviews"], [])
        self.assertTrue(any("reviewer_type must be human" in error for error in errors))

    def test_stale_evidence_is_rejected(self):
        review = self.review()
        review["evidence"]["alignment_claim_digest"] = "sha256:" + "0" * 64
        updated, _, errors = mod.prepare_review_append(
            self.ledger, [review], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(updated["reviews"], [])
        self.assertTrue(any("stale review evidence" in error for error in errors))

    def test_duplicate_review_id_is_rejected(self):
        review = self.review()
        ledger = copy.deepcopy(self.ledger)
        ledger["reviews"].append(review)
        updated, _, errors = mod.prepare_review_append(
            ledger, [review], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(len(updated["reviews"]), 1)
        self.assertTrue(any("duplicate review_id" in error for error in errors))

    def test_same_reviewer_revision_must_supersede_previous(self):
        first = self.review("review:alice:1")
        ledger = copy.deepcopy(self.ledger)
        ledger["reviews"].append(first)
        second = self.review("review:alice:2")
        second["reviewed_at"] = "2026-10-06T11:00:00Z"

        _, _, errors = mod.prepare_review_append(
            ledger, [second], self.case_id, self.alignments, self.indexes
        )
        self.assertTrue(any("must supersede latest review" in error for error in errors))

        second["supersedes_review_id"] = first["review_id"]
        updated, summaries, errors = mod.prepare_review_append(
            ledger, [second], self.case_id, self.alignments, self.indexes
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(updated["reviews"]), 2)
        self.assertEqual(len(summaries), 1)

    def test_loader_accepts_single_review_and_bundle(self):
        review = self.review()
        with tempfile.TemporaryDirectory() as tmp:
            single = Path(tmp) / "single.json"
            single.write_text(json.dumps(review), encoding="utf-8")
            self.assertEqual(len(mod.load_review_candidates(single)), 1)

            bundle = Path(tmp) / "bundle.json"
            bundle.write_text(json.dumps({"reviews": [review]}), encoding="utf-8")
            self.assertEqual(len(mod.load_review_candidates(bundle)), 1)


if __name__ == "__main__":
    unittest.main()
