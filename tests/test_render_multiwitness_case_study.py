import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "render_case_study", ROOT / "scripts" / "render_multiwitness_case_study.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class RenderCaseStudyTests(unittest.TestCase):
    def test_supplied_markup_is_visible(self):
        value = "evaṃ mayā <supplied>ś</supplied>r<supplied>utam</supplied>"
        self.assertEqual(
            mod.render_sanskrit_edition(value),
            "evaṃ mayā ⟦ś⟧r⟦utam⟧",
        )


if __name__ == "__main__":
    unittest.main()
