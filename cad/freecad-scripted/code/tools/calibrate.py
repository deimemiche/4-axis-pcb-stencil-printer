"""Measure each fastener's offset in the frame the builder actually uses.

    ASM_OUT=<offsets.json> ASM_HAND=<hand-poses.json> ASM_WIRING=<wiring.json> \
        freecadcmd calibrate.py <Assembly.FCStd>

Deriving a fastener's offset from the hand-built assembly's own geometry kept
going wrong, and always the same way: the frame it was measured in and the datum
the builder resolves are two different resolutions of one edge, and OCC hands
back opposite orientations for them.  Every attempt to reconcile the two by
composing transforms put some bolts out by exactly twice their offset.

So it is measured where it is used instead.  The scripted assembly puts all 145
parts exactly where the hand-built one does -- that is verified -- so a datum's
global frame here IS the frame the hand-built bolt sits in.  The offset is then
just the distance from the datum to the known position, along the datum's own
axis, with nothing to compose and no orientation to guess.
"""
import json, os, sys, traceback

def say(*a): os.write(1, (" ".join(str(x) for x in a) + "\n").encode())

def main():
    import FreeCAD as App
    path = os.path.abspath([a for a in sys.argv[1:] if a.endswith(".FCStd")][0])
    name = os.path.basename(path)[:-6]
    hand = json.load(open(os.environ["ASM_HAND"]))
    wiring = json.load(open(os.environ["ASM_WIRING"]))["fasteners"]
    doc = App.openDocument(path)
    docname = doc.Name

    out, missing = {}, 0
    for key, w in wiring.items():
        asm, fname = key.split("/", 1)
        if asm != docname or fname not in hand:
            continue
        link = None
        for o in doc.Objects:
            if o.Name == w.get("via_link"):
                link = o
                break
        if link is None:
            missing += 1
            continue
        sub = w.get("prefix", "") + w["object"] + "."
        try:
            frame = link.getSubObject(sub, retType=3)
        except Exception:
            frame = None
        if frame is None:
            # A reference reaching through a sub-assembly whose path this
            # cannot resolve.  Skipped rather than guessed at.
            missing += 1
            continue
        # The whole offset, in the datum's own frame.  Both sides of this are
        # known in one coordinate system -- the datum resolved here, and the
        # position the hand-built assembly puts the fastener at -- so there is
        # nothing to compose and no orientation to infer.  It also survives a
        # datum that is not exactly at the bolt's own hole, which 35 are.
        want = App.Placement(App.Vector(*hand[fname]["pos"]),
                             App.Rotation(*hand[fname]["rot"]))
        rel = frame.inverse().multiply(want)
        z = frame.Rotation.multVec(App.Vector(0, 0, 1))
        delta = want.Base.sub(frame.Base)
        along = delta.dot(z)
        out[key] = {"offset": [round(v, 9) for v in
                               (rel.Base.x, rel.Base.y, rel.Base.z,
                                rel.Rotation.Q[0], rel.Rotation.Q[1],
                                rel.Rotation.Q[2], rel.Rotation.Q[3])],
                    "perp": round(delta.sub(z.multiply(along)).Length, 9)}
    json.dump(out, open(os.environ["ASM_OUT"], "w"), indent=1, sort_keys=True)
    off = sum(1 for v in out.values() if v["perp"] > 1e-3)
    say(f"{name}: {len(out)} calibrated, {off} still off-axis, {missing} unresolved")

try: main()
except Exception: say("CALIBRATE RAISED:"); say(traceback.format_exc())
