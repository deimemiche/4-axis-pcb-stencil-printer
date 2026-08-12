"""Name the datums by what mates at them, and write the plan step 3 works from.

    python3 datum-names.py datums.json [--write plan.json] [--text out.txt]

A datum's name should say why it is there.  The measurement knows more than the
geometry: it knows the **other** part of every joint that uses the spot, and
which fasteners go through it.  So a place on `2020_300` where `BOT_BRACKETS`
lands is `BRACKET1`, not `JOINT7`, and a hole that only ever takes a cap screw
is `BOLT3`.

The order of preference is:

1. **A datum already there.**  24 of them exist at the right spot already; they
   keep their own label, because renaming what is already correct is churn.
2. **The mating part**, stripped to the noun that matters -- `BOT_RAIL_HOLDER`
   is a `RAIL_HOLDER`, `ROD_D8_300` is a `ROD`, `_2020_300` is `FRAME`.  Where
   several parts mate at one datum the commonest wins.
3. **The fastener**, when nothing but a bolt uses the spot: `BOLT`, `NUT`,
   `GRUB`, `INSERT`.
4. **The geometry**, when there is nothing else to go on: `BORE`, `FACE`,
   `EDGE`.

Numbering is per part and per stem, ordered along the part so `BOLT1`..`BOLT4`
run in a sensible direction rather than in whatever order the joints were made.
"""

import collections
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root
TOL, ATOL, RTOL = 4, 6, 3

# Stock and other parts whose name says nothing useful on its own.
STEM = {
    "LM8UU": "BEARING", "BEARING_14X5X5": "BEARING",
    "TUBE_D8_170": "TUBE", "HINGE_40_LEAF": "HINGE",
    "M5_270": "STUD", "M8_55": "STUD",
    "STAND": "FOOT", "ADAPTER_D5_TO_M3": "ADAPTER",
    "SR_WORM_GEAR": "WORM", "SR_INNER_RING": "RING",
    "SR_OUTER_RING_W_GEAR": "RING", "SR_BEARING_PLATE": "PLATE",
    # `ECCF_` strips to nouns that say nothing -- ECCF_BOT would become BOT.
    "ECCF_BOT": "ECC_BOT", "ECCF_TOP": "ECC_TOP", "ECCF_MOUNT": "ECC_MOUNT",
    "ECCF_HEIGHT": "ECC_HEIGHT", "ECCF_LEVER": "LEVER",
    "ECCF_LEVER_MIRRORED": "LEVER",
    # BOT_BRACKETS and BOT_BRACKET_X_AXIS both strip to BRACKET(S), which is
    # two different parts one letter apart.  Name them for what they brace.
    "BOT_BRACKETS": "BRACKET", "BOT_BRACKET_X_AXIS": "BRACKET_X",
}
PREFIX = ("BOT_", "TOP_CLAMP_", "TOP_", "SR_", "ECCF_", "ALPHA_", "STENCIL_")
# The axis a part serves is intent, so `_X_AXIS` shortens rather than vanishing:
# BEARING_MOUNT_X and BEARING_MOUNT_Y are different mounts, not one name twice.
SHORTEN = ((r"_X_AXIS$", "_X"), (r"_Y_AXIS$", "_Y"), (r"_Z_AXIS$", "_Z"))
SUFFIX = (r"_MIRRORED$", r"_AXIS$", r"_DRIVEN$", r"_SHORT$", r"_PLAIN$",
          r"_\d+$", r"\d+$")

FASTENER_STEM = {"ISO4762": "BOLT", "DIN934": "NUT", "ISO4035": "NUT",
                 "ISO4027": "GRUB", "IUTHeatInsert": "INSERT"}

# Names given on review, which beat anything the rules above can work out, keyed
# by the part and the position measured there.  This is the step the module
# docstring calls "Michael reviews and names them", written down so that a
# re-run reproduces the reviewed plan instead of undoing it.
#
# All fourteen are the same case: a spot on a part whose script already writes
# `BOLT`n somewhere else, so the counter's answer would be a second meaning for
# a name already taken.  Naming what is actually there says more anyway -- the
# far end of a bolt that goes right through is that bolt's head, and the two M4
# across the Z bracket's mount are the one that pulls it onto the member and the
# one that pinches the collar shut.
REVIEWED = {
    ("BOT_BRACKETS", (30.0, 4.0, 10.0)): "BOLT2_HEAD",
    ("BOT_BRACKETS", (50.0, 4.0, 10.0)): "BOLT3_HEAD",
    ("BOT_BRACKETS", (10.0, 4.0, 30.0)): "BOLT4_HEAD",
    ("BOT_BRACKETS", (10.0, 4.0, 50.0)): "BOLT5_HEAD",
    ("BOT_RAIL_CLAMP_X_DRIVE", (0.0, 3.0, -9.0)): "BOLT1_HEAD",
    ("BOT_RAIL_CLAMP_X_DRIVE", (0.0, 3.0, 9.0)): "BOLT2_HEAD",
    ("BOT_RAIL_CLAMP_Y_AXIS", (0.0, 3.0, -9.0)): "BOLT1_HEAD",
    ("BOT_RAIL_CLAMP_Y_AXIS", (0.0, 3.0, 9.0)): "BOLT2_HEAD",
    ("BOT_RAIL_CLAMP_Y_AXIS_1", (0.0, 3.0, -9.0)): "BOLT1_HEAD",
    ("BOT_RAIL_CLAMP_Y_AXIS_1", (0.0, 3.0, 9.0)): "BOLT2_HEAD",
    ("BOT_Z_AXIS_BRACKET", (7.0072, 14.0, -3.45)): "MOUNT_BOLT",
    ("BOT_Z_AXIS_BRACKET", (35.4181, 14.0, -13.4)): "PINCH_BOLT",
    ("BOT_Z_AXIS_BRACKET_MIRRORED", (-7.0072, 14.0, -3.45)): "MOUNT_BOLT",
    ("BOT_Z_AXIS_BRACKET_MIRRORED", (-35.4181, 14.0, -13.4)): "PINCH_BOLT",
}


