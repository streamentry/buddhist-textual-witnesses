import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("indic_units",ROOT/"scripts"/"build_indic_source_units.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class IndicSourceUnitTests(unittest.TestCase):
    def test_plain_text_preserves_content_not_editorial_tags(self):
        value="kiṃ nu bha<supplied>ga</supplied>vato <gap reason='lost'/> dharmaḥ"
        self.assertEqual(mod.plain_text(value),"kiṃ nu bhagavato dharmaḥ")

    def test_build_witness_preserves_edition_markup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            rp="root/san/sutta/sf/sf36_root-san.json"
            hp="html/san/sutta/sf/sf36_html.json"
            (root/rp).parent.mkdir(parents=True)
            (root/hp).parent.mkdir(parents=True)
            (root/rp).write_text(json.dumps({"sf36:1.1":"bud<supplied>dha</supplied>ḥ"}),encoding="utf-8")
            (root/hp).write_text(json.dumps({"sf36:1.1":"<p>{}</p>"}),encoding="utf-8")
            rows,errors=mod.build_witness(root,"SF 36",{
                "work_id":"DN 14","language":"san","provider":"SuttaCentral Bilara",
                "root_path":rp,"html_path":hp
            },"a"*40)
            self.assertEqual(errors,[])
            self.assertEqual(rows[0]["edition_text"],"bud<supplied>dha</supplied>ḥ")
            self.assertEqual(rows[0]["search_text"],"buddhaḥ")
            self.assertTrue(rows[0]["editorial_markup"]["has_supplied"])


if __name__=="__main__":
    unittest.main()
