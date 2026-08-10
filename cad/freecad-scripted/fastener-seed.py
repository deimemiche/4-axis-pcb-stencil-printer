"""Make the seed document that lets a headless build create fasteners.

    freecadcmd fastener-seed.py            # writes assembly/FASTENER_SEED.FCStd

`import FastenersCmd` **segfaults** under freecadcmd -- with or without
`FreeCADGui.setupWithoutGUI()`, and whether or not its directory is added to
sys.path (it is already there twice).  The module loads safely only when
FreeCAD restores it itself, while opening a document that already contains a
fastener.

So this is run once, against the hand-built assembly, to mint a document
holding one screw of each type the machine uses.  Afterwards `asmbuild.py`
opens the seed instead, and the frozen tree is never touched again.  The seed
is opened and closed before any scripted document exists, so the two trees are
never open together.
"""
import os, sys, traceback

def say(*a): os.write(1, (" ".join(str(x) for x in a) + "\n").encode())
HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = ("ISO4762", "DIN934", "ISO4035", "ISO4027", "IUTHeatInsert")

def main():
    import FreeCAD as App
    donor = os.path.join(HERE, "..", "freecad", "assembly", "Eccenter.FCStd")
    d = App.openDocument(os.path.abspath(donor))          # read-only, never saved
    fs = [o for o in d.Objects if "BaseObject" in o.PropertiesList]
    if not fs:
        raise RuntimeError("donor holds no fastener, so the module cannot load")
    cls = type(fs[0].Proxy)
    say(f"proxy class restored: {cls.__module__}.{cls.__name__}")
    App.closeDocument(d.Name)                             # before anything else opens

    out = os.path.join(HERE, "assembly", "FASTENER_SEED.FCStd")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    doc = App.newDocument("FASTENER_SEED")
    for t in TYPES:
        o = doc.addObject("Part::FeaturePython", t)
        cls(o, t, None)
        o.Type = t
    doc.recompute()
    doc.saveAs(out)
    say(f"seed written: {out}  ({len(doc.Objects)} fasteners)")

try: main()
except Exception: say("SEED RAISED:"); say(traceback.format_exc()); sys.exit(1)
