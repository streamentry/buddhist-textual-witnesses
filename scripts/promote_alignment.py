#!/usr/bin/env python3
"""Prepare or explicitly append a human-reviewed alignment promotion event."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from review_promotion_core import (
    PROMOTION_POLICY_VERSION,
    PROMOTION_SCHEMA_VERSION,
    active_review_ids,
    build_source_indexes,
    evidence_digest,
    review_digest,
    review_is_promotion_eligible,
    validate_review_record,
)


def slug(value: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return out or "actor"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--promotions", type=Path, required=True)
    p.add_argument("--alignment-id", required=True)
    p.add_argument("--review-id", required=True)
    p.add_argument("--promoter-name", required=True)
    p.add_argument("--promoter-id", required=True)
    p.add_argument("--promoted-at", help="Offset-aware ISO-8601; defaults to current UTC")
    p.add_argument("--notes", default="")
    p.add_argument(
        "--write",
        action="store_true",
        help="Append to the promotions file. Without this flag, only print a preview.",
    )
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    review_doc = json.loads(args.reviews.read_text(encoding="utf-8"))
    promotion_doc = json.loads(args.promotions.read_text(encoding="utf-8"))
    indexes = build_source_indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    case_id = case["case_study_id"]
    alignments = {row["alignment_id"]: row for row in case.get("alignments", [])}
    reviews_by_id = {
        row["review_id"]: row for row in review_doc.get("reviews", []) if row.get("review_id")
    }

    if args.alignment_id not in alignments:
        print(f"ERROR: unknown alignment_id {args.alignment_id}", file=sys.stderr)
        return 1
    review = reviews_by_id.get(args.review_id)
    if review is None:
        print(f"ERROR: unknown review_id {args.review_id}", file=sys.stderr)
        return 1
    if review.get("alignment_id") != args.alignment_id:
        print("ERROR: review does not belong to requested alignment", file=sys.stderr)
        return 1
    if args.review_id not in active_review_ids(review_doc.get("reviews", [])):
        print(
            "ERROR: review has been superseded and cannot be used for a new promotion",
            file=sys.stderr,
        )
        return 1

    errors, fresh, reasons = validate_review_record(
        review, case_id, alignments, indexes, require_fresh=True
    )
    if errors or not review_is_promotion_eligible(review, fresh):
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if not fresh:
            print(
                "ERROR: source/alignment drift makes this review ineligible: "
                + ", ".join(reasons),
                file=sys.stderr,
            )
        elif not errors:
            print("ERROR: review is not promotion-eligible", file=sys.stderr)
        return 1

    for existing in promotion_doc.get("promotions", []):
        if (
            existing.get("alignment_id") == args.alignment_id
            and existing.get("review_id") == args.review_id
        ):
            print("ERROR: this alignment/review pair is already promoted", file=sys.stderr)
            return 1

    promoted_at = args.promoted_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    stamp = re.sub(r"[^0-9]", "", promoted_at)[:14]
    event = {
        "promotion_schema_version": PROMOTION_SCHEMA_VERSION,
        "promotion_id": f"promotion:{slug(args.promoter_id)}:{slug(args.alignment_id)}:{stamp}",
        "case_study_id": case_id,
        "alignment_id": args.alignment_id,
        "review_id": args.review_id,
        "review_digest": review_digest(review),
        "evidence_digest": evidence_digest(review),
        "decision": "established",
        "promoter": {
            "actor_type": "human",
            "name": args.promoter_name.strip(),
            "actor_id": args.promoter_id.strip(),
        },
        "promoted_at": promoted_at,
        "policy_version": PROMOTION_POLICY_VERSION,
        "notes": args.notes,
    }

    if not args.write:
        print(json.dumps({"mode": "preview", "event": event}, ensure_ascii=False, indent=2))
        return 0

    promotion_doc.setdefault("promotions", []).append(event)
    args.promotions.write_text(
        json.dumps(promotion_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"mode": "written", "event": event}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
