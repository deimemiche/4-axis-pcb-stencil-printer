"""Stage 0 - does the Assembly workbench actually work headless?

[`ASSEMBLY.md`](../ASSEMBLY.md) makes two bets, and everything else in `asm/`
is built on them:

1. the Assembly workbench can be driven from `freecadcmd`, with no GUI -- its
   joints are Python features, so this was genuinely in doubt;
2. a joint can reference a **named datum** (`fcprim.lcs`) instead of a face
   name, which is what keeps the assembly from breaking every time a part is
   rebuilt.

Both hold.  This file is kept as a regression test rather than thrown away,
because a FreeCAD upgrade could take either of them back, and the failure would
otherwise turn up much later looking like a modelling mistake.

It checks, in order:

    joints reference datums     a reference resolves to the LCS, and carries
                                the LCS's own placement into the assembly
    Fixed really constrains     a part shoved somewhere arbitrary is brought
                                back to exactly where the joint says
    Cylindrical really frees    a bore ends up collinear with its rod, while
                                the slide and the spin stay free
    failure is reported         an impossible assembly returns -1 rather than
                                claiming success
    it survives a round trip    saved, reopened, and solved again

Run it with:

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/stage0.py
"""

import math
import os
import shutil
import sys

import FreeCAD as App
from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import fcprim   # noqa: E402
from asmprim import say  # noqa: E402

SCRATCH = os.path.join(asmprim.HERE, ".stage0")

TOL = 1e-6


def block(name, length):
    """A bored block with a datum on the bore axis, at the far end.

    The datum is deliberately *not* at the body origin.  If it were, a Fixed
    joint between two of these would be satisfied by leaving everything at the
    origin, and a solver that did nothing at all would pass the test.
    """
    doc = App.newDocument(name)
    bdy = fcprim.body(doc, name)

    box = doc.addObject("PartDesign::AdditiveBox", "Box")
    box.Length, box.Width, box.Height = length, 20.0, 20.0
    box.Placement = Placement(Vector(0, -10, -10), Rotation())
    bdy.addObject(box)

    bore = doc.addObject("PartDesign::SubtractiveCylinder", "Bore")
    bore.Radius, bore.Height = 4.1, length + 2
    bore.Placement = Placement(Vector(-1, 0, 0), Rotation(Vector(0, 1, 0), 90))
    bdy.addObject(bore)
    doc.recompute()

    fcprim.lcs(bdy, "BORE", at=(length, 0, 0), axis=(1, 0, 0))
    doc.recompute()

    doc.saveAs(os.path.join(SCRATCH, name + ".FCStd"))
    return bdy


def check(condition, message):
    if not condition:
        raise SystemExit("FAILED: " + message)
    say(f"  ok: {message}")


