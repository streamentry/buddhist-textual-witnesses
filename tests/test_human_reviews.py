import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_promotion_core as core

spec = importlib.util.spec_from_file_location(
    "human_reviews", ROOT / "scripts" / "validate_human_reviews.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.alignment = {
            "alignment_id": "mw:test",
            "work_id": "DN 14",
            "status": "model_reviewed",
            "relation_type": "parallel_passage",
            "scope": "test",
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
                    "edition_text": "evaṃ mayā śrutam",
                    "source": {"project": "Bilara", "revision": "aaa"},
                }
            },
        }

    def base(self):
        return {
            "review_schema_version": 2,
            "review_id": "review:1",
            "case_study_id": "case:test",
            "alignment_id": "mw:test",
            "supersedes_review_id": None,
            "reviewer": {
                "reviewer_type": "human",
                "name": "Scholar",
                "reviewer_id": "orcid:test",
                "affiliation": None,
                "identifier": None,
            },
            "decision": "accepted",
            "assessments": {
                "source_units": "agree",
                "relation_type": "agree",
                "variant_notes": "agree",
                "editorial_handling": "agree",
            },
            "reviewed_at": "2026-10-05T14:00:00Z",
            "notes": "Reviewed against sources.",
            "proposed_changes": None,
            "evidence": core.evidence_for_alignment(self.alignment, self.indexes),
        }

    def validate(self, review, alignments=None):
        return mod.validate_review_record(
            review,
            "case:test",
            alignments or {"mw:test": self.alignment},
            self.indexes,
        )[0]

    def test_valid_human_review(self):
        self.assertEqual(self.validate(self.base()), [])

    def test_model_cannot_be_human_review(self):
        row = self.base()
        row["reviewer"]["reviewer_type"] = "model"
        errors = self.validate(row)
        self.assertTrue(any("must be human" in e for e in errors))

    def test_unknown_alignment_fails(self):
        errors = self.validate(self.base(), {"mw:other": copy.deepcopy(self.alignment)})
        self.assertTrue(any("unknown alignment_id" in e for e in errors))

    def test_v1_review_is_rejected(self):
        row = self.base()
        row["review_schema_version"] = 1
        errors = self.validate(row)
        self.assertTrue(any("review_schema_version must be 2" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
