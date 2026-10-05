#!/usr/bin/env python3
"""Build auditable Pāli leaf-segment and paragraph units from pinned Bilara data."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HEADING_RE = re.compile(r"<h([1-6])\b", re.I)
P_OPEN_RE = re.compile(r"<p(?:\s|>)", re.I)
P_CLOSE_RE = re.compile(r"</p>", re.I)
SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def work_slug(canonical_id: str) -> str:
    match = re.fullmatch(r"DN\s+(\d+)", canonical_id)
    if not match:
        raise ValueError(f"Unsupported Pāli anchor: {canonical_id}")
    return f"dn{int(match.group(1))}"


def source_record(revision: str, root_path: str, html_path: str) -> dict[str, str]:
    base = "https://github.com/suttacentral/bilara-data/blob"
    return {
        "project": "SuttaCentral Bilara",
        "edition": "Mahāsaṅgīti Pāli",
        "revision": revision,
        "root_path": root_path,
        "html_path": html_path,
        "root_url": f"{base}/{revision}/{root_path}",
        "html_url": f"{base}/{revision}/{html_path}",
    }


def classify_leaf(segment_id: str, html: str) -> str:
    if HEADING_RE.search(html):
        return "heading"
    if P_OPEN_RE.search(html) or P_CLOSE_RE.search(html):
        return "paragraph_segment"
    if ":0." in segment_id:
        return "metadata"
    if "<li" in html or "</li>" in html:
        return "list_segment"
    if "<blockquote" in html or "</blockquote>" in html:
        return "blockquote_segment"
    return "continuation_or_other"


def emit_unit(
    out: list[dict[str, Any]],
    canonical_id: str,
    unit_type: str,
    ordinal: int,
    members: list[dict[str, Any]],
    source: dict[str, str],
) -> None:
    text = normalize(" ".join(member["text"] for member in members))
    if not text:
        return
    prefix = {
        "paragraph": "p",
        "heading": "h",
        "block": "b",
        "metadata": "m",
    }[unit_type]
    out.append(
        {
            "unit_id": f"{canonical_id}#{prefix}{ordinal:04d}",
            "work_id": canonical_id,
            "language": "pli",
            "unit_type": unit_type,
            "ordinal": ordinal,
            "segment_ids": [member["segment_id"] for member in members],
            "start_segment_id": members[0]["segment_id"],
            "end_segment_id": members[-1]["segment_id"],
            "text": text,
            "text_sha256": sha256(text),
            "html_templates": [member["html"] for member in members],
            "source": source,
        }
    )


def build_work(
    bilara_root: Path,
    canonical_id: str,
    revision: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    slug = work_slug(canonical_id)
    root_path = f"root/pli/ms/sutta/dn/{slug}_root-pli-ms.json"
    html_path = f"html/pli/ms/sutta/dn/{slug}_html.json"
    root_data = json.loads((bilara_root / root_path).read_text(encoding="utf-8"))
    html_data = json.loads((bilara_root / html_path).read_text(encoding="utf-8"))
    source = source_record(revision, root_path, html_path)

    errors: list[str] = []
    root_keys = list(root_data)
    html_keys = list(html_data)
    if root_keys != html_keys:
        missing_html = [key for key in root_keys if key not in html_data]
        missing_root = [key for key in html_keys if key not in root_data]
        errors.append(
            f"{canonical_id}: Bilara root/html key order mismatch; "
            f"missing_html={missing_html[:5]} missing_root={missing_root[:5]}"
        )

    leaves: list[dict[str, Any]] = []
    for ordinal, segment_id in enumerate(root_keys, 1):
        text = normalize(str(root_data[segment_id]))
        html = str(html_data.get(segment_id, "{}"))
        leaves.append(
            {
                "segment_id": segment_id,
                "work_id": canonical_id,
                "language": "pli",
                "ordinal": ordinal,
                "kind": classify_leaf(segment_id, html),
                "text": text,
                "text_sha256": sha256(text),
                "html": html,
                "source": source,
            }
        )

    units: list[dict[str, Any]] = []
    paragraph: list[dict[str, Any]] = []
    counters = {"paragraph": 0, "heading": 0, "block": 0, "metadata": 0}

    def flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        counters["paragraph"] += 1
        emit_unit(
            units,
            canonical_id,
            "paragraph",
            counters["paragraph"],
            paragraph,
            source,
        )
        paragraph = []

    for leaf in leaves:
        html = leaf["html"]
        is_heading = bool(HEADING_RE.search(html))
        opens_p = bool(P_OPEN_RE.search(html))
        closes_p = bool(P_CLOSE_RE.search(html))

        if is_heading:
            if paragraph:
                errors.append(
                    f"{canonical_id}: heading {leaf['segment_id']} encountered "
                    "before open paragraph closed"
                )
                flush_paragraph()
            counters["heading"] += 1
            emit_unit(
                units,
                canonical_id,
                "heading",
                counters["heading"],
                [leaf],
                source,
            )
            continue

        if opens_p:
            if paragraph:
                errors.append(
                    f"{canonical_id}: nested/new paragraph at {leaf['segment_id']} "
                    "before previous paragraph closed"
                )
                flush_paragraph()
            paragraph = [leaf]
            if closes_p:
                flush_paragraph()
            continue

        if paragraph:
            paragraph.append(leaf)
            if closes_p:
                flush_paragraph()
            continue

        unit_type = "metadata" if leaf["kind"] == "metadata" else "block"
        counters[unit_type] += 1
        emit_unit(
            units,
            canonical_id,
            unit_type,
            counters[unit_type],
            [leaf],
            source,
        )

    if paragraph:
        errors.append(f"{canonical_id}: unterminated paragraph at end of file")
        flush_paragraph()

    return leaves, units, errors


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilara-root", type=Path, required=True)
    parser.add_argument("--crosswalks", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    crosswalks = json.loads(args.crosswalks.read_text(encoding="utf-8"))
    leaves_all: list[dict[str, Any]] = []
    units_all: list[dict[str, Any]] = []
    errors: list[str] = []
    works: dict[str, Any] = {}

    for crosswalk in crosswalks["crosswalks"]:
        canonical_id = crosswalk["anchor"]["canonical_id"]
        leaves, units, work_errors = build_work(
            args.bilara_root, canonical_id, args.revision
        )
        leaves_all.extend(leaves)
        units_all.extend(units)
        errors.extend(work_errors)
        counts: dict[str, int] = {}
        for unit in units:
            counts[unit["unit_type"]] = counts.get(unit["unit_type"], 0) + 1
        works[canonical_id] = {
            "leaf_segments": len(leaves),
            "units": len(units),
            "unit_types": counts,
            "first_segment": leaves[0]["segment_id"] if leaves else None,
            "last_segment": leaves[-1]["segment_id"] if leaves else None,
        }

    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "segments.jsonl", leaves_all)
    write_jsonl(args.output / "units.jsonl", units_all)

    segment_lookup = {
        row["segment_id"]: {"line": i, "work_id": row["work_id"]}
        for i, row in enumerate(leaves_all, 1)
    }
    unit_lookup = {
        row["unit_id"]: {
            "line": i,
            "work_id": row["work_id"],
            "unit_type": row["unit_type"],
        }
        for i, row in enumerate(units_all, 1)
    }
    (args.output / "lookup.json").write_text(
        json.dumps(
            {"segments": segment_lookup, "units": unit_lookup},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "source_revision": args.revision,
        "works": works,
        "work_count": len(works),
        "leaf_segment_count": len(leaves_all),
        "unit_count": len(units_all),
        "paragraph_count": sum(
            row["unit_type"] == "paragraph" for row in units_all
        ),
        "errors": errors,
    }
    (args.output / "manifest.json").write_text(
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
