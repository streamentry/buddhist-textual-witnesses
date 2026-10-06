# DN 14 evidence audit — 2026-10-06

## Status

This is a **model-assisted evidence audit**, not a human scholarly review and not a promotion event.

- Alignments inspected: **9 / 9**
- Human reviews created: **0**
- Promotions created: **0**
- Human accepted / needs revision / rejected: **0 / 0 / 0**
- Model-audit outcome: **4 unchanged; 5 corrected or clarified**

The human-review and promotion ledgers remain untouched. A later human reviewer must assess the current evidence-bound claim state with a real identity and stable reviewer ID.

## Evidence basis

The audit compared the exact source units already pinned by the repository:

- Pāli: DN 14 source units from the pinned SuttaCentral Bilara revision
- Chinese: DA 1 and EA 48.4 blocks from the pinned CBETA XML-P5 revision
- Sanskrit: SF 36 edited source units from the pinned SuttaCentral Bilara revision

Editorially supplied Sanskrit remains visibly distinct from directly surviving text. The SF 36 Family Name and Bodhi Trees loci explicitly say that the Sanskrit text is completely lost and are treated only as loss loci.

## Per-alignment audit

| Alignment | Model-audit result | Change |
| --- | --- | --- |
| 01 opening / setting | retained | No substantive correction. Residence-detail differences remain explicit. |
| 02 monks discuss past Buddhas | clarified | Do not collapse Sanskrit `dharmadhātu`, DA `法性`, EA opening `法處`, and EA later `法界` into a claimed lexical or doctrinal identity. |
| 03 Buddha hears / approaches / asks | retained | Narrative relation remains a strong parallel despite different segmentation. |
| 04 monks report discussion | retained | `structural_correspondence` remains appropriate because DA compresses the reply while EA/SF preserve fuller speech and Pāli remains abbreviated. |
| 05 seven Buddhas chronology | clarified | Record prose/verse asymmetry: DA, EA, and SF selected units contain prose plus verse; selected Pāli unit is prose only; Sanskrit verse is substantially fragmentary/supplied. |
| 06 lifespan lists | **reclassified** | `parallel_passage` → `structural_correspondence`. DA says `人壽` (human lifespan in each Buddha's era), unlike Buddha/Tathāgata lifespan framing in DN/SF/EA. Numerical disagreement remains unharmonized. |
| 07 caste | retained | Same overall caste sequence; DA still packages clan information in the same block. Sanskrit supplied material remains visible in the edition. |
| 08 family / clan names | **corrected** | EA's two selected passages are complete but internally incompatible clan-name sequences, not merely partial fragments. SF 36 is only a Family Name loss locus. The relation is scoped to Pāli/DA/EA. |
| 09 Bodhi trees | **corrected structurally** | The surviving Pāli/DA/EA lists remain a textual parallel; SF 36 is only a Bodhi Trees loss locus. The relation is explicitly scoped to Pāli/DA/EA. |

## Key witness findings

### Lifespan locus

DN 14 and SF 36 explicitly frame the quantities as Buddha lifespans. EA 48.4 explicitly frames them as Tathāgata lifespans.

DA 1 instead uses `人壽`: human lifespan in the time of each Buddha. Its prose gives 80k / 70k / 60k / 40k / 30k / 20k, while the verse changes Vipassī-era human lifespan to 84k.

The repository therefore preserves both:
1. numerical disagreement, and
2. the more fundamental semantic difference in what is being measured.

### EA 48.4 family-name divergence

EA 48.4 preserves two nearby complete sequences that disagree:

- b0015: first three Gotama; middle three Kassapa; present Gotama
- b0018: first three 拘鄰若; middle three 婆羅墮; present 拘鄰若

The corpus records this as internal recension evidence rather than selecting or harmonizing a preferred sequence.

### Textual loss

SF 36 p0019 (Family Name) and p0020 (Bodhi Trees) preserve no Sanskrit wording. They are valuable evidence for the locus and for the state of the edition, but not evidence for the wording of a cross-tradition textual parallel.

## Infrastructure correction

The multi-witness schema now supports:

```json
"relation_member_ids": ["pli", "da", "ea"]
```

This field is required whenever a row contains a `lost_text_marker`. The validator enforces that:

1. relation members exist and are unique;
2. at least two surviving members participate;
3. a `lost_text_marker` cannot participate in the asserted textual relation;
4. every loss marker has an explicit `textual_loss` variant.

This preserves the useful lost locus in the graph without letting absence masquerade as surviving parallel text.

## Remaining uncertainty and human-review boundary

This audit does **not** decide whether any alignment is human-accepted or established. In particular:

- lexical history behind `dharmadhātu / 法性 / 法處 / 法界` deserves specialist assessment;
- heavily supplied Sanskrit passages should be judged with the critical edition and manuscript context where necessary;
- relation classifications remain model-reviewed hypotheses until a real human reviewer signs the current evidence snapshot;
- no promotion should occur until that accepted review is fresh and passes policy.

The next legitimate state transition is therefore **human review of the corrected evidence**, not automatic promotion.
