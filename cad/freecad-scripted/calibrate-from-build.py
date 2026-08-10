"""Fastener offsets, measured against the frame the build itself used.

    python3 calibrate-from-build.py frames.json model.json out.json hand-*.json

`calibrate.py` measures in a saved, reopened document.  For the six leaf
sub-assemblies that is the same frame the build used, and every bolt in them
lands exact.  For a container it is not: a sub-assembly's links are still
settling while the container is being assembled, so a datum reached through one
resolves differently then than it does afterwards.  Calibrating against a frame
the builder never sees pushes the bolt off a datum that was already right --
for five of the eight, the build-time frame sits exactly on the hand-built
position, and the "correction" was the whole error.

So `asmbuild.py` records the frame it used for each fastener (`ASM_FRAMES`) and
this measures against that.  Plain Python: composing placements is arithmetic,
and it needs no FreeCAD.
"""
import json, math, sys


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def rot(q, v):
    t = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qconj(q))
    return (t[0], t[1], t[2])


def inverse(pos, q):
    qi = qconj(q)
    p = rot(qi, pos)
    return ((-p[0], -p[1], -p[2]), qi)


def compose(a, b):
    (ap, ar), (bp, br) = a, b
    p = rot(ar, bp)
    return ((ap[0] + p[0], ap[1] + p[1], ap[2] + p[2]), qmul(ar, br))


def main():
    frames = json.load(open(sys.argv[1]))
    model = json.load(open(sys.argv[2]))
    out_path = sys.argv[3]

    hand = {}
    for p in sys.argv[4:]:
        asm = p.split("fh-")[-1][:-5]
        doc = model[asm]["document"] if asm in model else asm
        for name, rec in json.load(open(p)).items():
            hand[f"{doc}/{name}"] = rec

    out, big = {}, 0
    for key, fr in frames.items():
        rec = hand.get(key)
        if rec is None:
            continue
        finv = inverse(tuple(fr[:3]), tuple(fr[3:]))
        rel = compose(finv, (tuple(rec["pos"]), tuple(rec["rot"])))
        d = math.dist((0.0, 0.0, 0.0), rel[0])
        big += d > 1.0
        out[key] = {"offset": [round(v, 9) for v in tuple(rel[0]) + tuple(rel[1])],
                    "shift": round(d, 6)}
    json.dump(out, open(out_path, "w"), indent=1, sort_keys=True)
    print(f"{len(out)} offsets from build-time frames "
          f"({big} shifted more than 1 mm from their datum)")


main()
