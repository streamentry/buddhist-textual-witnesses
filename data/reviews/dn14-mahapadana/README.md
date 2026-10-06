# Human reviews for DN 14 / Mahāpadāna

Human review records are deliberately separate from model-reviewed alignments and from explicit promotions.

Files:

- `reviews.json` — committed human review decisions; starts empty.
- `review-template.json` — review record shape.
- `promotions.json` — explicit promotion events; starts empty.
- `promotion-template.json` — promotion record shape.

## Boundary

```text
model review != human review
accepted human review != established
accepted human review + current evidence + explicit human promotion = established
```

Each review carries an `evidence_snapshot` generated from the exact alignment claim and referenced source-unit records. If those records or pinned revisions drift, the review becomes stale for promotion.

Use either generated review surface:

- `generated/review-packets/dn14-mahapadana.md`
- `generated/review-ui/dn14-mahapadana/index.html`

The HTML UI is self-contained and offline-first. It prepares review JSON including the current evidence digest and source revisions. It never writes to the repository, fabricates reviewer identity, or promotes an alignment.

Promotion is a separate, auditable human action validated by `scripts/validate_promotions.py`. Established status is derived from valid promotion events; the curated case-study alignment remains unchanged.

See `docs/HUMAN_REVIEW_PROMOTION.md`.

Current committed state: **0 human reviews, 0 promotions, 0 established alignments**.
