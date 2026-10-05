import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_pali_units.py"
spec = importlib.util.spec_from_file_location("pali_units", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class PaliUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        base_root = self.root / "root/pli/ms/sutta/dn"
        base_html = self.root / "html/pli/ms/sutta/dn"
        base_root.mkdir(parents=True)
        base_html.mkdir(parents=True)
        root = {
            "dn1:0.1": "Dīgha Nikāya 1 ",
            "dn1:0.2": "Brahmajālasutta ",
            "dn1:1.1.1": "Evaṁ me sutaṁ—",
            "dn1:1.1.2": "ekaṁ samayaṁ bhagavā ... ",
            "dn1:1.1.3": "iti. ",
            "dn1:1.2.0": "Section ",
            "dn1:1.2.1": "Second paragraph. ",
        }
        html = {
            "dn1:0.1": "<article><li class='division'>{}</li>",
            "dn1:0.2": "<h1>{}</h1>",
            "dn1:1.1.1": "<p><span class='evam'>{}</span>",
            "dn1:1.1.2": "{}",
            "dn1:1.1.3": "{}</p>",
            "dn1:1.2.0": "<h2>{}</h2>",
            "dn1:1.2.1": "<p>{}</p>",
        }
        (base_root / "dn1_root-pli-ms.json").write_text(
            json.dumps(root, ensure_ascii=False), encoding="utf-8"
        )
        (base_html / "dn1_html.json").write_text(
            json.dumps(html, ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_preserves_leaf_ids_and_groups_paragraphs(self):
        leaves, units, errors = mod.build_work(
            self.root, "DN 1", "a" * 40
        )
        self.assertEqual(errors, [])
        self.assertEqual(leaves[2]["segment_id"], "dn1:1.1.1")
        paragraphs = [u for u in units if u["unit_type"] == "paragraph"]
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(
            paragraphs[0]["segment_ids"],
            ["dn1:1.1.1", "dn1:1.1.2", "dn1:1.1.3"],
        )
        self.assertIn("Evaṁ me sutaṁ", paragraphs[0]["text"])
        headings = [u for u in units if u["unit_type"] == "heading"]
        self.assertEqual(len(headings), 2)


if __name__ == "__main__":
    unittest.main()
