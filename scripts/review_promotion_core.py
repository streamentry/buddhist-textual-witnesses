#!/usr/bin/env python3
"""Shared primitives for human review evidence and explicit promotion events."""
from __future__ import annotations

import hashlib
import html
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

HASH_PREFIX = "sha256:"
PROMOTION_POLICY_VERSION = "human-review-promotion-v1"
REVIEW_SCHEMA_VERSION = 2
PROMOTION_SCHEMA_VERSION = 1
DECISIONS = {"accepted", "rejected", "needs_work"}
ASSESSMENTS = {"agree", "revise", "uncertain"}
ASSESSMENT_KEYS = (
    "source_units",
    "relation_type",
    "variant_notes",
    "editorial_handling",
)
SUPPLIED_RE = re.compile(r"<supplied>(.*?)</supplied>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return HASH_PREFIX + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_source_indexes(
    pali_path: Path,
    chinese_path: Path,
    indic_path: Path,
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "pli": {row["unit_id"]: row for row in load_jsonl(pali_path)},
        "lzh": {row["block_id"]: row for row in load_jsonl(chinese_path)},
        "san": {row["unit_id"]: row for row in load_jsonl(indic_path)},
    }


def clean_text(value: str) -> str:
    return html.unescape(" ".join(TAG_RE.sub("", value).split()))


def render_sanskrit_html(value: str) -> str:
    out: list[str] = []
    cursor = 0
    for match in SUPPLIED_RE.finditer(value):
        before = clean_text(value[cursor : match.start()])
        supplied = clean_text(match.group(1))
        if before:
            out.append(html.escape(before))
        out.append(
            '<span class="supplied" title="Editorially supplied in the upstream edition">'
            + html.escape(supplied)
            + "</span>"
        )
        cursor = match.end()
    tail = clean_text(value[cursor:])
    if tail:
        out.append(html.escape(tail))
    return " ".join(part for part in out if part)


def row_text_html(row: dict[str, Any]) -> str:
    if row.get("language") == "san":
        return render_sanskrit_html(str(row.get("edition_text", "")))
    value = row.get("text") or row.get("search_text") or ""
    return html.escape(" ".join(str(value).split()))


def source_meta(row: dict[str, Any]) -> dict[str, Any]:
    source = row.get("source") or {}
    locator = row.get("locator") or row.get("discourse_locator") or {}
    urls: list[str] = []
    for key in ("root_url", "html_url", "url"):
        value = source.get(key)
        if value and value not in urls:
            urls.append(value)
    return {
        "project": source.get("project"),
        "revision": source.get("revision"),
        "path": source.get("path") or source.get("root_path"),
        "start_ref": locator.get("start_ref"),
        "end_ref": locator.get("end_ref"),
        "urls": urls,
    }


def review_source_view(row: dict[str, Any], source_id: str) -> dict[str, Any]:
    """The exact source projection shown to a reviewer and bound into a review."""
    return {
        "source_id": source_id,
        "text_html": row_text_html(row),
        "meta": source_meta(row),
    }


def alignment_claim_payload(alignment: dict[str, Any]) -> dict[str, Any]:
    """Epistemically relevant claim, excluding mutable workflow/review state."""
    payload = {
        key: deepcopy(value)
        for key, value in alignment.items()
        if key not in {"status", "review", "existing_reviews"}
    }
    payload["members"] = [
        {key: deepcopy(value) for key, value in member.items() if key != "units"}
        for member in alignment.get("members", [])
    ]
    return payload


