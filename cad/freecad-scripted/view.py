"""Write the view data a GUI needs before it will show a built part.

`freecadcmd` has no view providers at all, so the `.FCStd` files it writes
contain no `GuiDocument.xml`.  Opening one in the real FreeCAD then goes wrong
in two ways at once: the GUI builds a view provider for every object from
scratch and each one comes up *hidden* -- overriding the App level `Visibility`
that `fcprim.dress` sets, which is why the whole tree greys out -- and with no
saved camera the 3D view starts a few millimetres wide at the origin, so even
an unhidden part would be off screen.  The document opens looking empty.

Both of those live in `GuiDocument.xml`, and only a GUI can write one.  So this
is the one script here that runs under the full FreeCAD binary rather than
under `freecadcmd`, with Qt's offscreen platform so that it still needs no
display:

    flatpak run --filesystem=home --env=QT_QPA_PLATFORM=offscreen \\
        org.freecad.FreeCAD cad/freecad/view.py                    # everything
    flatpak run --filesystem=home --env=QT_QPA_PLATFORM=offscreen \\
        org.freecad.FreeCAD cad/freecad/view.py shared/BOT_HANDWHEEL.FCStd

Paths are relative to this directory.  Run it after `build.py` -- building
stays headless, and this dresses what the build produced.
"""

import os
import re
import sys
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Rotation, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ASSEMBLIES = os.path.join(HERE, "asm")
# Assemblies that do not live in `asm/`.  There are none now that the
# microscope has been shelved, but the ordering rule below still needs the hook.
ELSEWHERE = ()

# Folders this script must not walk into.  Michael's hand-built `assembly/`
# lives in the frozen `../freecad/` tree and holds its parts together with
# **face and edge names** rather than with the LCS datums `asm/` uses.  Nothing
# in it is generated, so there is nothing here to dress -- and re-saving a
# document whose topological references have gone stale is how they get quietly
# rebound to the wrong edge.  Naming one on the command line still works; this
# only stops a bare run from finding it.
KEEP_OUT = ("assembly",)
sys.path.insert(0, HERE)

import fcprim  # noqa: E402  (needs the path above)

# How far the camera stands back, and how much air is left around the model,
# both as multiples of its diagonal.  An orthographic view is framed by its
# height rather than by its distance, so the standoff only has to clear the
# geometry and keep it between the near and far planes.
STANDOFF = 3.0
MARGIN = 1.15

# What FreeCAD stores in GuiDocument.xml as <Camera settings="...">, and reads
# back when the document is opened.
CAMERA = """#Inventor V2.1 ascii


OrthographicCamera {{
  viewportMapping ADJUST_CAMERA
  position {p.x:.6g} {p.y:.6g} {p.z:.6g}
  orientation {axis.x:.8g} {axis.y:.8g} {axis.z:.8g}  {angle:.8g}
  nearDistance {near:.6g}
  farDistance {far:.6g}
  aspectRatio 1
  focalDistance {focal:.6g}
  height {height:.6g}
}}
"""

SKIP = ("Assembly::AssemblyObject", "Assembly::JointGroup")

# A camera no real fit could produce: one millimetre tall, looking at the
# origin from a millimetre away.  `check_visible` points the camera here and
# asks FreeCAD to fit, so that a scene with anything at all in it must move it.
BOGUS = """#Inventor V2.1 ascii


OrthographicCamera {
  viewportMapping ADJUST_CAMERA
  position 0 0 1
  orientation 0 0 1  0
  aspectRatio 1
  focalDistance 5
  height 1
}
"""

# The octant FreeCAD's own isometric view looks from: front, right and above.
EYE = Vector(1, -1, 1)


def say(*args):
    """Print, straight down the file descriptor.

    Not `print`: the GUI puts its own object in `sys.stdout` and what goes
    into it is not seen until the process ends, so a run that takes ten
    minutes says nothing for ten minutes and a run that dies says nothing at
    all.  Writing to fd 1 is neither buffered nor redirected.
    """
    os.write(1, (" ".join(str(a) for a in args) + "\n").encode())


