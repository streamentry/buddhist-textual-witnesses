import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "anchor_windows", ROOT / "scripts" / "generate_anchor_window_candidates.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class AnchorWindowTests(unittest.TestCase):
    def setUp(self):
        self.lexicon = [
            {
                "id": "open",
                "pali": ["evaṁ me sutaṁ"],
                "lzh": ["如是我聞"],
                "weight": 4.0,
            },
            {
                "id": "name",
                "pali": ["suppiya"],
                "lzh": ["善念"],
                "weight": 4.0,
            },
        ]
        self.pali = [
            {
                "unit_id": "DN 1#p0001",
                "text": "Evaṁ me sutaṁ. Suppiya followed behind.",
            },
            {
                "unit_id": "DN 1#p0002",
                "text": "Other passage.",
            },
        ]
        self.chinese = [
            {
                "block_id": "DA 21#b0001",
                "ordinal": 1,
                "text": "如是我聞：",
            },
            {
                "block_id": "DA 21#b0002",
                "ordinal": 2,
                "text": "善念隨佛後行。",
            },
            {
                "block_id": "DA 21#b0003",
                "ordinal": 3,
                "text": "其他。",
            },
        ]

    def test_anchor_window_prefers_combined_lexical_evidence(self):
        rows = mod.candidate_windows(
            "DN 1",
            "DA 21",
            self.pali,
            self.chinese,
            self.lexicon,
            top_k=3,
            max_width=2,
        )
        first = [
            row for row in rows
            if row["pali_unit_ids"] == ["DN 1#p0001"]
        ][0]
        self.assertEqual(
            first["chinese_unit_ids"],
            ["DA 21#b0001", "DA 21#b0002"],
        )
        self.assertEqual(
            len(first["method"]["signals"]["matched_anchors"]), 2
        )

    def test_evaluation_supports_many_to_many_gold(self):
        rows = mod.candidate_windows(
            "DN 1",
            "DA 21",
            self.pali,
            self.chinese,
            self.lexicon,
            top_k=3,
            max_width=2,
        )
        reviewed = {
            "alignments": [
                {
                    "alignment_id": "gold:1",
                    "work_id": "DN 1",
                    "chinese_witness_id": "DA 21",
                    "pali_unit_ids": ["DN 1#p0001"],
                    "chinese_unit_ids": [
                        "DA 21#b0001",
                        "DA 21#b0002",
                    ],
                    "review": {"decision": "accepted"},
                }
            ]
        }
        metrics = mod.evaluate(rows, reviewed)
        self.assertEqual(metrics["overlap_at_3"], 1.0)
        self.assertEqual(metrics["full_cover_at_3"], 1.0)


if __name__ == "__main__":
    unittest.main()
