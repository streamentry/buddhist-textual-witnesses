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

The initial nine model-reviewed passage alignments cover:

1. opening formula and setting;
2. monks' discussion of past Buddhas;
3. Buddha hearing, approaching, and asking;
4. the monks' report of their discussion;
5. seven Buddhas and kalpa chronology;
6. lifespans of the seven Buddhas;
7. caste pattern across the seven Buddhas;
8. family/clan names with an explicit Sanskrit textual-loss locus;
9. Bodhi trees with an explicit Sanskrit textual-loss locus.

The validator resolves every cited source-unit ID against generated Pāli, Chinese, and Sanskrit source layers. Multi-witness case-study rows are never allowed to set `status: established` directly; `established` is a derived state produced only from an evidence-bound accepted human review plus a separate explicit promotion event. A member marked `coverage: lost_text_marker` must resolve to a source unit that explicitly signals textual loss; the marker cannot be used as a generic stand-in for missing data.

When a row preserves a textual-loss locus alongside surviving witnesses, `relation_member_ids` explicitly scopes the row-level `relation_type` to the witnesses that actually preserve wording. A `lost_text_marker` member cannot appear in `relation_member_ids`, and every such member requires a `textual_loss` variant claim. This lets the graph preserve the lost locus without implying that absent Sanskrit wording participates in a textual parallel.

This scope is now explicit on **every** multi-witness alignment, not only loss cases. Each member also declares `editorial_features` (`supplied`, `gap`, `unclear`), and validation derives the expected feature set from the pinned source units. A case-study claim therefore fails validation if, for example, it cites a Sanskrit unit containing `<supplied>` while declaring no supplied material.

The generated human-readable report is:

`generated/case-studies/dn14-mahapadana.md`

In that report, Sanskrit text inside `⟦…⟧` corresponds to upstream `<supplied>` markup. This display convention does not alter the stored edition text.

### Example numerical and semantic variant

The lifespan-list locus intentionally preserves both numerical disagreement and a difference in what is being measured:

- DN 14 explicitly gives the Buddhas' lifespans: 80k / 70k / 60k / 40k / 30k / 20k;
- SF 36 prose likewise gives Buddha lifespans with the same sequence;
- DA 1 prose instead says **人壽**, human lifespan in each Buddha's era: 80k / 70k / 60k / 40k / 30k / 20k;
- DA 1 verse still describes human lifespan but changes Vipassī's era to 84k;
- EA 48.4 explicitly gives Tathāgata lifespans: 84k / 70k / 60k / 50k / 40k / 20k.

Because the semantic subject is not identical across all four witnesses, the current multi-witness row is conservatively classified as `structural_correspondence`, not `parallel_passage`. No harmonized value or subject is emitted.

### Textual loss as first-class evidence

The DN 14 slice now includes two Sanskrit loss loci from SF 36:

- **Family Name** → `SF 36#p0019`
- **Bodhi Trees** → `SF 36#p0020`

In both cases the edited Sanskrit source explicitly states that the text is completely lost. The alignment layer keeps those loci in the graph with `coverage: lost_text_marker`, allowing surviving Pāli and Chinese witnesses to remain comparable without inventing Sanskrit wording. Their row-level relations are scoped with `relation_member_ids` to the surviving Pāli and Chinese witnesses only.

## Human review and explicit promotion

Model review, human review, and establishment are three intentionally separate layers.

Human decisions live under:

`data/reviews/dn14-mahapadana/`

Explicit promotion events live under:

`data/promotions/dn14-mahapadana/`

The current ledgers intentionally begin empty. A human review must identify a real human reviewer with a stable `reviewer_id`, reference an existing alignment, and assess source-unit boundaries, relation type, variant notes, and editorial handling. Review schema v2 also binds the exact alignment claim and the exact source-unit views shown to the reviewer using SHA-256 digests.

The preferred review surface is the self-contained offline UI:

`generated/review-ui/dn14-mahapadana/index.html`

The Markdown packet at `generated/review-packets/dn14-mahapadana.md` remains a plain-text audit surface. The HTML UI computes the evidence snapshot from the exact embedded source views in the browser. It cannot write to the repository or promote anything.

The state transition is deliberately two-phase:

```text
model_reviewed
      ↓
accepted fresh human review
      ↓
promotion_required
      ↓
explicit human promotion event
      ↓
established
```

The following are hard invariants:

- model reviews never count as human reviews, regardless of quantity;
- `accepted` requires all four human assessments to be `agree`;
- an accepted review is not itself an establishment event;
- review and promotion ledgers are append-only in CI;
- a corrected human review is appended as a new record with `supersedes_review_id`; the previous record is not edited;
- each promotion binds one exact review record and its evidence digest;
- if an alignment claim, source text, source locator, or pinned revision changes, the affected review becomes stale for current promotion purposes;
- historical review and promotion events remain in the audit trail after drift;
- a superseded review cannot be used for a new promotion;
- `status: established` is rejected inside curated case-study rows.

Current state is derived into:

`generated/promotion-state/dn14-mahapadana.json`

Possible current states are:

- `model_reviewed` — no active accepted human review;
- `promotion_required` — an active accepted review is fresh but has no matching current promotion;
- `established` — an explicit promotion references an active, fresh accepted review;
- `review_stale` — historical review/promotion evidence exists but no longer binds the current source/claim state.

Validate the ledgers and rebuild derived state with:

```bash
make validate-human-reviews
make validate-promotions
make promotion-state
```

To prepare an explicit promotion, run `scripts/promote_alignment.py` without `--write`. The command prints the event but does not mutate the ledger. Supplying `--write` is the explicit mutation boundary. It refuses stale, rejected, model-authored, or superseded reviews.

There is intentionally no transition of the form:

```text
AI confidence
→ established
```
