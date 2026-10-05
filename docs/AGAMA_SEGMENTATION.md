# CBETA Āgama discourse segmentation

## Goal

Turn whole-container CBETA XML files into exact discourse-level locators so scholarly IDs such as `DA 21`, `MA 98`, `SA 1192`, `SA2 105`, and `EA 48.4` resolve to a reproducible local span.

Raw CBETA text is **not duplicated** in this repository. The generated layer stores metadata, source revision, exact structural locator, Taishō line span, and hashes. Text or XML can be extracted on demand from the pinned CBETA source.

## Collections

| Project ID | Taishō container | ID mode | Structural `經` nodes | Canonical discourses | Supplements |
|---|---|---|---:|---:|---:|
| DA | T0001 | global | 30 | 30 | 0 |
| MA | T0026 | global | 222 | 222 | 0 |
| SA | T0099 | global | 1,355 | 1,355 | 0 |
| SA2 | T0100 | global | 364 | 364 | 0 |
| EA | T0125 | chapter.item | 472 | 471 | 1 |

Total: **2,443 structural segments = 2,442 canonical discourse segments + 1 supplement**.

The T0125 non-canonical node is explicitly labelled `5（卷末附文）` by CBETA and sits outside every `品`. It is preserved as `T0125 supplement 1`; the pipeline does not invent an `EA x.5` identifier for it.

## Structural rule

A discourse segment is:

> any `div` with a **direct child** `mulu type="經"`.

Do not use `div/@type="jing"` alone. T0100 contains 364 discourse markers but its containers are represented as `div type="other"`.

## Numbering

### DA / MA / SA / SA2

Use the **visible leading number in the `mulu` text** as the canonical discourse number.

This matters for T0099. CBETA has 1,355 discourse nodes, but visible canonical numbering extends to SA 1362 because seven numbers are absent. Late in the file, internal `mulu/@n` and visible numbering diverge.


For the pinned 2026.R2 witness, the missing canonical numbers are:

```text
141, 144, 756, 757, 773, 774, 812
```

### EA

EA numbering is local to a `品` chapter. The canonical ID is:

```text
EA <nearest 品 number>.<discourse number>
```

For example, chapter 48 discourse 4 becomes `EA 48.4`.

## Generated outputs

`make agama` produces:

```text
generated/
├── agama-segments/
│   ├── da.jsonl
│   ├── ma.jsonl
│   ├── sa.jsonl
│   ├── sa2.jsonl
│   ├── ea.jsonl
│   ├── lookup.json
│   └── manifest.json
└── crosswalks/
    └── first-20-resolved.json
```

Each structural segment record includes a `record_kind` of `canonical` or `supplement`, plus:

- canonical ID and container
- title / `mulu` / `head`
- structural hierarchy
- exact pinned CBETA revision
- XPath by discourse ordinal
- starting and ending Taishō `lb` references
- starting/ending juan when available
- structural XML SHA-256
- normalized reading-text SHA-256
- normalized character count

The XPath form is intentionally namespace-prefix independent:

```text
(//*[local-name()='div'][*[local-name()='mulu' and @type='經']])[N]
```

## Why both XPath and hashes?

A line reference is useful to humans but is not sufficient for machine identity. A discourse is therefore pinned by:

```text
CBETA commit
+ source XML path
+ structural XPath/ordinal
+ Taishō line span
+ structural fingerprint
```

If upstream structure changes, `extract_agama_segment.py` refuses to extract a segment whose fingerprint no longer matches.

## Commands

Build everything:

```bash
make agama
```

Extract one discourse as normalized text:

```bash
python3 scripts/extract_agama_segment.py \
  --cbeta-root .cache/cbeta-agamas \
  --segments generated/agama-segments \
  --id "DA 21" \
  --format text
```

Inspect metadata:

```bash
python3 scripts/extract_agama_segment.py \
  --cbeta-root .cache/cbeta-agamas \
  --segments generated/agama-segments \
  --id "EA 48.4" \
  --format metadata
```

Exact XML for the discourse can be emitted with `--format xml`.

## Crosswalk resolution

The curated benchmark remains the scholarly source of truth at:

`data/crosswalks/first-20.json`.

The generated file:

`generated/crosswalks/first-20-resolved.json`

adds a `local_resolution` object to DA/MA/SA/SA2/EA witnesses. Standalone Taishō texts such as `T 21` remain bibliographic references because they are outside the five-container segmentation scope.

Ranges such as `SA 154–163` are expanded into individual segment records and fail strict validation if any requested canonical ID is unavailable.

## Epistemic boundary

Segmentation identifies **where a discourse lives in the pinned Chinese witness**. It does not by itself prove that a Pāli and Chinese discourse are exact textual equivalents. Parallel classification continues to come from the curated crosswalk evidence layer.

## Verified benchmark resolution

The first-20 curated benchmark currently contains **33** Chinese collection references in the DA/MA/SA/SA2/EA namespaces. Strict resolution against the generated index produced:

```text
collection_witnesses: 33
resolved_witnesses:   33
resolved_segments:    42
unresolved_witnesses: 0
```

The segment count is larger than the witness count because ranges such as `SA 154–163` expand to individual discourse segments.

## Verified source revision

All generated records in the current committed snapshot derive from:

```text
CBETA XML-P5
commit dbdea41071e1e260ad84b72faefd4587333cf76d
release lineage: 2026.R2
```

Changing the upstream pin requires regenerating the metadata and re-verifying the structural fingerprints.
