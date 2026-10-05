import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_chinese_alignment_units.py"
spec = importlib.util.spec_from_file_location("chinese_units", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

TEI = "http://www.tei-c.org/ns/1.0"
CB = "http://www.cbeta.org/ns/1.0"


class ChineseUnitTests(unittest.TestCase):
    def test_extracts_p_and_lg_with_line_spans(self):
        xml = f"""<cb:div xmlns="{TEI}" xmlns:cb="{CB}" type="jing">
          <cb:mulu type="經">21 梵動經</cb:mulu>
          <head>梵動經</head>
          <lb ed="T" n="0088b12"/>
          <p xml:id="p1">如是我聞：<lb ed="T" n="0088b13"/>一時佛在。</p>
          <lb ed="T" n="0088b14"/>
          <lg xml:id="g1"><l>偈頌一</l><l>偈頌二</l></lg>
        </cb:div>"""
        elem = ET.fromstring(xml)
        meta = {
            "canonical_id": "DA 21",
            "container_id": "T0001",
            "source": {"path": "T/T01/T01n0001.xml"},
            "locator": {
                "start_lb": "0088b12",
                "end_lb": "0088b14",
                "start_ref": "T01n0001_p0088b12",
                "end_ref": "T01n0001_p0088b14",
            },
        }
        blocks, coverage = mod.extract_blocks(elem, meta)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["block_id"], "DA 21#b0001")
        self.assertIn("如是我聞", blocks[0]["text"])
        self.assertEqual(blocks[0]["locator"]["end_lb"], "0088b13")
        self.assertEqual(blocks[1]["block_kind"], "lg")
        self.assertGreater(coverage, 0.9)


if __name__ == "__main__":
    unittest.main()
