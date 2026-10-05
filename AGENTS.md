# AGENTS.md

## Purpose

This repository supports textual-critical study of Buddhist sources across multiple witness traditions.

## Non-negotiable rules

1. Do not invent Sanskrit, BHS, Gāndhārī, Prakrit, Chinese, or Tibetan witnesses.
2. A reconstructed form must be explicitly labeled `reconstructed`.
3. Do not call a modern edition a manuscript.
4. Do not infer an Indic original merely from a Chinese translation.
5. Do not collapse textual, doctrinal, and thematic parallels into one category.
6. Preserve provenance for every imported or normalized record.
7. Do not commit bulk upstream corpora unless their redistribution terms clearly allow it and the project explicitly decides to vendor them.
8. Prefer stable upstream identifiers over local filenames.
9. Record uncertainty instead of resolving it by guesswork.
10. When evidence conflicts, keep both readings and document the disagreement.
11. Never merge two upstream IDs into one `work_id` solely because their titles look similar. Add a reviewed crosswalk with bibliographic support.
12. Label a witness `bhs` only from explicit upstream metadata or a reviewed language override, not from heuristic language guessing.

## Preferred workflow

- Register and pin the source.
- Fetch according to licensing.
- Preserve raw witness upstream.
- Build the metadata catalog with `make catalog`.
- Normalize into a separate derived record.
- Map parallels with explicit relationship type.
- Add confidence and bibliographic support.
- Run `make test` before merge.
- Rebuild the catalog after source pins, language overrides, or crosswalks change.

## Current priority

Start with Early Buddhist parallel sets where independent witnesses exist across Pāli, Chinese Āgama, Sanskrit/BHS, and Gāndhārī/Prakrit.
