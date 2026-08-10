"""Step 2's answer: how many distinct datums the 298 joint references collapse to.

Plain Python -- it reads what `datums-all.sh` measured, so it needs no FreeCAD.

    python3 datum-report.py datums.json [--calls]

`--calls` also prints the proposed `fcprim.lcs()` line for every datum, grouped
by the part script that would carry it.  Positions are rounded to 4 decimals and
directions to 6 when deciding whether two references mean the same datum; a bolt
circle therefore stays one datum per hole, but two joints onto the same bore at
the same height become one.
"""

import collections
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET
import zipfile

TOL, ATOL, RTOL = 4, 6, 3
ASSEMBLY_DOCS = {
    "_4_Axis_Stencil_Printer", "Bottom_Assembly", "Bottom_Frame", "Eccenter",
    "Rotation_Table", "Stencil_Clamp", "Top_Assembly", "Top_Frame",
    "X_Axis_Carriage",
}


def existing_datums(root):
    """Every PartDesign::CoordinateSystem already in the part documents.

    Read out of the XML rather than through FreeCAD: this only needs each
    datum's placement, and opening 59 documents to get it would be absurd.
    """
    out = {}
    for f in glob.glob(os.path.join(root, "*", "*.FCStd")):
        doc = ET.fromstring(zipfile.ZipFile(f).read("Document.xml"))
        types = {o.get("name"): o.get("type") for o in doc.iter("Object")
                 if o.get("type")}
        got = []
        for od in doc.iter("Object"):
            props = od.find("Properties")
            if props is None:
                continue
            if types.get(od.get("name")) != "PartDesign::CoordinateSystem":
                continue
            pl = props.find(".//PropertyPlacement")
            if pl is None:
                continue
            g = lambda k: float(pl.get(k, 0))
            x, y, z, w = g("Q0"), g("Q1"), g("Q2"), g("Q3")
            label = props.find("./Property[@name='Label']/String")
            got.append({
                "label": label.get("value") if label is not None else "?",
                "at": (g("Px"), g("Py"), g("Pz")),
                "axis": (2 * (x * z + w * y), 2 * (y * z - w * x),
                         1 - 2 * (x * x + y * y)),
            })
        if got:
            out[os.path.basename(f)[:-6]] = got
    return out


def match_doc(doc, have):
    """Document names lose leading digits: 2020_300.FCStd opens as _2020_300."""
    for cand in (doc, doc.lstrip("_"), doc.replace("_", "-")):
        if cand in have:
            return cand
    return None


def key(r):
    return (r["part"],
            tuple(round(v, TOL) for v in r["at"]),
            tuple(round(v, ATOL) for v in r["axis"]),
            round(r["roll"], RTOL))


def fmt(v, n=3):
    return f"{v:.{n}f}".rstrip("0").rstrip(".") or "0"


def main():
    path = [a for a in sys.argv[1:] if a.endswith(".json")][0]
    show_calls = "--calls" in sys.argv
    data = json.load(open(path))
    rows = data["rows"]

    onto_part = [r for r in rows if r["part"] not in ASSEMBLY_DOCS]
    onto_asm = [r for r in rows if r["part"] in ASSEMBLY_DOCS]

    groups = collections.defaultdict(list)
    for r in onto_part:
        groups[key(r)].append(r)

    per_part = collections.Counter(k[0] for k in groups)
    refs_per_part = collections.Counter(r["part"] for r in onto_part)

    print(f"joint references measured        : {len(rows)}")
    print(f"  landing on a part document     : {len(onto_part)}")
    print(f"  landing on a sub-assembly      : {len(onto_asm)}"
          f"   (a datum in the sub-assembly, not in a part script)")
    print(f"failed to resolve                : {len(data['failed'])}")
    print()
    print(f"DISTINCT DATUMS NEEDED           : {len(groups)}")
    print(f"  across part documents          : {len(per_part)}")
    print(f"  collapse ratio                 : "
          f"{len(onto_part)}/{len(groups)} = "
          f"{len(onto_part) / max(len(groups), 1):.2f} references per datum")
    print()

    kinds = collections.Counter(f"{r['kind']}/{r['geom']}" for r in onto_part)
    print("what the references land on:")
    for k, v in kinds.most_common():
        print(f"   {k:22} {v}")
    print()

    have = existing_datums(os.path.join(os.path.dirname(os.path.abspath(__file__))))
    n_have = sum(len(v) for v in have.values())
    close = lambda a, b: all(abs(p - q) < 1e-3 for p, q in zip(a, b))
    already = 0
    per_have = collections.Counter()
    for k in groups:
        d = match_doc(k[0], have)
        if d and any(close(k[1], e["at"]) and close(k[2], e["axis"])
                     for e in have[d]):
            already += 1
            per_have[k[0]] += 1
    print(f"datums already on disk           : {n_have}"
          f"   in {len(have)} part documents")
    print(f"  of those, where a joint wants  : {already}")
    print(f"DATUMS TO ADD OR MOVE            : {len(groups) - already}")
    print()

    print(f"{'part document':34} {'refs':>5} {'datums':>7} {'have':>5} {'add':>5}")
    for p in sorted(per_part, key=lambda p: -per_part[p]):
        print(f"   {p:31} {refs_per_part[p]:5} {per_part[p]:7} "
              f"{per_have[p]:5} {per_part[p] - per_have[p]:5}")
    print(f"   {'TOTAL':31} {len(onto_part):5} {len(groups):7} "
          f"{already:5} {len(groups) - already:5}")

    if not show_calls:
        print("\n(pass --calls for the proposed lcs() lines)")
        return

    print("\n" + "=" * 72)
    print("PROPOSED DATUMS -- names are placeholders, the numbers are measured")
    print("=" * 72)
    by_part = collections.defaultdict(list)
    for k, rs in groups.items():
        by_part[k[0]].append((k, rs))
    for part in sorted(by_part):
        print(f"\n# {part}")
        entries = sorted(by_part[part], key=lambda e: e[0][1])
        for i, (k, rs) in enumerate(entries, 1):
            _, at, axis, roll = k
            users = sorted({f"{r['assembly']}.{r['joint_type']}" for r in rs})
            arg_at = "" if at == (0.0, 0.0, 0.0) else \
                f"at=({fmt(at[0])}, {fmt(at[1])}, {fmt(at[2])}), "
            arg_roll = "" if abs(roll) < 1e-6 else f", roll={fmt(roll, 3)}"
            print(f"    fcprim.lcs(bdy, \"JOINT{i}\", {arg_at}"
                  f"axis=({fmt(axis[0], 6)}, {fmt(axis[1], 6)}, "
                  f"{fmt(axis[2], 6)}){arg_roll})")
            print(f"        # {len(rs)} ref(s): {', '.join(users)}")
            print(f"        # was: {', '.join(sorted({r['sub'] for r in rs}))}")


main()
