# Catalog pipeline

The catalog pipeline converts three pinned upstream corpora into one provenance-first index:

```text
work_id
  -> language
    -> witness
      -> source
```

It does **not** copy raw texts out of their upstream repositories and it does not infer textual equivalence from similar titles.

## Inputs

- `upstream/suttacentral-bilara/root/san/**` — Sanskrit root texts
- `upstream/suttacentral-bilara/root/pra/**` — Prakrit root texts
- `upstream/gretil-mirror/.../corpustei/*.xml` — TEI editions whose own GRETIL metadata identifies them as Buddhist
- Six configured CBETA Āgama witnesses: T0001, T0026, T0099, T0100, T0101, T0125

Exact source revisions come from `sources/lock.json`.

## Outputs

Running `make catalog` writes:

- `catalog/catalog.json` — nested `work_id -> language -> witness[]`
- `catalog/catalog.jsonl` — one witness per line for streaming/grep
- `catalog/catalog.csv` — spreadsheet-friendly flat index
- `catalog/stats.json` — counts by source and language

The outputs are deterministic for the same upstream revisions and configuration.

## Canonical IDs and work IDs

The pipeline preserves source-native IDs:

- Taishō: `T0001`, `T0099`, ...
- SuttaCentral: `sf36`, `pdhp1-13`, ...
- GRETIL: TEI `xml:id`, e.g. `sa_AryAnityatAsUtra`

A `work_id` groups witnesses believed to represent the same work. By default it is source-qualified, for example `suttacentral:sf36` or `gretil:sa_AryAnityatAsUtra`.

Only curated entries in `config/catalog.json -> crosswalks` may merge two upstream IDs under one project work ID. This is deliberate: title similarity is not evidence of textual identity.

Example:

```json
{
  "crosswalks": {
    "suttacentral:sf36": "work:mahavadana",
    "gretil:sa_example": "work:mahavadana"
  }
}
```

Add such mappings only with bibliographic support.

## Sanskrit vs Buddhist Hybrid Sanskrit

The pipeline includes Buddhist Sanskrit material from GRETIL and Sanskrit material from SuttaCentral.

It labels a witness `bhs` only when:

1. upstream metadata explicitly says “Buddhist Hybrid Sanskrit”, or
2. `config/catalog.json -> language_overrides` explicitly marks the witness as BHS.

It does **not** infer BHS from word forms. Many texts commonly discussed as BHS or mixed Sanskrit may therefore remain labeled `san` until reviewed. That false-negative bias is intentional.

Example override:

```json
{
  "language_overrides": {
    "gretil:sa_someText": "bhs"
  }
}
```

## Buddhist filtering in GRETIL

GRETIL contains far more than Buddhist literature. The filter accepts a TEI witness only when its own header provides explicit Buddhist provenance, primarily a legacy GRETIL source path containing `/buddh/`, or explicit Sanskrit Buddhist project metadata.

No keyword search of the scripture body is used.

## CBETA scope

This stage intentionally selects the major Āgama collections rather than all of Taishō:

| ID | Collection |
|---|---|
| T0001 | Dīrgha Āgama / 長阿含經 |
| T0026 | Madhyama Āgama / 中阿含經 |
| T0099 | Saṃyukta Āgama / 雜阿含經 |
| T0100 | alternate Saṃyukta / 別譯雜阿含經 |
| T0101 | short Saṃyukta witness / 雜阿含經 |
| T0125 | Ekottarika Āgama / 增壹阿含經 |

The list is explicit in `config/catalog.json`, so expansion is reviewable rather than accidental.

## Commands

```bash
make fetch
make test
make catalog
```

Or directly:

```bash
python3 scripts/build_catalog.py --strict
```

`--strict` verifies that all three upstream sources are present and that each emits at least one witness. By default the script also checks that checked-out submodule SHAs match `sources/lock.json`.

## Updating sources

Do not silently build against moving branches. Update the submodule gitlink and `sources/lock.json` together, review the diff in catalog output, then commit both.

## GitHub Actions

- `CI` runs unit tests without downloading the large corpora.
- `Refresh catalog` is manual. It checks out submodules, builds the catalog, uploads the result as an artifact, and commits changed catalog files back to the selected branch.
