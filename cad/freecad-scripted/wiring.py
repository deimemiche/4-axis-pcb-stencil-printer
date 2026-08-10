"""What each joint and fastener attaches to, once datums replace edge names.

    python3 wiring.py datums.json datum-plan.json wiring.json

The bridge between the hand-built assembly and the scripted one.  For every
joint reference and every fastener attachment it says: this part, this datum --
where the hand-built assembly said `Pocket001.Edge34`.

It also records each datum's **internal object name**.  FreeCAD addresses a
sub-element by internal name, not by label, so a joint reads `LCS007.` even
though the datum is called `LEVER2`.  `fcprim.lcs` creates them in plan order,
so the mapping is read out of the built part documents rather than assumed.
"""

import collections
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOL, ATOL, RTOL = 4, 6, 3

# PartDesign features, which sit beside a datum in the body rather than above it
FEATURE = re.compile(r"^(Pad|Pocket|Revolution|Groove|Loft|Pipe|Helix|Chamfer|"
                     r"Fillet|Draft|Thickness|Mirrored|LinearPattern|"
                     r"PolarPattern|MultiTransform|Body|Sketch)\d*$")


def key(r):
    return (r["part"],
            tuple(round(v, TOL) for v in r["at"]),
            tuple(round(v, ATOL) for v in r["axis"]),
            round(r["roll"], RTOL))


def plan_key(part, d):
    return (part,
            tuple(round(v, TOL) for v in d["at"]),
            tuple(round(v, ATOL) for v in d["axis"]),
            round(d["roll"], RTOL))


def datum_names():
    """document -> {label: internal name} for every datum in the built parts."""
    out = {}
    for f in glob.glob(os.path.join(HERE, "*", "*.FCStd")):
        root = ET.fromstring(zipfile.ZipFile(f).read("Document.xml"))
        types = {o.get("name"): o.get("type") for o in root.iter("Object")
                 if o.get("type")}
        got = {}
        for od in root.iter("Object"):
            props = od.find("Properties")
            if props is None or types.get(od.get("name")) != \
                    "PartDesign::CoordinateSystem":
                continue
            lab = props.find("./Property[@name='Label']/String")
            if lab is not None:
                got[lab.get("value")] = od.get("name")
        if got:
            out[os.path.basename(f)[:-6]] = got
    return out


def match(doc, table):
    for cand in (doc, doc.lstrip("_"), doc.replace("_", "-")):
        if cand in table:
            return cand
    return None


def main():
    rows = json.load(open(sys.argv[1]))["rows"]
    plan = json.load(open(sys.argv[2]))
    out_path = sys.argv[3]

    # measured spot -> the datum the plan put there
    by_spot = {}
    for part, ds in plan.items():
        for d in ds:
            by_spot[plan_key(part, d)] = d["name"]

    internal = datum_names()

    joints, fasteners, unmapped = {}, {}, []
    for r in rows:
        name = by_spot.get(key(r))
        doc = match(r["part"], internal)
        obj = internal.get(doc, {}).get(name) if doc else None
        # A reference reaching into a sub-assembly needs the whole path:
        #   Bottom_Frame001.BOT_Z_AXIS_BRACKET.LCS007.
        # not the bare datum.  The prefix is the original sub's link chain --
        # its leading components, minus the element and minus any PartDesign
        # feature, which lives inside the body next to the datum rather than
        # above it.
        parts = r["sub"].split(".")[:-1]
        while parts and FEATURE.match(parts[-1]):
            parts.pop()
        prefix = ".".join(parts) + "." if parts else ""
        rec = {"part": r["part"], "datum": name, "object": obj,
               "prefix": prefix, "was": r["sub"]}
        if name is None or obj is None:
            unmapped.append({**rec, "assembly": r["assembly"],
                             "joint": r["joint"], "prop": r["prop"]})
            continue
        if r["prop"] == "BaseObject":
            fasteners[f"{r['assembly']}/{r['joint']}"] = {
                **rec, "type": r.get("fastener"),
                "diameter": r.get("diameter")}
        else:
            joints.setdefault(f"{r['assembly']}/{r['joint']}", {})[r["prop"]] = rec

    json.dump({"joints": joints, "fasteners": fasteners,
               "unmapped": unmapped, "internal": internal},
              open(out_path, "w"), indent=1, sort_keys=True)

    both = sum(1 for v in joints.values() if len(v) == 2)
    print(f"joint references wired  : {sum(len(v) for v in joints.values())}"
          f"   ({both} joints with both ends)")
    print(f"fastener attachments    : {len(fasteners)}")
    print(f"UNMAPPED                : {len(unmapped)}")
    for u in unmapped[:12]:
        print(f"   {u['assembly']}.{u['joint']}.{u['prop']} "
              f"-> {u['part']} datum={u['datum']} object={u['object']}")
    print(f"\nwritten to {out_path}")


main()
