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


def build_witness(
    root_dir: Path,
    witness_id: str,
    cfg: dict[str, Any],
    revision: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    root_path = cfg["root_path"]
    html_path = cfg["html_path"]
    root_data = json.loads((root_dir / root_path).read_text(encoding="utf-8"))
    html_data = json.loads((root_dir / html_path).read_text(encoding="utf-8"))
    errors: list[str] = []

    if list(root_data) != list(html_data):
        errors.append(f"{witness_id}: root/html segment order mismatch")

    base = "https://github.com/suttacentral/bilara-data/blob"
    rows = []
    for ordinal, (segment_id, edition_text) in enumerate(root_data.items(), 1):
        template = str(html_data.get(segment_id, "{}"))
        search_text = plain_text(str(edition_text))
        rows.append(
            {
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
                "source": {
                    "project": cfg["provider"],
                    "revision": revision,
                    "root_path": root_path,
                    "html_path": html_path,
                    "root_url": f"{base}/{revision}/{root_path}",
                    "html_url": f"{base}/{revision}/{html_path}",
                },
            }
        )
    return rows, errors


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bilara-root",type=Path,required=True)
    p.add_argument("--config",type=Path,required=True)
    p.add_argument("--crosswalks",type=Path,required=True)
    p.add_argument("--revision",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--strict",action="store_true")
    args=p.parse_args(argv)

    cfg=json.loads(args.config.read_text(encoding="utf-8"))
    cross=json.loads(args.crosswalks.read_text(encoding="utf-8"))

    selected=[]
    for cw in cross["crosswalks"]:
        for witness in cw["indic_witnesses"]["sanskrit_bhs"]:
            selected.append({
                "work_id":cw["anchor"]["canonical_id"],
                "witness_id":witness["canonical_id"],
                "language":witness["language"],
            })

    available=cfg["sources"]
    availability=[]
    rows=[]
    errors=[]
    for item in selected:
        wid=item["witness_id"]
        source_cfg=available.get(wid)
        if source_cfg and source_cfg.get("status")=="text_available":
            if source_cfg["work_id"] != item["work_id"]:
                errors.append(
                    f"{wid}: configured work {source_cfg['work_id']} "
                    f"does not match crosswalk {item['work_id']}"
                )
                continue
            witness_rows,witness_errors=build_witness(
                args.bilara_root,wid,source_cfg,args.revision
            )
            rows.extend(witness_rows)
            errors.extend(witness_errors)
            availability.append({
                **item,
                "status":"text_available",
                "provider":source_cfg["provider"],
                "segments":len(witness_rows),
                "root_path":source_cfg["root_path"],
                "html_path":source_cfg["html_path"],
            })
        else:
            availability.append({
                **item,
                "status":cfg["policy"]["absent_status"],
                "provider":"SuttaCentral Bilara",
                "segments":0,
                "note":cfg["policy"]["note"],
            })

    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/"segments.jsonl").open("w",encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
    (args.output/"availability.json").write_text(
        json.dumps({
            "schema_version":1,
            "source_revision":args.revision,
            "selected_witness_count":len(selected),
            "text_available_count":sum(x["status"]=="text_available" for x in availability),
            "not_textualized_count":sum(x["status"]!="text_available" for x in availability),
            "policy":cfg["policy"],
            "witnesses":availability,
        },ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8"
    )
    (args.output/"manifest.json").write_text(
        json.dumps({
            "schema_version":1,
            "source_revision":args.revision,
            "witnesses_with_text":sorted(set(x["witness_id"] for x in rows)),
            "segment_count":len(rows),
            "segments_with_supplied":sum(x["editorial_markup"]["has_supplied"] for x in rows),
            "segments_with_gap":sum(x["editorial_markup"]["has_gap"] for x in rows),
            "segments_with_unclear":sum(x["editorial_markup"]["has_unclear"] for x in rows),
            "errors":errors,
        },ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8"
    )

    if errors:
        for error in errors:
            print("ERROR:",error,file=sys.stderr)
        if args.strict:
            return 1

    print(json.dumps({
        "selected_witnesses":len(selected),
        "text_available":sum(x["status"]=="text_available" for x in availability),
        "segments":len(rows),
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
