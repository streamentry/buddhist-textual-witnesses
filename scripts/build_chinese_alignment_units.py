#!/usr/bin/env python3
"""Build paragraph/block units for the Chinese witnesses used by the curated crosswalks.

The discourse identity and Taishō spans come from generated/crosswalks/first-20-resolved.json.
Raw CBETA remains upstream; this derived layer stores only normalized block text plus exact
source locators and hashes for the selected benchmark witnesses.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "agama_builder", HERE / "build_agama_segments.py"
)
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)

BLOCK_TAGS = {"p", "lg", "table", "list"}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ref_for(stem: str, lb: str | None) -> str | None:
    return f"{stem}_p{lb}" if lb else None


def discourse_elements(root: ET.Element) -> list[ET.Element]:
    rows: list[ET.Element] = []
    for elem in root.iter():
        if BUILDER.local(elem.tag) != "div":
            continue
        mulu = BUILDER.direct_child(elem, "mulu")
        if mulu is not None and mulu.attrib.get("type") == "經":
            rows.append(elem)
    return rows


def iter_lbs(elem: ET.Element) -> list[str]:
    return [
        child.attrib["n"]
        for child in elem.iter()
        if BUILDER.local(child.tag) == "lb"
        and child.attrib.get("ed") == "T"
        and child.attrib.get("n")
    ]


def extract_blocks(
    segment: ET.Element,
    segment_meta: dict[str, Any],
) -> tuple[list[dict[str, Any]], float]:
    stem = Path(segment_meta["source"]["path"]).stem
    blocks: list[dict[str, Any]] = []
    current_lb = segment_meta["locator"].get("start_lb")
    block_ordinal = 0

    def walk(node: ET.Element, inside_block: bool = False) -> None:
        nonlocal current_lb, block_ordinal
        name = BUILDER.local(node.tag)

        if name == "lb":
            if node.attrib.get("ed") == "T" and node.attrib.get("n"):
                current_lb = node.attrib["n"]
            return

        if not inside_block and name in BLOCK_TAGS:
            block_ordinal += 1
            start_lb = current_lb
            lbs = iter_lbs(node)
            if lbs:
                end_lb = lbs[-1]
                current_lb = end_lb
            else:
                end_lb = start_lb

            text = BUILDER.normalize_text(BUILDER.render_text(node))
            if text:
                blocks.append(
                    {
                        "block_id": (
                            f"{segment_meta['canonical_id']}#b{block_ordinal:04d}"
                        ),
                        "canonical_id": segment_meta["canonical_id"],
                        "container_id": segment_meta["container_id"],
                        "language": "lzh",
                        "unit_type": "text_block",
                        "block_kind": name,
                        "ordinal": block_ordinal,
                        "text": text,
                        "text_sha256": sha256(text),
                        "source": segment_meta["source"],
                        "discourse_locator": segment_meta["locator"],
                        "locator": {
                            "block_ordinal": block_ordinal,
                            "xml_id": node.attrib.get(XML_ID),
                            "start_lb": start_lb,
                            "end_lb": end_lb,
                            "start_ref": ref_for(stem, start_lb),
                            "end_ref": ref_for(stem, end_lb),
                            "relative_xpath": (
                                "(.//*[local-name()='p' or local-name()='lg' "
                                "or local-name()='table' or local-name()='list'])"
                                f"[{block_ordinal}]"
                            ),
                            "xml_sha256": BUILDER.xml_fingerprint(node),
                        },
                    }
                )
            return

        for child in node:
            walk(child, inside_block)

    walk(segment)

    full_text = BUILDER.normalize_text(BUILDER.render_text(segment))
    captured = BUILDER.normalize_text("".join(block["text"] for block in blocks))
    if not blocks and full_text:
        block_ordinal = 1
        blocks.append(
            {
                "block_id": f"{segment_meta['canonical_id']}#b0001",
                "canonical_id": segment_meta["canonical_id"],
                "container_id": segment_meta["container_id"],
                "language": "lzh",
                "unit_type": "text_block",
                "block_kind": "discourse_fallback",
                "ordinal": 1,
                "text": full_text,
                "text_sha256": sha256(full_text),
                "source": segment_meta["source"],
                "discourse_locator": segment_meta["locator"],
                "locator": {
                    "block_ordinal": 1,
                    "xml_id": None,
                    "start_lb": segment_meta["locator"].get("start_lb"),
                    "end_lb": segment_meta["locator"].get("end_lb"),
                    "start_ref": segment_meta["locator"].get("start_ref"),
                    "end_ref": segment_meta["locator"].get("end_ref"),
                    "relative_xpath": ".",
                    "xml_sha256": BUILDER.xml_fingerprint(segment),
                },
            }
        )
        captured = full_text

    denominator = max(1, len(full_text))
    coverage = min(1.0, len(captured) / denominator)
    return blocks, coverage


def collect_segment_metadata(resolved: dict[str, Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def collect_witness(witness: dict[str, Any], work_id: str, relation: str) -> None:
        local = witness.get("local_resolution")
        if not local:
            return
        for segment in local.get("segments", []):
            cid = segment["canonical_id"]
            row = found.setdefault(
                cid,
                {
                    **segment,
                    "used_by": [],
                },
            )
            row["used_by"].append(
                {
                    "work_id": work_id,
                    "relation_class": relation,
                    "witness_id": witness["canonical_id"],
                }
            )

    for crosswalk in resolved["crosswalks"]:
        work_id = crosswalk["anchor"]["canonical_id"]
        for witness in crosswalk["full_parallels"]["chinese"]:
            collect_witness(
                witness,
                work_id,
                witness.get("relation_class", "full_textual_parallel"),
            )
        for witness in crosswalk["partial_parallels"]:
            collect_witness(
                witness,
                work_id,
                witness.get("relation_class", "partial_textual_parallel"),
            )
    return found


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cbeta-root", type=Path, required=True)
    parser.add_argument("--resolved-crosswalks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--min-coverage", type=float, default=0.90)
    args = parser.parse_args(argv)

    resolved = json.loads(args.resolved_crosswalks.read_text(encoding="utf-8"))
    segment_meta = collect_segment_metadata(resolved)

    xml_cache: dict[str, tuple[ET.Element, list[ET.Element]]] = {}
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    discourse_stats: dict[str, Any] = {}

    for canonical_id in sorted(segment_meta):
        meta = segment_meta[canonical_id]
        source_path = meta["source"]["path"]
        if source_path not in xml_cache:
            root = ET.parse(args.cbeta_root / source_path).getroot()
            xml_cache[source_path] = (root, discourse_elements(root))
        _, discourses = xml_cache[source_path]

        ordinal = int(meta["locator"]["segment_ordinal"])
        if ordinal < 1 or ordinal > len(discourses):
            errors.append(
                f"{canonical_id}: segment ordinal {ordinal} outside source range"
            )
            continue

        segment = discourses[ordinal - 1]
        actual_hash = BUILDER.xml_fingerprint(segment)
        expected_hash = meta["locator"]["xml_sha256"]
        if actual_hash != expected_hash:
            errors.append(
                f"{canonical_id}: discourse fingerprint mismatch "
                f"expected={expected_hash} actual={actual_hash}"
            )
            continue

        blocks, coverage = extract_blocks(segment, meta)
        if not blocks:
            errors.append(f"{canonical_id}: no text blocks extracted")
            continue
        if coverage < args.min_coverage:
            errors.append(
                f"{canonical_id}: text-block coverage {coverage:.3f} "
                f"below threshold {args.min_coverage:.3f}"
            )

        for block in blocks:
            block["used_by"] = meta["used_by"]
        rows.extend(blocks)
        discourse_stats[canonical_id] = {
            "blocks": len(blocks),
            "coverage": round(coverage, 6),
            "source_path": source_path,
            "segment_ordinal": ordinal,
            "used_by": meta["used_by"],
        }

    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "blocks.jsonl", rows)

    lookup = {
        row["block_id"]: {
            "line": i,
            "canonical_id": row["canonical_id"],
            "start_ref": row["locator"]["start_ref"],
            "end_ref": row["locator"]["end_ref"],
        }
        for i, row in enumerate(rows, 1)
    }
    (args.output / "lookup.json").write_text(
        json.dumps(lookup, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    coverages = [item["coverage"] for item in discourse_stats.values()]
    manifest = {
        "schema_version": 1,
        "discourse_count": len(discourse_stats),
        "block_count": len(rows),
        "minimum_coverage": min(coverages) if coverages else None,
        "mean_coverage": (
            round(statistics.mean(coverages), 6) if coverages else None
        ),
        "discourses": discourse_stats,
        "errors": errors,
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
