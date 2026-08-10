"""Helpers for building the machine as a real FreeCAD assembly.

The parts in `../` are reconstructions, each one a PartDesign body in its own
document.  This module puts them together using the Assembly workbench, so the
machine is held together by *joints* rather than by hard-coded placements: pose
comes from the joints' own driving values, an axis can be driven end to end and
re-checked, and an exploded view is an offset along each joint rather than a
second model.

Joints refer to the named datums `fcprim.lcs` puts on the parts, never to face
names -- see that function for why.

Everything here runs under `freecadcmd`; the Assembly workbench needs no GUI.
See [`ASSEMBLY.md`](../ASSEMBLY.md) for what is being built and in what order.

Three things about the Assembly API cost a while to find, and all three are
silent rather than loud, so they are worth stating plainly:

* **A cross-document `App::Link` needs the owner document to exist on disk.**
  Creating the link before the assembly has ever been saved raises
  `RuntimeError: Owner document not saved`.  `assembly()` therefore saves
  immediately, before anything can be linked in.

* **Whatever is not grounded is fair game.**  A joint constrains two parts
  *relative to each other*; if both are free the solver may satisfy it by
  moving whichever it likes.  A rod that was meant to stay put will happily
  come to the bracket instead, `solve()` will report success, and the result
  looks exactly like a solver that did nothing.  Ground the datum part of every
  chain.

* **`solve()` returns 0 on success and -1 on failure**, and on failure it
  leaves every placement untouched rather than raising.  `solve()` here checks
  the value and raises, so a joint that cannot be satisfied stops the build at
  the joint that caused it instead of quietly producing a wrong machine.
"""

import os
import sys

import FreeCAD as App
from FreeCAD import Matrix, Placement, Rotation, Vector

import JointObject
import UtilsAssembly

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim  # noqa: E402  (needs the path above)

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.dirname(HERE)

# The joint types this machine uses, from JointObject.JointTypes.
FIXED = "Fixed"
REVOLUTE = "Revolute"
CYLINDRICAL = "Cylindrical"
SLIDER = "Slider"
SCREW = "Screw"
GEARS = "Gears"


def assembly(name, path=None):
    """A fresh document holding an empty assembly, already saved.

    Saving straight away is not tidiness: a cross-document link cannot be made
    from a document that has no file yet.
    """
    if name in App.listDocuments():
        App.closeDocument(name)
    doc = App.newDocument(name)
    doc.saveAs(path or os.path.join(HERE, name + ".FCStd"))
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
    asm.newObject("Assembly::JointGroup", "Joints")
    doc.recompute()
    return doc, asm


def part(relpath):
    """Open a built part document and hand back its body.

    `relpath` is as the parts are laid out, e.g. `bot/BOT_RAIL_HOLDER`.  The
    document is left open, because a link into it needs it loaded.
    """
    path = os.path.join(PARTS, relpath + ".FCStd")
    if not os.path.exists(path):
        raise SystemExit(f"part not built: {path}  (run build.py first)")
    name = os.path.basename(relpath)
    doc = App.getDocument(name) if name in App.listDocuments() \
        else App.openDocument(path)
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            return obj
    raise SystemExit(f"no PartDesign body in {path}")


def link(asm, label, body, placement=None):
    """Bring a part into the assembly as an App::Link.

    The same body can be linked any number of times -- the eight LM8UU, the
    four stands -- and each link carries its own placement.
    """
    obj = asm.newObject("App::Link", "Link")
    obj.LinkedObject = body
    obj.Label = label
    if placement is not None:
        obj.Placement = placement
    asm.Document.recompute()
    return obj


def ground(asm, obj):
    """Pin a part to the assembly's own origin.

    Every joint chain needs one, or the solver is free to move the wrong end of
    it; see the module docstring.
    """
    group = UtilsAssembly.getJointGroup(asm)
    g = group.newObject("App::FeaturePython", "Grounded")
    JointObject.GroundedJoint(g, obj)
    g.Label = f"Ground {obj.Label}"
    asm.Document.recompute()
    return g


