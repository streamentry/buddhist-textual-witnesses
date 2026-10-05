#!/usr/bin/env python3
"""Targeted structural probe for CBETA T0125 discourse/chapter layout."""
from __future__ import annotations
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    return " ".join("".join(elem.itertext()).split())[:100]


def direct_mulu(elem: ET.Element) -> ET.Element | None:
    for child in elem:
        if local(child.tag) == "mulu":
            return child
    return None


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("root",type=Path)
    args=p.parse_args()
    path=args.root/"T/T02/T02n0125.xml"
    root=ET.parse(path).getroot()
    events=[]
    def walk(elem, depth=0, ancestors=None):
        ancestors=ancestors or []
        if local(elem.tag)=="div":
            m=direct_mulu(elem)
            if m is not None:
                mt=m.attrib.get("type")
                if mt in {"品","經","其他"}:
                    pin_anc=[a for a in ancestors if a.get("mulu_type")=="品"]
                    events.append({
                        "depth":depth,
                        "div_type":elem.attrib.get("type"),
                        "mulu_type":mt,
                        "mulu_n":m.attrib.get("n"),
                        "mulu":text(m),
                        "pin_ancestors":pin_anc[-2:],
                    })
            entry=None
            if m is not None:
                entry={"mulu_type":m.attrib.get("type"),"mulu":text(m),"mulu_n":m.attrib.get("n")}
            next_anc=ancestors+([entry] if entry else [])
        else:
            next_anc=ancestors
        for child in elem:
            walk(child,depth+1,next_anc)
    walk(root)
    print("events",len(events))
    for i,item in enumerate(events[:140],1):
        print(i,item)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
