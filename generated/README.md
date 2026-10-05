# Generated research indexes

Files under this directory are reproducible derived data.

- `agama-segments/` is generated from the exact CBETA XML-P5 commit pinned by the repository.
- `crosswalks/first-20-resolved.json` is generated from the curated crosswalk benchmark plus the Āgama segment index.
- `alignment-source/pali/` is generated from pinned SuttaCentral Bilara Pāli root + HTML segmentation files.
- `alignment-source/chinese/` contains normalized source blocks for only the Chinese discourses used by the current benchmark.
- `alignment-source/indic/` contains only Indic edited-text units actually available from selected pinned upstreams, plus an explicit availability audit for benchmark witness IDs.
- `alignments/` contains **machine candidates only**. These are not established textual alignments.
- `case-studies/` contains generated, source-backed comparative reports from curated case-study alignment data.

Do not hand-edit generated files. Change source configuration, scripts, source pins, curated crosswalks, or the curated human-review layer and rebuild.

Current Indic snapshot: SF 36 contributes 943 edited Sanskrit segments grouped into 396 auditable source units. The availability registry audits all 61 Sanskrit/SHT witness IDs in the first-20 benchmark and keeps unavailable-in-this-upstream distinct from nonexistent.

- review-packets/ contains generated Markdown human-review surfaces. They are derived from curated case-study data and human review records; they are not themselves review decisions.
- review-ui/ contains self-contained offline HTML review interfaces. They are read-only with respect to repository state and only prepare review JSON for explicit human handling.
