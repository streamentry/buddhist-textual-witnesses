import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_promotion_core as core


class PromotionCliIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pali = self.dir / "pali.jsonl"
        self.chinese = self.dir / "chinese.jsonl"
        self.indic = self.dir / "indic.jsonl"
        self.case = self.dir / "case.json"
        self.reviews = self.dir / "reviews.json"
        self.promotions = self.dir / "promotions.json"
        self.state = self.dir / "state.json"

        self.pali.write_text(
            json.dumps(
                {
                    "unit_id": "DN 14#p1",
                    "language": "pli",
                    "work_id": "DN 14",
                    "text": "Evaṃ me sutaṃ",
                    "source": {
                        "project": "Bilara",
                        "revision": "aaa",
                        "root_path": "dn14.json",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        self.chinese.write_text("", encoding="utf-8")
        self.indic.write_text(
            json.dumps(
                {
                    "unit_id": "SF 36#p1",
                    "language": "san",
                    "witness_id": "SF 36",
                    "edition_text": "evaṃ <supplied>mayā</supplied> śrutam",
                    "source": {
                        "project": "Bilara",
                        "revision": "aaa",
                        "root_path": "sf36.json",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        alignment = {
            "alignment_id": "mw:test",
            "work_id": "DN 14",
            "status": "model_reviewed",
            "relation_type": "parallel_passage",
            "scope": "test",
            "members": [
                {
                    "member_id": "pli",
                    "language": "pli",
                    "witness_id": "DN 14",
                    "source_unit_ids": ["DN 14#p1"],
                    "coverage": "full",
                },
                {
                    "member_id": "san",
                    "language": "san",
                    "witness_id": "SF 36",
                    "source_unit_ids": ["SF 36#p1"],
                    "coverage": "full",
                },
            ],
            "variants": [],
            "review": {
                "status": "reviewed",
                "reviewer_type": "model",
                "reviewer": "test-model",
                "decision": "accepted",
                "confidence": "high",
            },
        }
        case_doc = {
            "case_study_id": "case:test",
            "title": "test",
            "alignments": [alignment],
        }
        self.case.write_text(
            json.dumps(case_doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        indexes = core.build_source_indexes(self.pali, self.chinese, self.indic)
        review = {
            "review_schema_version": 2,
            "review_id": "review:alice:mw-test:1",
            "case_study_id": "case:test",
            "alignment_id": "mw:test",
            "supersedes_review_id": None,
            "reviewer": {
                "reviewer_type": "human",
                "name": "Alice",
                "reviewer_id": "orcid:test",
                "affiliation": None,
                "identifier": None,
            },
            "decision": "accepted",
            "assessments": {
                "source_units": "agree",
                "relation_type": "agree",
                "variant_notes": "agree",
                "editorial_handling": "agree",
            },
            "reviewed_at": "2026-10-05T14:00:00Z",
            "notes": "synthetic test only",
            "proposed_changes": None,
            "evidence": core.evidence_for_alignment(alignment, indexes),
        }
        self.reviews.write_text(
            json.dumps(
                {
                    "version": 2,
                    "case_study_id": "case:test",
                    "promotion_policy": "test",
                    "reviews": [review],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.promotions.write_text(
            json.dumps(
                {
                    "version": 1,
                    "case_study_id": "case:test",
                    "policy_version": core.PROMOTION_POLICY_VERSION,
                    "promotions": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, script, *extra):
        common = [
            "--pali-units",
            str(self.pali),
            "--chinese-blocks",
            str(self.chinese),
            "--indic-units",
            str(self.indic),
            "--case-study",
            str(self.case),
        ]
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *common, *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_preview_then_write_then_established(self):
        result = self.run_script(
            "validate_human_reviews.py",
            "--reviews",
            str(self.reviews),
            "--require-fresh",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        promote_args = (
            "--reviews",
            str(self.reviews),
            "--promotions",
            str(self.promotions),
            "--alignment-id",
            "mw:test",
            "--review-id",
            "review:alice:mw-test:1",
            "--promoter-name",
            "Maintainer",
            "--promoter-id",
            "github:maintainer",
            "--promoted-at",
            "2026-10-05T15:00:00Z",
        )
        preview = self.run_script("promote_alignment.py", *promote_args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(
            json.loads(self.promotions.read_text(encoding="utf-8"))["promotions"],
            [],
        )

        written = self.run_script("promote_alignment.py", *promote_args, "--write")
        self.assertEqual(written.returncode, 0, written.stderr)
        promotion_doc = json.loads(self.promotions.read_text(encoding="utf-8"))
        self.assertEqual(len(promotion_doc["promotions"]), 1)

        validated = self.run_script(
            "validate_promotions.py",
            "--reviews",
            str(self.reviews),
            "--promotions",
            str(self.promotions),
            "--require-current-fresh",
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)

        built = self.run_script(
            "build_promotion_state.py",
            "--reviews",
            str(self.reviews),
            "--promotions",
            str(self.promotions),
            "--output",
            str(self.state),
        )
        self.assertEqual(built.returncode, 0, built.stderr)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["counts"], {"established": 1})
        self.assertEqual(state["alignments"][0]["derived_status"], "established")


if __name__ == "__main__":
    unittest.main()
