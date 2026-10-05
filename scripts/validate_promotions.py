#!/usr/bin/env python3
"""Validate explicit promotion events without erasing historical stale states."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from review_promotion_core import (
    PROMOTION_POLICY_VERSION,
    active_review_ids,
    build_source_indexes,
    validate_promotion_record,
    validate_review_lineage,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--promotions", type=Path, required=True)
    p.add_argument("--require-current-fresh", action="store_true")
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    review_doc = json.loads(args.reviews.read_text(encoding="utf-8"))
    promotion_doc = json.loads(args.promotions.read_text(encoding="utf-8"))
    indexes = build_source_indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    case_id = case["case_study_id"]
    alignments = {row["alignment_id"]: row for row in case.get("alignments", [])}
    review_rows = review_doc.get("reviews", [])
    reviews_by_id = {
        row["review_id"]: row for row in review_rows if row.get("review_id")
    }
    active_ids = active_review_ids(review_rows)

    errors: list[str] = []
    errors.extend(validate_review_lineage(review_rows))
    if promotion_doc.get("version") != 1:
        errors.append("promotion document version must be 1")
    if promotion_doc.get("case_study_id") != case_id:
        errors.append("promotion document case_study_id does not match case study")
    if promotion_doc.get("policy_version") != PROMOTION_POLICY_VERSION:
        errors.append("promotion document policy_version mismatch")

    seen_ids: set[str] = set()
    seen_review_promotions: set[tuple[str, str]] = set()
    current_fresh = 0
    historical_stale = 0
    for promotion in promotion_doc.get("promotions", []):
        pid = promotion.get("promotion_id")
        if not pid:
            errors.append("promotion missing promotion_id")
            continue
        if pid in seen_ids:
            errors.append(f"duplicate promotion_id: {pid}")
        seen_ids.add(pid)

        pair = (str(promotion.get("alignment_id")), str(promotion.get("review_id")))
        if pair in seen_review_promotions:
            errors.append(
                f"{pid}: duplicate promotion for the same alignment/review pair"
            )
        seen_review_promotions.add(pair)

        promotion_errors, fresh = validate_promotion_record(
            promotion,
            case_id,
            alignments,
            reviews_by_id,
            indexes,
            require_current_fresh=args.require_current_fresh,
        )
        errors.extend(promotion_errors)
        is_current = fresh and str(promotion.get("review_id") or "") in active_ids
        if args.require_current_fresh and not is_current:
            errors.append(
                f"{pid}: referenced review is stale or superseded for current promotion"
            )
        if is_current:
            current_fresh += 1
        else:
            historical_stale += 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "case_study": case_id,
                "promotion_count": len(promotion_doc.get("promotions", [])),
                "current_fresh_promotion_count": current_fresh,
                "historical_stale_promotion_count": historical_stale,
                "policy_version": PROMOTION_POLICY_VERSION,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
