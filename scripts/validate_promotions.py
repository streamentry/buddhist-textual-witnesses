#!/usr/bin/env python3
"""Validate explicit human-review promotions and derive established state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from review_evidence import alignment_evidence_digest, build_source_index

POLICY_VERSION = "human-review-promotion-v1"


def validate_promotions(
    case: dict[str, Any],
    reviews_doc: dict[str, Any],
    promotions_doc: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    case_id = case["case_study_id"]
    alignments = {
        row["alignment_id"]: row for row in case.get("alignments", [])
    }
    reviews = {
        row["review_id"]: row for row in reviews_doc.get("reviews", [])
        if row.get("review_id")
    }

    if promotions_doc.get("case_study_id") != case_id:
        errors.append("promotion document case_study_id does not match case study")
    if promotions_doc.get("policy_version") != POLICY_VERSION:
        errors.append(f"promotion policy_version must be {POLICY_VERSION}")

    seen_promotions: set[str] = set()
    promoted_alignments: set[str] = set()
    established: list[str] = []

    for promotion in promotions_doc.get("promotions", []):
        pid = str(promotion.get("promotion_id") or "")
        aid = str(promotion.get("alignment_id") or "")
        if not pid:
            errors.append("promotion missing promotion_id")
            continue
        if pid in seen_promotions:
            errors.append(f"duplicate promotion_id: {pid}")
        seen_promotions.add(pid)

        alignment = alignments.get(aid)
        if alignment is None:
            errors.append(f"{pid}: unknown alignment_id {aid}")
            continue
        if aid in promoted_alignments:
            errors.append(f"{pid}: alignment already has an active promotion")
        promoted_alignments.add(aid)

        if promotion.get("case_study_id") != case_id:
            errors.append(f"{pid}: wrong case_study_id")
        if promotion.get("target_status") != "established":
            errors.append(f"{pid}: target_status must be established")
        if promotion.get("policy_version") != POLICY_VERSION:
            errors.append(f"{pid}: wrong policy_version")

        actor = promotion.get("promoted_by") or {}
        if actor.get("actor_type") != "human":
            errors.append(f"{pid}: promoted_by.actor_type must be human")
        if not str(actor.get("name") or "").strip():
            errors.append(f"{pid}: promoted_by.name is required")
        promoted_on = str(promotion.get("promoted_on") or "")
        if len(promoted_on) < 10 or promoted_on == "YYYY-MM-DD":
            errors.append(f"{pid}: promoted_on must be a real date")

        review_ids = promotion.get("review_ids") or []
        if not review_ids:
            errors.append(f"{pid}: at least one human review_id is required")
            continue

        current_digest = alignment_evidence_digest(
            case_id, alignment, source_index
        )
        if promotion.get("evidence_digest") != current_digest:
            errors.append(
                f"{pid}: evidence_digest is stale or does not match current sources"
            )

        for rid in review_ids:
            review = reviews.get(rid)
            if review is None:
                errors.append(f"{pid}: unknown review_id {rid}")
                continue
            if review.get("alignment_id") != aid:
                errors.append(f"{pid}: review {rid} belongs to another alignment")
            if (review.get("reviewer") or {}).get("reviewer_type") != "human":
                errors.append(f"{pid}: review {rid} is not human")
            if review.get("decision") != "accepted":
                errors.append(f"{pid}: review {rid} is not accepted")
            snapshot = review.get("evidence_snapshot") or {}
            if snapshot.get("digest") != current_digest:
                errors.append(
                    f"{pid}: review {rid} evidence is stale or missing"
                )

        if not any(error.startswith(f"{pid}:") for error in errors):
            established.append(aid)

    summary = {
        "case_study": case_id,
        "promotion_count": len(promotions_doc.get("promotions", [])),
        "established_count": len(established),
        "established_alignment_ids": established,
        "derived_state_only": True,
        "case_study_mutated": False,
    }
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--promotions", type=Path, required=True)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    args = p.parse_args(argv)

    case = json.loads(args.case_study.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    promotions = json.loads(args.promotions.read_text(encoding="utf-8"))
    source_index = build_source_index(
        args.pali_units, args.chinese_blocks, args.indic_units
    )
    errors, summary = validate_promotions(
        case, reviews, promotions, source_index
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
