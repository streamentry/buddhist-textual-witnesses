import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "multi_validator", ROOT / "scripts" / "validate_multiwitness_alignments.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class MultiWitnessValidatorTests(unittest.TestCase):
    def setUp(self):
        self.indexes = {
            "pli": {
                "DN 14#p0001": {"unit_id": "DN 14#p0001", "work_id": "DN 14"}
            },
            "lzh": {
                "DA 1#b0001": {
                    "block_id": "DA 1#b0001",
                    "canonical_id": "DA 1",
                }
            },
            "san": {
                "SF 36#p0001": {
                    "unit_id": "SF 36#p0001",
                    "witness_id": "SF 36",
                    "search_text": "evaṃ mayā śrutam",
                    "editorial_summary": {
                        "segments_with_supplied": 1,
                        "segments_with_gap": 0,
                        "segments_with_unclear": 0,
                    },
                },
                "SF 36#p0019": {
                    "unit_id": "SF 36#p0019",
                    "witness_id": "SF 36",
                    "search_text": "Sanskrit text is completely lost",
                },
            },
        }

    def base(self):
        return {
            "alignment_id": "mw:test",
            "work_id": "DN 14",
            "status": "model_reviewed",
            "relation_type": "parallel_passage",
            "members": [
                {
                    "member_id": "pli",
                    "language": "pli",
                    "witness_id": "DN 14",
                    "source_unit_ids": ["DN 14#p0001"],
                    "coverage": "full",
                    "editorial_features": [],
                },
                {
                    "member_id": "san",
                    "language": "san",
                    "witness_id": "SF 36",
                    "source_unit_ids": ["SF 36#p0001"],
                    "coverage": "full",
                    "editorial_features": ["supplied"],
                },
            ],
            "relation_member_ids": ["pli", "san"],
            "variants": [],
            "review": {
                "status": "reviewed",
                "reviewer_type": "model",
                "reviewer": "test-model",
                "decision": "accepted",
                "confidence": "high",
                "notes": "test",
            },
        }

    def test_model_reviewed_resolves(self):
        self.assertEqual(mod.validate_alignment(self.base(), self.indexes), [])

    def test_established_must_come_from_promotion_ledger(self):
        row = self.base()
        row["status"] = "established"
        row["review"] = {
            "status": "reviewed",
            "reviewer_type": "human",
            "reviewer": "real-human",
            "decision": "accepted",
        }
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(any("derived from the promotion ledger" in e for e in errors))

    def test_lost_text_marker_requires_explicit_loss_and_relation_scope(self):
        row = self.base()
        row["members"].append(
            {
                "member_id": "da",
                "language": "lzh",
                "witness_id": "DA 1",
                "source_unit_ids": ["DA 1#b0001"],
                "coverage": "full",
                "editorial_features": [],
            }
        )
        row["members"][1]["coverage"] = "lost_text_marker"
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(
            any("does not explicitly indicate textual loss" in e for e in errors)
        )

        row["members"][1]["source_unit_ids"] = ["SF 36#p0019"]
        row["members"][1]["editorial_features"] = []
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(any("requires a textual_loss variant claim" in e for e in errors))

        row["relation_member_ids"] = ["pli", "da"]
        row["variants"] = [
            {
                "type": "textual_loss",
                "statement": "Sanskrit wording is lost.",
                "member_ids": ["san"],
            }
        ]
        self.assertEqual(mod.validate_alignment(row, self.indexes), [])

    def test_lost_text_member_cannot_participate_in_asserted_relation(self):
        row = self.base()
        row["members"].append(
            {
                "member_id": "da",
                "language": "lzh",
                "witness_id": "DA 1",
                "source_unit_ids": ["DA 1#b0001"],
                "coverage": "full",
            }
        )
        row["members"][1]["coverage"] = "lost_text_marker"
        row["members"][1]["source_unit_ids"] = ["SF 36#p0019"]
        row["members"][1]["editorial_features"] = []
        row["relation_member_ids"] = ["pli", "san"]
        row["variants"] = [
            {
                "type": "textual_loss",
                "statement": "Sanskrit wording is lost.",
                "member_ids": ["san"],
            }
        ]
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(
            any("cannot participate in the asserted textual relation" in e for e in errors)
        )

    def test_relation_scope_is_always_explicit(self):
        row = self.base()
        del row["relation_member_ids"]
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(any("must explicitly contain" in e for e in errors))

    def test_editorial_features_must_match_source_evidence(self):
        row = self.base()
        row["members"][1]["editorial_features"] = []
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(any("do not match source evidence" in e for e in errors))

    def test_unknown_variant_member_fails(self):
        row = self.base()
        row["variants"] = [
            {
                "type": "structural",
                "statement": "test",
                "member_ids": ["missing"],
            }
        ]
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(any("unknown member" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
