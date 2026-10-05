# First 20 textual crosswalks

This directory is the first curated benchmark for mapping independent Buddhist textual witnesses.

## Why these 20?

The first batch deliberately starts with **Dīgha Nikāya**, not a random mixture of collections. SuttaCentral's methodology states that the DN and MN correspondence data had been thoroughly checked, while SN/AN correspondence data was less complete at that stage.

Selection rule:

1. Pāli DN anchor.
2. At least one **Chinese full parallel**.
3. At least one independent non-Pāli Indic witness in the selected evidence set:
   - Sanskrit fragment/recension, or
   - Gāndhārī/Prākrit witness.
4. Relationship type and confidence must be explicit.
5. No Sanskrit/BHS reconstruction is invented to fill a gap.

This yields 20 high-confidence benchmark works.

## Important terminology

We intentionally do **not** use `exact_parallel`. Independent recensions may descend from a common ancestor while differing in wording, structure, or content.

- `full_textual_parallel`: whole-discourse correspondence.
- `partial_textual_parallel`: only part of the discourse corresponds.
- `fragmentary_textual_parallel`: surviving manuscript is fragmentary; this is not the same as a partial discourse parallel.
- `shared_passage`: passage-level correspondence only.
- `doctrinal_parallel`: conceptual similarity only.

The last two fields are present but empty in this first benchmark unless a source explicitly supports them. We do not manufacture them to make the dataset look richer.

## Files

- `first-20.json` — machine-readable crosswalk set.
- `bibliography.json` — reusable bibliography records.
- `FIRST_20.md` — generated human-readable overview.

## Chinese IDs

A Chinese sūtra such as `DA 21` is a sub-work inside a canonical container, e.g. `T0001`. The crosswalk records both the discourse ID and `container_id` when known.

This is important because the current raw CBETA catalog indexes whole XML canon texts. A later segmentation layer should extract individual DA/MA/SA/EA discourse units without pretending the whole Āgama collection is a single parallel to one Pāli sutta.

## BHS policy

A text is not labeled `bhs` merely because its Sanskrit looks non-classical. BHS requires explicit scholarly or edition-level support.

## Validation

```bash
make validate-crosswalks
```

The validator checks:

- exactly 20 benchmark records,
- unique IDs and anchors,
- at least one Chinese full parallel per record,
- at least one Sanskrit/BHS/Gāndhārī/Prākrit witness per record,
- allowed relation classes,
- bibliography references resolve,
- no use of the misleading `exact_parallel` label.
