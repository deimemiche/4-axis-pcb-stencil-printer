"""Draw the assemblies, so they can be looked at and compared with the manual.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/render.py                 # every assembly
    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/render.py Machine         # just one

Writes four orthographic views of each into [`render/`](render/), next to the
`.FCStd` they came from, and says which of the author's own build-step images
each one should be held up against.

Michael asked for the renders to be checked against the pictures in the build
manual, and this is the half of that a script can do: it produces ours and
names his.  Deciding whether they agree is still a job for eyes -- `reference.py`
fetches his into `reference/`, which is git-ignored because they are his
images.  Ours are committed, because they are the deliverable.

The heavy lifting is already written: `stlrender.py` rasterises a mesh with
nothing but Pillow, and the flatpak's own Python has Pillow in it, so this
tessellates and draws in one pass rather than shelling out.

An `App::Link` carries its own placement and shares its shape with every other
link to the same part, so each one's shape has to be copied and moved before it
is meshed -- otherwise four LM8UU all come out at the origin, on top of each
other.
"""

import os
import sys
import traceback

import FreeCAD as App
import Mesh
import MeshPart

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stlmeasure  # noqa: E402
import stlrender   # noqa: E402
from asmprim import HERE, say  # noqa: E402

INTO = os.path.join(HERE, "render")

# Which of the author's build-step images each assembly answers to.
AGAINST = {
    "BottomFrame": ("STEP_1_1-1", "STEP_1_2-1"),
    "Carriage": ("STEP_2_2",),
    "Alpha": ("STEP_4_2",),
    "Column": ("STEP_10_1", "STEP_12_1"),
    "Machine": ("STEP_18_1",),
    "MachineExploded": (),
}

# Tessellation: fine enough to read a T-slot, coarse enough to stay quick.
DEVIATION = 0.1
ANGULAR = 0.35

SIZE = 520
VIEWS = ("iso", "front", "side", "top")


def tessellate(doc, path):
    """Every placed solid in the document, as one mesh on disk."""
    mesh = Mesh.Mesh()
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or not shape.Solids:
            continue
        if obj.TypeId in ("Assembly::AssemblyObject", "Assembly::JointGroup"):
            continue                       # the container's shape is the union
        if obj.TypeId == "App::Link":
            shape = obj.LinkedObject.Shape.copy()
            shape.Placement = obj.Placement.multiply(shape.Placement)
        mesh.addMesh(MeshPart.meshFromShape(
            Shape=shape, LinearDeflection=DEVIATION,
            AngularDeflection=ANGULAR, Relative=False))
    mesh.write(path)
    return mesh.CountFacets


def draw(name):
    source = os.path.join(HERE, name + ".FCStd")
    if not os.path.exists(source):
        say(f"  {name}: not built yet, skipping")
        return None
    doc = App.openDocument(source)
    stl = os.path.join(INTO, name + ".stl")
    facets = tessellate(doc, stl)

    png = os.path.join(INTO, name + ".png")
    stlrender.sheet([stlmeasure.read_stl(stl)], list(VIEWS), SIZE).save(png)
    App.closeDocument(doc.Name)

    shown = ", ".join(AGAINST.get(name, ())) or "nothing in the manual"
    say(f"  {name}.png  ({facets} facets)   compare with {shown}")
    return png


def main(argv):
    os.makedirs(INTO, exist_ok=True)
    wanted = [a for a in argv if not a.endswith(".py")] or list(AGAINST)
    say(f"drawing into {INTO}")
    for name in wanted:
        try:
            draw(name)
        except BaseException:
            # freecadcmd prints nothing at all for an uncaught exception, so a
            # failure here would otherwise look like a render that silently
            # did not happen.
            say(f"  {name}: FAILED")
            say(traceback.format_exc())
    say("\nthe author's own images are in reference/ -- "
        "run reference.py if they are not there yet")


main(sys.argv[1:])
