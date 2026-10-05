# Alignment review layer

This directory contains **curated review decisions**, not machine-generated candidates.

Generated candidates live under `generated/alignments/`.

## Promotion rule

A candidate may become `status: established` only after a human reviewer records:

- `review.status = reviewed`
- `review.reviewer_type = human`
- `review.decision = accepted`
- reviewer identity and notes/evidence

A model-generated score, positional similarity, shared opening formula, or discourse-level parallel classification is never sufficient by itself.

## Current state

`reviewed.json` intentionally starts empty. The pipeline first creates an auditable review queue; established paragraph/phrase alignments are added only after textual inspection.
