#!/usr/bin/env python3
"""Build a human-review packet for the DN14 multi-witness case study."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "case_renderer", HERE / "render_multiwitness_case_study.py"
)
RENDERER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RENDERER
assert SPEC.loader is not None
SPEC.loader.exec_module(RENDERER)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    idx = RENDERER.indexes(
        args.pali_units, args.chinese_blocks, args.indic_units
    )
    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    reviews_by_alignment = {}
    for review in reviews.get("reviews", []):
        reviews_by_alignment.setdefault(
            review["alignment_id"], []
        ).append(review)

    lines = [
        f"# Human review packet: {case['title']}",
        "",
        "This packet is a review surface, not a scholarly verdict.",
        "Model-reviewed alignments remain non-established until an evidence-bound human review and a separate explicit promotion are recorded.",
        "",
        "## Review protocol",
        "",
        "For each alignment, check four things:",
        "1. Are the cited source-unit boundaries correct?",
        "2. Is the relation type appropriate?",
        "3. Are the variant notes accurate and non-harmonizing?",
        "4. Is editorial reconstruction/textual loss handled transparently?",
        "",
        "Prefer the offline review UI to prepare machine-readable schema-v2 JSON because it binds the exact displayed evidence. Commit decisions to data/reviews/dn14-mahapadana/reviews.json; accepted review still does not establish an alignment.",
        "",
    ]

    for number, alignment in enumerate(case["alignments"], 1):
        lines += [
            f"## {number}. {alignment['scope'].replace('_', ' ').title()}",
            "",
            f"Alignment ID: {alignment['alignment_id']}",
            f"Model relation: {alignment['relation_type']}",
            f"Model confidence: {alignment['review']['confidence']}",
            "",
        ]

        for member in alignment["members"]:
            lines += [
                f"### {member['witness_id']} · {member['language']} · {member['coverage']}",
                "",
                "Units: " + ", ".join(member["source_unit_ids"]),
                "",
            ]
            text_parts = [
                RENDERER.source_text(idx[source_id])
                for source_id in member["source_unit_ids"]
            ]
            lines.append("> " + " ".join(text_parts).replace("\n", " "))
            if member.get("notes"):
                lines += ["", "Model note: " + member["notes"]]
            lines.append("")

        if alignment.get("variants"):
            lines += ["### Model variant claims", ""]
            for variant in alignment["variants"]:
                lines.append(
                    f"- {variant['type']}: {variant['statement']}"
                )
            lines.append("")

        existing = reviews_by_alignment.get(alignment["alignment_id"], [])
        lines += ["### Human review worksheet", ""]
        if existing:
            for review in existing:
                lines.append(
                    f"- Existing review {review['review_id']}: "
                    f"{review['decision']} by {review['reviewer']['name']}"
                )
            lines.append("")
        lines += [
            "- [ ] source units: agree / revise / uncertain",
            "- [ ] relation type: agree / revise / uncertain",
            "- [ ] variant notes: agree / revise / uncertain",
            "- [ ] editorial handling: agree / revise / uncertain",
            "",
            "Decision: accepted / rejected / needs_work",
            "",
            "Reviewer:",
            "",
            "Stable reviewer ID (required):",
            "",
            "Affiliation / identifier:",
            "",
            "Notes / proposed changes:",
            "",
            "---",
            "",
        ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "case_study": case["case_study_id"],
                "alignments": len(case["alignments"]),
                "existing_human_reviews": len(reviews.get("reviews", [])),
                "output": str(args.output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
