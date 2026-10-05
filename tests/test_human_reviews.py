import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "human_reviews", ROOT / "scripts" / "validate_human_reviews.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class HumanReviewTests(unittest.TestCase):
    def base(self):
        return {
            "review_id": "review:1",
            "case_study_id": "case:test",
            "alignment_id": "mw:test",
            "reviewer": {
                "reviewer_type": "human",
                "name": "Scholar",
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
            "reviewed_on": "2026-10-05",
            "notes": "Reviewed against sources.",
            "proposed_changes": None,
        }

    def test_valid_human_review(self):
        self.assertEqual(
            mod.validate_review(self.base(), "case:test", {"mw:test"}),
            [],
        )

    def test_model_cannot_be_human_review(self):
        row = self.base()
        row["reviewer"]["reviewer_type"] = "model"
        errors = mod.validate_review(row, "case:test", {"mw:test"})
        self.assertTrue(any("must be human" in e for e in errors))

    def test_unknown_alignment_fails(self):
        errors = mod.validate_review(
            self.base(), "case:test", {"mw:other"}
        )
        self.assertTrue(any("unknown alignment_id" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
