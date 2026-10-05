# Human reviews for DN 14 / Mahāpadāna

Human review records are deliberately separate from model-reviewed case-study alignments and from promotion events.

## Review v2 invariants

- reviewer_type must be human.
- name and a stable reviewer_id are required.
- reviewed_at is an offset-aware ISO-8601 timestamp.
- every review binds the exact alignment claim and exact source-unit views through SHA-256 evidence digests.
- an accepted review requires all four assessments to be agree.
- accepted does not mean established.
- committed reviews are historical records and the ledger is append-only in CI. Do not edit an existing record; create a new record with `supersedes_review_id` pointing to the latest review by the same reviewer for that alignment.
- if the alignment claim or displayed source evidence changes later, the old review remains part of the audit history but becomes stale for current promotion purposes.

Files:

- reviews.json - committed human review decisions; starts empty.
- review-template.json - structural example. Prefer the generated review UI because it fills the evidence snapshot deterministically.
- ../../promotions/dn14-mahapadana/promotions.json - explicit promotion ledger.

Review surfaces:

- generated/review-packets/dn14-mahapadana.md
- generated/review-ui/dn14-mahapadana/index.html

The offline HTML UI never writes the repository and never invents reviewer identity. It prepares a schema-v2 record containing the evidence snapshot shown to the reviewer.

Current state remains intentionally empty: 0 human reviews and 0 promotion events.
