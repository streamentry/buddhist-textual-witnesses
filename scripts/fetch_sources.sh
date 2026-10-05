#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT/vendor"
mkdir -p "$VENDOR"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

need git
need curl
need unzip

echo "==> Fetching SuttaCentral Bilara (published branch)"
if [ ! -d "$VENDOR/suttacentral/.git" ]; then
  git clone --depth 1 --branch published --filter=blob:none --sparse \
    https://github.com/suttacentral/bilara-data.git "$VENDOR/suttacentral"
  git -C "$VENDOR/suttacentral" sparse-checkout set root/san root/pra root/lzh
else
  git -C "$VENDOR/suttacentral" fetch --depth 1 origin published
  git -C "$VENDOR/suttacentral" checkout published
  git -C "$VENDOR/suttacentral" reset --hard origin/published
fi

echo "==> Fetching CBETA XML-P5"
if [ ! -d "$VENDOR/cbeta/.git" ]; then
  git clone --depth 1 https://github.com/cbeta-git/xml-p5.git "$VENDOR/cbeta"
else
  git -C "$VENDOR/cbeta" pull --ff-only
fi

echo
echo "GRETIL note:"
echo "  The repository registers GRETIL, but its cumulative archive URLs can move between"
echo "  institutional mirrors. Add a pinned URL + checksum before automating the bulk fetch."
echo
echo "Not bulk-mirrored:"
echo "  - Gandhari.org"
echo "  - DSBC"
echo
echo "Done."
