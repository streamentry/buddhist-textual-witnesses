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

Three candidate layers are generated.

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

### Lexicon-assisted candidate windows

A small reviewed seed lexicon in `data/alignments/lexicon.json` provides weighted Pāli ↔ Classical Chinese retrieval anchors for proper names, stock formulas, doctrinal vocabulary, and precepts. These entries are **search anchors**, not dictionary claims or proof of common ancestry.

For each Pāli paragraph, the retriever scores every consecutive Chinese window of 1–3 blocks using:

- saturated bilingual-anchor evidence;
- a weak monotonic position prior.

It keeps the top 3 windows. This explicitly supports one-to-many retrieval when a Chinese recension compresses several Pāli paragraphs into one block, or when one Pāli unit corresponds to several Chinese blocks.

The current model-reviewed DN 1 ↔ DA 21 batch is used only as a falsification/retrieval diagnostic. The pipeline reports `overlap@3`, `full-cover@3`, and overlap MRR. These metrics do **not** create scholarly confidence.

On the current 18 reviewed Pāli seed units, the 26-entry lexicon/window retriever returns:

```text
overlap@3:              1.0  (18/18)
full-cover@3:           1.0  (18/18)
mean reciprocal rank:  1.0
```

This is deliberately labeled a **self-consistency sanity check**, not a benchmark accuracy score. The lexicon was itself developed from the DN 1 seed, so the evaluation is not independent and should not be used to claim generalization to other suttas.

Outputs:

```text
generated/alignments/
├── shared-formula-candidates.jsonl
├── monotonic-candidates.jsonl
├── anchor-window-candidates.jsonl
├── anchor-window-evaluation.json
├── anchor-window-manifest.json
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

1. Sanskrit/BHS/Gāndhārī fragment source units where actual edited text is legally and reproducibly available;
2. stronger sequence/window retrieval with a larger independently reviewed seed set;
3. a human review UI showing Pāli, Chinese, Indic witnesses, provenance, and variant notes side by side.

## Indic edited-text source units

The alignment layer now has a separate Indic ingestion path. It only materializes witnesses whose **actual edited text** is available in a pinned, reproducible upstream.

For the current first-20 benchmark, the pinned Bilara snapshot exposes segmented Sanskrit text for **SF 36**, a DN 14 witness. The generated source layer contains **943 SF 36 segments**; **496** retain explicit `<supplied>` editorial markup. No generated segment currently contains `<gap>` or `<unclear>` in this upstream edition snapshot.

The availability audit covers all **61** Sanskrit/SHT witness IDs selected by the first-20 benchmark. Exactly **1** is currently `text_available` from the selected pinned Bilara source and **60** are `not_textualized_in_selected_upstream`. The latter means only “not ingestible from this selected reproducible upstream”, never “no edition exists elsewhere”.

Outputs:

```text
generated/alignment-source/indic/
├── segments.jsonl
├── units.jsonl
├── availability.json
└── manifest.json
```

Each Indic segment stores two distinct forms:

- `edition_text`: the upstream scholarly edition exactly enough to preserve editorial tags such as `<supplied>`;
- `search_text`: a derived text-only form for retrieval/alignment.

This distinction is non-negotiable. Reconstructed/supplied letters must remain visible as editorial intervention in the witness layer even if the search layer strips markup.


## DN 14 multi-witness vertical slice

The first end-to-end Pāli–Chinese–Sanskrit case study is stored at:

`data/case-studies/dn14-mahapadana/alignments.json`

It uses a separate multi-witness schema because a research passage may contain more than one Chinese recension and an Indic fragment at the same time.

Current witnesses:

- DN 14, Pāli anchor;
- DA 1, Dīrgha Āgama Chinese parallel;
- EA 48.4, Ekottarika Āgama Chinese parallel;
- SF 36, Sanskrit edited fragmentary witness.

The initial six model-reviewed passage alignments cover:

1. opening formula and setting;
2. monks' discussion of past Buddhas;
3. Buddha hearing, approaching, and asking;
4. the monks' report of their discussion;
5. seven Buddhas and kalpa chronology;
6. lifespans of the seven Buddhas.

The validator resolves every cited source-unit ID against generated Pāli, Chinese, and Sanskrit source layers. An `established` multi-witness alignment requires an accepted human review.

The generated human-readable report is:

`generated/case-studies/dn14-mahapadana.md`

In that report, Sanskrit text inside `⟦…⟧` corresponds to upstream `<supplied>` markup. This display convention does not alter the stored edition text.

### Example numerical variant

The lifespan passage intentionally preserves disagreement:

- DN 14: 80k / 70k / 60k / 40k / 30k / 20k;
- SF 36 prose: same sequence;
- DA 1 prose: same sequence;
- DA 1 verse: Vipassī becomes 84k;
- EA 48.4 prose: 84k / 70k / 60k / 50k / 40k / 20k.

No harmonized value is emitted.
