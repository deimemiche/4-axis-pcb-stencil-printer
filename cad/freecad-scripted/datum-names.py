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

HERE = os.path.dirname(os.path.abspath(__file__))
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
    for f in glob.glob(os.path.join(HERE, "*", "*.FCStd")):
        doc = ET.fromstring(zipfile.ZipFile(f).read("Document.xml"))
        types = {o.get("name"): o.get("type") for o in doc.iter("Object")
                 if o.get("type")}
        got = []
        for od in doc.iter("Object"):
            props = od.find("Properties")
            if props is None or types.get(od.get("name")) != \
                    "PartDesign::CoordinateSystem":
                continue
            pl = props.find(".//PropertyPlacement")
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

    plan = collections.defaultdict(list)
    for k, rs in groups.items():
        part, at, axis, roll = k

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

    # number per part and stem, ordered along the part
    for part, ds in plan.items():
        ds.sort(key=lambda d: (d["stem"], d["at"]))
        counts = collections.Counter(d["stem"] for d in ds)
        seen = collections.Counter()
        for d in ds:
            if d["fixed"]:
                d["name"] = d["stem"]
                continue
            seen[d["stem"]] += 1
            d["name"] = (d["stem"] if counts[d["stem"]] == 1
                         else f"{d['stem']}{seen[d['stem']]}")
        ds.sort(key=lambda d: (d["name"]))

    total = sum(len(v) for v in plan.values())
    kept_n = sum(1 for v in plan.values() for d in v if d["fixed"])
    why = collections.Counter(d["why"] for v in plan.values() for d in v)
    print(f"datums          : {total} across {len(plan)} part documents")
    print(f"  kept existing : {kept_n}")
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
