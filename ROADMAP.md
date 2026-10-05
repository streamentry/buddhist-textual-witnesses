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
- [ ] Validate curated witness JSON against schema in CI
- [ ] Add reviewed BHS language overrides where scholarship supports them

## Phase 2 — Early Buddhist parallel graph

Build a small, high-confidence benchmark before scaling.

- [ ] Choose 20 well-studied Pāli ↔ Chinese Āgama parallels
- [ ] Add Sanskrit/BHS witnesses where extant
- [ ] Add Gāndhārī/Prakrit witnesses where extant
- [ ] Record bibliographic support for every parallel link
- [ ] Add curated `crosswalks` that group equivalent upstream IDs into shared work IDs
- [ ] Distinguish exact, partial, shared-passage, and doctrinal parallels

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
