#!/usr/bin/env python3
"""Generate lexicon-assisted many-to-many Chinese windows for each Pāli paragraph.

This remains a retrieval layer only. Candidate windows are not established alignments.
The search combines reviewed lexical anchors with a weak monotonic position prior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
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


def stable_id(*parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"cand:{digest}"


def norm_pali(text: str) -> str:
    return " ".join(text.lower().split())


def norm_lzh(text: str) -> str:
    return re.sub(r"\s+", "", text)


def lexicon_signals(
    pali_text: str,
    chinese_text: str,
    entries: list[dict[str, Any]],
) -> tuple[float, list[dict[str, Any]]]:
    p = norm_pali(pali_text)
    c = norm_lzh(chinese_text)
    matched = []
    total = 0.0
    for entry in entries:
        p_hit = next(
            (form for form in entry.get("pali", []) if norm_pali(form) in p),
            None,
        )
        c_hit = next(
            (form for form in entry.get("lzh", []) if norm_lzh(form) in c),
            None,
        )
        if p_hit and c_hit:
            weight = float(entry.get("weight", 1.0))
            total += weight
            matched.append(
                {
                    "id": entry["id"],
                    "pali": p_hit,
                    "lzh": c_hit,
                    "weight": weight,
                }
            )
    return total, matched


def cumulative_centers(rows: list[dict[str, Any]]) -> dict[str, float]:
    lengths = [max(1, len(row["text"])) for row in rows]
    total = max(1, sum(lengths))
    cursor = 0
    out = {}
    for row, length in zip(rows, lengths):
        key = row.get("unit_id") or row.get("block_id")
        out[key] = (cursor + length / 2) / total
        cursor += length
    return out


def windows(rows: list[dict[str, Any]], max_width: int) -> list[list[dict[str, Any]]]:
    out = []
    for start in range(len(rows)):
        for width in range(1, max_width + 1):
            end = start + width
            if end <= len(rows):
                out.append(rows[start:end])
    return out


def score_window(
    pali_row: dict[str, Any],
    chinese_window: list[dict[str, Any]],
    p_center: float,
    c_centers: dict[str, float],
    lexicon: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    chinese_text = " ".join(row["text"] for row in chinese_window)
    lexical_weight, anchors = lexicon_signals(
        pali_row["text"], chinese_text, lexicon
    )
    first = chinese_window[0]["block_id"]
    last = chinese_window[-1]["block_id"]
    c_center = (
        c_centers[first] + c_centers[last]
    ) / 2
    position_delta = abs(p_center - c_center)
    position_similarity = max(0.0, 1.0 - position_delta)

    # Saturate lexical evidence rather than allowing a long list to dominate.
    lexical_score = 1.0 - math.exp(-lexical_weight / 5.0)
    score = 0.72 * lexical_score + 0.28 * position_similarity
    return score, {
        "lexical_weight": round(lexical_weight, 6),
        "lexical_score": round(lexical_score, 6),
        "matched_anchors": anchors,
        "pali_relative_center": round(p_center, 6),
        "chinese_relative_center": round(c_center, 6),
        "position_delta": round(position_delta, 6),
        "window_width": len(chinese_window),
    }


def candidate_windows(
    work_id: str,
    witness_id: str,
    pali_rows: list[dict[str, Any]],
    chinese_rows: list[dict[str, Any]],
    lexicon: list[dict[str, Any]],
    top_k: int = 3,
    max_width: int = 3,
) -> list[dict[str, Any]]:
    p_centers = cumulative_centers(pali_rows)
    c_centers = cumulative_centers(chinese_rows)
    c_windows = windows(chinese_rows, max_width)
    out = []

    for p_row in pali_rows:
        scored = []
        for c_window in c_windows:
            score, signals = score_window(
                p_row,
                c_window,
                p_centers[p_row["unit_id"]],
                c_centers,
                lexicon,
            )
            scored.append((score, c_window, signals))
        scored.sort(
            key=lambda item: (
                -item[0],
                item[2]["position_delta"],
                item[2]["window_width"],
                item[1][0]["ordinal"],
            )
        )

        for rank, (score, c_window, signals) in enumerate(
            scored[:top_k], 1
        ):
            cids = [row["block_id"] for row in c_window]
            out.append(
                {
                    "alignment_id": stable_id(
                        work_id,
                        witness_id,
                        "lexicon_anchor_window_v1",
                        p_row["unit_id"],
                        *cids,
                    ),
                    "work_id": work_id,
                    "chinese_witness_id": witness_id,
                    "status": "machine_candidate",
                    "assertion": "not_established",
                    "relation_type": "possible_parallel_passage",
                    "scope": "candidate_window",
                    "pali_unit_ids": [p_row["unit_id"]],
                    "chinese_unit_ids": cids,
                    "method": {
                        "name": "lexicon_anchor_window_v1",
                        "kind": "lexical_rule",
                        "ranking_score": round(score, 6),
                        "signals": {
                            **signals,
                            "rank": rank,
                        },
                        "limitations": (
                            "Lexical anchors and monotonic position are retrieval "
                            "signals only. Shared vocabulary, stock formulas, and "
                            "similar position do not establish textual dependence "
                            "or passage identity."
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


def evaluate(
    candidates: list[dict[str, Any]],
    reviewed: dict[str, Any],
) -> dict[str, Any]:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in candidates:
        if row["method"]["name"] != "lexicon_anchor_window_v1":
            continue
        pid = row["pali_unit_ids"][0]
        key = (row["work_id"], row["chinese_witness_id"], pid)
        by_key.setdefault(key, []).append(row)

    cases = 0
    overlap_hits = 0
    full_cover_hits = 0
    reciprocal_ranks = []

    details = []
    for review in reviewed.get("alignments", []):
        if review.get("review", {}).get("decision") != "accepted":
            continue
        gold = set(review["chinese_unit_ids"])
        for pid in review["pali_unit_ids"]:
            key = (
                review["work_id"],
                review["chinese_witness_id"],
                pid,
            )
            rows = sorted(
                by_key.get(key, []),
                key=lambda row: row["method"]["signals"]["rank"],
            )
            cases += 1
            overlap_rank = None
            full_rank = None
            for row in rows:
                predicted = set(row["chinese_unit_ids"])
                rank = row["method"]["signals"]["rank"]
                if overlap_rank is None and predicted & gold:
                    overlap_rank = rank
                if full_rank is None and gold.issubset(predicted):
                    full_rank = rank
            if overlap_rank is not None:
                overlap_hits += 1
                reciprocal_ranks.append(1.0 / overlap_rank)
            if full_rank is not None:
                full_cover_hits += 1
            details.append(
                {
                    "review_alignment_id": review["alignment_id"],
                    "pali_unit_id": pid,
                    "gold_chinese_unit_ids": sorted(gold),
                    "overlap_rank": overlap_rank,
                    "full_cover_rank": full_rank,
                }
            )

    return {
        "gold_case_count": cases,
        "overlap_at_3": (
            round(overlap_hits / cases, 6) if cases else None
        ),
        "full_cover_at_3": (
            round(full_cover_hits / cases, 6) if cases else None
        ),
        "mean_reciprocal_rank_overlap": (
            round(sum(reciprocal_ranks) / cases, 6) if cases else None
        ),
        "details": details,
        "note": (
            "Gold cases are model-reviewed seed alignments, not a human gold "
            "standard. Metrics are retrieval diagnostics only."
        ),
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--resolved-crosswalks", type=Path, required=True)
    p.add_argument("--lexicon", type=Path, required=True)
    p.add_argument("--reviewed-seed", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--max-width", type=int, default=3)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)

    pali = load_jsonl(args.pali_units)
    chinese = load_jsonl(args.chinese_blocks)
    resolved = json.loads(
        args.resolved_crosswalks.read_text(encoding="utf-8")
    )
    lexicon_doc = json.loads(args.lexicon.read_text(encoding="utf-8"))
    reviewed = json.loads(args.reviewed_seed.read_text(encoding="utf-8"))

    pali_by_work: dict[str, list[dict[str, Any]]] = {}
    for row in pali:
        if row["unit_type"] == "paragraph":
            pali_by_work.setdefault(row["work_id"], []).append(row)

    chinese_by_discourse: dict[str, list[dict[str, Any]]] = {}
    for row in chinese:
        chinese_by_discourse.setdefault(row["canonical_id"], []).append(row)

    rows: list[dict[str, Any]] = []
    errors = []
    pair_count = 0
    for crosswalk in resolved["crosswalks"]:
        work_id = crosswalk["anchor"]["canonical_id"]
        p_rows = pali_by_work.get(work_id, [])
        for witness in crosswalk["full_parallels"]["chinese"]:
            local = witness.get("local_resolution")
            if not local:
                continue
            witness_id = witness["canonical_id"]
            c_rows = []
            for segment in local.get("segments", []):
                c_rows.extend(
                    chinese_by_discourse.get(segment["canonical_id"], [])
                )
            if not p_rows or not c_rows:
                errors.append(
                    f"{work_id} ↔ {witness_id}: missing source units"
                )
                continue
            pair_count += 1
            rows.extend(
                candidate_windows(
                    work_id,
                    witness_id,
                    p_rows,
                    c_rows,
                    lexicon_doc["entries"],
                    top_k=args.top_k,
                    max_width=args.max_width,
                )
            )

    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "anchor-window-candidates.jsonl", rows)
    metrics = evaluate(rows, reviewed)
    (args.output / "anchor-window-evaluation.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "method": "lexicon_anchor_window_v1",
        "pair_count": pair_count,
        "candidate_count": len(rows),
        "top_k": args.top_k,
        "max_width": args.max_width,
        "lexicon_entries": len(lexicon_doc["entries"]),
        "evaluation": {
            key: value
            for key, value in metrics.items()
            if key != "details"
        },
        "errors": errors,
        "status": "machine_candidates_only",
    }
    (args.output / "anchor-window-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
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
