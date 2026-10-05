import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "review_ui", ROOT / "scripts" / "build_multiwitness_review_ui.py"
)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


class ReviewUiTests(unittest.TestCase):
    def test_page_preserves_supplied_text_and_human_boundary(self):
        payload = {
            "case_study_id": "test-case",
            "title": "Test",
            "scope": "scope",
            "epistemic_policy": "policy",
            "witnesses": [],
            "review_count": 0,
            "alignments": [{
                "alignment_id": "mw:test:1",
                "work_id": "DN 14",
                "status": "model_reviewed",
                "relation_type": "parallel_passage",
                "scope": "opening",
                "members": [{
                    "member_id": "sf",
                    "language": "san",
                    "witness_id": "SF 36",
                    "source_unit_ids": ["SF 36#p0001"],
                    "coverage": "full",
                    "notes": None,
                    "units": [{
                        "source_id": "SF 36#p0001",
                        "text_html": 'evaṃ <span class="supplied">ś</span>rutam',
                        "meta": {"project":"Bilara","revision":"abc","path":"x","start_ref":None,"end_ref":None,"urls":[]}
                    }]
                }],
                "variants": [{"type":"textual_loss","statement":"Keep uncertainty visible.","member_ids":["sf"]}],
                "review": {"confidence":"high","notes":"Model note."},
                "existing_reviews": []
            }]
        }
        page = mod.build_page(payload)
        self.assertIn('class="supplied"', page)
        self.assertIn("never writes to the repository", page)
        self.assertIn("reviewer_type", page)
        self.assertIn('"human"', page)
        self.assertIn("The UI will not invent a human identity.", page)
        self.assertNotIn("<script src=", page.lower())

    def test_sanskrit_renderer_escapes_and_marks_supplied(self):
        rendered = mod.render_sanskrit_html(
            "bha<supplied>ga</supplied>vān <b>&</b>"
        )
        self.assertIn('class="supplied"', rendered)
        self.assertIn("ga", rendered)
        self.assertIn("&amp;", rendered)
        self.assertNotIn("<b>", rendered)


if __name__ == "__main__":
    unittest.main()
