import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_promotion_core as core


class ReviewUiContractTests(unittest.TestCase):
    def test_committed_ui_is_evidence_bound_v2(self):
        html = (
            ROOT / "generated" / "review-ui" / "dn14-mahapadana" / "index.html"
        ).read_text(encoding="utf-8")
        for marker in (
            "review_schema_version: 2",
            "Stable reviewer ID",
            "crypto.subtle.digest",
            "evidence: await evidenceForAlignment(alignment)",
            "supersedes_review_id: previous ? previous.review_id : null",
            "An accepted review requires all four assessments to be agree.",
            "this page never writes to the repository and never promotes an alignment",
        ):
            self.assertIn(marker, html)

    def test_embedded_ui_evidence_matches_current_sources(self):
        html = (
            ROOT / "generated" / "review-ui" / "dn14-mahapadana" / "index.html"
        ).read_text(encoding="utf-8")
        match = re.search(
            r"const DATA = (.*?);\nconst LANG_ORDER",
            html,
            re.S,
        )
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))

        case = json.loads(
            (
                ROOT
                / "data"
                / "case-studies"
                / "dn14-mahapadana"
                / "alignments.json"
            ).read_text(encoding="utf-8")
        )
        indexes = core.build_source_indexes(
            ROOT / "generated" / "alignment-source" / "pali" / "units.jsonl",
            ROOT / "generated" / "alignment-source" / "chinese" / "blocks.jsonl",
            ROOT / "generated" / "alignment-source" / "indic" / "units.jsonl",
        )
        ui_by_id = {
            alignment["alignment_id"]: alignment
            for alignment in payload["alignments"]
        }
        self.assertEqual(
            set(ui_by_id),
            {alignment["alignment_id"] for alignment in case["alignments"]},
        )

        for alignment in case["alignments"]:
            ui_alignment = ui_by_id[alignment["alignment_id"]]
            expected = core.evidence_for_alignment(alignment, indexes)
            displayed_units = []
            for member in ui_alignment["members"]:
                for unit in member["units"]:
                    displayed_units.append(
                        {
                            "language": member["language"],
                            "witness_id": member["witness_id"],
                            "source_unit_id": unit["source_id"],
                            "digest": core.digest(
                                {
                                    "source_id": unit["source_id"],
                                    "text_html": unit["text_html"],
                                    "meta": unit["meta"],
                                }
                            ),
                        }
                    )
            displayed = {
                "evidence_version": 1,
                "alignment_claim_digest": core.digest(
                    core.alignment_claim_payload(ui_alignment)
                ),
                "source_units": displayed_units,
            }
            self.assertEqual(displayed, expected)

    def test_generator_emits_same_security_contract(self):
        source = (
            ROOT / "scripts" / "build_multiwitness_review_ui.py"
        ).read_text(encoding="utf-8")
        for marker in (
            "review_schema_version: 2",
            "crypto.subtle.digest",
            "evidence: await evidenceForAlignment(alignment)",
            "supersedes_review_id: previous ? previous.review_id : null",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
