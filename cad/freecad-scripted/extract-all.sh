#!/bin/sh
# Step 1: extract all nine assemblies, one FreeCAD process each.
#
# One per process is not caution, it is required: opening several of the nine in
# one session and closing each before the next makes FreeCAD fail to restore the
# links between them.  See extract.py's docstring.
#
#     sh extract-all.sh out.json
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE/extracted.json}
TMP=$(mktemp -d)
FC="flatpak run --command=freecadcmd --filesystem=home --filesystem=$TMP org.freecad.FreeCAD"

for f in "$HERE"/../freecad/assembly/*.FCStd; do
    n=$(basename "$f" .FCStd)
    ASM_OUT="$TMP/$n.json" $FC "$HERE/extract.py" "$f" 2>&1 \
        | tr '\r' '\n' | grep -E 'RAISED|UNRESOLVED|Traceback|^   ' || true
done

python3 - "$TMP" "$OUT" <<'PY'
import glob, json, os, sys
tmp, out = sys.argv[1], sys.argv[2]
model = {}
for f in sorted(glob.glob(os.path.join(tmp, "*.json"))):
    model.update(json.load(open(f)))
json.dump(model, open(out, "w"), indent=1, sort_keys=True)
print(f"merged {len(model)} documents -> {out}")
PY
rm -rf "$TMP"
