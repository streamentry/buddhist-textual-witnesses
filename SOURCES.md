# Sources and provenance

This repository distinguishes between **source registration** and **redistribution**.

## Automated bulk sources

### GRETIL
- Purpose: Sanskrit and Prakrit machine-readable corpora.
- Access: official cumulative archives / mirrors.
- Use: fetched into `vendor/gretil/`.
- Note: preserve upstream bibliographic headers and licensing metadata.

### SuttaCentral Bilara
- Repository: `suttacentral/bilara-data`
- Branch: `published`
- Relevant roots:
  - `root/san` — Sanskrit
  - `root/pra` — Prakrit
  - `root/lzh` — Classical Chinese
- Use: fetched into `vendor/suttacentral/`.

### CBETA XML-P5
- Purpose: canonical Chinese Buddhist witnesses, including the principal Āgamas.
- Use: fetch official XML-P5 repository, then select required Taishō texts.
- Principal Āgamas:
  - T0001 長阿含經 — Dīrgha Āgama
  - T0026 中阿含經 — Madhyama Āgama
  - T0099 雜阿含經 — Saṃyukta Āgama
  - T0100 別譯雜阿含經 — Alternate Saṃyukta Āgama
  - T0101 雜阿含經 — Short Saṃyukta witness
  - T0125 增壹阿含經 — Ekottarika Āgama

## Registered but not bulk-mirrored

### Gandhari.org
Use as an authoritative catalog and text source for Gāndhārī manuscripts and fragments. Do not assume bulk redistribution rights merely because texts are viewable online.

### Digital Sanskrit Buddhist Canon (DSBC)
Use as an authoritative Sanskrit/BHS research source. Do not bulk mirror or redistribute the DSBC compilation unless permission and licensing explicitly allow it.

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
