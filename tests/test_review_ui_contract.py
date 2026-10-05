import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
