#!/usr/bin/env python3
"""Validate human review records and report current evidence freshness."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from review_promotion_core import (
    build_source_indexes,
    validate_review_lineage,
    validate_review_record,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--require-fresh", action="store_true")
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    doc = json.loads(args.reviews.read_text(encoding="utf-8"))
    indexes = build_source_indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    case_id = case["case_study_id"]
    alignments = {row["alignment_id"]: row for row in case.get("alignments", [])}

    errors: list[str] = []
    if doc.get("case_study_id") != case_id:
        errors.append("review document case_study_id does not match case study")
    if doc.get("version") != 2:
        errors.append("review document version must be 2")

    seen_review_ids: set[str] = set()
    accepted = 0
    fresh_accepted = 0
    stale_accepted = 0

    for review in doc.get("reviews", []):
        rid = review.get("review_id")
        if not rid:
            errors.append("review missing review_id")
            continue
        if rid in seen_review_ids:
            errors.append(f"duplicate review_id: {rid}")
        seen_review_ids.add(rid)

        review_errors, fresh, _ = validate_review_record(
            review,
            case_id,
            alignments,
            indexes,
            require_fresh=args.require_fresh,
        )
        errors.extend(review_errors)
        if review.get("decision") == "accepted":
            accepted += 1
            if fresh:
                fresh_accepted += 1
            else:
                stale_accepted += 1

    errors.extend(validate_review_lineage(doc.get("reviews", [])))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "case_study": case_id,
                "alignment_count": len(alignments),
                "human_review_count": len(doc.get("reviews", [])),
                "accepted_review_count": accepted,
                "fresh_accepted_review_count": fresh_accepted,
                "stale_accepted_review_count": stale_accepted,
                "auto_promotions": 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
