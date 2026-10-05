# Generated catalog

This directory contains the generated unified metadata catalog. Raw texts remain in `upstream/`.

Generate or refresh it with:

```bash
make fetch
make catalog
```

Generated files:

- `catalog.json` — nested work/language/witness/source graph
- `catalog.jsonl` — flat streaming form
- `catalog.csv` — tabular form
- `stats.json` — summary counts

Do not hand-edit generated files. Change `config/catalog.json`, the pipeline, or the upstream pins and rebuild.
