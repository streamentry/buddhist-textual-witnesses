import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "append_only", ROOT / "scripts" / "validate_append_only_ledger.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class AppendOnlyLedgerTests(unittest.TestCase):
    def test_append_is_allowed(self):
        base = {"reviews": [{"review_id": "r1", "decision": "accepted"}]}
        current = {
            "reviews": [
                {"review_id": "r1", "decision": "accepted"},
                {"review_id": "r2", "decision": "rejected"},
            ]
        }
        self.assertEqual(
            mod.validate_append_only(base, current, "reviews", "review_id"), []
        )

    def test_rewrite_is_rejected(self):
        base = {"reviews": [{"review_id": "r1", "decision": "accepted"}]}
        current = {"reviews": [{"review_id": "r1", "decision": "rejected"}]}
        errors = mod.validate_append_only(base, current, "reviews", "review_id")
        self.assertTrue(any("changed in place" in error for error in errors))

    def test_deletion_is_rejected(self):
        base = {"promotions": [{"promotion_id": "p1"}]}
        current = {"promotions": []}
        errors = mod.validate_append_only(
            base, current, "promotions", "promotion_id"
        )
        self.assertTrue(any("fewer records" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
