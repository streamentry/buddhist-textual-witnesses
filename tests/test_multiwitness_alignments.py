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
                },
                {
                    "member_id": "san",
                    "language": "san",
                    "witness_id": "SF 36",
                    "source_unit_ids": ["SF 36#p0001"],
                    "coverage": "full",
                },
            ],
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

    def test_established_requires_human(self):
        row = self.base()
        row["status"] = "established"
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(any("requires human reviewer" in e for e in errors))

    def test_lost_text_marker_requires_explicit_loss_source(self):
        row = self.base()
        row["members"][1]["coverage"] = "lost_text_marker"
        errors = mod.validate_alignment(row, self.indexes)
        self.assertTrue(
            any("does not explicitly indicate textual loss" in e for e in errors)
        )

        row["members"][1]["source_unit_ids"] = ["SF 36#p0019"]
        errors = mod.validate_alignment(row, self.indexes)
        self.assertEqual(errors, [])

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
