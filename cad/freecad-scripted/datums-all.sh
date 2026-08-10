#!/bin/sh
# Step 2: measure every joint reference's coordinate system, one process each.
#     sh datums-all.sh out.json
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE/datums.json}
TMP=$(mktemp -d)
FC="flatpak run --command=freecadcmd --filesystem=home --filesystem=$TMP org.freecad.FreeCAD"
for f in "$HERE"/../freecad/assembly/*.FCStd; do
    n=$(basename "$f" .FCStd)
    ASM_OUT="$TMP/$n.json" $FC "$HERE/datums.py" "$f" 2>&1 \
        | tr '\r' '\n' | grep -E 'references,|FAILED|RAISED|Error' || true
done
python3 - "$TMP" "$OUT" <<'PY'
import glob, json, os, sys
tmp, out = sys.argv[1], sys.argv[2]
merged = {"rows": [], "failed": []}
for f in sorted(glob.glob(os.path.join(tmp, "*.json"))):
    d = json.load(open(f))
    merged["rows"] += d["rows"]; merged["failed"] += d["failed"]
json.dump(merged, open(out, "w"), indent=1, sort_keys=True)
print(f"merged {len(merged['rows'])} references -> {out}")
PY
rm -rf "$TMP"
