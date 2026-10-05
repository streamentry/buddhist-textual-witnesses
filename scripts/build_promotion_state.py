#!/usr/bin/env python3
"""Build the derived current state and audit chain for alignment promotions."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from review_promotion_core import build_source_indexes, derived_alignment_status


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--promotions", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8")).get("reviews", [])
    promotions = json.loads(args.promotions.read_text(encoding="utf-8")).get("promotions", [])
    indexes = build_source_indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    case_id = case["case_study_id"]
    alignments = {row["alignment_id"]: row for row in case.get("alignments", [])}

    states = [
        derived_alignment_status(
            alignment_id,
            reviews,
            promotions,
            case_id,
            alignments,
            indexes,
        )
        for alignment_id in alignments
    ]
    counts = Counter(row["derived_status"] for row in states)
    output = {
        "version": 1,
        "case_study_id": case_id,
        "derivation": "Current status is derived from immutable review evidence plus explicit promotion events; case-study rows are never mutated to established.",
        "counts": dict(sorted(counts.items())),
        "alignments": states,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "counts": output["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
