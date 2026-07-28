"""Stage 3 - the X axis: rails, holders and the linear bearings on them.

Manual step 2, "X-Axis Carriage": 2 rails 8 x 300, 4 `BOT_RAIL_HOLDER`,
4 `BOT_BEARING_MOUNT_X_AXIS`, 8 LM8UU, and the 257 x 162 print plate.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/carriage.py

## Where the rails go, and why nothing here is a guess

Every number below is forced by something already known, which is worth setting
out because the layout looked underdetermined for a long time.

* **Along X:** the rails are 300 and run between the inner faces of the two
  side members, which `frame.py` puts at X = +-150.  So a rail runs -150 .. 150
  and its holders sit on those two faces.
* **Across Z:** the print plate's sixteen holes are four clusters of four,
  centred on +-111 and +-67.5 in the drawing.  Manual step 2 has **16 M3x6 for
  4 bearing mounts** -- four screws each -- so one mount lands on each cluster.
  The mounts ride the rails, so the rails are **222 apart**, at Z = +-111, and
  the two mounts on a rail sit at X = +-67.5.
* **In Y:** `BOT_RAIL_HOLDER` bolts flat to a face with both screws in one
  T-slot, and a 2020's inner face has a single slot on its centre line, which
  `frame.py` puts at Y = -10.  The holder's bore sits 1 mm off its bolt line --
  the asymmetry that is the whole point of the part -- so the rail lands at
  **Y = -11**.

## Which way round the print plate goes

**257 across the rails and 162 along them.**  That looks like a coin toss from
the plate alone and it is not: `BOT_BEARING_MOUNT_X_AXIS` bolts down to it with
four screws at +-8.5 along the rail and +-13.35 across, so **17 by 26.7**.  The
plate's holes come in fours at 76 - 59 = **17** one way and
124.35 - 97.65 = **26.7** the other.  Only one orientation makes those meet, and
it puts the plate's 257 across the rails.

Two things then fall out, and both check:

* the plate reaches Z = +-128.5 and the mounts sit at +-111 with a half width
  of 17.5, so each mount's outer face lands **flush with the plate's edge**;
* the Y rails are 244 and run across the plate's 257, 6.5 mm clear at each end.

## How the three axes stack up

The mount is the corner of the XY stage and carries all three at right angles.
Its bearing seat sits 11.6 mm above its own foot and its trough 14.6 mm above
the seat, so once the bearing is on the X rail everything else follows:

| | Y |
|---|---|
| print plate, top face | -22.6 |
| X rail | -11 |
| Y rail, in the troughs | +3.6 |

The print plate therefore hangs inside the frame's opening, a little below its
underside, and the Y rails run above the frame's top face -- which is where the
alpha axis has to be, since it rides them.

## What it checks

The plan calls the collinearity of the X bores the first real test, because it
is the first thing that can catch an error no single part's own volume or point
check could.  It is checked here two ways -- the pair of holder datums on each
rail, and the rod actually passing through both bores.
"""

import math
import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import frame    # noqa: E402
import stock    # noqa: E402
from asmprim import say  # noqa: E402

RAIL_D = 8.0
RAIL_LENGTH = 300.0
Y_RAIL_LENGTH = 244.0

RAIL_Z = (-111.0, 111.0)         # from the print plate's hole clusters
BEARING_X = (-67.5, 67.5)        # the two mounts on each rail
SLOT_Y = -10.0                   # a 2020's inner face slot, on its centre line
RAIL_Y = SLOT_Y - 1.0            # the holder's bore sits 1 mm off its bolts

PLATE_THICKNESS = 2.0

TOL = 1e-6


