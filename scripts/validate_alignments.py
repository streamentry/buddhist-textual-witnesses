#!/usr/bin/env python3
"""Validate source-unit references and epistemic guardrails for alignments."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PALI_FORMULA = "evaṁ me sutaṁ"
CHINESE_FORMULAS = ("如是我聞", "聞如是", "我聞如是")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def index(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out = {}
    for row in rows:
        value = row[key]
        if value in out:
            raise ValueError(f"duplicate {key}: {value}")
        out[value] = row
    return out


def validate_candidate(
    row: dict[str, Any],
    pali: dict[str, dict[str, Any]],
    chinese: dict[str, dict[str, Any]],
) -> list[str]:
    errors = []
    aid = row.get("alignment_id", "<missing>")
    pids = row.get("pali_unit_ids")
    cids = row.get("chinese_unit_ids")

    if not isinstance(pids, list) or not pids:
        errors.append(f"{aid}: pali_unit_ids must be a non-empty list")
        pids = []
    if not isinstance(cids, list) or not cids:
        errors.append(f"{aid}: chinese_unit_ids must be a non-empty list")
        cids = []

    if len(set(pids)) != len(pids):
        errors.append(f"{aid}: duplicate Pāli unit in alignment")
    if len(set(cids)) != len(cids):
        errors.append(f"{aid}: duplicate Chinese unit in alignment")

    for pid in pids:
        if pid not in pali:
            errors.append(f"{aid}: unresolved Pāli unit {pid}")
    for cid in cids:
        if cid not in chinese:
            errors.append(f"{aid}: unresolved Chinese unit {cid}")

    status = row.get("status")
    if status not in {"machine_candidate", "reviewed", "established", "rejected"}:
        errors.append(f"{aid}: invalid status {status}")

    review = row.get("review") or {}
    if status == "established":
        if review.get("status") != "reviewed":
            errors.append(f"{aid}: established alignment lacks reviewed status")
        if review.get("reviewer_type") != "human":
            errors.append(f"{aid}: established alignment requires human reviewer")
        if review.get("decision") != "accepted":
            errors.append(f"{aid}: established alignment requires accepted decision")
        if not review.get("reviewer"):
            errors.append(f"{aid}: established alignment requires reviewer identity")

    if status == "machine_candidate" and row.get("assertion") != "not_established":
        errors.append(f"{aid}: machine candidate must say not_established")

    if row.get("relation_type") == "shared_formula":
        resolved_p = [pali[pid] for pid in pids if pid in pali]
        resolved_c = [chinese[cid] for cid in cids if cid in chinese]
        if resolved_p and not any(
            PALI_FORMULA in item["text"].lower() for item in resolved_p
        ):
            errors.append(f"{aid}: Pāli shared-formula evidence absent")
        if resolved_c and not any(
            formula in item["text"]
            for item in resolved_c
            for formula in CHINESE_FORMULAS
        ):
            errors.append(f"{aid}: Chinese shared-formula evidence absent")

    method = row.get("method") or {}
    if method.get("kind") == "structural_ranking" and status == "established":
        errors.append(
            f"{aid}: structural-ranking output cannot be established directly"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--candidates", type=Path, nargs="+", required=True)
    p.add_argument("--reviewed", type=Path, nargs="*")
    args = p.parse_args(argv)

    pali = index(load_jsonl(args.pali_units), "unit_id")
    chinese = index(load_jsonl(args.chinese_blocks), "block_id")
    rows = []
    for path in args.candidates:
        rows.extend(load_jsonl(path))
    for reviewed_path in args.reviewed or []:
        reviewed_data = json.loads(reviewed_path.read_text(encoding="utf-8"))
        rows.extend(reviewed_data.get("alignments", []))

    errors = []
    seen = set()
    established = 0
    reviewed = 0
    for row in rows:
        aid = row.get("alignment_id")
        if not aid:
            errors.append("alignment missing alignment_id")
            continue
        if aid in seen:
            errors.append(f"duplicate alignment_id: {aid}")
        seen.add(aid)
        errors.extend(validate_candidate(row, pali, chinese))
        if row.get("status") == "established":
            established += 1
        if row.get("status") == "reviewed":
            reviewed += 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "alignments_checked": len(rows),
                "reviewed_alignments": reviewed,
                "established_alignments": established,
                "pali_units": len(pali),
                "chinese_units": len(chinese),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
