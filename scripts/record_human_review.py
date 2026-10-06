#!/usr/bin/env python3
"""Validate and append evidence-bound human reviews without editing the ledger by hand."""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from review_promotion_core import (
    build_source_indexes,
    review_is_promotion_eligible,
    validate_review_lineage,
    validate_review_record,
)


def load_review_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        reviews = payload
    elif isinstance(payload, dict) and isinstance(payload.get("reviews"), list):
        reviews = payload["reviews"]
    elif isinstance(payload, dict):
        reviews = [payload]
    else:
        raise ValueError("review input must be a review object, an array, or an object with reviews[]")

    if not reviews or not all(isinstance(review, dict) for review in reviews):
        raise ValueError("review input contains no review records")
    return reviews


def prepare_review_append(
    ledger: dict[str, Any],
    candidates: list[dict[str, Any]],
    case_id: str,
    alignments: dict[str, dict[str, Any]],
    indexes: dict[str, dict[str, dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if ledger.get("version") != 2:
        errors.append("review document version must be 2")
    if ledger.get("case_study_id") != case_id:
        errors.append("review document case_study_id does not match case study")
    if errors:
        return deepcopy(ledger), [], errors

    existing = ledger.get("reviews")
    if not isinstance(existing, list):
        return deepcopy(ledger), [], ["review document reviews must be an array"]

    next_ledger = deepcopy(ledger)
    next_reviews = next_ledger["reviews"]
    known_ids = {
        str(review.get("review_id"))
        for review in next_reviews
        if review.get("review_id")
    }
    summaries: list[dict[str, Any]] = []

    for review in candidates:
        rid = str(review.get("review_id") or "<missing-review>")
        if rid in known_ids:
            errors.append(f"duplicate review_id already present or repeated in input: {rid}")
            continue

        review_errors, fresh, stale_reasons = validate_review_record(
            review,
            case_id,
            alignments,
            indexes,
            require_fresh=True,
        )
        if review_errors:
            errors.extend(review_errors)
            continue

        trial = next_reviews + [deepcopy(review)]
        lineage_errors = validate_review_lineage(trial)
        if lineage_errors:
            errors.extend(lineage_errors)
            continue

        next_reviews.append(deepcopy(review))
        known_ids.add(rid)
        summaries.append(
            {
                "review_id": rid,
                "alignment_id": review.get("alignment_id"),
                "decision": review.get("decision"),
                "fresh": fresh,
                "stale_reasons": stale_reasons,
                "promotion_eligible": review_is_promotion_eligible(review, fresh),
            }
        )

    return next_ledger, summaries, errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review", type=Path, required=True, help="Review JSON prepared by the human-review UI")
    p.add_argument(
        "--reviews",
        type=Path,
        default=ROOT / "data/reviews/dn14-mahapadana/reviews.json",
        help="Append-only review ledger",
    )
    p.add_argument(
        "--case-study",
        type=Path,
        default=ROOT / "data/case-studies/dn14-mahapadana/alignments.json",
    )
    p.add_argument(
        "--pali-units",
        type=Path,
        default=ROOT / "generated/alignment-source/pali/units.jsonl",
    )
    p.add_argument(
        "--chinese-blocks",
        type=Path,
        default=ROOT / "generated/alignment-source/chinese/blocks.jsonl",
    )
    p.add_argument(
        "--indic-units",
        type=Path,
        default=ROOT / "generated/alignment-source/indic/units.jsonl",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="Append validated review records to the ledger. Without this flag the command is dry-run only.",
    )
    args = p.parse_args(argv)

    try:
        candidates = load_review_candidates(args.review)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    ledger = json.loads(args.reviews.read_text(encoding="utf-8"))
    indexes = build_source_indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    case_id = case["case_study_id"]
    alignments = {row["alignment_id"]: row for row in case.get("alignments", [])}

    updated, summaries, errors = prepare_review_append(
        ledger,
        candidates,
        case_id,
        alignments,
        indexes,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    result = {
        "mode": "write" if args.write else "dry_run",
        "case_study": case_id,
        "submitted_review_count": len(candidates),
        "validated_review_count": len(summaries),
        "ledger_review_count_before": len(ledger.get("reviews", [])),
        "ledger_review_count_after": len(updated.get("reviews", [])),
        "reviews": summaries,
        "auto_promotions": 0,
    }

    if args.write:
        args.reviews.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result["written_to"] = str(args.reviews)
    else:
        result["next_step"] = "Re-run the same command with --write after inspecting this validation result."

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
