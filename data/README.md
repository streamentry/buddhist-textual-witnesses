# Normalized data

This directory is for curated, normalized witness records produced from upstream material.

Suggested layout:

```text
data/
  texts/
    <work-id>/
      witnesses/
        <witness-id>.json
      alignments/
        <alignment-id>.json
```

Do not place bulk upstream corpora here. Those belong under git-ignored `vendor/`.
