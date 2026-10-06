#!/usr/bin/env python3
"""Canonical evidence snapshots for human review and promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_source_index(
    pali_units: Path,
    chinese_blocks: Path,
    indic_units: Path,
) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(pali_units):
        idx[row["unit_id"]] = row
    for row in load_jsonl(chinese_blocks):
        idx[row["block_id"]] = row
    for row in load_jsonl(indic_units):
        idx[row["unit_id"]] = row
    return idx


def evidence_payload(
    case_study_id: str,
    alignment: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_units: list[dict[str, Any]] = []
    seen: set[str] = set()
    for member in alignment.get("members", []):
        for source_id in member.get("source_unit_ids", []):
            if source_id in seen:
                continue
            seen.add(source_id)
            if source_id not in source_index:
                raise KeyError(f"missing source unit: {source_id}")
            source_units.append(
                {"source_id": source_id, "record": source_index[source_id]}
            )

    alignment_claim = {
        "alignment_id": alignment.get("alignment_id"),
        "work_id": alignment.get("work_id"),
        "relation_type": alignment.get("relation_type"),
        "scope": alignment.get("scope"),
        "members": alignment.get("members", []),
        "variants": alignment.get("variants", []),
    }
    return {
        "schema_version": 1,
        "case_study_id": case_study_id,
        "alignment": alignment_claim,
        "source_units": source_units,
    }


def digest_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def alignment_evidence_digest(
    case_study_id: str,
    alignment: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> str:
    return digest_payload(
        evidence_payload(case_study_id, alignment, source_index)
    )


def alignment_source_revisions(
    alignment: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for member in alignment.get("members", []):
        for source_id in member.get("source_unit_ids", []):
            row = source_index[source_id]
            source = row.get("source") or {}
            key = (
                source.get("project"),
                source.get("revision"),
                source.get("path") or source.get("root_path"),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "project": key[0],
                    "revision": key[1],
                    "path": key[2],
                }
            )
    return rows