def reviewed_name(part, at):
    """The name review gave this spot, if it gave it one."""
    return REVIEWED.get((part, tuple(round(v, 4) + 0.0 for v in at)))


def stem_for(part):
    """The noun in a part's name: BOT_RAIL_CLAMP_Y_AXIS_1 -> RAIL_CLAMP."""
    if part in STEM:
        return STEM[part]
    n = part.lstrip("_")
    if n.startswith("2020"):
        return "FRAME"
    if n.startswith("ROD_D8"):
        return "ROD"
    if n.startswith("SPRING"):
        return "SPRING"
    for p in PREFIX:
        if n.startswith(p):
            n = n[len(p):]
            break
    for pat, rep in SHORTEN:
        n = re.sub(pat, rep, n)
    for s in SUFFIX:
        n = re.sub(s, "", n)
    return n.strip("_") or "MOUNT"


def key(r):
    return (r["part"],
            tuple(round(v, TOL) for v in r["at"]),
            tuple(round(v, ATOL) for v in r["axis"]),
            round(r["roll"], RTOL))


def existing_datums():
    out = {}
    # Read the FROZEN tree, not this one.  Once `fcprim.apply_datums` has run,
    # this tree's parts carry the plan's own datums, and counting those as
    # pre-existing would make the plan agree with itself.
    frozen = os.path.normpath(os.path.join(HERE, "..", "freecad"))
    for f in glob.glob(os.path.join(frozen, "*", "*.FCStd")):
        doc = ET.fromstring(zipfile.ZipFile(f).read("Document.xml"))
        types = {o.get("name"): o.get("type") for o in doc.iter("Object")
                 if o.get("type")}
        got = []
        for od in doc.iter("Object"):
            props = od.find("Properties")
            if props is None or types.get(od.get("name")) != \
                    "PartDesign::CoordinateSystem":
                continue
            # `.//` would find AttachmentOffset, which precedes Placement in
            # the file and is identity on every one of these datums.
            pl = props.find("./Property[@name='Placement']/PropertyPlacement")
            if pl is None:
                continue
            g = lambda k: float(pl.get(k, 0))
            x, y, z, w = g("Q0"), g("Q1"), g("Q2"), g("Q3")
            lab = props.find("./Property[@name='Label']/String")
            got.append({"label": lab.get("value") if lab is not None else "?",
                        "at": (g("Px"), g("Py"), g("Pz")),
                        "axis": (2 * (x * z + w * y), 2 * (y * z - w * x),
                                 1 - 2 * (x * x + y * y))})
        if got:
            out[os.path.basename(f)[:-6]] = got
    return out


def match_doc(doc, have):
    for cand in (doc, doc.lstrip("_"), doc.replace("_", "-")):
        if cand in have:
            return cand
    return None


