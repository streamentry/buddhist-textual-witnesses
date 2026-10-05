#!/usr/bin/env python3
"""Extract one CBETA Āgama discourse using pinned XML plus generated metadata."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "agama_builder", HERE / "build_agama_segments.py"
)
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def load_record(
    directory: Path,
    canonical_id: str,
) -> dict:
    lookup = json.loads(
        (directory / "lookup.json").read_text(encoding="utf-8")
    )
    location = lookup.get(canonical_id)
    if not location:
        raise KeyError(f"Unknown canonical ID: {canonical_id}")

    path = directory / location["file"]
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if line_no == location["line"]:
                return json.loads(line)

    raise RuntimeError(
        f"Catalog line missing for {canonical_id}"
    )


def locate_element(
    xml_path: Path,
    ordinal: int,
) -> ET.Element:
    root = ET.parse(xml_path).getroot()
    seen = 0
    for elem in root.iter():
        if BUILDER.local(elem.tag) != "div":
            continue
        mulu = BUILDER.direct_child(elem, "mulu")
        if mulu is not None and mulu.attrib.get("type") == "經":
            seen += 1
            if seen == ordinal:
                return elem

    raise RuntimeError(
        f"Cannot locate segment ordinal {ordinal} in {xml_path}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cbeta-root", type=Path, required=True)
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--id", required=True, dest="canonical_id")
    parser.add_argument(
        "--format",
        choices=["text", "xml", "metadata"],
        default="text",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    record = load_record(args.segments, args.canonical_id)
    xml_path = args.cbeta_root / record["source"]["path"]
    elem = locate_element(
        xml_path, record["locator"]["segment_ordinal"]
    )

    actual = BUILDER.xml_fingerprint(elem)
    expected = record["locator"]["xml_sha256"]
    if actual != expected:
        raise RuntimeError(
            f"XML fingerprint mismatch for {args.canonical_id}: "
            f"expected {expected}, got {actual}"
        )

    if args.format == "xml":
        output = ET.tostring(elem, encoding="unicode")
    elif args.format == "metadata":
        output = json.dumps(
            record, ensure_ascii=False, indent=2, sort_keys=True
        )
    else:
        output = BUILDER.normalize_text(BUILDER.render_text(elem))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
