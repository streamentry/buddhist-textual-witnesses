import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

cand = load("alignment_candidates", "generate_alignment_candidates.py")
valid = load("alignment_validator", "validate_alignments.py")


class AlignmentCandidateTests(unittest.TestCase):
    def setUp(self):
        self.pali = [
            {
                "unit_id": "DN 1#p0001",
                "work_id": "DN 1",
                "text": "Evaṁ me sutaṁ— ekaṁ samayaṁ bhagavā.",
            },
            {
                "unit_id": "DN 1#p0002",
                "work_id": "DN 1",
                "text": "Atha kho bhagavā.",
            },
        ]
        self.chinese = [
            {
                "block_id": "DA 21#b0001",
                "canonical_id": "DA 21",
                "text": "如是我聞：一時佛在。",
            },
            {
                "block_id": "DA 21#b0002",
                "canonical_id": "DA 21",
                "text": "爾時世尊。",
            },
        ]

    def test_shared_formula_is_candidate_not_established(self):
        rows = cand.formula_candidates(
            "DN 1", "DA 21", self.pali, self.chinese
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["relation_type"], "shared_formula")
        self.assertEqual(row["status"], "machine_candidate")
        self.assertEqual(row["assertion"], "not_established")
        errors = valid.validate_candidate(
            row,
            {p["unit_id"]: p for p in self.pali},
            {c["block_id"]: c for c in self.chinese},
        )
        self.assertEqual(errors, [])

    def test_machine_structural_candidate_cannot_be_established(self):
        row = cand.monotonic_candidates(
            "DN 1", "DA 21", self.pali, self.chinese
        )[0]
        row["status"] = "established"
        row["assertion"] = "established_claim"
        row["review"] = {
            "status": "reviewed",
            "reviewer_type": "human",
            "reviewer": "Reviewer",
            "decision": "accepted",
            "notes": "Test",
        }
        errors = valid.validate_candidate(
            row,
            {p["unit_id"]: p for p in self.pali},
            {c["block_id"]: c for c in self.chinese},
        )
        self.assertTrue(
            any("structural-ranking output cannot be established" in e for e in errors)
        )


if __name__ == "__main__":
    unittest.main()
