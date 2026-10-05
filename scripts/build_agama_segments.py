#!/usr/bin/env python3
"""Build exact discourse-level metadata for the five principal Chinese Āgama containers.

A discourse is defined structurally as any CBETA div with a *direct* mulu child whose
type is 經. This rule is intentionally independent of div/@type because T0100 uses
"other" rather than "jing" for its discourse containers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NUM_RE = re.compile(r"^\s*(\d+)(?:\s+|$)")
SKIP_TEXT = {
    "mulu", "head", "jhead", "juan", "byline", "trailer",
    "note", "rdg", "anchor", "pb", "milestone",
}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def compact_text(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    return " ".join("".join(elem.itertext()).split())


def direct_child(elem: ET.Element, name: str, **attrs: str) -> ET.Element | None:
    for child in elem:
        if local(child.tag) != name:
            continue
        if all(child.attrib.get(k) == v for k, v in attrs.items()):
            return child
    return None


def leading_int(text: str) -> int | None:
    match = NUM_RE.match(text or "")
    return int(match.group(1)) if match else None


def mulu_number(mulu: ET.Element) -> int | None:
    # Visible mulu numbering is canonical for this project. In T0099, @n is an
    # internal running index and diverges from visible canonical numbering late
    # in the collection.
    visible = leading_int(compact_text(mulu))
    if visible is not None:
        return visible
    n = mulu.attrib.get("n")
    return int(n) if n and n.isdigit() else None


def title_from_mulu(mulu_text: str) -> str | None:
    title = NUM_RE.sub("", mulu_text, count=1).strip()
    return title or None


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def render_text(elem: ET.Element) -> str:
    """Produce a stable research reading without committing a second raw corpus."""
    name = local(elem.tag)
    if name == "app":
        lemma = direct_child(elem, "lem")
        return render_text(lemma) if lemma is not None else ""
    if name == "choice":
        for preferred in ("corr", "reg", "orig", "sic"):
            child = direct_child(elem, preferred)
            if child is not None:
                return render_text(child)
        return ""
    if name in SKIP_TEXT:
        return ""
    if name == "g" and not (elem.text or "").strip():
        return f"[gaiji:{elem.attrib.get('ref', '?')}]"

    # CBETA XML is pretty-printed. Strip only chunk-edge whitespace so XML
    # indentation does not become artificial spaces inside Chinese running text.
    pieces = [(elem.text or "").strip()]
    for child in elem:
        if local(child.tag) == "lb":
            pieces.append("\n")
        else:
            pieces.append(render_text(child))
        pieces.append((child.tail or "").strip())
    return "".join(pieces)


def xml_fingerprint(elem: ET.Element) -> str:
    """Stable structural fingerprint independent of namespace-prefix serialization."""
    digest = hashlib.sha256()

    def visit(node: ET.Element) -> None:
        digest.update(b"<")
        digest.update(node.tag.encode("utf-8"))
        for key, value in sorted(node.attrib.items()):
            digest.update(b"\0A")
            digest.update(key.encode("utf-8"))
            digest.update(b"=")
            digest.update(value.encode("utf-8"))
        digest.update(b"\0T")
        digest.update((node.text or "").encode("utf-8"))
        for child in node:
            visit(child)
            digest.update(b"\0L")
            digest.update((child.tail or "").encode("utf-8"))
        digest.update(b">")

    visit(elem)
    return digest.hexdigest()


def ref_for(stem: str, lb: str | None) -> str | None:
    return f"{stem}_p{lb}" if lb else None


def hierarchy_entry(div: ET.Element) -> dict[str, Any] | None:
    mulu = direct_child(div, "mulu")
    if mulu is None:
        return None
    return {
        "div_type": div.attrib.get("type"),
        "mulu_type": mulu.attrib.get("type"),
        "number": mulu_number(mulu),
        "text": compact_text(mulu),
    }


@dataclass
class WalkState:
    last_lb: str | None = None
    juan: str | None = None
    segment_ordinal: int = 0
    supplement_ordinal: int = 0


def build_collection(
    xml_path: Path,
    cfg: dict[str, Any],
    revision: str,
    repo_url: str,
) -> list[dict[str, Any]]:
    root = ET.parse(xml_path).getroot()
    stem = xml_path.stem
    state = WalkState()
    segments: list[dict[str, Any]] = []

    def walk(elem: ET.Element, hierarchy: list[dict[str, Any]]) -> None:
        name = local(elem.tag)

        if name == "lb" and elem.attrib.get("ed") == "T" and elem.attrib.get("n"):
            state.last_lb = elem.attrib["n"]
            return

        if name == "juan" and elem.attrib.get("fun") == "open":
            state.juan = elem.attrib.get("n")

        next_hierarchy = hierarchy
        segment_mulu = None

        if name == "div":
            mulu = direct_child(elem, "mulu")
            if mulu is not None:
                if mulu.attrib.get("type") == "經":
                    segment_mulu = mulu
                else:
                    entry = hierarchy_entry(elem)
                    if entry:
                        next_hierarchy = hierarchy + [entry]

        if segment_mulu is not None:
            state.segment_ordinal += 1
            ordinal = state.segment_ordinal
            start_lb = state.last_lb
            start_juan = state.juan
            mulu_text = compact_text(segment_mulu)
            number = mulu_number(segment_mulu)
            if number is None:
                raise ValueError(
                    f"Cannot derive discourse number in {xml_path}: {mulu_text!r}"
                )

            head = direct_child(elem, "head")

            # Advance document state through the whole discourse.
            for child in elem:
                walk(child, next_hierarchy)

            end_lb = state.last_lb
            end_juan = state.juan

            record_kind = "canonical"
            if cfg["id_mode"] == "chapter.item":
                pin = next(
                    (
                        item
                        for item in reversed(next_hierarchy)
                        if item.get("mulu_type") == "品"
                    ),
                    None,
                )
                if not pin or pin.get("number") is None:
                    # T0125 contains one source-labelled 卷末附文 encoded with
                    # mulu/@type=經 but outside every 品. Preserve it as a
                    # structural supplement without inventing an EA x.y ID.
                    state.supplement_ordinal += 1
                    record_kind = "supplement"
                    canonical_id = (
                        f"{cfg['container_id']} supplement "
                        f"{state.supplement_ordinal}"
                    )
                else:
                    canonical_id = (
                        f"{cfg['prefix']} {pin['number']}.{number}"
                    )
            else:
                canonical_id = f"{cfg['prefix']} {number}"

            plain = normalize_text(render_text(elem))
            rel_path = cfg["path"]
            xpath = (
                "(//*[local-name()='div']"
                "[*[local-name()='mulu' and @type='經']])"
                f"[{ordinal}]"
            )

            segments.append(
                {
                    "canonical_id": canonical_id,
                    "record_kind": record_kind,
                    "collection": cfg["prefix"],
                    "container_id": cfg["container_id"],
                    "number": number,
                    "title": title_from_mulu(mulu_text),
                    "mulu_text": mulu_text,
                    "head_text": compact_text(head) or None,
                    "hierarchy": next_hierarchy,
                    "source": {
                        "project": "CBETA XML-P5 / Taishō",
                        "path": rel_path,
                        "revision": revision,
                        "url": (
                            f"{repo_url.removesuffix('.git')}/blob/"
                            f"{revision}/{rel_path}"
                        ),
                    },
                    "locator": {
                        "xpath": xpath,
                        "segment_ordinal": ordinal,
                        "start_lb": start_lb,
                        "end_lb": end_lb,
                        "start_ref": ref_for(stem, start_lb),
                        "end_ref": ref_for(stem, end_lb),
                        "start_juan": start_juan,
                        "end_juan": end_juan,
                        "xml_sha256": xml_fingerprint(elem),
                        "normalized_text_sha256": hashlib.sha256(
                            plain.encode("utf-8")
                        ).hexdigest(),
                        "normalized_text_chars": len(plain),
                    },
                }
            )
            return

        for child in elem:
            walk(child, next_hierarchy)

    walk(root, [])
    return segments


def validate_collection(
    records: list[dict[str, Any]],
    cfg: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    ids = [record["canonical_id"] for record in records]

    if len(ids) != len(set(ids)):
        errors.append(f"{cfg['container_id']}: duplicate canonical IDs")

    expected = cfg.get("expected_segments")
    if expected is not None and len(records) != expected:
        errors.append(
            f"{cfg['container_id']}: expected {expected} structural segments, "
            f"got {len(records)}"
        )

    canonical_count = sum(
        record.get("record_kind") == "canonical" for record in records
    )
    supplement_count = sum(
        record.get("record_kind") == "supplement" for record in records
    )
    expected_canonical = cfg.get(
        "expected_canonical_segments", expected
    )
    if (
        expected_canonical is not None
        and canonical_count != expected_canonical
    ):
        errors.append(
            f"{cfg['container_id']}: expected {expected_canonical} canonical "
            f"segments, got {canonical_count}"
        )
    expected_supplements = cfg.get("expected_supplements", 0)
    if supplement_count != expected_supplements:
        errors.append(
            f"{cfg['container_id']}: expected {expected_supplements} "
            f"supplements, got {supplement_count}"
        )

    for record in records:
        locator = record["locator"]
        if not locator["start_lb"] or not locator["end_lb"]:
            errors.append(
                f"{record['canonical_id']}: missing Taishō line span"
            )
        if locator["normalized_text_chars"] <= 0:
            errors.append(f"{record['canonical_id']}: empty normalized text")

    return errors


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cbeta-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument(
        "--repo-url",
        default="https://github.com/cbeta-org/xml-p5.git",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    config = json.loads(args.config.read_text(encoding="utf-8"))
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "source_revision": args.revision,
        "collections": {},
        "total_segments": 0,
        "total_canonical_segments": 0,
        "total_supplements": 0,
    }
    lookup: dict[str, Any] = {}
    all_errors: list[str] = []

    for container_id, original_cfg in config["collections"].items():
        cfg = {**original_cfg, "container_id": container_id}
        rows = build_collection(
            args.cbeta_root / cfg["path"],
            cfg,
            args.revision,
            args.repo_url,
        )
        all_errors.extend(validate_collection(rows, cfg))

        filename = f"{cfg['prefix'].lower()}.jsonl"
        write_jsonl(args.output / filename, rows)

        for line_no, row in enumerate(rows, 1):
            lookup[row["canonical_id"]] = {
                "file": filename,
                "line": line_no,
                "container_id": row["container_id"],
                "start_ref": row["locator"]["start_ref"],
                "end_ref": row["locator"]["end_ref"],
                "xpath": row["locator"]["xpath"],
            }

        canonical_rows = [
            row for row in rows if row["record_kind"] == "canonical"
        ]
        supplement_rows = [
            row for row in rows if row["record_kind"] == "supplement"
        ]
        numbers = sorted(row["number"] for row in canonical_rows)
        missing: list[int] = []
        if cfg["id_mode"] == "global" and numbers:
            present = set(numbers)
            missing = [
                number
                for number in range(numbers[0], numbers[-1] + 1)
                if number not in present
            ]

        manifest["collections"][cfg["prefix"]] = {
            "container_id": container_id,
            "file": filename,
            "segments": len(rows),
            "canonical_segments": len(canonical_rows),
            "supplements": len(supplement_rows),
            "canonical_first": (
                canonical_rows[0]["canonical_id"]
                if canonical_rows else None
            ),
            "canonical_last": (
                canonical_rows[-1]["canonical_id"]
                if canonical_rows else None
            ),
            "supplement_ids": [
                row["canonical_id"] for row in supplement_rows
            ],
            "source_path": cfg["path"],
            "missing_numbers": missing,
        }
        manifest["total_segments"] += len(rows)
        manifest["total_canonical_segments"] += len(canonical_rows)
        manifest["total_supplements"] += len(supplement_rows)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (args.output / "lookup.json").write_text(
        json.dumps(lookup, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if args.strict:
            return 1

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
