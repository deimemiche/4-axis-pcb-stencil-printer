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
import json, math, os, sys


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
        # `data/hand/<Assembly>.json`, as `rebuild.py`'s poses stage writes it.
        # This used to split on an `fh-` prefix those files have not carried
        # for some time, so every key came out as a whole path, nothing matched
        # the frames, and the calibration wrote an **empty** offsets file --
        # silently, since a run with nothing to say still says "0 offsets".
        asm = os.path.basename(p)[:-5]
        if asm not in model:
            raise SystemExit(f"{p}: {asm!r} is not an assembly in the model")
        doc = model[asm]["document"]
        for name, rec in json.load(open(p)).items():
            hand[f"{doc}/{name}"] = rec

    out, off_axis = {}, []
    for key, fr in frames.items():
        rec = hand.get(key)
        if rec is None:
            continue
        finv = inverse(tuple(fr[:3]), tuple(fr[3:]))
        rel = compose(finv, (tuple(rec["pos"]), tuple(rec["rot"])))
        # How far the bolt sits from its datum, split the only way that means
        # anything: **along** the datum's own Z is what an offset is *for* --
        # a nut 20 mm up a stud is not an error -- while **across** it says
        # the datum is not on the bolt's line at all.  Reporting the total
        # distance flagged the honest ones and buried the rest.
        across = math.hypot(rel[0][0], rel[0][1])
        if across > 0.05:
            off_axis.append((across, key))
        out[key] = {"offset": [round(v, 9) for v in tuple(rel[0]) + tuple(rel[1])],
                    "along": round(rel[0][2], 6), "across": round(across, 6)}
    json.dump(out, open(out_path, "w"), indent=1, sort_keys=True)
    print(f"{len(out)} offsets from build-time frames, "
          f"{len(out) - len(off_axis)} of them on their datum's own axis")
    for across, key in sorted(off_axis, reverse=True):
        print(f"    {across:9.3f} mm across the axis  {key}")


main()
