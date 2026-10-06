#!/usr/bin/env python3
"""Validate multi-witness case-study alignments and their source-unit references."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def source_indexes(
    pali_path: Path,
    chinese_path: Path,
    indic_path: Path,
) -> dict[str, dict[str, dict[str, Any]]]:
    pali = {row["unit_id"]: row for row in load_jsonl(pali_path)}
    chinese = {row["block_id"]: row for row in load_jsonl(chinese_path)}
    indic = {row["unit_id"]: row for row in load_jsonl(indic_path)}
    return {"pli": pali, "lzh": chinese, "san": indic}


def source_editorial_features(source: dict[str, Any]) -> set[str]:
    features: set[str] = set()
    markup = source.get("editorial_markup") or {}
    summary = source.get("editorial_summary") or {}
    if markup.get("has_supplied") or summary.get("segments_with_supplied", 0):
        features.add("supplied")
    if markup.get("has_gap") or summary.get("segments_with_gap", 0):
        features.add("gap")
    if markup.get("has_unclear") or summary.get("segments_with_unclear", 0):
        features.add("unclear")
    return features


def validate_alignment(
    row: dict[str, Any],
    indexes: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    errors = []
    aid = row.get("alignment_id", "<missing>")
    members = row.get("members") or []
    if len(members) < 2:
        errors.append(f"{aid}: fewer than two members")
        return errors

    member_ids = [member.get("member_id") for member in members]
    if len(set(member_ids)) != len(member_ids):
        errors.append(f"{aid}: duplicate member_id")

    languages = set()
    for member in members:
        mid = member.get("member_id", "<missing-member>")
        language = member.get("language")
        languages.add(language)
        if language not in indexes:
            errors.append(f"{aid}/{mid}: unsupported language {language}")
            continue
        source_ids = member.get("source_unit_ids")
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(f"{aid}/{mid}: source_unit_ids must be non-empty")
            continue
        resolved_sources = []
        for source_id in source_ids:
            if source_id not in indexes[language]:
                errors.append(
                    f"{aid}/{mid}: unresolved {language} source unit {source_id}"
                )
                continue
            source = indexes[language][source_id]
            resolved_sources.append(source)
            expected_witness = member.get("witness_id")
            actual_witness = (
                source.get("witness_id")
                or source.get("canonical_id")
                or source.get("work_id")
            )
            if language == "pli":
                actual_witness = source.get("work_id")
            if language == "lzh":
                actual_witness = source.get("canonical_id")
            if expected_witness != actual_witness:
                errors.append(
                    f"{aid}/{mid}: unit {source_id} belongs to "
                    f"{actual_witness}, not {expected_witness}"
                )

        declared_features = member.get("editorial_features")
        if not isinstance(declared_features, list):
            errors.append(f"{aid}/{mid}: editorial_features must be an array")
        else:
            if len(set(declared_features)) != len(declared_features):
                errors.append(f"{aid}/{mid}: duplicate editorial_features")
            allowed_features = {"supplied", "gap", "unclear"}
            unknown_features = set(declared_features) - allowed_features
            if unknown_features:
                errors.append(
                    f"{aid}/{mid}: unsupported editorial_features "
                    + ", ".join(sorted(unknown_features))
                )
            actual_features: set[str] = set()
            for source in resolved_sources:
                actual_features.update(source_editorial_features(source))
            if set(declared_features) != actual_features:
                errors.append(
                    f"{aid}/{mid}: editorial_features {sorted(declared_features)} "
                    f"do not match source evidence {sorted(actual_features)}"
                )

        if member.get("coverage") == "lost_text_marker":
            resolved_rows = [
                indexes[language][source_id]
                for source_id in source_ids
                if source_id in indexes[language]
            ]
            if not resolved_rows:
                errors.append(
                    f"{aid}/{mid}: lost_text_marker has no resolved source units"
                )
            elif not any(
                "lost" in (
                    row.get("search_text")
                    or row.get("text")
                    or row.get("edition_text")
                    or ""
                ).lower()
                for row in resolved_rows
            ):
                errors.append(
                    f"{aid}/{mid}: lost_text_marker source does not explicitly "
                    "indicate textual loss"
                )

    if len(languages) < 2:
        errors.append(f"{aid}: alignment must contain at least two languages")

    known_members = set(member_ids)
    lost_member_ids = {
        member.get("member_id")
        for member in members
        if member.get("coverage") == "lost_text_marker"
    }
    relation_member_ids = row.get("relation_member_ids")
    if not isinstance(relation_member_ids, list) or len(relation_member_ids) < 2:
        errors.append(
            f"{aid}: relation_member_ids must explicitly contain at least two members"
        )
    else:
        if len(set(relation_member_ids)) != len(relation_member_ids):
            errors.append(f"{aid}: duplicate relation_member_ids")
        for member_id in relation_member_ids:
            if member_id not in known_members:
                errors.append(
                    f"{aid}: relation_member_ids references unknown member {member_id}"
                )
            if member_id in lost_member_ids:
                errors.append(
                    f"{aid}: lost_text_marker member {member_id} cannot participate "
                    "in the asserted textual relation"
                )

    variants = row.get("variants", [])
    for variant in variants:
        for member_id in variant.get("member_ids", []):
            if member_id not in known_members:
                errors.append(
                    f"{aid}: variant references unknown member {member_id}"
                )

    for member_id in lost_member_ids:
        if not any(
            variant.get("type") == "textual_loss"
            and member_id in variant.get("member_ids", [])
            for variant in variants
        ):
            errors.append(
                f"{aid}: lost_text_marker member {member_id} requires a textual_loss "
                "variant claim"
            )

    status = row.get("status")
    review = row.get("review") or {}
    if status == "established":
        errors.append(
            f"{aid}: established is derived from the promotion ledger; "
            "case-study rows must not set it directly"
        )

    if status == "model_reviewed":
        if review.get("status") != "reviewed":
            errors.append(f"{aid}: model_reviewed requires reviewed status")
        if review.get("reviewer_type") != "model":
            errors.append(f"{aid}: model_reviewed requires model reviewer")
        if review.get("decision") != "accepted":
            errors.append(f"{aid}: model_reviewed requires accepted decision")

    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    args = p.parse_args(argv)

    indexes = source_indexes(
        args.pali_units, args.chinese_blocks, args.indic_units
    )
    doc = json.loads(args.case_study.read_text(encoding="utf-8"))
    errors = []
    seen = set()
    for row in doc.get("alignments", []):
        aid = row.get("alignment_id")
        if not aid:
            errors.append("alignment missing alignment_id")
            continue
        if aid in seen:
            errors.append(f"duplicate alignment_id: {aid}")
        seen.add(aid)
        errors.extend(validate_alignment(row, indexes))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "case_study": doc.get("case_study_id"),
                "alignments_checked": len(doc.get("alignments", [])),
                "pali_units": len(indexes["pli"]),
                "chinese_blocks": len(indexes["lzh"]),
                "indic_units": len(indexes["san"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