def rail_holders(doc, asm):
    """Four holders, two per rail, bolted to the side members' inner faces.

    The holder is modelled with its bore along +X, its bolt line on Y = 0 and
    its long axis up Z, so the left hand pair go in unturned and the right hand
    pair turn half a turn about Y to face back the other way.
    """
    body = asmprim.part("bot/BOT_RAIL_HOLDER")
    bore_z = asmprim.datum(body, "RAIL").Placement.Base.z
    face_x = frame.HALF_SPAN                      # 150, the inner faces
    foot = -asmprim.datum(body, "MOUNT").Placement.Base.x   # 1.4

    holders = []
    for side in (-1, 1):
        for z in RAIL_Z:
            if side < 0:
                turn, at = 0.0, Vector(-face_x + foot, SLOT_Y, z - bore_z)
            else:
                turn, at = 180.0, Vector(face_x - foot, SLOT_Y, z + bore_z)
            holder = asmprim.link(
                asm, f"BOT_RAIL_HOLDER {'L' if side < 0 else 'R'}{z:+.0f}",
                body, Placement(at, Rotation(Vector(0, 1, 0), turn)))
            asmprim.ground(asm, holder)
            holders.append(holder)
    doc.recompute()
    return holders


def rails(doc, asm):
    """The two 8 mm rails, spanning the frame."""
    made = []
    for z in RAIL_Z:
        rod = stock.rod(doc, f"X rail {z:+.0f}", RAIL_D, RAIL_LENGTH)
        # Built along +Z, so turn it to lie along X at the height the holders
        # put it.
        rod.Placement = Placement(Vector(-RAIL_LENGTH / 2.0, SLOT_Y - 1.0, z),
                                  Rotation(Vector(0, 1, 0), 90))
        asmprim.ground(asm, rod)
        made.append(rod)
    doc.recompute()
    return made


def bearings(doc, asm, rods):
    """The four LM8UU that ride the X rails, where the mounts hold them.

    Manual step 2 buys eight; these are the four the X rails carry, and the
    other four go on the Y rails in the stage that builds those.

    These are the one thing in this file that genuinely moves, so they are
    joined with `Cylindrical` rather than placed: the joint leaves the slide
    along the rail and the spin about it free, which is what a linear bearing
    does.
    """
    made = []
    for rod, z in zip(rods, RAIL_Z):
        for x in BEARING_X:
            sleeve = stock.linear_bearing(doc, f"LM8UU {x:+.0f},{z:+.0f}")
            sleeve.Placement = Placement(
                Vector(x - 12.0, SLOT_Y - 1.0, z),
                Rotation(Vector(0, 1, 0), 90))
            doc.recompute()
            asmprim.joint(asm, asmprim.CYLINDRICAL,
                          [sleeve, ["Face2", "Face2"]],
                          [rod, ["Face1", "Face1"]],
                          label=f"LM8UU {x:+.0f},{z:+.0f} on rail {z:+.0f}")
            made.append(sleeve)
    return made


def bearing_mounts(doc, asm):
    """The four mounts, one on each of the print plate's hole clusters.

    They go in unturned: the part is drawn with its bearing along X, its trough
    across Z and its foot down -Y, which is exactly how the machine wants it.
    """
    body = asmprim.part("bot/BOT_BEARING_MOUNT_X_AXIS")
    mounts = []
    for z in RAIL_Z:
        for x in BEARING_X:
            mount = asmprim.link(
                asm, f"BOT_BEARING_MOUNT_X_AXIS {x:+.0f},{z:+.0f}", body,
                Placement(Vector(x, RAIL_Y, z), Rotation()))
            mounts.append(mount)
    doc.recompute()
    return mounts


def print_plate(doc, asm, mounts):
    """The 257 x 162 plate the mounts stand on.

    Turned a quarter turn about Y so its 257 runs across the rails, which is
    the orientation its own bolt pattern forces -- see the module docstring.
    """
    body = asmprim.part("plate/XY_PLATE")
    # The mounts' feet all sit at the same height; the plate's top face meets
    # them, and the plate hangs below that.
    top = asmprim.frame(mounts[0], "PLATE").Base.y
    plate = asmprim.link(asm, "XY_PLATE", body,
                         Placement(Vector(0.0, top - PLATE_THICKNESS, 0.0),
                                   Rotation(Vector(0, 1, 0), 90)))
    doc.recompute()
    return plate


