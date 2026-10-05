#!/usr/bin/env python3
"""Validate curated textual crosswalk benchmarks using only the Python standard library."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_RELATIONS = {
    "anchor",
    "full_textual_parallel",
    "partial_textual_parallel",
    "fragmentary_textual_parallel",
    "shared_passage",
    "doctrinal_parallel",
}
ALLOWED_LANGS = {"pli", "lzh", "san", "bhs", "pra", "gdh", "bo", "other"}
ALLOWED_CONFIDENCE = {"high", "medium", "low", "unknown"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def all_witnesses(record: dict[str, Any]):
    yield record["anchor"]
    yield from record["full_parallels"]["chinese"]
    yield from record["full_parallels"]["other_pali"]
    yield from record["indic_witnesses"]["sanskrit_bhs"]
    yield from record["indic_witnesses"]["gandhari_prakrit"]
    yield from record["partial_parallels"]
    yield from record["shared_passages"]
    yield from record["doctrinal_parallels"]


def validate(root: Path) -> list[str]:
    data = load_json(root / "data" / "crosswalks" / "first-20.json")
    bib = load_json(root / "data" / "crosswalks" / "bibliography.json")
    errors: list[str] = []

    records = data.get("crosswalks", [])
    if len(records) != 20:
        errors.append(f"benchmark must contain exactly 20 records, found {len(records)}")

    ids = [r.get("id") for r in records]
    anchors = [r.get("anchor", {}).get("canonical_id") for r in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate crosswalk id")
    if len(anchors) != len(set(anchors)):
        errors.append("duplicate Pāli anchor")
    if sorted(r.get("rank") for r in records) != list(range(1, 21)):
        errors.append("ranks must be exactly 1..20")

    bib_ids = set(bib.get("entries", {}))
    relation_counts = Counter()

    for record in records:
        rid = record.get("id", "<missing>")
        anchor = record.get("anchor", {})
        if anchor.get("language") != "pli":
            errors.append(f"{rid}: anchor must be Pāli")
        if anchor.get("relation_class") != "anchor":
            errors.append(f"{rid}: anchor relation_class must be anchor")

        chinese = record.get("full_parallels", {}).get("chinese", [])
        if not chinese:
            errors.append(f"{rid}: must have at least one Chinese full parallel")
        for w in chinese:
            if w.get("language") != "lzh":
                errors.append(f"{rid}: Chinese full parallel has wrong language: {w}")
            if w.get("relation_class") != "full_textual_parallel":
                errors.append(f"{rid}: Chinese benchmark witness must be full_textual_parallel")
            cid = str(w.get("canonical_id", ""))
            if cid.startswith(("DA ", "MA ", "EA ", "SA ", "SA2 ")) and not w.get("container_id"):
                errors.append(f"{rid}: {cid} must record its Taishō container_id")

        indic = (
            record.get("indic_witnesses", {}).get("sanskrit_bhs", [])
            + record.get("indic_witnesses", {}).get("gandhari_prakrit", [])
        )
        if not indic:
            errors.append(f"{rid}: must have at least one non-Pāli Indic witness")

        for w in all_witnesses(record):
            lang = w.get("language")
            rel = w.get("relation_class")
            conf = w.get("confidence", "high" if rel == "anchor" else None)
            if lang not in ALLOWED_LANGS:
                errors.append(f"{rid}: unsupported language {lang}")
            if rel not in ALLOWED_RELATIONS:
                errors.append(f"{rid}: unsupported relation {rel}")
            if rel == "exact_parallel":
                errors.append(f"{rid}: exact_parallel is forbidden")
            if rel != "anchor" and conf not in ALLOWED_CONFIDENCE:
                errors.append(f"{rid}: invalid confidence {conf}")
            relation_counts[rel] += 1
            if lang == "bhs" and not w.get("evidence_basis"):
                errors.append(f"{rid}: BHS classification requires explicit evidence_basis")

        for ref in record.get("bibliography", []):
            if ref not in bib_ids:
                errors.append(f"{rid}: unresolved bibliography id {ref}")
        for w in all_witnesses(record):
            for ref in w.get("bibliography", []):
                if ref not in bib_ids:
                    errors.append(f"{rid}: unresolved witness bibliography id {ref}")

    # Benchmark-level scholarly guardrails.
    if relation_counts["full_textual_parallel"] < 20:
        errors.append("benchmark unexpectedly contains fewer than 20 full textual parallels")
    if relation_counts["fragmentary_textual_parallel"] < 19:
        errors.append("benchmark unexpectedly contains fewer than 19 fragmentary textual witnesses")

    dn16 = next((r for r in records if r.get("id") == "work:dn16"), None)
    if not dn16 or not any(w.get("language") == "gdh" for w in dn16["indic_witnesses"]["gandhari_prakrit"]):
        errors.append("DN 16 must preserve its Gāndhārī witness")

    dn23 = next((r for r in records if r.get("id") == "work:dn23"), None)
    if not dn23:
        errors.append("DN 23 missing")
    else:
        prak = dn23["indic_witnesses"]["gandhari_prakrit"]
        if not any(w.get("language") == "pra" and w.get("tradition") == "Jain" for w in prak):
            errors.append("DN 23 must preserve the Jain Prākrit caveat")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    data = load_json(root / "data" / "crosswalks" / "first-20.json")
    print(f"Validated {len(data['crosswalks'])} curated textual crosswalks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
