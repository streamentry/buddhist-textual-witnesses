#!/usr/bin/env python3
"""Build a unified catalog from pinned Buddhist textual witness corpora.

The pipeline intentionally indexes provenance and metadata only. Raw source texts remain
inside upstream Git submodules. Equivalent works are grouped only when a curated crosswalk
says so; otherwise each upstream canonical identifier remains source-qualified.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
HTML_TAG_RE = re.compile(r"<[^>]+>")
SC_FILE_RE = re.compile(r"^(?P<id>.+?)_root-(?P<lang>[a-z]+)(?:-[^.]+)?\.json$")


@dataclass(frozen=True)
class Witness:
    work_id: str
    canonical_id: str
    canonical_namespace: str
    language: str
    witness_id: str
    title: str
    witness_kind: str
    source_project: str
    source_identifier: str
    source_path: str
    source_revision: str
    source_url: str
    license: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def strip_markup(value: str) -> str:
    value = HTML_TAG_RE.sub("", value)
    return " ".join(html.unescape(value).split()).strip()


def first_title_from_segments(data: dict[str, Any], fallback: str) -> str:
    preferred = []
    other = []
    for key, value in data.items():
        if not isinstance(value, str):
            continue
        cleaned = strip_markup(value)
        if not cleaned:
            continue
        if re.search(r":0(?:\.0|\.1)?$", key):
            preferred.append(cleaned)
        elif key.endswith(":0.1") or key.endswith(":0.0"):
            preferred.append(cleaned)
        else:
            other.append(cleaned)
    if preferred:
        return preferred[0]
    if other:
        return other[0][:160]
    return fallback


def get_revision(lock: dict[str, Any], source_id: str) -> str:
    return str(lock.get("sources", {}).get(source_id, {}).get("commit", ""))


def source_url(repo_url: str, revision: str, path: str) -> str:
    repo_url = repo_url.removesuffix(".git")
    return f"{repo_url}/blob/{revision}/{path}"


def classify_language(default: str, source_key: str, metadata_text: str, overrides: dict[str, str]) -> str:
    if source_key in overrides:
        return overrides[source_key]
    # Only use explicit metadata wording. Do not infer BHS from linguistic heuristics.
    if default == "san" and "buddhist hybrid sanskrit" in metadata_text.casefold():
        return "bhs"
    return default


def scan_suttacentral(root: Path, lock: dict[str, Any], overrides: dict[str, str], crosswalks: dict[str, str]) -> list[Witness]:
    base = root / "upstream" / "suttacentral-bilara" / "root"
    revision = get_revision(lock, "suttacentral-bilara")
    repo_url = lock["sources"]["suttacentral-bilara"]["repository"]
    out: list[Witness] = []

    for lang in ("san", "pra"):
        lang_root = base / lang
        if not lang_root.exists():
            continue
        for path in sorted(lang_root.rglob("*.json")):
            match = SC_FILE_RE.match(path.name)
            if not match:
                continue
            canonical_id = match.group("id")
            try:
                data = load_json(path)
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Failed to parse SuttaCentral file {path}: {exc}") from exc
            if not isinstance(data, dict):
                continue
            rel = path.relative_to(root / "upstream" / "suttacentral-bilara").as_posix()
            title = first_title_from_segments(data, canonical_id)
            work_key = f"suttacentral:{canonical_id}"
            witness_key = f"suttacentral:{lang}:{canonical_id}"
            classified = classify_language(lang, witness_key, title, overrides)
            work_id = crosswalks.get(witness_key, crosswalks.get(work_key, work_key))
            out.append(Witness(
                work_id=work_id,
                canonical_id=canonical_id,
                canonical_namespace="suttacentral",
                language=classified,
                witness_id=witness_key,
                title=title,
                witness_kind="digital_root_text",
                source_project="SuttaCentral Bilara",
                source_identifier=canonical_id,
                source_path=rel,
                source_revision=revision,
                source_url=source_url(repo_url, revision, rel),
                notes="Root text segmented by SuttaCentral/Bilara.",
            ))
    return out


def xml_text(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    return " ".join("".join(elem.itertext()).split())


def gretil_is_buddhist(root_elem: ET.Element) -> tuple[bool, str]:
    refs = [el.attrib.get("target", "") for el in root_elem.findall(".//tei:ref", TEI_NS)]
    all_text = " ".join(xml_text(el) for el in root_elem.findall(".//tei:teiHeader//*", TEI_NS))
    # Strongest signal is GRETIL's own Buddhist taxonomy encoded in legacy source path.
    if any("/buddh/" in ref.casefold() for ref in refs):
        return True, all_text
    # Secondary explicit metadata signal, not linguistic inference.
    if "sanskrit buddhist" in all_text.casefold() or "buddhist hybrid sanskrit" in all_text.casefold():
        return True, all_text
    return False, all_text


def gretil_license(root_elem: ET.Element) -> str | None:
    lic = root_elem.find(".//tei:publicationStmt//tei:licence", TEI_NS)
    if lic is None:
        return None
    target = lic.attrib.get("target")
    label = xml_text(lic)
    if target and label:
        return f"{label} ({target})"
    return target or label or None


def scan_gretil(root: Path, lock: dict[str, Any], overrides: dict[str, str], crosswalks: dict[str, str]) -> list[Witness]:
    base = root / "upstream" / "gretil-mirror"
    tei_dir = base / "gretil.sub.uni-goettingen.de" / "gretil" / "corpustei"
    revision = get_revision(lock, "gretil")
    repo_url = lock["sources"]["gretil"]["repository"]
    out: list[Witness] = []
    if not tei_dir.exists():
        return out

    for path in sorted(tei_dir.glob("*.xml")):
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            # A malformed upstream TEI file should not silently poison the whole catalog.
            continue
        root_elem = tree.getroot()
        is_buddhist, metadata_text = gretil_is_buddhist(root_elem)
        if not is_buddhist:
            continue
        xml_id = root_elem.attrib.get("{http://www.w3.org/XML/1998/namespace}id") or path.stem
        title = xml_text(root_elem.find(".//tei:titleStmt/tei:title", TEI_NS)) or xml_id
        source_key = f"gretil:{xml_id}"
        language = classify_language("san", source_key, metadata_text, overrides)
        rel = path.relative_to(base).as_posix()
        work_id = crosswalks.get(source_key, source_key)
        out.append(Witness(
            work_id=work_id,
            canonical_id=xml_id,
            canonical_namespace="gretil",
            language=language,
            witness_id=source_key,
            title=title,
            witness_kind="digital_edition",
            source_project="GRETIL",
            source_identifier=xml_id,
            source_path=rel,
            source_revision=revision,
            source_url=source_url(repo_url, revision, rel),
            license=gretil_license(root_elem),
            notes="Buddhist classification comes from explicit GRETIL taxonomy/metadata, not language-model inference.",
        ))
    return out


def scan_cbeta(root: Path, lock: dict[str, Any], agama_config: list[dict[str, str]], crosswalks: dict[str, str]) -> list[Witness]:
    base = root / "upstream" / "cbeta-xml-p5"
    revision = get_revision(lock, "cbeta-xml")
    repo_url = lock["sources"]["cbeta-xml"]["repository"]
    out: list[Witness] = []

    for item in agama_config:
        canonical_id = item["id"]
        rel = item["path"]
        path = base / rel
        if not path.exists():
            continue
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            raise RuntimeError(f"Failed to parse CBETA file {path}: {exc}") from exc
        root_elem = tree.getroot()
        title = xml_text(root_elem.find(".//tei:titleStmt/tei:title", TEI_NS)) or item.get("title", canonical_id)
        source_key = f"cbeta:{canonical_id}"
        work_id = crosswalks.get(source_key, source_key)
        out.append(Witness(
            work_id=work_id,
            canonical_id=canonical_id,
            canonical_namespace="taisho",
            language="lzh",
            witness_id=source_key,
            title=title,
            witness_kind="canonical_translation_edition",
            source_project="CBETA XML-P5 / Taishō",
            source_identifier=canonical_id,
            source_path=rel,
            source_revision=revision,
            source_url=source_url(repo_url, revision, rel),
            notes=item.get("notes", "Selected Chinese Āgama witness."),
        ))
    return out


def verify_submodule_revisions(root: Path, lock: dict[str, Any]) -> list[str]:
    mapping = {
        "suttacentral-bilara": root / "upstream" / "suttacentral-bilara",
        "cbeta-xml": root / "upstream" / "cbeta-xml-p5",
        "gretil": root / "upstream" / "gretil-mirror",
    }
    errors: list[str] = []
    for source_id, path in mapping.items():
        expected = get_revision(lock, source_id)
        if not path.exists():
            errors.append(f"Missing submodule: {path}")
            continue
        try:
            actual = subprocess.check_output(
                ["git", "-C", str(path), "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append(f"Cannot read Git revision for {path}")
            continue
        if expected and actual != expected:
            errors.append(f"Revision mismatch for {source_id}: expected {expected}, got {actual}")
    return errors


def validate_witnesses(witnesses: Iterable[Witness]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    allowed_langs = {"san", "bhs", "pra", "gdh", "lzh", "pli", "bo", "other"}
    for w in witnesses:
        if w.witness_id in seen:
            errors.append(f"Duplicate witness_id: {w.witness_id}")
        seen.add(w.witness_id)
        if w.language not in allowed_langs:
            errors.append(f"Unsupported language {w.language} for {w.witness_id}")
        for field in ("work_id", "canonical_id", "canonical_namespace", "source_project", "source_path", "source_revision"):
            if not getattr(w, field):
                errors.append(f"Missing {field} for {w.witness_id}")
    return errors


def build_catalog(witnesses: list[Witness], lock: dict[str, Any]) -> dict[str, Any]:
    works: dict[str, dict[str, Any]] = {}
    grouped: dict[str, dict[str, list[Witness]]] = defaultdict(lambda: defaultdict(list))
    for w in witnesses:
        grouped[w.work_id][w.language].append(w)

    for work_id in sorted(grouped):
        languages: dict[str, list[dict[str, Any]]] = {}
        for lang in sorted(grouped[work_id]):
            languages[lang] = [w.to_dict() for w in sorted(grouped[work_id][lang], key=lambda x: x.witness_id)]
        works[work_id] = {"languages": languages}

    return {
        "schema_version": 1,
        "source_revisions": {k: v.get("commit", "") for k, v in sorted(lock.get("sources", {}).items())},
        "works": works,
    }


def write_outputs(output_dir: Path, witnesses: list[Witness], catalog: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "catalog.json").open("w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    ordered = sorted(witnesses, key=lambda w: (w.work_id, w.language, w.witness_id))
    with (output_dir / "catalog.jsonl").open("w", encoding="utf-8") as f:
        for w in ordered:
            f.write(json.dumps(w.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    fieldnames = [
        "work_id", "canonical_id", "canonical_namespace", "language", "witness_id", "title",
        "witness_kind", "source_project", "source_identifier", "source_path", "source_revision",
        "source_url", "license", "notes",
    ]
    with (output_dir / "catalog.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for w in ordered:
            writer.writerow(w.to_dict())

    by_source = Counter(w.source_project for w in witnesses)
    by_language = Counter(w.language for w in witnesses)
    stats = {
        "total_witnesses": len(witnesses),
        "total_works": len({w.work_id for w in witnesses}),
        "by_language": dict(sorted(by_language.items())),
        "by_source": dict(sorted(by_source.items())),
    }
    with (output_dir / "stats.json").open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def load_config(root: Path) -> tuple[dict[str, str], dict[str, str], list[dict[str, str]]]:
    config = load_json(root / "config" / "catalog.json")
    return (
        dict(config.get("language_overrides", {})),
        dict(config.get("crosswalks", {})),
        list(config.get("cbeta_agamas", [])),
    )


def run(root: Path, output_dir: Path, strict: bool, check_lock: bool) -> int:
    lock = load_json(root / "sources" / "lock.json")
    overrides, crosswalks, agama_config = load_config(root)

    if check_lock:
        revision_errors = verify_submodule_revisions(root, lock)
        if revision_errors:
            for err in revision_errors:
                print(f"ERROR: {err}", file=sys.stderr)
            if strict:
                return 2

    witnesses: list[Witness] = []
    witnesses.extend(scan_suttacentral(root, lock, overrides, crosswalks))
    witnesses.extend(scan_gretil(root, lock, overrides, crosswalks))
    witnesses.extend(scan_cbeta(root, lock, agama_config, crosswalks))

    errors = validate_witnesses(witnesses)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 3

    if strict:
        expected_sources = {"SuttaCentral Bilara", "GRETIL", "CBETA XML-P5 / Taishō"}
        present_sources = {w.source_project for w in witnesses}
        missing = expected_sources - present_sources
        if missing:
            for source in sorted(missing):
                print(f"ERROR: no witnesses emitted from {source}", file=sys.stderr)
            return 4

    catalog = build_catalog(witnesses, lock)
    write_outputs(output_dir, witnesses, catalog)
    print(f"Built {len(witnesses)} witnesses across {len(catalog['works'])} works -> {output_dir}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="fail if a pinned source is missing or produces zero witnesses")
    parser.add_argument("--no-lock-check", action="store_true", help="skip pinned Git revision verification")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "catalog"
    return run(root, output, args.strict, not args.no_lock_check)


if __name__ == "__main__":
    raise SystemExit(main())