def main():
    src = [a for a in sys.argv[1:] if a.endswith(".json")][0]
    rows = json.load(open(src))["rows"]

    # the other end of each joint, so a datum knows what mates at it
    by_joint = collections.defaultdict(dict)
    for r in rows:
        if r["prop"] in ("Reference1", "Reference2"):
            by_joint[(r["assembly"], r["joint"])][r["prop"]] = r

    groups = collections.defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)

    have = existing_datums()
    close = lambda a, b: all(abs(p - q) < 1e-3 for p, q in zip(a, b))

    assemblies = {"_4_Axis_Stencil_Printer", "Bottom_Assembly", "Bottom_Frame",
                  "Eccenter", "Rotation_Table", "Stencil_Clamp", "Top_Assembly",
                  "Top_Frame", "X_Axis_Carriage"}

    plan = collections.defaultdict(list)
    for k, rs in groups.items():
        part, at, axis, roll = k
        if part in assemblies:
            continue

        kept = None
        d = match_doc(part, have)
        if d:
            for e in have[d]:
                if close(at, e["at"]) and close(axis, e["axis"]):
                    kept = e["label"]
                    break

        mates, fasteners = collections.Counter(), collections.Counter()
        for r in rs:
            if r["prop"] == "BaseObject":
                fasteners[r.get("fastener", "?")] += 1
                continue
            other = "Reference2" if r["prop"] == "Reference1" else "Reference1"
            o = by_joint[(r["assembly"], r["joint"])].get(other)
            if o and o["part"] and o["part"] != part:
                mates[o["part"]] += 1

        if kept:
            stem, why = kept, "kept"
        elif mates:
            stem, why = stem_for(mates.most_common(1)[0][0]), "mates"
        elif fasteners:
            stem = FASTENER_STEM.get(fasteners.most_common(1)[0][0], "BOLT")
            why = "fastener"
        else:
            kinds = {f"{r['kind']}/{r['geom']}" for r in rs}
            stem = ("BORE" if any("Cylinder" in x or "Circle" in x for x in kinds)
                    else "FACE" if any("Plane" in x for x in kinds) else "EDGE")
            why = "geometry"

        plan[part].append({
            "stem": stem, "fixed": bool(kept), "why": why,
            "at": list(at), "axis": list(axis), "roll": roll,
            "refs": len(rs),
            "mates": sorted(mates), "fasteners": sorted(fasteners),
            "joints": sorted({f"{r['assembly']}.{r['joint_type']}" for r in rs}),
            "was": sorted({r["sub"] for r in rs}),
        })

    # Number per part and stem, ordered along the part.
    #
    # A generated name must not collide with a datum the part script already
    # writes somewhere else.  This was got wrong once and cost eleven datums:
    # the line here used to drop the kept labels from `taken` -- "kept ones are
    # ours" -- and a kept `BOLT3` therefore freed `BOLT3` for the numbering to
    # hand to a different spot.  Every label the part carries stays taken; a
    # kept datum does not need its own name reserved, because it never asks the
    # counter for one.
    #
    # The eleven were `BOLT1`..`BOLT5` on `BOT_BRACKETS`, the three rail clamps
    # and both hands of `BOT_Z_AXIS_BRACKET`, and they are the reason
    # `apply_datums` now *checks* a datum it finds rather than stepping over it.
    for part, ds in plan.items():
        d0 = match_doc(part, have)
        taken = {e["label"] for e in have.get(d0, [])} if d0 else set()
        ds.sort(key=lambda d: (d["stem"], d["at"]))
        for d in ds:
            given = reviewed_name(part, d["at"])
            if given:
                d["name"], d["why"] = given, "reviewed"
                taken.add(given)
        counts = collections.Counter(d["stem"] for d in ds
                                     if not d.get("name"))
        seen = collections.Counter()
        for d in ds:
            if d.get("name"):
                continue
            if d["fixed"]:
                d["name"] = d["stem"]
                continue
            seen[d["stem"]] += 1
            name = (d["stem"] if counts[d["stem"]] == 1
                    else f"{d['stem']}{seen[d['stem']]}")
            while name in taken:
                seen[d["stem"]] += 1
                name = f"{d['stem']}{seen[d['stem']]}"
            taken.add(name)
            d["name"] = name
        ds.sort(key=lambda d: (d["name"]))

    total = sum(len(v) for v in plan.values())
    kept_n = sum(1 for v in plan.values() for d in v if d["fixed"])
    why = collections.Counter(d["why"] for v in plan.values() for d in v)
    print(f"datums          : {total} across {len(plan)} part documents")
    print(f"  kept existing : {kept_n}")
    print(f"  named on review: {why['reviewed']}")
    print(f"  named by mate : {why['mates']}")
    print(f"  by fastener   : {why['fastener']}")
    print(f"  by geometry   : {why['geometry']}   <- the ones with no intent to read")
    print()
    named = collections.Counter(d["name"].rstrip("0123456789")
                                for v in plan.values() for d in v)
    print("name stems used:")
    for n, c in named.most_common(18):
        print(f"   {n:16} {c}")

    w = [a for a in sys.argv if a.startswith("--write=")]
    if w:
        json.dump(dict(plan), open(w[0][8:], "w"), indent=1, sort_keys=True)
        print(f"\nplan written to {w[0][8:]}")
    t = [a for a in sys.argv if a.startswith("--text=")]
    if t:
        with open(t[0][7:], "w") as fh:
            for part in sorted(plan):
                fh.write(f"\n# {part}\n")
                for d in plan[part]:
                    at = "" if d["at"] == [0.0, 0.0, 0.0] else \
                        "at=({}), ".format(", ".join(f"{v:g}" for v in d["at"]))
                    roll = "" if abs(d["roll"]) < 1e-6 else \
                        f", roll={d['roll']:g}"
                    fh.write(f'    fcprim.lcs(bdy, "{d["name"]}", {at}'
                             f'axis=({", ".join(f"{v:g}" for v in d["axis"])})'
                             f'{roll})\n')
                    fh.write(f'        # {d["why"]}: '
                             f'{", ".join(d["mates"] + d["fasteners"]) or d["joints"][0]}'
                             f'  [{d["refs"]} ref(s), was {", ".join(d["was"])}]\n')
        print(f"text written to {t[0][7:]}")


main()
