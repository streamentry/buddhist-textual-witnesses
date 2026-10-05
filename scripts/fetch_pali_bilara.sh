#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/.cache/bilara-pali}"
CROSSWALKS="$ROOT/data/crosswalks/first-20.json"
LOCK="$ROOT/sources/lock.json"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1" >&2
    exit 1
  }
}

need git
need python3

PINNED_SHA="$(git -C "$ROOT" ls-files -s upstream/suttacentral-bilara | awk '{print $2}')"
LOCK_SHA="$(python3 - "$LOCK" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["sources"]["suttacentral-bilara"]["commit"])
PY
)"

if [ -z "$PINNED_SHA" ]; then
  echo "Cannot determine SuttaCentral Bilara submodule gitlink SHA" >&2
  exit 1
fi

if [ "$PINNED_SHA" != "$LOCK_SHA" ]; then
  echo "Bilara pin mismatch: gitlink=$PINNED_SHA lock=$LOCK_SHA" >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
git -C "$DEST" init -q
git -C "$DEST" remote add origin https://github.com/suttacentral/bilara-data.git
git -C "$DEST" config core.sparseCheckout true

python3 - "$CROSSWALKS" "$DEST/.git/info/sparse-checkout" <<'PY'
import json, re, sys
data=json.load(open(sys.argv[1], encoding="utf-8"))
slugs=[]
for item in data["crosswalks"]:
    cid=item["anchor"]["canonical_id"]
    m=re.fullmatch(r"DN\s+(\d+)", cid)
    if not m:
        raise SystemExit(f"Unsupported Pāli anchor for Bilara fetch: {cid}")
    slugs.append(f"dn{int(m.group(1))}")
paths=[]
for slug in sorted(set(slugs), key=lambda s:int(s[2:])):
    paths.append(f"root/pli/ms/sutta/dn/{slug}_root-pli-ms.json")
    paths.append(f"html/pli/ms/sutta/dn/{slug}_html.json")
with open(sys.argv[2], "w", encoding="utf-8") as out:
    out.write("\n".join(paths)+"\n")
PY

git -C "$DEST" fetch -q --depth 1 --filter=blob:none origin "$PINNED_SHA"
git -C "$DEST" checkout -q --detach FETCH_HEAD

ACTUAL_SHA="$(git -C "$DEST" rev-parse HEAD)"
if [ "$ACTUAL_SHA" != "$PINNED_SHA" ]; then
  echo "Fetched Bilara SHA mismatch: expected=$PINNED_SHA actual=$ACTUAL_SHA" >&2
  exit 1
fi

echo "$ACTUAL_SHA"
