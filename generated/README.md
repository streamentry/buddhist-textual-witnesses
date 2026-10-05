# Generated research indexes

Files under this directory are reproducible derived data.

- `agama-segments/` is generated from the exact CBETA XML-P5 commit pinned by the repository.
- `crosswalks/first-20-resolved.json` is generated from the curated crosswalk benchmark plus the Āgama segment index.
- `alignment-source/pali/` is generated from pinned SuttaCentral Bilara Pāli root + HTML segmentation files.
- `alignment-source/chinese/` contains normalized source blocks for only the Chinese discourses used by the current benchmark.
- `alignments/` contains **machine candidates only**. These are not established textual alignments.

Do not hand-edit generated files. Change source configuration, scripts, source pins, curated crosswalks, or the curated human-review layer and rebuild.
