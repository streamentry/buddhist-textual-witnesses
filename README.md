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


## Exact CBETA Āgama discourse segments

The five principal Chinese Āgama containers are now segmented into reproducible discourse-level records against the pinned CBETA 2026.R2 source:

| Collection | Container | Canonical segments | Notes |
|---|---|---:|---|
| DA | T0001 | 30 | DA 1–30 |
| MA | T0026 | 222 | MA 1–222 |
| SA | T0099 | 1,355 | SA numbering reaches 1362 with seven missing numbers |
| SA2 | T0100 | 364 | discourse divs are encoded as `type="other"` in this source |
| EA | T0125 | 471 | plus one explicitly labelled volume-end supplement |

**2,443 structural segments = 2,442 canonical discourse segments + 1 supplement.**

The seven absent SA canonical numbers in the pinned witness are:

`141, 144, 756, 757, 773, 774, 812`.

Generated metadata is under `generated/agama-segments/`. It does not duplicate the raw Chinese corpus. Each segment records the exact CBETA commit, source path, structural XPath, Taishō line span, juan span, structural hash, and normalized-text hash.

The first 20 benchmark crosswalks are also fully resolved:

- **33** DA/MA/SA/SA2/EA witness references
- **42** exact local segments after range expansion
- **0 unresolved**

See `generated/crosswalks/first-20-resolved.json` and `docs/AGAMA_SEGMENTATION.md`.

Build and verify locally:

```bash
make agama
```

Extract one source segment on demand:

```bash
python3 scripts/extract_agama_segment.py \
  --cbeta-root .cache/cbeta-agamas \
  --segments generated/agama-segments \
  --id "DA 21" \
  --format text
```

## Pāli ↔ Chinese source-unit alignment

The repository now has a reproducible alignment layer for the first 20 Dīgha anchors.

Current generated source units:

- **9,990** Bilara Pāli leaf segments
- **3,031** Pāli paragraph units
- **42** benchmark-relevant Chinese discourse segments
- **2,189** CBETA Chinese text blocks
- **SF 36 (DN 14)** as the first reproducible Sanskrit edited-text witness: **943 segments**, including **496 segments with explicit `<supplied>` editorial markup**
- Chinese block extraction coverage: **98.01% minimum**, **99.77% mean**

Current machine review queue:

- **31** shared-opening-formula candidates
- **4,468** monotonic structural candidates
- **13,404** lexicon-assisted 1–3-block window candidates
- **0** machine candidates treated as established

The 26-entry seed lexicon retrieves the correct model-reviewed DN 1 ↔ DA 21 region in the top 3 for **18/18 seed Pāli units** (`overlap@3 = 1.0`, `full-cover@3 = 1.0`). This is a self-consistency sanity check against the same model-reviewed seed used to design the lexicon, **not** an independent accuracy estimate.

Alignment records are **many-to-many** so recension-level splitting and compression remain visible.

The first five model-reviewed passage alignments are in `data/alignments/model-reviewed.json` for **DN 1 ↔ DA 21**. They are explicitly `reviewer_type: model` and are not human-established.

The Indic availability audit currently covers all **61** Sanskrit/SHT witness IDs in the first-20 benchmark: **1** has actual edited text in the selected pinned Bilara upstream (SF 36), while **60** are marked `not_textualized_in_selected_upstream`. That status is intentionally narrower than “no edition exists”.

Run:

```bash
make alignment
```

See `docs/ALIGNMENT_PIPELINE.md`.

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
│   ├── build_agama_segments.py
│   ├── resolve_crosswalk_segments.py
│   ├── extract_agama_segment.py
│   ├── fetch_cbeta_agamas.sh
│   ├── build_pali_units.py
│   ├── build_indic_source_units.py
│   ├── build_chinese_alignment_units.py
│   ├── generate_alignment_candidates.py
│   ├── generate_anchor_window_candidates.py
│   ├── validate_alignments.py
│   ├── validate_crosswalks.py
│   └── render_crosswalks.py
├── docs/
│   ├── METHODOLOGY.md
│   ├── CATALOG_PIPELINE.md
│   ├── AGAMA_SEGMENTATION.md
│   └── ALIGNMENT_PIPELINE.md
├── catalog/
│   └── README.md
├── data/
│   ├── alignments/
│   ├── crosswalks/
│   └── texts/
├── generated/
│   ├── agama-segments/
│   ├── alignment-source/   # Pāli, Chinese, Indic derived source units
│   ├── alignments/
│   └── crosswalks/
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
