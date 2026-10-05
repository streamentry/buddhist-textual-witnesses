# Alignment review layer

This directory contains **curated review decisions**, not machine-generated candidates.

Generated candidates live under `generated/alignments/`.

## Files

- `reviewed.json` — human-reviewed/established layer. It intentionally starts empty.
- `model-reviewed.json` — model-assisted comparative reviews. These may record accepted model judgments but are **not established scholarship**.

## Many-to-many model

A reviewed alignment may link multiple source units on either side:

```text
Pāli [p1, p2]
    ↕
Chinese [b1, b2]
```

This preserves recension-level splitting and compression instead of forcing 1↔1 alignment.

## Promotion rule

A candidate may become `status: established` only after a human reviewer records:

- `review.status = reviewed`
- `review.reviewer_type = human`
- `review.decision = accepted`
- reviewer identity and notes/evidence

A model review, positional score, shared opening formula, or discourse-level parallel classification is never sufficient by itself.

## Current reviewed batch

`model-reviewed.json` contains the first five source-unit comparisons for **DN 1 ↔ DA 21**. They are deliberately labeled `reviewer_type: model`.