def test_datums_and_joints():
    say("=== parts, each with a named datum")
    body_a = block("Stage0BlockA", 30.0)
    body_b = block("Stage0BlockB", 40.0)

    doc, asm = asmprim.assembly("Stage0", os.path.join(SCRATCH, "Stage0.FCStd"))
    a = asmprim.link(asm, "BlockA", body_a)
    b = asmprim.link(asm, "BlockB", body_b)
    rod = asm.newObject("Part::Cylinder", "Rod")
    rod.Radius, rod.Height = 4.0, 200.0
    rod.Placement = Placement(Vector(0, 0, 0), Rotation(Vector(0, 1, 0), 90))
    doc.recompute()

    asmprim.ground(asm, a)
    asmprim.ground(asm, rod)

    say("=== a reference resolves to the datum, not to a face")
    ref_a, ref_b = asmprim.at(a, "BORE"), asmprim.at(b, "BORE")
    import UtilsAssembly
    target = UtilsAssembly.getObject(ref_a)
    check(target.TypeId == "PartDesign::CoordinateSystem",
          f"reference resolves to a coordinate system (got {target.TypeId})")
    world = UtilsAssembly.getGlobalPlacement(ref_a)
    check((world.Base - Vector(30, 0, 0)).Length < TOL,
          f"the datum's own placement reaches the assembly (at {world.Base})")

    say("=== Fixed brings a part back to exactly where the joint says")
    b.Placement = Placement(Vector(37, -22, 61), Rotation(Vector(1, 2, 3), 47))
    doc.recompute()
    fixed = asmprim.joint(asm, asmprim.FIXED, ref_a, ref_b, label="A to B")

    # Fixed makes the two datums coincide in machine coordinates, so B's
    # placement is forced: whatever carries B's own datum onto A's.
    want = asmprim.frame(a, "BORE") * asmprim.datum(b, "BORE").Placement.inverse()
    got = b.Placement
    moved = (got.Base - Vector(37, -22, 61)).Length
    check(moved > 1.0, f"the solver actually moved the part ({moved:.1f} mm)")
    check((got.Base - want.Base).Length < TOL
          and abs((got.Rotation * want.Rotation.inverted()).Angle) < TOL,
          f"and to the placement the joint implies ({got.Base})")

    say("=== Cylindrical puts the bore on the rod and leaves it free")
    group = UtilsAssembly.getJointGroup(asm)
    group.removeObject(fixed)
    doc.removeObject(fixed.Name)
    b.Placement = Placement(Vector(-14, 55, -8), Rotation(Vector(3, 1, 2), 110))
    doc.recompute()
    asmprim.joint(asm, asmprim.CYLINDRICAL, ref_b,
                  [rod, ["Face1", "Face1"]], label="B on rod")

    seat = asmprim.frame(b, "BORE")
    tilt = math.degrees(
        asmprim.axis_of(b, "BORE").getAngle(Vector(1, 0, 0)))
    tilt = min(tilt, 180.0 - tilt)          # the axis direction is not signed
    off = math.hypot(seat.Base.y, seat.Base.z)
    check(off < TOL and tilt < TOL,
          f"bore is collinear with the rod (off-axis {off:.2e} mm, "
          f"tilt {tilt:.2e} deg)")
    check(abs(seat.Base.x) > 1.0,
          f"and free to slide along it (sitting at x = {seat.Base.x:.1f})")

    say("=== saved, reopened, solved again")
    asmprim.save(doc)
    for name in ("Stage0", "Stage0BlockA", "Stage0BlockB"):
        App.closeDocument(name)
    again = App.openDocument(os.path.join(SCRATCH, "Stage0.FCStd"))
    asm2 = again.getObject("Assembly")
    joints = [o.JointType for o in again.Objects if hasattr(o, "JointType")]
    check(asm2 is not None and joints == ["Cylindrical"],
          f"the assembly and its joints came back ({joints})")
    check(asm2.solve() == 0, "and it still solves")
    App.closeDocument("Stage0")


def test_failure_is_reported():
    """An impossible assembly must not report success.

    Building one joint at a time and solving after each is only worth doing if
    a solve that cannot be done actually says so.
    """
    say("=== an impossible assembly is reported, not silently accepted")
    doc, asm = asmprim.assembly("Stage0Fail",
                                os.path.join(SCRATCH, "Stage0Fail.FCStd"))
    one = asm.newObject("Part::Box", "One")
    two = asm.newObject("Part::Box", "Two")
    two.Placement = Placement(Vector(50, 0, 0), Rotation())
    doc.recompute()

    # Both grounded 50 mm apart, then told to coincide.
    asmprim.ground(asm, one)
    asmprim.ground(asm, two)

    raised = False
    try:
        asmprim.joint(asm, asmprim.FIXED,
                      [one, ["Vertex1", "Vertex1"]],
                      [two, ["Vertex1", "Vertex1"]], label="impossible")
    except SystemExit:
        raised = True
    check(raised, "solve() reported the failure and asmprim raised on it")
    check((two.Placement.Base - Vector(50, 0, 0)).Length < TOL,
          "and nothing was moved by the attempt")
    App.closeDocument("Stage0Fail")


def main():
    shutil.rmtree(SCRATCH, ignore_errors=True)
    os.makedirs(SCRATCH)
    try:
        test_datums_and_joints()
        test_failure_is_reported()
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    say("\nSTAGE 0 PASSED -- joints work headless and reference named datums")


if asmprim.is_entry(__file__):
    main()
