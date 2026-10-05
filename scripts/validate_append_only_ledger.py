#!/usr/bin/env python3
"""Verify that an audit ledger only appends records and never rewrites history."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def validate_append_only(
    base_doc: dict[str, Any],
    current_doc: dict[str, Any],
    array_key: str,
    id_key: str,
) -> list[str]:
    errors: list[str] = []
    base_rows = base_doc.get(array_key, [])
    current_rows = current_doc.get(array_key, [])

    if not isinstance(base_rows, list) or not isinstance(current_rows, list):
        return [f"{array_key} must be an array in both ledgers"]
    if len(current_rows) < len(base_rows):
        errors.append(
            f"{array_key} is not append-only: current ledger has fewer records "
            f"({len(current_rows)} < {len(base_rows)})"
        )
        return errors

    for index, old_row in enumerate(base_rows):
        new_row = current_rows[index]
        old_id = old_row.get(id_key) if isinstance(old_row, dict) else None
        new_id = new_row.get(id_key) if isinstance(new_row, dict) else None
        if old_row != new_row:
            errors.append(
                f"{array_key}[{index}] changed in place "
                f"({id_key} {old_id!r} -> {new_id!r}); append a new record instead"
            )

    current_ids = [
        row.get(id_key) for row in current_rows if isinstance(row, dict) and row.get(id_key)
    ]
    if len(current_ids) != len(set(current_ids)):
        errors.append(f"{array_key} contains duplicate {id_key} values")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--array-key", required=True)
    parser.add_argument("--id-key", required=True)
    args = parser.parse_args(argv)

    base_doc = json.loads(args.base.read_text(encoding="utf-8"))
    current_doc = json.loads(args.current.read_text(encoding="utf-8"))
    errors = validate_append_only(
        base_doc, current_doc, args.array_key, args.id_key
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "array_key": args.array_key,
                "base_records": len(base_doc.get(args.array_key, [])),
                "current_records": len(current_doc.get(args.array_key, [])),
                "append_only": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
