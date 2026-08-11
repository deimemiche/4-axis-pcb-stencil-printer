"""The scripted assembly against the hand-built one.

    python3 asmverify.py            # after rebuild.py's poses and verify stages

Compares `data/hand/` with `data/made/`, both written by `asmpose.py`, one
FreeCAD process per document.  Plain Python: the comparison is arithmetic.

**Two things this deliberately does not do**, both of which invented
discrepancies that cost hours before they were understood.

It does not compare every link by name.  A container assembly mirrors its
sub-assemblies' contents upward, and those mirrored children carry the *same
object names* as the originals.  Matching by name then pairs a part with a copy
of a different part -- which once read as a 520 mm error in a spring that was
in exactly the right place.  Only instances the model says were authored are
compared.

It does not compare fasteners by name at all.  A fastener created as `Screw107`
in a container is renamed by FreeCAD, because a mirrored child already holds
that name; the `Screw107` you then read is the mirror.  Bolts are compared as a
multiset of positions, which nothing can rename: how many of the hand-built
bolt positions have a scripted bolt standing on them.

The tolerance is 1e-4 mm.  The plan expected to need 1e-5 because the solve was
thought not to be idempotent; in practice every authored part lands at
0.000000.
"""

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TOL = 1e-4

NINE = ["Bottom_Frame", "Eccenter", "Rotation_Table", "X-Axis_Carriage",
        "Stencil_Clamp", "Top_Frame", "Bottom_Assembly", "Top_Assembly",
        "4-Axis_Stencil_Printer"]


def spot(pos):
    return tuple(round(v, 4) for v in pos)


def main():
    model = json.load(open(os.path.join(DATA, "model.json")))
    rows, worst = [], 0.0
    tp = tb = op = ob = 0

    for name in NINE:
        try:
            hand = json.load(open(os.path.join(DATA, "hand", name + ".json")))
            made = json.load(open(os.path.join(DATA, "made", name + ".json")))
        except FileNotFoundError as e:
            print(f"!! missing {e.filename}; run rebuild.py poses verify")
            raise SystemExit(1)
        spec = model[name]

        # parts: authored only, matched by name
        authored = {i["name"] for i in spec["instances"]}
        shared = sorted(authored & set(hand) & set(made))
        dev = [max(abs(a - b) for a, b in zip(hand[k]["pos"], made[k]["pos"]))
               for k in shared] or [0.0]
        p_ok = sum(1 for d in dev if d < TOL)
        worst = max(worst, max(dev))

        # bolts: by position, never by name -- and on the scripted side, not
        # selected by name either.  Picking the made bolts out by the hand
        # document's names looks harmless and is the same trap one step back:
        # `Screw108` is taken by a mirrored child before the builder gets to
        # it, so the bolt it authored is called `Screw115` and was left out of
        # the count entirely, while the mirror standing 18 mm away was counted
        # in its place.  Six bolts read as missing that were exactly where they
        # belong.  `asmpose` marks what the assembly itself holds, so take all
        # of that which is not a part instance: those are the bolts this
        # document authored, whatever FreeCAD ended up calling them.
        want = {f["name"] for f in spec["fasteners"]}
        h = collections.Counter(spot(hand[n]["pos"]) for n in want if n in hand)
        m = collections.Counter(
            spot(v["pos"]) for n, v in made.items()
            if v.get("authored") and n not in authored)
        b_ok = sum((h & m).values())

        tp += len(shared); op += p_ok
        tb += len(spec["fasteners"]); ob += b_ok
        rows.append((name, len(shared), p_ok, len(spec["fasteners"]),
                     sum(m.values()), b_ok))

    print(f"{'assembly':26} {'parts':>6} {'exact':>6} | "
          f"{'bolts':>6} {'placed':>7} {'right':>6}")
    for r in rows:
        print(f"{r[0]:26} {r[1]:6} {r[2]:6} | {r[3]:6} {r[4]:7} {r[5]:6}")
    print(f"{'TOTAL':26} {tp:6} {op:6} | {tb:6} {'':7} {ob:6}")
    print(f"\nworst part deviation: {worst:.6f} mm")

    bad = tp - op
    print(f"parts wrong : {bad}")
    print(f"bolts short : {tb - ob}")
    if bad:
        print("\nFAIL: an authored part moved")
        raise SystemExit(1)
    print("\nPASS: every authored part is where the hand-built assembly puts it")


main()
