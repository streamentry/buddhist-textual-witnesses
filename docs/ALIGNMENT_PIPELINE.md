# Pāli ↔ Chinese source-unit alignment pipeline

## Goal

Move from discourse-level crosswalks such as:

```text
DN 1 ↔ DA 21
```

to auditable source units that can support phrase- and paragraph-level comparison:

```text
Bilara Pāli segment IDs / paragraphs
            ↕
CBETA paragraph and verse blocks
```

The pipeline deliberately separates **source segmentation**, **machine candidates**, **model review**, and **human-established scholarly assertions**. Alignment records are many-to-many: one passage may contain several Pāli units and several Chinese blocks.

## 1. Pāli source units

The Pāli side uses the exact SuttaCentral Bilara revision pinned in `sources/lock.json`.

For each of the first 20 DN anchors, the pipeline sparse-fetches:

```text
root/pli/ms/sutta/dn/dnN_root-pli-ms.json
html/pli/ms/sutta/dn/dnN_html.json
```

Bilara leaf IDs such as:

```text
dn1:1.1.1
dn1:1.1.2
dn16:1.4.5
```

are preserved unchanged.

The corresponding Bilara HTML templates provide paragraph and heading boundaries. A generated Pāli paragraph therefore records:

- exact constituent Bilara segment IDs
- first and last segment IDs
- normalized source text
- text SHA-256
- exact root/html paths and pinned revision

Outputs:

```text
generated/alignment-source/pali/
├── segments.jsonl
├── units.jsonl
├── lookup.json
└── manifest.json
```

## 2. Chinese source units

The Chinese side starts from the exact CBETA discourse records already resolved by the first-20 crosswalk benchmark.

Only benchmark-relevant resolved discourses are materialized as normalized text blocks. Raw CBETA remains upstream.

Block types currently preserved are:

- `p`
- `lg`
- `table`
- `list`

Each block records:

- canonical discourse ID
- Taishō container
- block ordinal
- source XML ID when present
- Taishō start/end line references
- relative XPath
- structural XML SHA-256
- normalized text and text SHA-256
- exact pinned source revision

Outputs:

```text
generated/alignment-source/chinese/
├── blocks.jsonl
├── lookup.json
└── manifest.json
```

The builder checks that block extraction covers at least 90% of the normalized discourse text. Falling below that threshold fails strict generation rather than silently discarding material.

## 3. Machine candidates

Two candidate layers are generated.

### Shared opening formula

A direct lexical rule detects:

```text
Evaṁ me sutaṁ
↕
如是我聞 / 聞如是 / 我聞如是
```

This is useful evidence **only for the formula itself**. It does not establish that the full surrounding paragraphs are equivalent.

### Monotonic structural ranking

For each Pāli paragraph, the pipeline finds the nearest Chinese block by normalized cumulative position within the known full-parallel discourse pair.

The ranking score combines:

- relative position similarity
- relative unit-length similarity

This is deliberately weak. It exists to order a review queue, not to make a textual-critical claim.

Outputs:

```text
generated/alignments/
├── shared-formula-candidates.jsonl
├── monotonic-candidates.jsonl
└── manifest.json
```

## 4. Many-to-many alignment model

Alignment records use arrays:

```json
{
  "pali_unit_ids": ["DN 1#p0001", "DN 1#p0002"],
  "chinese_unit_ids": ["DA 21#b0001", "DA 21#b0002"]
}
```

This is essential because recensions frequently merge, split, omit, or reorder material. The schema does not force a false 1↔1 geometry onto the witnesses.

## 5. Review boundary

All generated records have:

```text
status: machine_candidate
assertion: not_established
```

A record may become `established` only when a human reviewer explicitly records an accepted decision in the curated review layer:

`data/alignments/reviewed.json`

Model-assisted comparative reviews are kept separately in `data/alignments/model-reviewed.json`. They may be `status: reviewed`, but **never** `status: established` unless a human accepts them.

The validator rejects:

- unresolved source-unit references
- machine candidates mislabeled as established
- established alignments without human acceptance
- structural-ranking output promoted directly to established
- shared-formula candidates whose claimed formulas are absent from the source units

This boundary is intentional. Similar position is not textual evidence, and a shared stock formula is not proof of paragraph identity.

## Initial model-reviewed batch

The first curated comparison is **DN 1 ↔ DA 21**. Five passage alignments have been reviewed at source-unit level and stored as model-reviewed claims:

1. opening narrative, including Suppiya/善念 and Brahmadatta/梵摩達;
2. monks discuss the teacher/disciple praise-blame contrast;
3. Buddha enters the hall, asks, and the monks report their discussion;
4. partial overlap in the instruction about reacting to criticism and praise;
5. the opening of the minor-morality section, where eight Pāli paragraphs are compressed into one Chinese block.

These reviews explicitly preserve differences and compression. They are not human-established.

## Commands

Build everything locally:

```bash
make alignment
```

Validate the current candidate/review layer:

```bash
make validate-alignments
```

## Next research step

The next layer should add stronger signals without weakening the epistemic boundary:

1. reviewed bilingual anchor lexicon for names, locations, doctrinal terms, and repeated formulas;
2. candidate windows rather than single-block guesses;
3. Sanskrit/BHS/Gāndhārī fragment source units where actual edited text is legally and reproducibly available;
4. a human review UI showing Pāli, Chinese, Indic witnesses, provenance, and variant notes side by side.
