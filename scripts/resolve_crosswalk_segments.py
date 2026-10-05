#!/usr/bin/env python3
"""Resolve curated DA/MA/SA/SA2/EA crosswalk IDs to generated local CBETA segments."""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

COLLECTION_RE = re.compile(r"^(SA2|DA|MA|SA|EA)\s+(.+)$")
RANGE_RE = re.compile(r"^(\d+)[–-](\d+)$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_segments(directory: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                canonical_id = row["canonical_id"]
                if canonical_id in records:
                    raise ValueError(
                        f"duplicate segment id {canonical_id}"
                    )
                row["_catalog_file"] = path.name
                row["_catalog_line"] = line_no
                records[canonical_id] = row
    return records


def expand_id(
    canonical_id: str,
    segments: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    if canonical_id in segments:
        return [canonical_id], []

    match = COLLECTION_RE.match(canonical_id)
    if not match:
        return [], []

    prefix, body = match.groups()
    range_match = RANGE_RE.match(body)
    if not range_match:
        return [], [canonical_id]

    start, end = map(int, range_match.groups())
    if end < start:
        return [], [canonical_id]

    wanted = [f"{prefix} {number}" for number in range(start, end + 1)]
    found = [item for item in wanted if item in segments]
    missing = [item for item in wanted if item not in segments]
    return found, missing


def compact_segment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_id": row["canonical_id"],
        "container_id": row["container_id"],
        "title": row.get("title"),
        "head_text": row.get("head_text"),
        "hierarchy": row.get("hierarchy", []),
        "source": row["source"],
        "locator": row["locator"],
        "catalog": {
            "file": row["_catalog_file"],
            "line": row["_catalog_line"],
        },
    }


def resolve_witness(
    witness: dict[str, Any],
    segments: dict[str, dict[str, Any]],
    strict: bool,
    errors: list[str],
) -> dict[str, Any]:
    out = copy.deepcopy(witness)
    canonical_id = str(witness.get("canonical_id", ""))

    if not COLLECTION_RE.match(canonical_id):
        return out

    ids, missing = expand_id(canonical_id, segments)
    if not ids:
        errors.append(f"unresolved collection witness: {canonical_id}")
        out["local_resolution"] = {
            "status": "unresolved",
            "missing": missing or [canonical_id],
        }
        return out

    if missing and strict:
        errors.append(
            f"partially unresolved range {canonical_id}: "
            f"missing {', '.join(missing)}"
        )

    out["local_resolution"] = {
        "status": "resolved" if not missing else "partially_resolved",
        "segments": [compact_segment(segments[item]) for item in ids],
    }
    if missing:
        out["local_resolution"]["missing"] = missing
    return out


def resolve(
    data: dict[str, Any],
    segments: dict[str, dict[str, Any]],
    strict: bool = True,
) -> tuple[dict[str, Any], list[str], dict[str, int]]:
    out = copy.deepcopy(data)
    errors: list[str] = []
    counts = {
        "collection_witnesses": 0,
        "resolved_witnesses": 0,
        "resolved_segments": 0,
        "unresolved_witnesses": 0,
    }

    for record in out["crosswalks"]:
        witness_lists = [
            record["full_parallels"]["chinese"],
            record["partial_parallels"],
        ]
        for witnesses in witness_lists:
            for index, witness in enumerate(witnesses):
                canonical_id = str(witness.get("canonical_id", ""))
                if not COLLECTION_RE.match(canonical_id):
                    continue

                counts["collection_witnesses"] += 1
                resolved = resolve_witness(
                    witness, segments, strict, errors
                )
                witnesses[index] = resolved
                local_resolution = resolved.get("local_resolution", {})

                if local_resolution.get("status") in {
                    "resolved", "partially_resolved"
                }:
                    counts["resolved_witnesses"] += 1
                    counts["resolved_segments"] += len(
                        local_resolution.get("segments", [])
                    )
                else:
                    counts["unresolved_witnesses"] += 1

    out["local_resolution"] = {
        "schema_version": 1,
        "source": "generated/agama-segments",
        "summary": counts,
        "note": (
            "Only DA/MA/SA/SA2/EA collection references are resolved here. "
            "Standalone Taishō T-texts remain bibliographic references outside "
            "this segmentation scope."
        ),
    }
    return out, errors, counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    segments = load_segments(args.segments)
    resolved, errors, counts = resolve(
        load_json(args.input), segments, args.strict
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(resolved, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if args.strict:
            return 1

    print(json.dumps(counts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