def evidence_for_alignment(
    alignment: dict[str, Any],
    indexes: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    source_units: list[dict[str, Any]] = []
    for member in alignment.get("members", []):
        language = member["language"]
        for source_id in member.get("source_unit_ids", []):
            row = indexes[language][source_id]
            source_units.append(
                {
                    "language": language,
                    "witness_id": member["witness_id"],
                    "source_unit_id": source_id,
                    "digest": digest(review_source_view(row, source_id)),
                }
            )
    return {
        "evidence_version": 1,
        "alignment_claim_digest": digest(alignment_claim_payload(alignment)),
        "source_units": source_units,
    }


def parse_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_review_record(
    review: dict[str, Any],
    case_study_id: str,
    alignments: dict[str, dict[str, Any]],
    indexes: dict[str, dict[str, dict[str, Any]]],
    *,
    require_fresh: bool = False,
) -> tuple[list[str], bool, list[str]]:
    errors: list[str] = []
    stale_reasons: list[str] = []
    rid = str(review.get("review_id") or "<missing-review>")

    if review.get("review_schema_version") != REVIEW_SCHEMA_VERSION:
        errors.append(f"{rid}: review_schema_version must be {REVIEW_SCHEMA_VERSION}")
    if review.get("case_study_id") != case_study_id:
        errors.append(f"{rid}: wrong case_study_id")

    alignment_id = review.get("alignment_id")
    alignment = alignments.get(str(alignment_id))
    if alignment is None:
        errors.append(f"{rid}: unknown alignment_id {alignment_id}")

    reviewer = review.get("reviewer") or {}
    if reviewer.get("reviewer_type") != "human":
        errors.append(f"{rid}: reviewer_type must be human")
    if not str(reviewer.get("name") or "").strip():
        errors.append(f"{rid}: reviewer name is required")
    if not str(reviewer.get("reviewer_id") or "").strip():
        errors.append(f"{rid}: stable reviewer_id is required")

    decision = review.get("decision")
    if decision not in DECISIONS:
        errors.append(f"{rid}: invalid decision {decision}")

    assessments = review.get("assessments") or {}
    for key in ASSESSMENT_KEYS:
        if assessments.get(key) not in ASSESSMENTS:
            errors.append(f"{rid}: assessment {key} must be agree/revise/uncertain")

    if decision == "accepted" and any(assessments.get(k) != "agree" for k in ASSESSMENT_KEYS):
        errors.append(f"{rid}: accepted review requires all assessments=agree")

    if not parse_timestamp(review.get("reviewed_at")):
        errors.append(f"{rid}: reviewed_at must be an offset-aware ISO-8601 timestamp")

    evidence = review.get("evidence")
    if not isinstance(evidence, dict):
        errors.append(f"{rid}: evidence snapshot is required")
        fresh = False
    elif alignment is None:
        fresh = False
    else:
        try:
            expected = evidence_for_alignment(alignment, indexes)
        except KeyError as exc:
            errors.append(f"{rid}: unresolved source unit while computing evidence: {exc}")
            fresh = False
        else:
            fresh = evidence == expected
            if not fresh:
                if evidence.get("alignment_claim_digest") != expected.get("alignment_claim_digest"):
                    stale_reasons.append("alignment_claim_digest_changed")
                actual_units = evidence.get("source_units")
                if actual_units != expected.get("source_units"):
                    stale_reasons.append("source_unit_evidence_changed")
                if not stale_reasons:
                    stale_reasons.append("evidence_snapshot_changed")

    if require_fresh and not fresh:
        errors.append(f"{rid}: stale review evidence ({', '.join(stale_reasons) or 'unknown drift'})")

    return errors, fresh, stale_reasons


def review_is_promotion_eligible(review: dict[str, Any], fresh: bool) -> bool:
    reviewer = review.get("reviewer") or {}
    assessments = review.get("assessments") or {}
    return (
        fresh
        and review.get("review_schema_version") == REVIEW_SCHEMA_VERSION
        and review.get("decision") == "accepted"
        and reviewer.get("reviewer_type") == "human"
        and bool(str(reviewer.get("name") or "").strip())
        and bool(str(reviewer.get("reviewer_id") or "").strip())
        and all(assessments.get(key) == "agree" for key in ASSESSMENT_KEYS)
    )


def review_digest(review: dict[str, Any]) -> str:
    return digest(review)


def evidence_digest(review: dict[str, Any]) -> str:
    return digest(review.get("evidence"))


def validate_promotion_record(
    promotion: dict[str, Any],
    case_study_id: str,
    alignments: dict[str, dict[str, Any]],
    reviews_by_id: dict[str, dict[str, Any]],
    indexes: dict[str, dict[str, dict[str, Any]]],
    *,
    require_current_fresh: bool = False,
) -> tuple[list[str], bool]:
    errors: list[str] = []
    pid = str(promotion.get("promotion_id") or "<missing-promotion>")

    if promotion.get("promotion_schema_version") != PROMOTION_SCHEMA_VERSION:
        errors.append(f"{pid}: promotion_schema_version must be {PROMOTION_SCHEMA_VERSION}")
    if promotion.get("policy_version") != PROMOTION_POLICY_VERSION:
        errors.append(f"{pid}: unsupported policy_version {promotion.get('policy_version')}")
    if promotion.get("case_study_id") != case_study_id:
        errors.append(f"{pid}: wrong case_study_id")
    if promotion.get("decision") != "established":
        errors.append(f"{pid}: decision must be established")
    if not parse_timestamp(promotion.get("promoted_at")):
        errors.append(f"{pid}: promoted_at must be an offset-aware ISO-8601 timestamp")

    promoter = promotion.get("promoter") or {}
    if promoter.get("actor_type") != "human":
        errors.append(f"{pid}: promoter actor_type must be human")
    if not str(promoter.get("name") or "").strip():
        errors.append(f"{pid}: promoter name is required")
    if not str(promoter.get("actor_id") or "").strip():
        errors.append(f"{pid}: stable promoter actor_id is required")

    alignment_id = str(promotion.get("alignment_id") or "")
    if alignment_id not in alignments:
        errors.append(f"{pid}: unknown alignment_id {alignment_id}")

    review_id = str(promotion.get("review_id") or "")
    review = reviews_by_id.get(review_id)
    if review is None:
        errors.append(f"{pid}: unknown review_id {review_id}")
        return errors, False

    if review.get("alignment_id") != alignment_id:
        errors.append(f"{pid}: review alignment_id does not match promotion")
    if promotion.get("review_digest") != review_digest(review):
        errors.append(f"{pid}: review_digest does not bind the exact current review record")
    if promotion.get("evidence_digest") != evidence_digest(review):
        errors.append(f"{pid}: evidence_digest does not bind the exact review evidence")

    review_errors, fresh, _ = validate_review_record(
        review,
        case_study_id,
        alignments,
        indexes,
        require_fresh=False,
    )
    if review_errors:
        errors.extend(f"{pid}: referenced review invalid: {err}" for err in review_errors)
    if not review_is_promotion_eligible(review, True):
        errors.append(f"{pid}: referenced review is not an accepted human review eligible for promotion")
    elif require_current_fresh and not fresh:
        errors.append(f"{pid}: referenced review is not currently promotion-eligible because its evidence is stale")
    return errors, fresh


def derived_alignment_status(
    alignment_id: str,
    reviews: list[dict[str, Any]],
    promotions: list[dict[str, Any]],
    case_study_id: str,
    alignments: dict[str, dict[str, Any]],
    indexes: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    reviews_by_id = {str(r.get("review_id")): r for r in reviews if r.get("review_id")}
    matching_reviews = [r for r in reviews if r.get("alignment_id") == alignment_id]
    fresh_eligible: list[str] = []
    stale_accepted: list[str] = []
    for review in matching_reviews:
        errors, fresh, _ = validate_review_record(
            review, case_study_id, alignments, indexes, require_fresh=False
        )
        if errors:
            continue
        if review_is_promotion_eligible(review, fresh):
            fresh_eligible.append(review["review_id"])
        elif review.get("decision") == "accepted" and not fresh:
            stale_accepted.append(review["review_id"])

    valid_promotions: list[tuple[str, bool]] = []
    for promotion in promotions:
        if promotion.get("alignment_id") != alignment_id:
            continue
        errors, fresh = validate_promotion_record(
            promotion,
            case_study_id,
            alignments,
            reviews_by_id,
            indexes,
            require_current_fresh=False,
        )
        if not errors:
            valid_promotions.append((promotion["promotion_id"], fresh))

    if any(fresh for _, fresh in valid_promotions):
        status = "established"
    elif valid_promotions:
        status = "review_stale"
    elif fresh_eligible:
        status = "promotion_required"
    elif stale_accepted:
        status = "review_stale"
    else:
        status = "model_reviewed"

    return {
        "alignment_id": alignment_id,
        "derived_status": status,
        "fresh_accepted_review_ids": fresh_eligible,
        "stale_accepted_review_ids": stale_accepted,
        "valid_promotion_ids": [pid for pid, _ in valid_promotions],
    }
