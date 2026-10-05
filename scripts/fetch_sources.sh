#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

need git

echo "==> Syncing submodule definitions"
git submodule sync --recursive

echo "==> Fetching pinned upstream corpora"
git submodule update --init --recursive --depth 1

echo
echo "Pinned sources now available:"
echo "  upstream/suttacentral-bilara"
echo "  upstream/cbeta-xml-p5"
echo "  upstream/gretil-mirror"
echo
echo "External research sources intentionally not bulk-mirrored:"
echo "  Gandhari.org"
echo "  Digital Sanskrit Buddhist Canon (DSBC)"
echo
echo "Exact pins: sources/lock.json"