def y_rails(doc, asm, mounts):
    """The two 244 mm Y rails, clamped in the mounts' troughs."""
    seat = asmprim.frame(mounts[0], "TROUGH").Base.y
    made = []
    for x in BEARING_X:
        rod = stock.rod(doc, f"Y rail {x:+.0f}", RAIL_D, Y_RAIL_LENGTH)
        rod.Placement = Placement(
            Vector(x, seat, -Y_RAIL_LENGTH / 2.0), Rotation())
        asmprim.ground(asm, rod)
        made.append(rod)
    doc.recompute()
    return made


def check_bolts_land(mounts, plate):
    """Do the mounts' feet bolt into holes that are actually there?

    This is the check the plan calls fastener alignment, and it is the one that
    exercises hole positions *across* a part boundary -- nothing before the
    assembly could test it.  Each mount has four M3 through its foot; every one
    of them has to find a hole in the print plate.
    """
    holes = []
    for face in plate.LinkedObject.Shape.Faces:
        surface = face.Surface
        if surface.TypeId != "Part::GeomCylinder" or surface.Radius > 2.0:
            continue
        centre = plate.Placement.multVec(surface.Center)
        holes.append(centre)
    say(f"  the plate offers {len(holes)} holes")

    worst = 0.0
    misses = 0
    for mount in mounts:
        for i in range(4):
            bolt = asmprim.frame(mount, f"BOLT{i + 1}").Base
            near = min(math.hypot(bolt.x - h.x, bolt.z - h.z) for h in holes)
            worst = max(worst, near)
            if near > 0.05:
                say(f"  FAIL {mount.Label} BOLT{i + 1} is {near:.2f} mm "
                    f"from the nearest hole")
                misses += 1
    if misses:
        raise SystemExit(f"{misses} mounting bolts have no hole to go into")
    say(f"  ok: all 16 bolts land on holes, worst off by {worst:.3f} mm")


def check_stack(mounts, plate, rails_y):
    """The three axes are where the mount's own geometry says they should be.

    Also the thing worth knowing about this machine's layout: the plate hangs
    below the frame and the Y rails run above it.
    """
    # The link's own shape is unturned, so its X is what ends up across the
    # rails once the quarter turn is applied.
    plate_bb = plate.LinkedObject.Shape.BoundBox
    top = asmprim.frame(mounts[0], "PLATE").Base.y
    say(f"  print plate top at Y {top:.1f}, "
        f"{plate_bb.XLength:.0f} across the rails and "
        f"{plate_bb.ZLength:.0f} along them")
    say(f"  X rail at Y {RAIL_Y:.1f}, "
        f"Y rail at Y {asmprim.frame(mounts[0], 'TROUGH').Base.y:.1f}")

    ok = True
    # Each mount's outer face should land flush with the plate's edge.
    reach = max(abs(m.LinkedObject.Shape.BoundBox.ZMin) for m in mounts)
    edge = max(RAIL_Z) + reach
    plate_edge = 257.0 / 2.0
    if abs(edge - plate_edge) > 0.01:
        say(f"  FAIL the mounts reach Z {edge:.2f} but the plate ends at "
            f"{plate_edge:.2f}")
        ok = False

    for rod, x in zip(rails_y, BEARING_X):
        bb = rod.Shape.BoundBox
        if abs(bb.ZLength - Y_RAIL_LENGTH) > TOL:
            say(f"  FAIL Y rail {x:+.0f} is {bb.ZLength:.1f}")
            ok = False
        if bb.ZMin < -plate_edge or bb.ZMax > plate_edge:
            say(f"  FAIL Y rail {x:+.0f} runs off the plate")
            ok = False
    if not ok:
        raise SystemExit("the carriage does not stack up")
    say(f"  ok: mounts flush with the plate edge at Z {edge:.1f}, "
        f"Y rails 244 with {plate_edge - Y_RAIL_LENGTH / 2.0:.1f} mm to spare")


