# Upstream corpus snapshots

These directories are Git submodules pinned to exact upstream revisions.

Run:

```bash
git submodule update --init --recursive --depth 1
```

or:

```bash
./scripts/fetch_sources.sh
```

The combined working tree is large. The parent repository intentionally stores only the gitlinks and provenance metadata, not duplicate copies of every upstream blob.

Do not modify files inside these submodules when creating normalized project data. Derived records belong under `data/`.
