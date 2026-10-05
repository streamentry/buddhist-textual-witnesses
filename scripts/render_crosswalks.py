#!/usr/bin/env python3
"""Render the curated first-20 benchmark into a review-friendly Markdown table."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def esc(value: str) -> str:
    return str(value).replace("|", "\\|")


def render(data: dict) -> str:
    lines = [
        "# First 20 high-confidence crosswalks",
        "",
        "Generated from `data/crosswalks/first-20.json`. Treat the JSON as canonical.",
        "",
        "| # | Pāli anchor | Chinese full parallels | Sanskrit witnesses | Gāndhārī / Prākrit | Partial parallels recorded | Confidence |",
        "|---:|---|---|---|---|---|---|",
    ]
    for c in data["crosswalks"]:
        zh = ", ".join(w["canonical_id"] for w in c["full_parallels"]["chinese"])
        san = ", ".join(w["canonical_id"] for w in c["indic_witnesses"]["sanskrit_bhs"]) or "—"
        gp_parts = []
        for w in c["indic_witnesses"]["gandhari_prakrit"]:
            suffix = w["language"]
            if w.get("tradition"):
                suffix += f", {w['tradition']}"
            gp_parts.append(f"{w['canonical_id']} ({suffix})")
        gp = ", ".join(gp_parts) or "—"
        partial = ", ".join(w["canonical_id"] for w in c["partial_parallels"]) or "—"
        anchor = f"{c['anchor']['canonical_id']} {c['anchor']['title']}"
        lines.append(
            f"| {c['rank']} | {esc(anchor)} | {esc(zh)} | {esc(san)} | {esc(gp)} | {esc(partial)} | {c['overall_confidence']} |"
        )

    lines += [
        "",
        "## Reading the table",
        "",
        "- Chinese entries shown here are **full textual parallels** in the SuttaCentral comparative dataset.",
        "- Sanskrit entries are surviving **fragmentary textual witnesses** (SF/SHT identifiers), not necessarily complete Sanskrit sūtras.",
        "- DN 16 includes an independently published Gāndhārī Mahāparinirvāṇasūtra witness.",
        "- DN 23 includes a Prākrit parallel from the Jain canon. It is retained because it is valuable cross-tradition textual evidence, but it must not be mislabeled as a Buddhist canonical recension.",
        "- An empty `shared_passages` or `doctrinal_parallels` list means “not curated yet”, not “none exist”.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "data/crosswalks/first-20.json"
    target = root / "data/crosswalks/FIRST_20.md"
    expected = render(load(source))
    if args.check:
        actual = target.read_text(encoding="utf-8") if target.exists() else ""
        if actual != expected:
            print(f"ERROR: {target} is stale; run scripts/render_crosswalks.py", file=sys.stderr)
            return 1
        print("Crosswalk Markdown is up to date.")
        return 0
    target.write_text(expected, encoding="utf-8")
    print(f"Wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
