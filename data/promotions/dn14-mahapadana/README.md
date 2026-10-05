# Explicit promotions for DN 14 / Mahāpadāna

This directory is the audit ledger for transitions to the derived status established.

A promotion is a separate human action from a human review. It must reference one exact accepted review by review_id, review_digest, and evidence_digest.

The policy intentionally enforces:

accepted human review != established

accepted fresh human review + explicit valid promotion = established

If source evidence or the alignment claim later drifts, the historical promotion event is retained, while the current derived status becomes review_stale until fresh review and promotion evidence exists.

Use scripts/promote_alignment.py without --write to preview an event. Adding --write is the explicit repository mutation.
