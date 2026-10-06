#!/usr/bin/env python3
"""Render a multi-witness case study from source-backed alignment JSON."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

SUPPLIED_RE = re.compile(r"<supplied>(.*?)</supplied>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def indexes(pali: Path, chinese: Path, indic: Path) -> dict[str, dict[str, Any]]:
    return {
        **{row["unit_id"]: row for row in load_jsonl(pali)},
        **{row["block_id"]: row for row in load_jsonl(chinese)},
        **{row["unit_id"]: row for row in load_jsonl(indic)},
    }


def render_sanskrit_edition(value: str) -> str:
    value = SUPPLIED_RE.sub(lambda m: f"⟦{m.group(1)}⟧", value)
    value = TAG_RE.sub("", value)
    return html.unescape(" ".join(value.split()))


def source_text(row: dict[str, Any]) -> str:
    if row.get("language") == "san":
        return render_sanskrit_edition(row["edition_text"])
    return row.get("text") or row.get("search_text") or ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pali-units", type=Path, required=True)
    p.add_argument("--chinese-blocks", type=Path, required=True)
    p.add_argument("--indic-units", type=Path, required=True)
    p.add_argument("--case-study", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    idx = indexes(args.pali_units, args.chinese_blocks, args.indic_units)
    doc = json.loads(args.case_study.read_text(encoding="utf-8"))
    lines = [
        f"# {doc['title']}",
        "",
        f"Case study: {doc['case_study_id']}",
        "",
        doc["scope"],
        "",
        "> Epistemic status: model-reviewed research alignment. Nothing in this report is human-established unless separately marked.",
        "",
        "## Witnesses",
        "",
    ]
    for witness in doc["witnesses"]:
        lines.append(
            f"- **{witness['witness_id']}** ({witness['language']}): {witness['role']}"
        )
    lines += [
        "",
        "### Sanskrit editorial legend",
        "",
        "⟦text⟧ = letters or words marked <supplied> in the upstream scholarly edition. The generated source data retains the original markup; this report only changes its display.",
        "",
    ]

    for number, alignment in enumerate(doc["alignments"], 1):
        lines += [
            f"## {number}. {alignment['scope'].replace('_', ' ').title()}",
            "",
            f"- Alignment: {alignment['alignment_id']}",
            f"- Relation: **{alignment['relation_type']}**",
            (
                "- Relation members: **"
                + ", ".join(alignment.get("relation_member_ids", [
                    member["member_id"] for member in alignment["members"]
                ]))
                + "**"
            ),
            f"- Status: **{alignment['status']}**",
            f"- Review confidence: **{alignment['review']['confidence']}**",
            "",
        ]
        for member in alignment["members"]:
            lines += [
                f"### {member['witness_id']} · {member['language']} · {member['coverage']}",
                "",
                "Units: " + ", ".join(member["source_unit_ids"]),
                "",
            ]
            texts = [source_text(idx[source_id]) for source_id in member["source_unit_ids"]]
            lines.append("> " + " ".join(texts).replace("\n", " "))
            if member.get("notes"):
                lines += ["", f"Note: {member['notes']}"]
            lines.append("")

        if alignment.get("variants"):
            lines += ["### Variant notes", ""]
            for variant in alignment["variants"]:
                lines.append(f"- **{variant['type']}**: {variant['statement']}")
            lines.append("")

        lines += [
            "### Review note",
            "",
            alignment["review"]["notes"] or "",
            "",
        ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "case_study": doc["case_study_id"],
                "alignments": len(doc["alignments"]),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
