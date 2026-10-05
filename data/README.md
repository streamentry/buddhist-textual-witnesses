# Curated data

This directory contains derived, reviewable research data. Bulk upstream corpora remain under `upstream/` as pinned submodules.

```text
data/
  crosswalks/
    first-20.json
    bibliography.json
    FIRST_20.md
    README.md
  texts/
    <work-id>/
      witnesses/
        <witness-id>.json
      alignments/
        <alignment-id>.json
```

## Crosswalks

`crosswalks/first-20.json` is the first curated benchmark linking Pāli anchors to independent Chinese and Indic textual witnesses. It keeps relation type, confidence, evidence, bibliography, and canonical container IDs explicit.

Validate with:

```bash
make benchmark
```

## Text records

`texts/` is for work- and witness-level curated metadata such as the T0825 case study.

Do not copy bulk upstream corpora into `data/`.
