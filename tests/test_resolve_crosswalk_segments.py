import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "resolve_crosswalk_segments.py"
spec = importlib.util.spec_from_file_location("resolver", MODULE_PATH)
resolver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = resolver
assert spec.loader is not None
spec.loader.exec_module(resolver)


def row(canonical_id):
    return {
        "canonical_id": canonical_id,
        "container_id": "T0099",
        "title": None,
        "head_text": None,
        "hierarchy": [],
        "source": {
            "project": "CBETA XML-P5 / Taishō",
            "path": "x",
            "revision": "a" * 40,
            "url": "https://example.invalid/x",
        },
        "locator": {
            "xpath": "x",
            "segment_ordinal": 1,
            "start_lb": "a",
            "end_lb": "b",
            "start_ref": "s",
            "end_ref": "e",
            "start_juan": "1",
            "end_juan": "1",
            "xml_sha256": "h",
            "normalized_text_sha256": "t",
            "normalized_text_chars": 1,
        },
        "_catalog_file": "sa.jsonl",
        "_catalog_line": 1,
    }


class ResolveCrosswalkTests(unittest.TestCase):
    def test_exact_and_range_resolution(self):
        segments = {
            f"SA {number}": row(f"SA {number}")
            for number in range(154, 164)
        }
        ids, missing = resolver.expand_id("SA 154–163", segments)
        self.assertEqual(len(ids), 10)
        self.assertEqual(missing, [])

        ids, missing = resolver.expand_id("SA 154", segments)
        self.assertEqual(ids, ["SA 154"])
        self.assertEqual(missing, [])

    def test_only_collection_ids_are_annotated(self):
        segments = {"DA 21": row("DA 21")}
        data = {
            "crosswalks": [
                {
                    "full_parallels": {
                        "chinese": [
                            {"canonical_id": "DA 21"},
                            {"canonical_id": "T 21"},
                        ]
                    },
                    "partial_parallels": [],
                }
            ]
        }
        out, errors, counts = resolver.resolve(
            data, segments, strict=True
        )
        self.assertEqual(errors, [])
        self.assertEqual(counts["resolved_witnesses"], 1)
        self.assertIn(
            "local_resolution",
            out["crosswalks"][0]["full_parallels"]["chinese"][0],
        )
        self.assertNotIn(
            "local_resolution",
            out["crosswalks"][0]["full_parallels"]["chinese"][1],
        )


if __name__ == "__main__":
    unittest.main()
