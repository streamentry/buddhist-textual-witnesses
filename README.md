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

## Repository layout

```text
.
├── sources/
│   └── manifest.yaml          # source registry and acquisition policy
├── schemas/
│   └── witness.schema.json    # metadata contract for a textual witness
├── scripts/
│   └── fetch_sources.sh       # reproducible downloader for permitted bulk sources
├── docs/
│   └── METHODOLOGY.md         # textual-critical rules and confidence model
├── data/
│   └── README.md              # normalized-data conventions
├── SOURCES.md                 # human-readable provenance and licensing notes
├── AGENTS.md                  # rules for humans and AI agents editing this repo
└── .gitignore
```

Large upstream corpora are intentionally **not committed**. Run the fetch script to place them under `vendor/`, which is git-ignored.

## Quick start

Requirements: `bash`, `git`, `curl`, and `unzip`.

```bash
chmod +x scripts/fetch_sources.sh
./scripts/fetch_sources.sh
```

This currently acquires the sources that have clear bulk/repository access:

1. **GRETIL** cumulative Sanskrit and Prakrit archives.
2. **SuttaCentral Bilara** Sanskrit, Prakrit, and Classical Chinese root texts from the published branch.
3. **CBETA XML-P5** with the Taishō volumes containing the principal Chinese Āgamas.

**Gandhari.org** and **DSBC** remain registered as authoritative research sources but are not bulk-mirrored by this repository unless their redistribution terms clearly permit it.

## First research target

The first useful milestone is not "download everything". It is a small set of high-confidence parallel maps:

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

## Status

**Bootstrap / research infrastructure.** Corpus acquisition and witness mapping are being built incrementally.

## Upstream rights

Upstream texts retain their own copyright, license, and attribution requirements. See [SOURCES.md](SOURCES.md) before redistributing any fetched material.
