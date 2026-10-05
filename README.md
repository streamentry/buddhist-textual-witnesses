# Buddhist Textual Witnesses

**A source-aligned corpus of Buddhist textual witnesses across Indic and Chinese traditions.**

This repository is infrastructure for studying how Buddhist texts survive across languages, recensions, manuscripts, and translation lineages. It is **not** a claim that a single reconstructed "original Buddhist canon" exists.

## Scope

Primary target languages and witness families:

- Sanskrit
- Buddhist Hybrid Sanskrit (BHS)
- Prakrit, including Gāndhārī where available
- Classical Chinese Āgama and other translation witnesses
- Pāli as an alignment baseline when needed, but not vendored by default

Tibetan can be added later using the same witness model.

## Core principle

> Preserve the witness first. Reconstruct only as a separate, explicitly labeled scholarly layer.

A manuscript, edition, Chinese translation, Sanskrit fragment, and modern reconstruction are different kinds of evidence. This project keeps those distinctions visible.

## Included upstream corpora

Large public upstream corpora are pinned as Git submodules so the exact scholarly source revision is reproducible without copying gigabytes into this repository's own Git history:

- `upstream/suttacentral-bilara` — SuttaCentral Bilara, published branch
- `upstream/cbeta-xml-p5` — official CBETA XML-P5
- `upstream/gretil-mirror` — archival GRETIL mirror

The exact SHAs are recorded in `sources/lock.json`.

**Gandhari.org** and **DSBC** are registered research sources but are not bulk-mirrored because this project does not currently have sufficiently clear redistribution permission for their complete compilations.

## Clone everything

```bash
git clone --recurse-submodules https://github.com/streamentry/buddhist-textual-witnesses.git
cd buddhist-textual-witnesses
./scripts/fetch_sources.sh
```

For an existing clone:

```bash
git pull
git submodule sync --recursive
git submodule update --init --recursive --depth 1
```

The upstream datasets are large. Expect a multi-gigabyte checkout.

## Build the unified corpus catalog

```bash
make test
make catalog
```

The pipeline filters only the relevant material and emits a deterministic metadata catalog:

```text
canonical work
  -> language
    -> witness
      -> source + exact revision
```

Generated outputs live in `catalog/`:

- `catalog.json` — nested work/language/witness graph
- `catalog.jsonl` — one witness per line
- `catalog.csv` — spreadsheet-friendly index
- `stats.json` — counts by source and language

BHS is labeled only when explicit metadata or a reviewed override supports that classification. Similar titles are never automatically treated as the same text. See `docs/CATALOG_PIPELINE.md`.

## First 20 curated textual crosswalks

The repository now includes a first research-grade benchmark under `data/crosswalks/`:

```text
Pāli anchor
  ↕
Chinese full/partial parallels
  ↕
Sanskrit manuscript witnesses
  ↕
Gāndhārī / Prākrit where attested
```

The first 20 use Dīgha Nikāya anchors because the comparative source explicitly reports DN/MN correspondence data as the most thoroughly checked part of that dataset.

Files:

- `data/crosswalks/first-20.json` — canonical machine-readable benchmark
- `data/crosswalks/FIRST_20.md` — human-readable table
- `data/crosswalks/bibliography.json` — bibliography records
- `schemas/crosswalk.schema.json` — crosswalk contract
- `scripts/validate_crosswalks.py` — scholarly guardrails

Run:

```bash
make benchmark
```

The benchmark deliberately uses `full_textual_parallel`, not `exact_parallel`. Independent recensions may share a common ancestor while differing in wording and structure.

## Repository layout

```text
.
├── upstream/
│   ├── suttacentral-bilara/
│   ├── cbeta-xml-p5/
│   └── gretil-mirror/
├── config/
│   └── catalog.json
├── sources/
│   ├── manifest.yaml
│   └── lock.json
├── schemas/
│   ├── witness.schema.json
│   ├── catalog.schema.json
│   └── crosswalk.schema.json
├── scripts/
│   ├── fetch_sources.sh
│   ├── build_catalog.py
│   ├── validate_crosswalks.py
│   └── render_crosswalks.py
├── docs/
│   ├── METHODOLOGY.md
│   └── CATALOG_PIPELINE.md
├── catalog/
│   └── README.md
├── data/
│   ├── crosswalks/
│   └── texts/
├── tests/
├── Makefile
├── SOURCES.md
├── AGENTS.md
└── .gitmodules
```

## First case study

`data/texts/t0825/` models **T0825 佛說甚深大迴向經** without pretending that a Sanskrit original has been identified. It separates the dated Dunhuang witness S.2154, the Korean canonical witness K0507, and Taishō/CBETA T0825.

## Data philosophy

- Never silently normalize away variant readings.
- Never label a back-translation as an attested Sanskrit title.
- Never call a modern edition a manuscript.
- Never call a translation witness an Indic-language original.
- Never treat a fragmentary manuscript as merely a “partial parallel”.
- Never use “exact parallel” when the evidence only establishes a full discourse correspondence.
- Keep manuscript date, text-composition date, translation date, and edition date separate.
- Prefer stable identifiers over filenames.
- Every normalized text and crosswalk must be traceable to evidence and upstream revision.

## Upstream rights

Upstream texts retain their own copyright, license, attribution, and usage requirements. A Git submodule is a pinned reference to the upstream repository, not a relicensing of its contents. See [SOURCES.md](SOURCES.md).
