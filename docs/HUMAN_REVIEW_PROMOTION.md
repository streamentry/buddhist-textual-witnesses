# Human Review Promotion Protocol v1

This repository separates **evidence**, **human judgment**, and **promotion**.

## Invariant

```text
model review != human review
accepted human review != established
accepted human review + current evidence + explicit human promotion = established
```

An alignment's curated source record remains `model_reviewed`. Established status is a **derived state** from a valid promotion event. No promotion script silently rewrites the case-study alignment.

## Review evidence snapshot

Every new human review records:

- `evidence_snapshot.digest` — SHA-256 over the alignment claim plus the exact referenced source-unit records.
- `evidence_snapshot.source_revisions` — the pinned upstream project/revision/path tuples visible to the reviewer.

If any referenced source unit, source revision, member boundary, relation type, or variant claim changes, the digest changes. The old review becomes **stale for promotion** rather than being silently carried forward.

## Promotion record

A promotion must:

1. reference an existing alignment;
2. reference at least one accepted human review for that alignment;
3. use the same current evidence digest as the accepted review;
4. be performed by an explicitly named human actor;
5. declare `target_status: established`;
6. use policy `human-review-promotion-v1`.

Multiple model reviews never count as independent human reviews.

## Audit chain

```text
established claim
  -> promotion event
  -> accepted human review
  -> evidence digest
  -> exact alignment
  -> exact source-unit records
  -> pinned upstream revisions
```

## Commands

Validate human reviews:

```bash
make validate-human-reviews
```

Validate promotions and derive established state:

```bash
make validate-promotions
```

Run the full DN 14 vertical slice:

```bash
make case-study
```

The repository intentionally ships with zero human reviews and zero promotions until a real reviewer acts.
