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

## Build the unified catalog

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
│   └── catalog.schema.json
├── scripts/
│   ├── fetch_sources.sh
│   └── build_catalog.py
├── docs/
│   ├── METHODOLOGY.md
│   └── CATALOG_PIPELINE.md
├── catalog/
│   └── README.md
├── tests/
│   └── test_build_catalog.py
├── data/
│   └── texts/
├── Makefile
├── SOURCES.md
├── AGENTS.md
└── .gitmodules
```

## First case study

`data/texts/t0825/` models **T0825 佛說甚深大迴向經** without pretending that a Sanskrit original has been identified. It separates the dated Dunhuang witness S.2154, the Korean canonical witness K0507, and Taishō/CBETA T0825.

## Research target

The long-term value is not merely storing texts. It is building auditable parallel maps:

```text
Pāli sutta
  ↕
Chinese Āgama parallel
  ↕
Sanskrit/BHS fragment or edition
  ↕
Gāndhārī/Prakrit fragment
```

Each link should record provenance, relationship type, scholarly basis, and uncertainty.

## Data philosophy

- Never silently normalize away variant readings.
- Never label a back-translation as an attested Sanskrit title.
- Never call a modern edition a manuscript.
- Never call a translation witness an Indic-language original.
- Keep manuscript date, text-composition date, translation date, and edition date separate.
- Prefer stable identifiers over filenames.
- Every normalized text must be traceable to an upstream source and retrieval revision.

## Upstream rights

Upstream texts retain their own copyright, license, attribution, and usage requirements. A Git submodule is a pinned reference to the upstream repository, not a relicensing of its contents. See [SOURCES.md](SOURCES.md).
