#!/usr/bin/env python3
"""Print a compact structural probe of selected CBETA Āgama XML files."""
from __future__ import annotations

import argparse
import collections
import xml.etree.ElementTree as ET
from pathlib import Path


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def compact_text(elem: ET.Element, limit: int = 100) -> str:
    text = " ".join("".join(elem.itertext()).split())
    return text[:limit]


def probe(path: Path) -> None:
    tag_counts = collections.Counter()
    div_types = collections.Counter()
    mulu_types = collections.Counter()
    jing_mulu = []
    jing_heads = []

    for event, elem in ET.iterparse(path, events=("start", "end")):
        name = local(elem.tag)
        if event == "start":
            tag_counts[name] += 1
            if name == "div":
                div_types[elem.attrib.get("type", "<none>")] += 1
        elif event == "end":
            if name == "mulu":
                kind = elem.attrib.get("type", "<none>")
                mulu_types[kind] += 1
                if kind == "經":
                    jing_mulu.append({
                        "n": elem.attrib.get("n"),
                        "level": elem.attrib.get("level"),
                        "text": compact_text(elem),
                    })
            elem.clear()

    # Parse again to inspect cb:div type=jing containers directly.
    for _, elem in ET.iterparse(path, events=("end",)):
        if local(elem.tag) == "div" and elem.attrib.get("type") == "jing":
            head = next((x for x in elem.iter() if local(x.tag) == "head"), None)
            mulu = next((x for x in elem.iter() if local(x.tag) == "mulu" and x.attrib.get("type") == "經"), None)
            lbs = [x.attrib.get("n") for x in elem.iter() if local(x.tag) == "lb" and x.attrib.get("ed") == "T" and x.attrib.get("n")]
            jing_heads.append({
                "mulu_n": mulu.attrib.get("n") if mulu is not None else None,
                "mulu": compact_text(mulu) if mulu is not None else "",
                "head": compact_text(head) if head is not None else "",
                "start_lb": lbs[0] if lbs else None,
                "end_lb": lbs[-1] if lbs else None,
            })
        elem.clear()

    print(f"=== {path.name} ===")
    print("tag_counts", dict(tag_counts.most_common(30)))
    print("div_types", dict(div_types.most_common()))
    print("mulu_types", dict(mulu_types.most_common()))
    print("jing_mulu_count", len(jing_mulu))
    print("jing_div_count", len(jing_heads))
    print("first_jing_mulu", jing_mulu[:10])
    print("last_jing_mulu", jing_mulu[-10:])
    print("first_jing_divs", jing_heads[:5])
    print("last_jing_divs", jing_heads[-5:])
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    targets = [
        "T/T01/T01n0001.xml",
        "T/T01/T01n0026.xml",
        "T/T02/T02n0099.xml",
        "T/T02/T02n0100.xml",
        "T/T02/T02n0125.xml",
    ]
    for rel in targets:
        probe(args.root / rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