def documents(argv):
    """Every built document, parts before the assemblies that link them.

    Order matters here even though each document is saved on its own: a link
    remembers when the part it points at was last written, so re-saving a part
    after the assembly leaves the assembly complaining that its links are out
    of date every time it is opened.  `asm/` sorts first alphabetically, which
    is exactly the wrong way round.

    A named path may point outside this tree, which is how the hand-built
    assembly in `../freecad/assembly/` gets dressed without this script ever
    walking into it.
    """
    chosen = [a for a in argv if a.endswith(".FCStd")]
    if chosen:
        return [c if os.path.isabs(c) else os.path.join(HERE, c)
                for c in chosen]
    found = []
    for folder, subs, names in os.walk(HERE):
        subs[:] = [s for s in subs if s not in KEEP_OUT]
        found += [os.path.join(folder, n)
                  for n in names if n.endswith(".FCStd")]

    def assembly(path):
        return (os.path.dirname(path) == ASSEMBLIES
                or os.path.basename(path) in ELSEWHERE)

    return sorted(found, key=lambda p: (assembly(p), p))


def placed_box(doc):
    """The bounding box of everything the document is going to show.

    An `App::Link` shares one shape with every other link to the same part and
    carries the placement itself, so its shape has to be moved before it
    counts -- otherwise a whole machine measures as one part at the origin.
    """
    box = None
    for obj in doc.Objects:
        if not getattr(obj, "Visibility", False) or obj.TypeId in SKIP:
            continue                       # the container's shape is the union
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull() or not shape.Solids:
            continue
        if obj.TypeId == "App::Link":
            shape = obj.LinkedObject.Shape.copy()
            shape.Placement = obj.Placement.multiply(shape.Placement)
        box = shape.BoundBox if box is None else box.united(shape.BoundBox)
    return box


def isometric():
    """The orientation FreeCAD's own isometric view uses.

    Built rather than borrowed: `View3DInventor.viewIsometric` animates the
    camera through the render loop, and an offscreen view never renders, so
    calling it leaves the camera exactly where it was.  A camera looks down its
    own -Z with +Y up the screen, so this turns +Z to face the eye and then
    spins about that axis until the screen's up is the world's up, flattened.
    It agrees with FreeCAD's own axonometric quaternion to six decimals.
    """
    axis = Vector(EYE)
    axis.normalize()
    swing = Rotation(Vector(0, 0, 1), axis)
    up = Vector(0, 0, 1) - axis * axis.z
    up.normalize()
    return Rotation(swing.multVec(Vector(0, 1, 0)), up).multiply(swing)


def height(view):
    """The height of `view`'s camera, which is what frames an orthographic one."""
    return float(re.search(r"height\s+(\S+)", view.getCamera()).group(1))


def check_visible(view, name):
    """Fail unless the document has something in its scene graph to show.

    The bug this guards against showed nothing and reported success: the check
    was that every `Body.ViewObject.Visibility` was `True`, which is necessary
    but not sufficient -- under `DisplayModeBody='Through'` a visible body with
    a hidden tip draws nothing, and all 49 part documents were saved blank.
    (The assemblies were not: `Assembly::AssemblyObject` carries the union
    shape itself, so they drew even while their links did not.)  So measure the
    scene, not the property.

    `fitAll` uses `SoGetBoundingBoxAction` and needs no GL context, so it works
    offscreen -- but an empty scene gives it no bounding box to fit and it
    leaves the camera exactly where it stands.  Park the camera somewhere no
    fit could ever return and the height failing to change *is* the failure.

    This runs before `frame`, which sets the camera that is actually saved.
    """
    view.setCamera(BOGUS)
    view.fitAll()
    if height(view) <= 1.0001:
        raise RuntimeError(f"{name}: nothing in the scene, opens blank")


