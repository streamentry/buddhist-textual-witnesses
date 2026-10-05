# Roadmap

## Phase 1 — Reproducible source layer

- [x] Repository architecture
- [x] Witness metadata schema
- [x] Provenance and licensing rules
- [x] Pin SuttaCentral, CBETA, and GRETIL as exact upstream revisions
- [x] Add source revisions to a machine-readable lockfile
- [x] Unified Buddhist Sanskrit/Prakrit/Āgama catalog pipeline
- [x] Unit-test catalog filtering and grouping in CI
- [x] Manual workflow to rebuild and commit the generated catalog
- [x] First case study: T0825
- [x] Crosswalk schema and standard-library validator
- [ ] Validate all curated per-text witness JSON against schema in CI
- [ ] Add reviewed BHS language overrides where scholarship supports them

## Phase 2 — Early Buddhist parallel graph

Build a small, high-confidence benchmark before scaling.

- [x] Choose 20 well-studied Pāli ↔ Chinese textual parallels
- [x] Add Sanskrit witnesses where extant
- [x] Add Gāndhārī/Prakrit witnesses where extant
- [x] Record bibliographic support for every crosswalk
- [x] Distinguish full, partial, fragmentary, shared-passage, and doctrinal relations
- [x] Add automated validation preventing “exact parallel” overclaiming
- [x] Preserve Chinese discourse IDs separately from their Taishō container IDs
- [x] Segment DA/MA/SA/SA2/EA CBETA XML into individual discourse records
- [x] Resolve the first 20 crosswalk IDs directly to local segment-level source paths
- [x] Verify 2,443 CBETA structural segments against pinned 2026.R2 source
- [x] Record exact XPath, Taishō line spans, juan spans, and hashes
- [x] Resolve all 33 collection references in the first-20 benchmark to 42 local segments with 0 unresolved
- [ ] Extend the benchmark to 50 high-confidence works after the segment layer is stable

## Phase 3 — Alignment

- [ ] Define segment-level alignment schema
- [ ] Preserve source segmentation
- [ ] Add normalized search text as a derived layer
- [ ] Add automated candidate matching
- [ ] Require human-reviewed status before treating a match as established

## Phase 4 — Research interface

- [ ] Generate static catalog pages
- [ ] Search by canonical identifier, title, language, school, and source
- [ ] Parallel-view interface
- [ ] Variant visualization
- [ ] Provenance graph

## Stop condition

Do not scale ingestion merely because more text is available. Expand only when provenance, licensing, identifiers, and witness distinctions remain auditable.
