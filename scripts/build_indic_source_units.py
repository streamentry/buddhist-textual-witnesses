#!/usr/bin/env python3
"""Build Indic edited-text source units only where reproducible source text is pinned."""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import sys
from pathlib import Path
from typing import Any

HEADING_RE = re.compile(r"<h([1-6])\b", re.I)
P_OPEN_RE = re.compile(r"<p(?:\s|>)", re.I)
P_CLOSE_RE = re.compile(r"</p>", re.I)


class TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_text(value: str) -> str:
    parser = TextOnly()
    parser.feed(value)
    parser.close()
    return " ".join(html.unescape("".join(parser.parts)).split())


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_record(cfg: dict[str, Any], revision: str) -> dict[str, str]:
    base = "https://github.com/suttacentral/bilara-data/blob"
    root_path = cfg["root_path"]
    html_path = cfg["html_path"]
    return {
        "project": cfg["provider"],
        "revision": revision,
        "root_path": root_path,
        "html_path": html_path,
        "root_url": f"{base}/{revision}/{root_path}",
        "html_url": f"{base}/{revision}/{html_path}",
    }


def segment_row(
    witness_id: str,
    cfg: dict[str, Any],
    revision: str,
    ordinal: int,
    segment_id: str,
    edition_text: str,
    template: str,
) -> dict[str, Any]:
    search_text = plain_text(str(edition_text))
    return {
        "witness_id": witness_id,
        "work_id": cfg["work_id"],
        "language": cfg["language"],
        "segment_id": segment_id,
        "ordinal": ordinal,
        "edition_text": edition_text,
        "search_text": search_text,
        "edition_text_sha256": sha256(str(edition_text)),
        "search_text_sha256": sha256(search_text),
        "editorial_markup": {
            "has_supplied": "<supplied>" in str(edition_text),
            "has_gap": "<gap" in str(edition_text),
            "has_unclear": "<unclear" in str(edition_text),
        },
        "html_template": template,
        "source": source_record(cfg, revision),
    }


def emit_unit(
    out: list[dict[str, Any]],
    witness_id: str,
    cfg: dict[str, Any],
    revision: str,
    unit_type: str,
    ordinal: int,
    members: list[dict[str, Any]],
) -> None:
    if not members:
        return
    prefix = {"paragraph": "p", "heading": "h", "block": "b"}[unit_type]
    edition_text = " ".join(str(row["edition_text"]).strip() for row in members).strip()
    search_text = " ".join(row["search_text"] for row in members).strip()
    out.append(
        {
            "unit_id": f"{witness_id}#{prefix}{ordinal:04d}",
            "witness_id": witness_id,
            "work_id": cfg["work_id"],
            "language": cfg["language"],
            "unit_type": unit_type,
            "ordinal": ordinal,
            "segment_ids": [row["segment_id"] for row in members],
            "start_segment_id": members[0]["segment_id"],
            "end_segment_id": members[-1]["segment_id"],
            "edition_text": edition_text,
            "search_text": search_text,
            "edition_text_sha256": sha256(edition_text),
            "search_text_sha256": sha256(search_text),
            "editorial_summary": {
                "segment_count": len(members),
                "segments_with_supplied": sum(
                    row["editorial_markup"]["has_supplied"] for row in members
                ),
                "segments_with_gap": sum(
                    row["editorial_markup"]["has_gap"] for row in members
                ),
                "segments_with_unclear": sum(
                    row["editorial_markup"]["has_unclear"] for row in members
                ),
            },
            "html_templates": [row["html_template"] for row in members],
            "source": source_record(cfg, revision),
        }
    )


