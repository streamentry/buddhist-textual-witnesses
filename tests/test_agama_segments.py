import importlib.util
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_agama_segments.py"
spec = importlib.util.spec_from_file_location("agama_builder", MODULE_PATH)
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
assert spec.loader is not None
spec.loader.exec_module(builder)

TEI = "http://www.tei-c.org/ns/1.0"
CB = "http://www.cbeta.org/ns/1.0"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class AgamaSegmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ea_chapter_item_from_pin_context(self):
        xml = f"""<TEI xmlns="{TEI}" xmlns:cb="{CB}"><text><body>
        <lb ed="T" n="0001a01"/>
        <cb:div type="pin"><cb:mulu type="品" level="1" n="48">48 禮三寶品</cb:mulu>
          <cb:div type="jing"><cb:mulu type="經" level="2" n="4">4</cb:mulu>
          <head>（四）</head><lb ed="T" n="0001a02"/><p>如是我聞。</p>
          <lb ed="T" n="0001a03"/></cb:div>
        </cb:div></body></text></TEI>"""
        path = self.root / "ea.xml"
        write(path, xml)
        cfg = {
            "prefix": "EA",
            "container_id": "T0125",
            "path": "ea.xml",
            "id_mode": "chapter.item",
            "expected_segments": 1,
        }
        rows = builder.build_collection(
            path, cfg, "a" * 40, "https://github.com/cbeta-org/xml-p5.git"
        )
        self.assertEqual(rows[0]["canonical_id"], "EA 48.4")
        self.assertEqual(rows[0]["locator"]["start_lb"], "0001a01")
        self.assertEqual(rows[0]["locator"]["end_lb"], "0001a03")
        self.assertEqual(rows[0]["hierarchy"][-1]["mulu_type"], "品")

    def test_sa_visible_mulu_number_wins_over_internal_n(self):
        xml = f"""<TEI xmlns="{TEI}" xmlns:cb="{CB}"><text><body>
        <lb ed="T" n="0001a01"/>
        <cb:div type="jing"><cb:mulu type="經" level="2" n="1348">1355</cb:mulu>
        <lb ed="T" n="0001a02"/><p>經文</p></cb:div>
        </body></text></TEI>"""
        path = self.root / "sa.xml"
        write(path, xml)
        cfg = {
            "prefix": "SA",
            "container_id": "T0099",
            "path": "sa.xml",
            "id_mode": "global",
            "expected_segments": 1,
        }
        rows = builder.build_collection(
            path, cfg, "a" * 40, "https://github.com/cbeta-org/xml-p5.git"
        )
        self.assertEqual(rows[0]["canonical_id"], "SA 1355")
        self.assertEqual(rows[0]["number"], 1355)

    def test_sa2_other_div_is_segment_when_direct_mulu_is_jing(self):
        xml = f"""<TEI xmlns="{TEI}" xmlns:cb="{CB}"><text><body>
        <lb ed="T" n="0001a01"/>
        <cb:div type="other"><cb:mulu type="經" level="2">105</cb:mulu>
        <lb ed="T" n="0001a02"/><p>經文</p></cb:div>
        </body></text></TEI>"""
        path = self.root / "sa2.xml"
        write(path, xml)
        cfg = {
            "prefix": "SA2",
            "container_id": "T0100",
            "path": "sa2.xml",
            "id_mode": "global",
            "expected_segments": 1,
        }
        rows = builder.build_collection(
            path, cfg, "a" * 40, "https://github.com/cbeta-org/xml-p5.git"
        )
        self.assertEqual(rows[0]["canonical_id"], "SA2 105")
        self.assertIn(
            "mulu' and @type='經'", rows[0]["locator"]["xpath"]
        )

    def test_ea_jing_outside_pin_is_preserved_as_supplement(self):
        xml = f"""<TEI xmlns="{TEI}" xmlns:cb="{CB}"><text><body>
        <lb ed="T" n="0001a01"/>
        <cb:div type="jing"><cb:mulu type="經">5（卷末附文）</cb:mulu>
        <lb ed="T" n="0001a02"/><p>附文</p></cb:div>
        </body></text></TEI>"""
        path = self.root / "ea-supplement.xml"
        write(path, xml)
        cfg = {
            "prefix": "EA",
            "container_id": "T0125",
            "path": "ea-supplement.xml",
            "id_mode": "chapter.item",
            "expected_segments": 1,
            "expected_canonical_segments": 0,
            "expected_supplements": 1,
        }
        rows = builder.build_collection(
            path, cfg, "a" * 40, "https://github.com/cbeta-org/xml-p5.git"
        )
        self.assertEqual(rows[0]["record_kind"], "supplement")
        self.assertEqual(rows[0]["canonical_id"], "T0125 supplement 1")
        self.assertEqual(builder.validate_collection(rows, cfg), [])

    def test_text_hash_uses_lemma_and_skips_notes(self):
        xml = f"""<TEI xmlns="{TEI}" xmlns:cb="{CB}"><text><body>
        <lb ed="T" n="0001a01"/>
        <cb:div type="jing"><cb:mulu type="經">1 Test</cb:mulu><head>Heading</head>
        <lb ed="T" n="0001a02"/><p>A<app><lem>B</lem><rdg>X</rdg></app>
        <note>N</note>C</p></cb:div></body></text></TEI>"""
        path = self.root / "da.xml"
        write(path, xml)
        cfg = {
            "prefix": "DA",
            "container_id": "T0001",
            "path": "da.xml",
            "id_mode": "global",
            "expected_segments": 1,
        }
        rows = builder.build_collection(
            path, cfg, "a" * 40, "https://github.com/cbeta-org/xml-p5.git"
        )
        root = ET.parse(path).getroot()
        segment = next(
            elem
            for elem in root.iter()
            if builder.local(elem.tag) == "div"
            and builder.direct_child(elem, "mulu") is not None
        )
        plain = builder.normalize_text(builder.render_text(segment))
        self.assertEqual(plain, "ABC")
        self.assertEqual(
            rows[0]["locator"]["normalized_text_chars"], 3
        )


if __name__ == "__main__":
    unittest.main()
