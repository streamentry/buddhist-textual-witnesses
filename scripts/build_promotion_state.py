#!/usr/bin/env python3
"""Build the derived current state and audit chain for alignment promotions."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from review_promotion_core import (
    PROMOTION_POLICY_VERSION,
    REVIEW_SCHEMA_VERSION,
    build_source_indexes,
    derived_alignment_status,
    validate_promotion_record,
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
    p.add_argument("--promotions", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    review_doc = json.loads(args.reviews.read_text(encoding="utf-8"))
    promotion_doc = json.loads(args.promotions.read_text(encoding="utf-8"))
    reviews = review_doc.get("reviews", [])
    promotions = promotion_doc.get("promotions", [])
    indexes = build_source_indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    case_id = case["case_study_id"]
    alignments = {row["alignment_id"]: row for row in case.get("alignments", [])}
    reviews_by_id = {
        row["review_id"]: row for row in reviews if row.get("review_id")
    }

    errors: list[str] = []
    if review_doc.get("version") != 2:
        errors.append("review document version must be 2")
    if review_doc.get("case_study_id") != case_id:
        errors.append("review document case_study_id does not match case study")
    if promotion_doc.get("version") != 1:
        errors.append("promotion document version must be 1")
    if promotion_doc.get("case_study_id") != case_id:
        errors.append("promotion document case_study_id does not match case study")
    if promotion_doc.get("policy_version") != PROMOTION_POLICY_VERSION:
        errors.append("promotion document policy_version mismatch")

    errors.extend(validate_review_lineage(reviews))
    for review in reviews:
        review_errors, _, _ = validate_review_record(
            review, case_id, alignments, indexes, require_fresh=False
        )
        errors.extend(review_errors)

    seen_promotion_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for promotion in promotions:
        pid = str(promotion.get("promotion_id") or "")
        if not pid:
            errors.append("promotion missing promotion_id")
            continue
        if pid in seen_promotion_ids:
            errors.append(f"duplicate promotion_id: {pid}")
        seen_promotion_ids.add(pid)

        pair = (
            str(promotion.get("alignment_id") or ""),
            str(promotion.get("review_id") or ""),
        )
        if pair in seen_pairs:
            errors.append(
                f"{pid}: duplicate promotion for the same alignment/review pair"
            )
        seen_pairs.add(pair)

        promotion_errors, _ = validate_promotion_record(
            promotion,
            case_id,
            alignments,
            reviews_by_id,
            indexes,
            require_current_fresh=False,
        )
        errors.extend(promotion_errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

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
        "policy_version": PROMOTION_POLICY_VERSION,
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "derivation": (
            "Current status is derived from immutable review evidence plus explicit "
            "promotion events; case-study rows are never mutated to established."
        ),
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