def datum(item, label):
    """The datum called `label` on a part, whether given the part or a link."""
    body = item.LinkedObject if item.TypeId == "App::Link" else item
    found = [o for o in body.Group
             if o.TypeId == "PartDesign::CoordinateSystem" and o.Label == label]
    if not found:
        have = sorted(o.Label for o in body.Group
                      if o.TypeId == "PartDesign::CoordinateSystem")
        raise SystemExit(
            f"{body.Label} has no datum {label!r}; it has {have or 'none'}")
    return found[0]


def at(item, label):
    """A joint reference to the datum called `label` inside a linked part.

    This is the whole point of `fcprim.lcs`: the reference names the datum, so
    it keeps meaning the same thing when the part is rebuilt.
    """
    # The API wants an element and a vertex; for a whole datum both are the
    # object itself.
    name = datum(item, label).Name
    return [item, [f"{name}.", f"{name}."]]


def joint(asm, kind, ref1, ref2, label=None, distance=None, distance2=None,
          offset=None, angle=None):
    """One joint between two references, solved straight away.

    Solving after each joint is deliberate: an assembly that will not solve
    tells you so at the joint that broke it, rather than at the end when
    anything might be to blame.
    """
    group = UtilsAssembly.getJointGroup(asm)
    j = group.newObject("App::FeaturePython", "Joint")
    JointObject.Joint(j, JointObject.JointTypes.index(kind))
    j.Reference1 = ref1
    j.Reference2 = ref2
    if distance is not None:
        j.Distance = distance
    if distance2 is not None:
        j.Distance2 = distance2
    if angle is not None:
        j.Angle = angle
    if offset is not None:
        j.Offset1 = Placement(Vector(0.0, 0.0, offset), Rotation())
    j.Label = label or f"{kind} {ref1[0].Label}-{ref2[0].Label}"
    asm.Document.recompute()
    solve(asm, context=j.Label)
    return j


def solve(asm, context=""):
    """Solve, and raise if it did not work.

    `AssemblyObject.solve()` reports -1 rather than raising, and leaves every
    placement where it was, so an unchecked call is indistinguishable from a
    machine that assembled correctly.
    """
    result = asm.solve()
    asm.Document.recompute()
    if result != 0:
        where = f" after {context}" if context else ""
        raise SystemExit(f"assembly failed to solve{where} (solve() = {result})")
    return result


def frame(item, label):
    """Where a part's datum has ended up in machine coordinates.

    The checks are written against these: a bore's axis, a face's position.
    """
    return item.Placement * datum(item, label).Placement


def axis_of(item, label):
    """The direction a datum's Z points, in machine coordinates."""
    return frame(item, label).Rotation.multVec(Vector(0.0, 0.0, 1.0))


def basis(xd, yd, zd):
    """A rotation given where it sends the three axes.

    Placing a reconstructed part usually means saying "its X runs along the
    machine's Z, its Y up" rather than naming an angle, and three unit vectors
    say that plainly where a pair of composed rotations does not.
    """
    m = Matrix()
    m.A11, m.A21, m.A31 = xd.x, xd.y, xd.z
    m.A12, m.A22, m.A32 = yd.x, yd.y, yd.z
    m.A13, m.A23, m.A33 = zd.x, zd.y, zd.z
    return Rotation(m)


def save(doc):
    # Saved already looking right: solids on, sketches and datums off.
    fcprim.dress(doc)
    doc.save()
    print(f"  saved {doc.FileName}")
    sys.stdout.flush()


def say(*args):
    """Print and flush -- freecadcmd exits without draining stdout."""
    print(*args)
    sys.stdout.flush()


def is_entry(script):
    """True when freecadcmd was asked to run this file, not one importing it.

    The usual `__name__ == "__main__"` guard is no help here: freecadcmd sets
    `__name__` to the module's basename, so a script that was run and the same
    script imported by another look identical.  The path it was handed on the
    command line does tell them apart.

    Without this, importing `frame` to reuse its geometry runs the whole of
    stage 1 as a side effect.
    """
    here = os.path.abspath(script)
    return any(os.path.abspath(arg) == here for arg in sys.argv[1:])
