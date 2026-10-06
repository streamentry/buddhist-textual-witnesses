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

evidence_spec = importlib.util.spec_from_file_location(
    "review_evidence", ROOT / "scripts" / "review_evidence.py"
)
evidence = importlib.util.module_from_spec(evidence_spec)
sys.modules[evidence_spec.name] = evidence
assert evidence_spec.loader is not None
evidence_spec.loader.exec_module(evidence)


class HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.alignment = {
            "alignment_id": "mw:test",
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
        self.alignments = {"mw:test": self.alignment}
        self.sources = {
            "W#1": {
                "unit_id": "W#1",
                "language": "pli",
                "text": "alpha",
                "source": {
                    "project": "fixture",
                    "revision": "r1",
                    "path": "x",
                },
            }
        }

    def base(self):
        digest = evidence.alignment_evidence_digest(
            "case:test", self.alignment, self.sources
        )
        revisions = evidence.alignment_source_revisions(
            self.alignment, self.sources
        )
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
            "evidence_snapshot": {
                "digest": digest,
                "source_revisions": revisions,
            },
            "notes": "Reviewed against sources.",
            "proposed_changes": None,
        }

    def test_valid_human_review(self):
        self.assertEqual(
            mod.validate_review(
                self.base(), "case:test", self.alignments, self.sources
            ),
            [],
        )

    def test_model_cannot_be_human_review(self):
        row = self.base()
        row["reviewer"]["reviewer_type"] = "model"
        errors = mod.validate_review(
            row, "case:test", self.alignments, self.sources
        )
        self.assertTrue(any("must be human" in e for e in errors))

    def test_unknown_alignment_fails(self):
        errors = mod.validate_review(
            self.base(), "case:test", {}, self.sources
        )
        self.assertTrue(any("unknown alignment_id" in e for e in errors))

    def test_source_drift_makes_review_stale(self):
        changed = {
            "W#1": {
                **self.sources["W#1"],
                "text": "beta",
            }
        }
        errors = mod.validate_review(
            self.base(), "case:test", self.alignments, changed
        )
        self.assertTrue(any("stale" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
