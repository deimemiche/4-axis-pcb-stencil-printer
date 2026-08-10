"""Dump the solved global placement of every part instance in one assembly.

    ASM_OUT=<poses.json> freecadcmd asmpose.py <path.FCStd>

One document per process, and never both trees in one: they hold documents with
the same internal names, and FreeCAD identifies open documents by name.  Opening
the hand-built Bottom_Frame and the scripted one together gets you
Bottom_Frame001 and links resolved against the wrong tree.  `asmdiff.py` runs
this twice and compares the two files.
"""
import json, os, sys, traceback

def say(*a): os.write(1, (" ".join(str(x) for x in a) + "\n").encode())

def main():
    import FreeCAD as App
    path = os.path.abspath([a for a in sys.argv[1:] if a.endswith(".FCStd")][0])
    doc = App.openDocument(path)
    out = {}
    for o in doc.Objects:
        if o.TypeId not in ("App::Link", "Assembly::AssemblyLink"):
            continue
        try:
            p = o.getGlobalPlacement()
        except Exception:
            p = o.Placement
        out[o.Name] = {"label": o.Label,
                       "pos": [p.Base.x, p.Base.y, p.Base.z],
                       "rot": list(p.Rotation.Q)}
    json.dump(out, open(os.environ["ASM_OUT"], "w"), indent=1, sort_keys=True)
    say(f"{os.path.basename(path)}: {len(out)} instances")

try: main()
except Exception: say("POSE RAISED:"); say(traceback.format_exc())
