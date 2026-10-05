# Sources and provenance

This repository distinguishes between **pinning an upstream source**, **deriving curated metadata**, and **redistributing a third-party compilation**.

## Pinned upstream repositories

### SuttaCentral Bilara

- Repository: `suttacentral/bilara-data`
- Branch: `published`
- Pinned under: `upstream/suttacentral-bilara/`
- Relevant roots:
  - `root/san` — Sanskrit
  - `root/pra` — Prakrit
  - `root/lzh` — Classical Chinese
- Note: individual publications/source texts may carry their own source and licensing metadata. Do not infer one blanket license for every file solely from repository visibility.

### CBETA XML-P5

- Repository: `cbeta-org/xml-p5`
- Pinned under: `upstream/cbeta-xml-p5/`
- Current pin: CBETA 2026.R2 lineage.
- Purpose: canonical Chinese Buddhist witnesses, including the principal Āgamas.
- Principal Āgamas:
  - T0001 長阿含經 — Dīrgha Āgama
  - T0026 中阿含經 — Madhyama Āgama
  - T0099 雜阿含經 — Saṃyukta Āgama
  - T0100 別譯雜阿含經 — Alternate Saṃyukta Āgama
  - T0101 雜阿含經 — Short Saṃyukta witness
  - T0125 增壹阿含經 — Ekottarika Āgama
- Rights: follow CBETA's own copyright/usage statement. The submodule does not relicense CBETA content.

### GRETIL

- Repository: `INDOLOGY/GRETIL-mirror`
- Pinned under: `upstream/gretil-mirror/`
- Purpose: machine-readable Sanskrit and Prakrit/Indic text corpus.
- Note: GRETIL is a collection of texts from many editions and projects. Preserve per-text bibliographic and rights information rather than assuming a single uniform license.

## Registered but not bulk-mirrored

### Gandhari.org

Use as an authoritative catalog and text source for Gāndhārī manuscripts and fragments. The project currently does **not** mirror the complete site because public readability is not sufficient evidence of permission to redistribute the whole compilation.

### Digital Sanskrit Buddhist Canon (DSBC)

Use as an authoritative Sanskrit/BHS research source. The project currently does **not** bulk mirror the complete DSBC compilation. Add individual material only when its usage terms or permission clearly allow it.

## Provenance rule

Every local witness derived from an upstream source must record:

- upstream project
- stable identifier
- source URL
- retrieval date
- upstream revision/commit if available
- language
- witness type
- edition/manuscript distinction
- license/usage note

See `sources/lock.json` for exact repository pins.
