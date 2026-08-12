"""Export the drawing pages to PDF, which is the one part that needs a GUI.

    flatpak run --filesystem=home org.freecad.FreeCAD drawings-pdf.py

[`drawings.py`](drawings.py) builds the pages, dimensions them and writes DXF
entirely headless.  PDF is the exception: it goes through `TechDrawGui`, and a
console FreeCAD refuses to load a Gui module at all.  So this is a second pass
over documents that already exist, and it draws nothing -- if a page is wrong,
it is wrong in `drawings.py`.

Like [`view.py`](view.py) this needs a real display, and for the same reason.
It also dresses each drawing document on the way past, so that opening one
shows the page rather than an empty 3D view.
"""

import os
import sys
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import TechDrawGui

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "technical-drawings"))


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def drawings(argv):
    named = [a for a in argv if a.endswith(".FCStd")]
    if named:
        return [a if os.path.isabs(a) else os.path.join(OUT, a) for a in named]
    return sorted(os.path.join(OUT, n) for n in os.listdir(OUT)
                  if n.endswith(".FCStd"))


def export(path):
    name = os.path.basename(path)[:-6]
    doc = App.openDocument(path)
    page = next(o for o in doc.Objects if o.TypeId == "TechDraw::DrawPage")

    # A page exports what its GUI view has drawn, so the view has to exist and
    # have caught up before the export runs.  Without the double click there
    # is no page view at all, and the SVG template -- the frame and the title
    # block -- never gets drawn into it, so the sheet comes out as bare views
    # floating on nothing.
    page.KeepUpdated = True
    doc.recompute()
    page.ViewObject.doubleClicked()
    from PySide import QtCore, QtGui
    for _ in range(3):
        QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 200)

    pdf = os.path.join(OUT, name + ".pdf")
    TechDrawGui.exportPageAsPdf(page, pdf)
    if not os.path.exists(pdf) or os.path.getsize(pdf) < 1000:
        raise RuntimeError(f"{name}: PDF came out empty")
    doc.save()
    return os.path.getsize(pdf)


def main(argv):
    paths = drawings(argv)
    if not paths:
        say("no drawings found -- run drawings.py first")
        return 1
    failed = []
    for path in paths:
        name = os.path.basename(path)[:-6]
        try:
            size = export(path)
            say(f"  {name}: {size // 1024} kB")
        except BaseException:
            failed.append(name)
            say(f"  {name}: FAILED")
            say(traceback.format_exc())
        for open_name in list(App.listDocuments()):
            App.closeDocument(open_name)
    say(f"\n{len(paths) - len(failed)}/{len(paths)} exported")
    for name in failed:
        say(f"  FAILED {name}")
    return 1 if failed else 0


STATUS = 1
try:
    STATUS = main(sys.argv[1:])
finally:
    os._exit(STATUS)      # see view.py: teardown can wedge, everything is saved
