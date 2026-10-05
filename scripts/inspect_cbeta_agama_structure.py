#!/usr/bin/env python3
"""Print a compact structural probe of selected CBETA Āgama XML files."""
from __future__ import annotations

import argparse
import collections
import xml.etree.ElementTree as ET
from pathlib import Path


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def compact_text(elem: ET.Element, limit: int = 90) -> str:
    text = " ".join("".join(elem.itertext()).split())
    return text[:limit]


def probe(path: Path, event_limit: int) -> None:
    counts = collections.Counter()
    events = []
    for event, elem in ET.iterparse(path, events=("start", "end")):
        name = local(elem.tag)
        if event == "start":
            counts[name] += 1
        if event == "end" and name in {"mulu", "head", "juan", "lb", "milestone"}:
            if len(events) < event_limit:
                events.append({
                    "tag": name,
                    "attrs": dict(elem.attrib),
                    "text": compact_text(elem),
                })
            elem.clear()

    print(f"=== {path.name} ===")
    print("tag counts:", dict(counts.most_common(25)))
    print("selected events:")
    for item in events:
        print(item)
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--events", type=int, default=120)
    args = parser.parse_args()
    targets = [
        "T/T01/T01n0001.xml",
        "T/T01/T01n0026.xml",
        "T/T02/T02n0099.xml",
        "T/T02/T02n0100.xml",
        "T/T02/T02n0125.xml",
    ]
    for rel in targets:
        probe(args.root / rel, args.events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
