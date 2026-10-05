#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/.cache/cbeta-agamas}"
CONFIG="$ROOT/config/agama-segmentation.json"
LOCK="$ROOT/sources/lock.json"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

need git
need python3

PINNED_SHA="$(git -C "$ROOT" ls-files -s upstream/cbeta-xml-p5 | awk '{print $2}')"
LOCK_SHA="$(python3 - "$LOCK" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["sources"]["cbeta-xml"]["commit"])
PY
)"

if [ -z "$PINNED_SHA" ]; then
  echo "Cannot determine CBETA submodule gitlink SHA" >&2
  exit 1
fi

if [ "$PINNED_SHA" != "$LOCK_SHA" ]; then
  echo "CBETA pin mismatch: gitlink=$PINNED_SHA lock=$LOCK_SHA" >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
git -C "$DEST" init -q
git -C "$DEST" remote add origin https://github.com/cbeta-org/xml-p5.git
git -C "$DEST" config core.sparseCheckout true

python3 - "$CONFIG" "$DEST/.git/info/sparse-checkout" <<'PY'
import json, sys
config=json.load(open(sys.argv[1],encoding="utf-8"))
paths=sorted({item["path"] for item in config["collections"].values()})
with open(sys.argv[2],"w",encoding="utf-8") as out:
    for path in paths:
        out.write(path+"\n")
PY

git -C "$DEST" fetch -q --depth 1 --filter=blob:none origin "$PINNED_SHA"
git -C "$DEST" checkout -q --detach FETCH_HEAD

ACTUAL_SHA="$(git -C "$DEST" rev-parse HEAD)"
if [ "$ACTUAL_SHA" != "$PINNED_SHA" ]; then
  echo "Fetched CBETA SHA mismatch: expected=$PINNED_SHA actual=$ACTUAL_SHA" >&2
  exit 1
fi

echo "$ACTUAL_SHA"
