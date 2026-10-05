#!/usr/bin/env python3
"""Validate human reviews against a curated multi-witness case study."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DECISIONS = {"accepted", "rejected", "needs_work"}
ASSESSMENTS = {"agree", "revise", "uncertain"}


def validate_review(
    review: dict[str, Any],
    case_study_id: str,
    alignment_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    rid = review.get("review_id", "<missing-review>")

    if review.get("case_study_id") != case_study_id:
        errors.append(f"{rid}: wrong case_study_id")

    alignment_id = review.get("alignment_id")
    if alignment_id not in alignment_ids:
        errors.append(f"{rid}: unknown alignment_id {alignment_id}")

    reviewer = review.get("reviewer") or {}
    if reviewer.get("reviewer_type") != "human":
        errors.append(f"{rid}: reviewer_type must be human")
    if not str(reviewer.get("name") or "").strip():
        errors.append(f"{rid}: reviewer name is required")

    if review.get("decision") not in DECISIONS:
        errors.append(f"{rid}: invalid decision {review.get('decision')}")

    assessments = review.get("assessments") or {}
    for key in (
        "source_units",
        "relation_type",
        "variant_notes",
        "editorial_handling",
    ):
        if assessments.get(key) not in ASSESSMENTS:
            errors.append(
                f"{rid}: assessment {key} must be agree/revise/uncertain"
            )

    reviewed_on = str(review.get("reviewed_on") or "")
    if len(reviewed_on) < 10 or reviewed_on == "YYYY-MM-DD":
        errors.append(f"{rid}: reviewed_on must be a real date")

    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    doc = json.loads(args.reviews.read_text(encoding="utf-8"))
    case_id = case["case_study_id"]
    alignment_ids = {
        row["alignment_id"] for row in case.get("alignments", [])
    }

    errors: list[str] = []
    if doc.get("case_study_id") != case_id:
        errors.append("review document case_study_id does not match case study")

    seen_review_ids: set[str] = set()
    seen_reviewer_alignment: set[tuple[str, str]] = set()
    accepted = 0

    for review in doc.get("reviews", []):
        rid = review.get("review_id")
        if not rid:
            errors.append("review missing review_id")
            continue
        if rid in seen_review_ids:
            errors.append(f"duplicate review_id: {rid}")
        seen_review_ids.add(rid)

        reviewer = review.get("reviewer") or {}
        reviewer_key = str(
            reviewer.get("identifier") or reviewer.get("name") or ""
        )
        pair = (reviewer_key, str(review.get("alignment_id")))
        if pair in seen_reviewer_alignment:
            errors.append(
                f"{rid}: same reviewer has duplicate review for alignment"
            )
        seen_reviewer_alignment.add(pair)

        errors.extend(validate_review(review, case_id, alignment_ids))
        if review.get("decision") == "accepted":
            accepted += 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "case_study": case_id,
                "alignment_count": len(alignment_ids),
                "human_review_count": len(doc.get("reviews", [])),
                "accepted_review_count": accepted,
                "auto_promotions": 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
