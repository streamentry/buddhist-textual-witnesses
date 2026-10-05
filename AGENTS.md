# AGENTS.md

## Purpose

This repository supports textual-critical study of Buddhist sources across multiple witness traditions.

## Non-negotiable rules

1. Do not invent Sanskrit, BHS, Gāndhārī, Prakrit, Chinese, or Tibetan witnesses.
2. A reconstructed form must be explicitly labeled `reconstructed`.
3. Do not call a modern edition a manuscript.
4. Do not infer an Indic original merely from a Chinese translation.
5. Do not collapse textual, doctrinal, thematic, fragmentary, and partial relationships into one category.
6. Preserve provenance for every imported or normalized record.
7. Do not commit bulk upstream corpora unless their redistribution terms clearly allow it and the project explicitly decides to vendor them.
8. Prefer stable upstream identifiers over local filenames.
9. Record uncertainty instead of resolving it by guesswork.
10. When evidence conflicts, keep both readings and document the disagreement.
11. Never merge two upstream IDs into one `work_id` solely because their titles look similar. Add a reviewed crosswalk with bibliographic support.
12. Label a witness `bhs` only from explicit upstream metadata or a reviewed scholarly override, not from heuristic language guessing.
13. Do not use `exact_parallel` for independent recensions. Use `full_textual_parallel` unless evidence truly establishes identity at the relevant textual level.
14. A fragmentary manuscript witness is not automatically a `partial_textual_parallel`. Fragmentary describes physical/textual survival; partial describes the relationship between discourse contents.
15. A Chinese discourse ID such as `DA 21` must not be collapsed into its whole canonical container `T0001`.
16. Cross-tradition witnesses must retain their tradition label. In particular, the DN 23 Prākrit Paesi witness must remain marked as Jain.
17. Chinese Āgama discourse IDs must resolve through generated segment metadata, not by assuming the whole Taishō container is the discourse.
18. For T0099, canonical SA numbering comes from visible `mulu` text, not `mulu/@n`.
19. For T0125, a `mulu type="經"` outside every `品` is not automatically an EA canonical discourse; preserve source-labelled supplements separately.
20. Do not hand-edit files under `generated/`; regenerate them from pinned upstream data and curated inputs.
21. Source-unit alignments are many-to-many. Never force 1↔1 when a recension merges, splits, omits, or reorders material.
22. A model-reviewed alignment is not an established alignment. Only an accepted human review may set `status=established`.
23. A shared stock formula such as `Evaṁ me sutaṁ ↔ 如是我聞` establishes only the formula-level correspondence unless additional passage evidence is reviewed.
24. Positional/length similarity is a review-queue heuristic, not textual evidence. Structural-ranking output may never be promoted directly to `established`.
25. Bilingual lexicon entries are retrieval anchors only. Never treat a lexicon match as proof of textual descent, translation equivalence in every context, or an established passage alignment.
26. Retrieval evaluation against model-reviewed seed alignments is a diagnostic, not a human gold standard and not a scholarly confidence score.

## Preferred workflow

- Register and pin the source.
- Fetch according to licensing.
- Preserve raw witness upstream.
- Build the metadata catalog with `make catalog`.
- Normalize into a separate derived record.
- Map parallels with explicit relationship type.
- Add confidence and bibliographic support.
- Run `make benchmark` before merging crosswalk changes.
- Rebuild the corpus catalog after source pins, language overrides, or catalog crosswalks change.

## Current priority

Build reviewed many-to-many source-unit alignments on top of the resolved Pāli/Chinese source layer, then ingest directly attested Sanskrit/BHS/Gāndhārī fragment text where provenance and redistribution allow.
