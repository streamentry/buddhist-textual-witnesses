# DN 14 human review guide

## Purpose

This guide is for a real human reviewer assessing the model-reviewed DN 14 / DA 1 / EA 48.4 / SF 36 vertical slice.

A human review is scholarly evidence, not a ceremonial approval. If any source boundary, relation type, variant note, or editorial treatment is uncertain, record `uncertain` or `revise`; do not accept the row merely because the current model confidence is high.

The repository never treats model judgment as human review and never promotes an alignment automatically.

## Recommended reviewer profile

The ideal reviewer is comfortable with early Buddhist parallel literature and can directly inspect at least two of the following while responsibly evaluating the others from the cited editions:

- Pāli Nikāya text;
- Classical Chinese Āgama text;
- Buddhist Sanskrit / fragment editions;
- comparative early Buddhist textual criticism.

A stable reviewer identity is required. ORCID is preferred when available; a stable institutional or GitHub identifier is acceptable if it unambiguously identifies the reviewer.

## Fastest legitimate first milestone

For the first end-to-end test of the review → promotion pipeline, start with:

`mw:dn14:opening-setting:01`

Why this row first:

- the narrative locus is clear;
- the relation is formulaic and structural rather than doctrinally subtle;
- all four witnesses preserve the locus;
- the Sanskrit editorially supplied letters are visibly marked;
- disagreement is limited mainly to residence-detail granularity.

This is a workflow pilot, not a claim that the row is automatically correct. The reviewer must still inspect all four witnesses.

After the pipeline is exercised successfully on one accepted row, continue through all nine alignments.

## Suggested review order

### Lower interpretive risk

1. `mw:dn14:opening-setting:01`
2. `mw:dn14:buddha-hears-asks:03`
3. `mw:dn14:bodhi-tree-loss:09`

### Moderate interpretive risk

4. `mw:dn14:caste:07`
5. `mw:dn14:seven-buddhas-kalpas:05`
6. `mw:dn14:monks-report:04`

### Specialist attention recommended

7. `mw:dn14:lifespans:06`
8. `mw:dn14:monks-discussion:02`
9. `mw:dn14:family-name-loss:08`

The last three are intentionally not simplified:

- **lifespans:06**: DA 1 uses `人壽`, human lifespan in the Buddha's era, while DN 14 / SF 36 / EA 48.4 frame Buddha or Tathāgata lifespan; numerical similarity must not erase this semantic difference;
- **monks-discussion:02**: `dharmadhātu`, `法性`, `法處`, and the later EA `法界` are preserved witness-by-witness; the current alignment does not assert lexical identity;
- **family-name-loss:08**: EA 48.4 preserves two incompatible nearby clan-name sequences, while SF 36 preserves only a textual-loss locus.

## Review surface

Preferred interface:

`generated/review-ui/dn14-mahapadana/index.html`

Plain-text audit surface:

`generated/review-packets/dn14-mahapadana.md`

The HTML UI is self-contained and read-only. It:

- shows the exact source units used by each alignment;
- highlights Sanskrit `<supplied>` material;
- shows provenance and pinned revisions;
- displays current model relation / variant claims;
- prepares schema-v2 evidence-bound review JSON;
- never writes to the repository;
- never promotes an alignment.

## Four required assessments

For every alignment, the reviewer must independently assess:

1. **source_units** — Are the cited units the correct textual locus and boundaries?
2. **relation_type** — Is the relation classification justified by the surviving evidence?
3. **variant_notes** — Are disagreements described accurately without harmonization?
4. **editorial_handling** — Are supplied/restored/lost materials represented transparently?

An `accepted` review is valid only when all four assessments are `agree`.

If any dimension is `revise` or `uncertain`, use `needs_work` or `rejected` as appropriate and explain why.

## Recording a review safely

The UI prepares one evidence-bound JSON record per alignment.

Save that JSON to a local file, for example:

```bash
/tmp/dn14-review.json
```

First run a dry validation:

```bash
python scripts/record_human_review.py --review /tmp/dn14-review.json
```

The command checks:

- reviewer is explicitly human and has a stable reviewer ID;
- review schema is current;
- alignment ID exists;
- evidence digests match the current claim;
- all cited source-unit evidence is fresh;
- accepted reviews have all four assessments set to `agree`;
- the review ID is new;
- same-reviewer corrections supersede the latest earlier record;
- no promotion is created.

If the dry run is correct, explicitly append:

```bash
python scripts/record_human_review.py --review /tmp/dn14-review.json --write
```

Then run:

```bash
make validate-human-reviews
make promotion-state
```

Commit the changed review ledger and regenerated promotion state through the normal repository workflow.

## Append-only rule

Do not edit an earlier human review in place.

A correction is a new record with:

```json
"supersedes_review_id": "review:..."
```

The prior review remains part of the audit trail.

## Promotion boundary

An accepted fresh human review does **not** establish an alignment.

The state becomes:

```text
promotion_required
```

Only a separate explicit human promotion event may produce:

```text
established
```

Use `scripts/promote_alignment.py` only after the accepted review is committed and validated. Its default mode is non-mutating; `--write` is the explicit promotion boundary.

## Reviewer red flags

Do not accept a row merely because:

- wording appears similar after normalization;
- numerical values happen to match;
- a Chinese term looks like an obvious translation of a Sanskrit term;
- a Sanskrit edition supplies enough text to make a passage readable;
- a lost Sanskrit locus sits in the expected structural position;
- all model confidence labels are high.

The question is always narrower: **what do these exact witnesses, in these exact source units, actually support?**

## Completion criteria

The DN 14 slice is fully human-reviewed only when all nine current alignment claims have active, fresh human review records.

The first pipeline milestone is reached earlier: one current alignment has a fresh accepted human review and can legitimately enter `promotion_required`.