def group_units(
    witness_id: str,
    cfg: dict[str, Any],
    revision: str,
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    units: list[dict[str, Any]] = []
    errors: list[str] = []
    paragraph: list[dict[str, Any]] = []
    counters = {"paragraph": 0, "heading": 0, "block": 0}

    def flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        counters["paragraph"] += 1
        emit_unit(
            units,
            witness_id,
            cfg,
            revision,
            "paragraph",
            counters["paragraph"],
            paragraph,
        )
        paragraph = []

    for row in rows:
        template = row["html_template"]
        is_heading = bool(HEADING_RE.search(template))
        opens_p = bool(P_OPEN_RE.search(template))
        closes_p = bool(P_CLOSE_RE.search(template))

        if is_heading:
            if paragraph:
                errors.append(
                    f"{witness_id}: heading {row['segment_id']} before paragraph close"
                )
                flush_paragraph()
            counters["heading"] += 1
            emit_unit(
                units,
                witness_id,
                cfg,
                revision,
                "heading",
                counters["heading"],
                [row],
            )
            continue

        if opens_p:
            if paragraph:
                errors.append(
                    f"{witness_id}: new paragraph {row['segment_id']} before close"
                )
                flush_paragraph()
            paragraph = [row]
            if closes_p:
                flush_paragraph()
            continue

        if paragraph:
            paragraph.append(row)
            if closes_p:
                flush_paragraph()
            continue

        counters["block"] += 1
        emit_unit(
            units,
            witness_id,
            cfg,
            revision,
            "block",
            counters["block"],
            [row],
        )

    if paragraph:
        errors.append(f"{witness_id}: unterminated paragraph at end of witness")
        flush_paragraph()

    return units, errors


def build_witness(
    root_dir: Path,
    witness_id: str,
    cfg: dict[str, Any],
    revision: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    root_path = cfg["root_path"]
    html_path = cfg["html_path"]
    root_data = json.loads((root_dir / root_path).read_text(encoding="utf-8"))
    html_data = json.loads((root_dir / html_path).read_text(encoding="utf-8"))
    errors: list[str] = []

    if list(root_data) != list(html_data):
        errors.append(f"{witness_id}: root/html segment order mismatch")

    rows = [
        segment_row(
            witness_id,
            cfg,
            revision,
            ordinal,
            segment_id,
            str(edition_text),
            str(html_data.get(segment_id, "{}")),
        )
        for ordinal, (segment_id, edition_text) in enumerate(root_data.items(), 1)
    ]
    units, unit_errors = group_units(witness_id, cfg, revision, rows)
    errors.extend(unit_errors)
    return rows, units, errors


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bilara-root", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--crosswalks", type=Path, required=True)
    p.add_argument("--revision", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    cross = json.loads(args.crosswalks.read_text(encoding="utf-8"))

    selected = []
    for cw in cross["crosswalks"]:
        for witness in cw["indic_witnesses"]["sanskrit_bhs"]:
            selected.append(
                {
                    "work_id": cw["anchor"]["canonical_id"],
                    "witness_id": witness["canonical_id"],
                    "language": witness["language"],
                }
            )

    available = cfg["sources"]
    availability = []
    rows: list[dict[str, Any]] = []
    units: list[dict[str, Any]] = []
    errors: list[str] = []

    for item in selected:
        wid = item["witness_id"]
        source_cfg = available.get(wid)
        if source_cfg and source_cfg.get("status") == "text_available":
            if source_cfg["work_id"] != item["work_id"]:
                errors.append(
                    f"{wid}: configured work {source_cfg['work_id']} "
                    f"does not match crosswalk {item['work_id']}"
                )
                continue
            witness_rows, witness_units, witness_errors = build_witness(
                args.bilara_root, wid, source_cfg, args.revision
            )
            rows.extend(witness_rows)
            units.extend(witness_units)
            errors.extend(witness_errors)
            availability.append(
                {
                    **item,
                    "status": "text_available",
                    "provider": source_cfg["provider"],
                    "segments": len(witness_rows),
                    "units": len(witness_units),
                    "root_path": source_cfg["root_path"],
                    "html_path": source_cfg["html_path"],
                }
            )
        else:
            availability.append(
                {
                    **item,
                    "status": cfg["policy"]["absent_status"],
                    "provider": "SuttaCentral Bilara",
                    "segments": 0,
                    "units": 0,
                    "note": cfg["policy"]["note"],
                }
            )

    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "segments.jsonl", rows)
    write_jsonl(args.output / "units.jsonl", units)

    (args.output / "availability.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_revision": args.revision,
                "selected_witness_count": len(selected),
                "text_available_count": sum(
                    x["status"] == "text_available" for x in availability
                ),
                "not_textualized_count": sum(
                    x["status"] != "text_available" for x in availability
                ),
                "policy": cfg["policy"],
                "witnesses": availability,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    unit_types: dict[str, int] = {}
    for unit in units:
        unit_types[unit["unit_type"]] = unit_types.get(unit["unit_type"], 0) + 1

    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_revision": args.revision,
                "witnesses_with_text": sorted(set(x["witness_id"] for x in rows)),
                "segment_count": len(rows),
                "unit_count": len(units),
                "unit_types": unit_types,
                "segments_with_supplied": sum(
                    x["editorial_markup"]["has_supplied"] for x in rows
                ),
                "segments_with_gap": sum(
                    x["editorial_markup"]["has_gap"] for x in rows
                ),
                "segments_with_unclear": sum(
                    x["editorial_markup"]["has_unclear"] for x in rows
                ),
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        if args.strict:
            return 1

    print(
        json.dumps(
            {
                "selected_witnesses": len(selected),
                "text_available": sum(
                    x["status"] == "text_available" for x in availability
                ),
                "segments": len(rows),
                "units": len(units),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