def check_collinear(holders):
    """Do the two bores on each rail share an axis?

    The first test the assembly can do that no part could do alone: each holder
    passed its own volume and point checks, and they can still fail to line up.
    """
    ok = True
    for z in RAIL_Z:
        pair = [h for h in holders if f"{z:+.0f}" in h.Label]
        if len(pair) != 2:
            raise SystemExit(f"expected two holders on rail {z:+.0f}")
        a, b = (asmprim.frame(h, "RAIL") for h in pair)
        axis_a = asmprim.axis_of(pair[0], "RAIL")
        axis_b = asmprim.axis_of(pair[1], "RAIL")

        tilt = math.degrees(axis_a.getAngle(axis_b))
        tilt = min(tilt, 180.0 - tilt)         # the sense is not signed
        # How far the second bore's centre lies off the first bore's axis.
        between = b.Base - a.Base
        off = between.cross(axis_a).Length / axis_a.Length

        say(f"  rail {z:+7.1f}: bores at {a.Base} and {b.Base}")
        say(f"               parallel to {tilt:.2e} deg, "
            f"offset {off:.2e} mm")
        if tilt > TOL or off > TOL:
            say("               FAIL these two bores are not collinear")
            ok = False
    if not ok:
        raise SystemExit("the X axis bores do not line up")
    say("  ok: both rails' bores are collinear")


def check_fit(holders, rods):
    """Does the rod actually pass through every bore, and reach both ends?"""
    ok = True
    for rod, z in zip(rods, RAIL_Z):
        bb = rod.Shape.BoundBox
        span = 2 * frame.HALF_SPAN
        if abs(bb.XLength - RAIL_LENGTH) > TOL:
            say(f"  FAIL rail {z:+.0f} is {bb.XLength:.2f}, "
                f"not {RAIL_LENGTH}")
            ok = False
        if abs(bb.XMin + span / 2.0) > TOL or abs(bb.XMax - span / 2.0) > TOL:
            say(f"  FAIL rail {z:+.0f} runs {bb.XMin:.1f}..{bb.XMax:.1f}, "
                f"not flush with the side members' faces")
            ok = False
        for holder in [h for h in holders if f"{z:+.0f}" in h.Label]:
            seat = asmprim.frame(holder, "RAIL").Base
            axis = asmprim.axis_of(holder, "RAIL")
            off = (seat - Vector(0, bb.YMin + RAIL_D / 2.0, z)) \
                .cross(axis).Length / axis.Length
            if off > TOL:
                say(f"  FAIL {holder.Label} is {off:.3f} mm off its rail")
                ok = False
    if not ok:
        raise SystemExit("the rails do not fit their holders")
    say(f"  ok: both rails are {RAIL_LENGTH:.0f} long and flush at each end")


def build():
    doc, asm = asmprim.assembly("Carriage")
    say("=== the bottom frame, as stage 1 leaves it")
    members = frame.bottom_frame(doc, asm)
    frame.check_size(members)

    say("=== four rail holders on the side members")
    holders = rail_holders(doc, asm)
    check_collinear(holders)

    say("=== the two X rails")
    rods = rails(doc, asm)
    check_fit(holders, rods)

    say("=== the four LM8UU on the X rails, joined so they still slide")
    sleeves = bearings(doc, asm, rods)
    asmprim.solve(asm, context="the linear bearings")
    for sleeve in sleeves[:2]:
        bb = sleeve.Shape.BoundBox
        say(f"  {sleeve.Label} sitting at x {bb.XMin:.1f}..{bb.XMax:.1f}")
    say(f"  ok: {len(sleeves)} bearings on the rails, free to slide")

    say("=== the four bearing mounts, and the plate they stand on")
    mounts = bearing_mounts(doc, asm)
    plate = print_plate(doc, asm, mounts)
    check_bolts_land(mounts, plate)

    say("=== the two Y rails, in the mounts' troughs")
    rails_y = y_rails(doc, asm, mounts)
    check_stack(mounts, plate, rails_y)

    asmprim.save(doc)
    say("\nSTAGE 3 (XY carriage) PASSED -- bores collinear, "
        "bolts land, axes stack up")


if asmprim.is_entry(__file__):
    build()
