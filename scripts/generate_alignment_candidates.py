#!/usr/bin/env python3
"""Generate explicitly non-established Pāli ↔ Chinese alignment candidates.

Two candidate families are emitted:
1. shared_formula: direct lexical formula evidence such as Evaṁ me sutaṁ ↔ 如是我聞.
2. monotonic_position: weak structural ranking by relative position/length only.

Neither family is an established textual alignment. Human review is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

PALI_OPENING = "evaṁ me sutaṁ"
CHINESE_OPENINGS = ("如是我聞", "聞如是", "我聞如是")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def stable_id(*parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"cand:{digest}"


def centers(rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], float, float]]:
    lengths = [max(1, len(row["text"])) for row in rows]
    total = max(1, sum(lengths))
    cursor = 0
    out = []
    for row, length in zip(rows, lengths):
        center = (cursor + length / 2) / total
        relative_length = length / total
        out.append((row, center, relative_length))
        cursor += length
    return out


def formula_candidates(
    work_id: str,
    witness_id: str,
    pali_rows: list[dict[str, Any]],
    chinese_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    p_matches = [
        row for row in pali_rows
        if PALI_OPENING in row["text"].lower()
    ]
    c_matches = [
        row for row in chinese_rows
        if any(formula in row["text"] for formula in CHINESE_OPENINGS)
    ]
    out = []
    for p_row in p_matches:
        for c_row in c_matches:
            matched_chinese = next(
                formula for formula in CHINESE_OPENINGS
                if formula in c_row["text"]
            )
            out.append(
                {
                    "alignment_id": stable_id(
                        work_id,
                        witness_id,
                        "shared_formula_v1",
                        p_row["unit_id"],
                        c_row["block_id"],
                    ),
                    "work_id": work_id,
                    "chinese_witness_id": witness_id,
                    "status": "machine_candidate",
                    "assertion": "not_established",
                    "relation_type": "shared_formula",
                    "scope": "formula_within_source_units",
                    "pali_unit_ids": [p_row["unit_id"]],
                    "chinese_unit_ids": [c_row["block_id"]],
                    "method": {
                        "name": "shared_formula_v1",
                        "kind": "lexical_rule",
                        "ranking_score": 1.0,
                        "signals": {
                            "pali_formula": "Evaṁ me sutaṁ",
                            "chinese_formula": matched_chinese,
                        },
                        "limitations": (
                            "Formulaic correspondence is strong evidence that the "
                            "opening formulas correspond, but does not establish "
                            "equivalence of the entire surrounding paragraphs."
                        ),
                    },
                    "review": {
                        "status": "unreviewed",
                        "reviewer_type": None,
                        "reviewer": None,
                        "decision": None,
                        "notes": None,
                    },
                }
            )
    return out


def monotonic_candidates(
    work_id: str,
    witness_id: str,
    pali_rows: list[dict[str, Any]],
    chinese_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not pali_rows or not chinese_rows:
        return []
    p_centers = centers(pali_rows)
    c_centers = centers(chinese_rows)
    out = []

    for p_row, p_center, p_len in p_centers:
        c_row, c_center, c_len = min(
            c_centers, key=lambda item: abs(item[1] - p_center)
        )
        position_delta = abs(p_center - c_center)
        position_similarity = max(0.0, 1.0 - position_delta)
        if p_len > 0 and c_len > 0:
            ratio = min(p_len, c_len) / max(p_len, c_len)
        else:
            ratio = 0.0
        score = 0.8 * position_similarity + 0.2 * ratio

        out.append(
            {
                "alignment_id": stable_id(
                    work_id,
                    witness_id,
                    "monotonic_position_v1",
                    p_row["unit_id"],
                    c_row["block_id"],
                ),
                "work_id": work_id,
                "chinese_witness_id": witness_id,
                "status": "machine_candidate",
                "assertion": "not_established",
                "relation_type": "possible_parallel_passage",
                "scope": "source_unit",
                "pali_unit_ids": [p_row["unit_id"]],
                "chinese_unit_ids": [c_row["block_id"]],
                "method": {
                    "name": "monotonic_position_v1",
                    "kind": "structural_ranking",
                    "ranking_score": round(score, 6),
                    "signals": {
                        "pali_relative_center": round(p_center, 6),
                        "chinese_relative_center": round(c_center, 6),
                        "position_delta": round(position_delta, 6),
                        "relative_length_similarity": round(ratio, 6),
                    },
                    "limitations": (
                        "Position and relative length are weak heuristics. This "
                        "candidate is a review-queue hint only and is not evidence "
                        "of textual correspondence by itself."
                    ),
                },
                "review": {
                    "status": "unreviewed",
                    "reviewer_type": None,
                    "reviewer": None,
                    "decision": None,
                    "notes": None,
                },
            }
        )
    return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pali-units", type=Path, required=True)
    parser.add_argument("--chinese-blocks", type=Path, required=True)
    parser.add_argument("--resolved-crosswalks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    pali = load_jsonl(args.pali_units)
    chinese = load_jsonl(args.chinese_blocks)
    resolved = json.loads(args.resolved_crosswalks.read_text(encoding="utf-8"))

    pali_by_work: dict[str, list[dict[str, Any]]] = {}
    for row in pali:
        if row["unit_type"] == "paragraph":
            pali_by_work.setdefault(row["work_id"], []).append(row)

    chinese_by_discourse: dict[str, list[dict[str, Any]]] = {}
    for row in chinese:
        chinese_by_discourse.setdefault(row["canonical_id"], []).append(row)

    formula_rows: list[dict[str, Any]] = []
    monotonic_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    pairs: dict[str, Any] = {}

    for crosswalk in resolved["crosswalks"]:
        work_id = crosswalk["anchor"]["canonical_id"]
        p_rows = pali_by_work.get(work_id, [])
        if not p_rows:
            errors.append(f"{work_id}: no Pāli paragraph units")
            continue

        for witness in crosswalk["full_parallels"]["chinese"]:
            local = witness.get("local_resolution")
            if not local:
                continue
            witness_id = witness["canonical_id"]
            c_rows: list[dict[str, Any]] = []
            segment_ids = []
            for segment in local.get("segments", []):
                cid = segment["canonical_id"]
                segment_ids.append(cid)
                blocks = chinese_by_discourse.get(cid, [])
                if not blocks:
                    errors.append(
                        f"{work_id} ↔ {witness_id}: no Chinese blocks for {cid}"
                    )
                c_rows.extend(blocks)

            if not c_rows:
                continue

            frows = formula_candidates(work_id, witness_id, p_rows, c_rows)
            mrows = monotonic_candidates(work_id, witness_id, p_rows, c_rows)
            formula_rows.extend(frows)
            monotonic_rows.extend(mrows)
            pairs[f"{work_id} ↔ {witness_id}"] = {
                "work_id": work_id,
                "chinese_witness_id": witness_id,
                "chinese_segments": segment_ids,
                "pali_paragraphs": len(p_rows),
                "chinese_blocks": len(c_rows),
                "shared_formula_candidates": len(frows),
                "monotonic_candidates": len(mrows),
            }

    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "shared-formula-candidates.jsonl", formula_rows)
    write_jsonl(args.output / "monotonic-candidates.jsonl", monotonic_rows)

    manifest = {
        "schema_version": 1,
        "status": "machine_candidates_only",
        "established_alignments": 0,
        "pair_count": len(pairs),
        "shared_formula_candidates": len(formula_rows),
        "monotonic_candidates": len(monotonic_rows),
        "pairs": pairs,
        "errors": errors,
        "epistemic_rule": (
            "Generated candidates are not established alignments. Human review "
            "is required before a candidate may be promoted."
        ),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if args.strict:
            return 1

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
