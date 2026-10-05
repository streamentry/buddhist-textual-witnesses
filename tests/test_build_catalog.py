import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_catalog.py"
spec = importlib.util.spec_from_file_location("build_catalog", MODULE_PATH)
bc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bc
assert spec.loader is not None
spec.loader.exec_module(bc)

TEI = "http://www.tei-c.org/ns/1.0"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CatalogPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root / "sources/lock.json", json.dumps({"sources": {
            "suttacentral-bilara": {"commit": "scsha", "repository": "https://github.com/suttacentral/bilara-data.git"},
            "cbeta-xml": {"commit": "cbsha", "repository": "https://github.com/cbeta-org/xml-p5.git"},
            "gretil": {"commit": "grsha", "repository": "https://github.com/INDOLOGY/GRETIL-mirror.git"}
        }}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_suttacentral_sanskrit_and_prakrit(self):
        write(self.root / "upstream/suttacentral-bilara/root/san/sutta/sf/sf36_root-san.json",
              json.dumps({"sf36:0.1": "Mahāvadānasūtra", "sf36:1.1": "evaṃ mayā śrutam"}, ensure_ascii=False))
        write(self.root / "upstream/suttacentral-bilara/root/pra/pts/sutta/pdhp/pdhp1-13_root-pra-pts.json",
              json.dumps({"pdhp1:0.0": "Patna Dharmapada", "pdhp1:1": "manopūrvvaṁgamā"}, ensure_ascii=False))
        rows = bc.scan_suttacentral(self.root, bc.load_json(self.root / "sources/lock.json"), {}, {})
        self.assertEqual({r.language for r in rows}, {"san", "pra"})
        self.assertEqual({r.canonical_id for r in rows}, {"sf36", "pdhp1-13"})

    def test_gretil_only_explicit_buddhist_metadata(self):
        buddh = f'''<TEI xmlns="{TEI}" xml:id="sa_test"><teiHeader><fileDesc><titleStmt><title>Test Sūtra</title></titleStmt><publicationStmt><licence target="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</licence></publicationStmt><notesStmt><note><ref target="http://example/1_sanskr/4_rellit/buddh/test.htm">source</ref></note></notesStmt></fileDesc></teiHeader><text><body><p>x</p></body></text></TEI>'''
        non = f'''<TEI xmlns="{TEI}" xml:id="sa_non"><teiHeader><fileDesc><titleStmt><title>Non Buddhist</title></titleStmt><notesStmt><note><ref target="http://example/1_sanskr/4_rellit/hindu/test.htm">source</ref></note></notesStmt></fileDesc></teiHeader><text><body><p>x</p></body></text></TEI>'''
        write(self.root / "upstream/gretil-mirror/gretil.sub.uni-goettingen.de/gretil/corpustei/sa_test.xml", buddh)
        write(self.root / "upstream/gretil-mirror/gretil.sub.uni-goettingen.de/gretil/corpustei/sa_non.xml", non)
        rows = bc.scan_gretil(self.root, bc.load_json(self.root / "sources/lock.json"), {}, {})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].canonical_id, "sa_test")
        self.assertEqual(rows[0].language, "san")

    def test_bhs_requires_explicit_signal_or_override(self):
        metadata = "This edition is Buddhist Hybrid Sanskrit."
        self.assertEqual(bc.classify_language("san", "gretil:x", metadata, {}), "bhs")
        self.assertEqual(bc.classify_language("san", "gretil:x", "Buddhist text", {}), "san")
        self.assertEqual(bc.classify_language("san", "gretil:x", "", {"gretil:x": "bhs"}), "bhs")

    def test_cbeta_config_selects_only_agama(self):
        xml = f'''<TEI xmlns="{TEI}"><teiHeader><fileDesc><titleStmt><title>長阿含經</title></titleStmt></fileDesc></teiHeader><text><body><p>x</p></body></text></TEI>'''
        write(self.root / "upstream/cbeta-xml-p5/T/T01/T01n0001.xml", xml)
        rows = bc.scan_cbeta(self.root, bc.load_json(self.root / "sources/lock.json"), [{"id":"T0001","path":"T/T01/T01n0001.xml","notes":"Dīrgha Āgama"}], {})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].canonical_id, "T0001")
        self.assertEqual(rows[0].language, "lzh")

    def test_crosswalk_groups_different_witnesses(self):
        a = bc.Witness("work:x", "a", "x", "san", "a", "A", "edition", "S", "a", "a", "sha", "url")
        b = bc.Witness("work:x", "b", "y", "lzh", "b", "B", "translation", "T", "b", "b", "sha", "url")
        cat = bc.build_catalog([a, b], {"sources": {}})
        self.assertEqual(set(cat["works"]["work:x"]["languages"]), {"san", "lzh"})

    def test_end_to_end_outputs_are_deterministic(self):
        a = bc.Witness("work:x", "a", "x", "san", "x:san:a", "A", "edition", "S", "a", "a", "sha", "url")
        b = bc.Witness("work:x", "b", "y", "lzh", "y:lzh:b", "B", "translation", "T", "b", "b", "sha", "url")
        out = self.root / "catalog"
        cat = bc.build_catalog([b, a], {"sources": {}})
        bc.write_outputs(out, [b, a], cat)
        self.assertTrue((out / "catalog.json").exists())
        self.assertTrue((out / "catalog.jsonl").exists())
        self.assertTrue((out / "catalog.csv").exists())
        stats = json.loads((out / "stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["total_witnesses"], 2)
        self.assertEqual(stats["total_works"], 1)


if __name__ == "__main__":
    unittest.main()