def frame(view, box):
    """Aim the camera at `box` from the standard isometric direction.

    `fitAll` would frame it tighter, and does work offscreen (see
    `check_visible`), but it only ever moves the camera along the direction it
    already points: it fits, it does not aim.  The isometric orientation and
    the near and far planes have to be computed from the geometry regardless,
    so the height is too, and the framing stays in one place.
    """
    rotation = isometric()
    span = box.DiagonalLength
    distance = span * STANDOFF
    view.setCamera(CAMERA.format(
        p=box.Center + rotation.multVec(Vector(0, 0, 1)) * distance,
        axis=rotation.Axis, angle=rotation.Angle,
        near=distance - span, far=distance + span,
        focal=distance, height=span * MARGIN))


def paint(doc):
    """Colour the printed parts, which is the half of a material only a GUI can.

    `fcprim.material` gives every body its material card as it is built, and
    for the two bought metals that is the whole job: their cards carry an
    appearance and FreeCAD shows it.  The printed parts wear the `Default`
    card, which the GUI insists on painting in `DefaultShapeColor` -- so their
    colour has to be set on the view provider, and a view provider only exists
    under a GUI.  This is the one, which is also the only thing that writes
    `GuiDocument.xml`, where the colour is stored.

    Only bodies that **say** they are printed are touched.  A document built
    before `PartMaterial` existed has no such property and is left exactly as
    it is, so dressing an old part cannot repaint a rod or a plate orange.
    """
    painted = 0
    for obj in doc.Objects:
        if getattr(obj, "PartMaterial", None) != fcprim.PRINTED:
            continue
        # The property hands back a copy, so the material has to be put back
        # for the change to reach the document.
        appearance = obj.ViewObject.ShapeAppearance
        appearance[0].DiffuseColor = fcprim.PRINTED_COLOUR
        obj.ViewObject.ShapeAppearance = appearance
        painted += 1
    return painted


def dress(path):
    """Give one document its visibilities and its camera, and save it back."""
    doc = App.openDocument(path)
    fcprim.dress(doc)
    paint(doc)
    view = Gui.getDocument(doc.Name).mdiViewsOfType("Gui::View3DInventor")[0]
    box = placed_box(doc)
    if box is not None:                    # nothing solid: leave the camera be
        check_visible(view, os.path.relpath(path, HERE))
        frame(view, box)
    doc.saveAs(path)                       # saveAs: save() skips a clean file
    return sum(1 for obj in doc.Objects if getattr(obj, "Visibility", False))


def main(argv):
    paths = documents(argv)
    if not paths:
        say("no documents found")
        return 1
    failed = []
    for path in paths:
        name = os.path.relpath(path, HERE)
        try:
            shown = dress(path)
            say(f"  {name}: {shown} object(s) shown")
        except BaseException:
            failed.append(name)
            say(f"  {name}: FAILED")
            say(traceback.format_exc())
        # An assembly pulls its parts open as links; close everything between
        # documents so the next one is saved on its own.
        for open_name in list(App.listDocuments()):
            App.closeDocument(open_name)
    say(f"\n{len(paths) - len(failed)}/{len(paths)} dressed")
    for name in failed:
        say(f"  FAILED {name}")
    return 1 if failed else 0


STATUS = 1                                 # until main says otherwise
try:
    STATUS = main(sys.argv[1:])
finally:
    # Nothing closes the application for us: the script runs inside a GUI that
    # would otherwise sit there with no window on an offscreen display.  So
    # leave the hard way.  Tearing down a run can wedge on a lock and sit there
    # at no CPU for ever, long after the last document is safely on disk --
    # `M8_55`, whose 44 turns of swept thread make much the biggest scene graph
    # here, hangs every time, minutes after it has printed that it is done.
    # Everything is saved and closed by now, so `os._exit` skips the teardown
    # entirely, and `say` has already written every line to fd 1.
    #
    # Not `Gui.getMainWindow().close()` first: that *is* the call that wedges,
    # and it buys nothing when the next line ends the process regardless.
    os._exit(STATUS)
