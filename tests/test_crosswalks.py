import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_crosswalks.py"
spec = importlib.util.spec_from_file_location("validate_crosswalks", MODULE_PATH)
vc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = vc
assert spec.loader is not None
spec.loader.exec_module(vc)


class FirstTwentyCrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/crosswalks/first-20.json").read_text(encoding="utf-8"))
        cls.records = cls.data["crosswalks"]

    def test_validator_passes_repository_data(self):
        self.assertEqual(vc.validate(ROOT), [])

    def test_exactly_twenty_high_confidence_records(self):
        self.assertEqual(len(self.records), 20)
        self.assertTrue(all(r["overall_confidence"] == "high" for r in self.records))

    def test_every_record_has_chinese_and_non_pali_indic_evidence(self):
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertGreater(len(record["full_parallels"]["chinese"]), 0)
                indic = (
                    record["indic_witnesses"]["sanskrit_bhs"]
                    + record["indic_witnesses"]["gandhari_prakrit"]
                )
                self.assertGreater(len(indic), 0)

    def test_no_exact_parallel_claims(self):
        for record in self.records:
            for witness in vc.all_witnesses(record):
                self.assertNotEqual(witness["relation_class"], "exact_parallel")

    def test_dn16_gandhari_and_dn23_prakrit_caveats(self):
        by_id = {r["id"]: r for r in self.records}
        dn16 = by_id["work:dn16"]["indic_witnesses"]["gandhari_prakrit"]
        self.assertTrue(any(w["language"] == "gdh" for w in dn16))
        dn23 = by_id["work:dn23"]["indic_witnesses"]["gandhari_prakrit"]
        self.assertTrue(any(w["language"] == "pra" and w["tradition"] == "Jain" for w in dn23))


if __name__ == "__main__":
    unittest.main()
