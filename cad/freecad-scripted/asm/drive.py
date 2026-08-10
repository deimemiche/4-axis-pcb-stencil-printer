"""Steps 3, 5, 7, 8 and 9 - the three screws, and everything they drive.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/drive.py

This is what finishes stage 3 and stage 4.  The manual does the axes in an
order the plan did not expect: the carriage in step 2, the alpha axis in
steps 3 to 6, and only then the drives, because two of the three are shared
between them.  Following the manual rather than the plan, they all land here.

| screw | runs along | supported by | its nuts are in | turned by |
|---|---|---|---|---|
| X | machine X | `BOT_BRACKET_X_AXIS` on the frame | `BOT_RAIL_CLAMP_X_DRIVE` | a handwheel |
| Y | machine Z | `BOT_RAIL_CLAMP_Y_AXIS_1`'s tube | `..._Y_AXIS_DRIVEN`'s arm | a handwheel |
| worm | machine Z | two saddles on the fixed plate | none - it turns the ring | a handwheel |

## The spring loaded drive, and which end is which

Steps 5 and 8 are the same trick twice and the manual only says "insert two M5
nuts as shown".  The parts say the rest of it, and `STEP_8_1` shows it plainly:
the two nuts sit in the **webbed arm's own pockets**, one either side of the
deep hollow between the ribs, and the spring goes between them.  Sprung apart,
the two nuts bite opposite flanks of the same thread, which is a backlash-free
nut made out of two nuts and a spring.

That also settles which end of each screw is which, because a nut carrier has
to travel and a bearing has to stay put:

* the X screw's nuts are in `BOT_RAIL_CLAMP_X_DRIVE`, which is bolted to the
  **carriage**, so the screw is anchored to the **frame** and the handwheel
  does not move;
* the Y screw's nuts are in `BOT_BEARING_MOUNT_Y_AXIS_DRIVEN`'s arm, which is
  bolted under the **alpha plate**, so the screw runs in the tube on
  `BOT_RAIL_CLAMP_Y_AXIS_1`, which is on the **carriage**, and again the
  handwheel stays where it is.

Both of those are the same shape hollowed the same way over the same spans,
which `STATUS.md` noticed long before anyone knew what the hollows were for.

## Two parts that are not what their names say

Worth writing down, because the reconstruction docstrings were written from the
meshes alone and read them differently:

* **`BOT_BEARING_MOUNT_Y_AXIS` is an LM8UU holder**, not a screw bearing.  Its
  seat is 15.2 mm with 13.2 mm lips, which is an LM8UU (15 mm across, 24 long)
  dropped in from below and retained; four of them clip the alpha plate onto
  the Y rails, which is what step 6 means by "clip the Alpha Axis Assembly to
  the LM8UU bearings".
* **`BOT_ROD_HOLDER_ALPHA_AXIS` carries the worm's shaft**, and the "alpha axis
  rod" of its name is that shaft rather than a rail.  Its bore is 5.3 - an M5
  clearance, not an 8 mm rail.

## Where the worm goes, and why the fixed plate is asymmetric

`ASSEMBLY.md` had `ALPHA_BOT_PLATE`'s asymmetry down as an open question: its
corner clusters of M3 are on the left of the drawing only.  They are the worm
shaft's two saddles, and that is the whole answer - the worm exists on one side
of the plate, so its saddles do too.

Everything about the worm follows from that cluster and the two gears:

* the clusters put the shaft at **x = -83.55**, and the saddle's own plate is
  6.5 mm thick, so the shaft sits 6.5 mm above the fixed plate;
* the ring's pitch radius is 79.23 and the worm's is 4.25, so a worm meshing
  with it has its axis **83.48** from the alpha axis.  The saddles say 83.55.
  Two parts drawn by different routes - a 2D drawing and a mesh - agreeing to
  **0.07 mm** on a number neither one states;
* and the ring has to be turned so its teeth face the shaft, which is what
  `alpha.check_clocking` tests.  Of the five ways the ring bolts to the top
  plate only one does, and it is the one that puts the teeth at 180 degrees.

## What is still read off the renders rather than derived

Two things, and both are stations along an axis rather than a fit:

* which of the four troughs each of step 7's clamps goes on.  The two that
  carry a screw are forced - the X drive's eye has to line up with the
  bracket, and the Y support's tube with the driven mount's arm - so it is only
  the two plain ones that could be swapped, and they are interchangeable;
* how far each screw's plain end sticks out.  The manual buys three M5 x 270
  and the machine does not need all of it, so each screw is placed from its
  handwheel and left to run its 270.
"""

import math
import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alpha     # noqa: E402
import asmprim   # noqa: E402
import carriage  # noqa: E402
import fasteners  # noqa: E402
import frame     # noqa: E402
import stock     # noqa: E402
from asmprim import say  # noqa: E402

TOL = 1e-6

SCREW_D = 5.0
SCREW_LENGTH = 270.0             # M5 x 270, three of them
NUT_ACROSS = 8.0                 # M5, across flats
NUT_THICK = 4.0                  # ISO 4032 M5, along the screw
SPRING_D = 8.0                   # over an M5, inside the arm's own hollow
SPRING_WIRE = 0.9

# The two hollows in a webbed arm that take the nuts, and the one between them
# that takes the spring.  Both arms are hollowed over identical spans, so one
# set of numbers does for both.
NUT_AT = (-9.5, 5.1)

# Where each of step 7's four clamps goes, as (x, z) on the carriage's four
# troughs.  The two that carry a screw are forced; see the docstring.
CLAMPS = {
    "bot/BOT_RAIL_CLAMP_X_DRIVE": (-1, -1),
    "bot/BOT_RAIL_CLAMP_Y_AXIS_1": (-1, 1),
    "bot/BOT_RAIL_CLAMP_Y_AXIS": ((1, -1), (1, 1)),
}

# Which of the alpha plate's four bearing clusters takes the driven mount, and
# which corner cluster takes the long saddle.
DRIVEN_AT = (-1, -1)             # -X for the drive side, -Z for the span
LONG_SADDLE_AT = 1               # the +Z end, with the handwheel beyond it

# A turn of a half turn about the diagonal: it sends local +X to +Z, +Y to -Y
# and +Z to +X, which is how a part drawn bore-along-X and bolted-face-up goes
# in when the machine wants the bore along Z and the face down.
DIAGONAL = Rotation(Vector(1, 0, 1), 180.0)
ANTI_DIAGONAL = Rotation(Vector(1, 0, -1), 180.0)


def small_holes(body, max_r=2.0):
    """Every small hole in a part, as (x, z) in its own coordinates."""
    points = set()
    for face in body.Shape.Faces:
        surface = face.Surface
        if surface.TypeId != "Part::GeomCylinder" or surface.Radius > max_r:
            continue
        points.add((round(surface.Center.x, 3), round(surface.Center.z, 3)))
    return sorted(points)


def rectangles(points, across, along, tol=0.05):
    """Every four holes making a rectangle of exactly this size, by centre.

    Asking for the *pattern* rather than grouping by distance is what makes
    this work on `ALPHA_BOT_PLATE`: two of its six clusters sit only 16 mm
    apart, which is closer than either one's own diagonal, so nothing that
    groups by proximity can tell them apart.  Their bolt rectangles are quite
    different, and each part knows its own.
    """
    def there(x, z):
        return any(abs(px - x) < tol and abs(pz - z) < tol for px, pz in points)

    found = []
    for x, z in points:
        if there(x + across, z) and there(x, z + along) \
                and there(x + across, z + along):
            found.append((x + across / 2.0, z + along / 2.0))
    return sorted(found)


def placed_box(link):
    """A link's bounding box in machine coordinates, not its own.

    An `App::Link` shares its shape with every other link to the same part, so
    the shape's own box is where the part was *drawn*.  Anything that has to
    sit against a face -- a handwheel against the boss it turns in -- needs the
    box after the placement.
    """
    shape = link.LinkedObject.Shape.copy()
    shape.Placement = link.Placement.multiply(shape.Placement)
    return shape.BoundBox


def rail_y(mounts):
    """The Y rails' axis, as the carriage's own mounts put it."""
    return asmprim.frame(mounts[0], "TROUGH").Base.y


def alpha_seat(body=None):
    """Y of the alpha plate's underside.

    The four LM8UU holders hang from it and ride the Y rails, so the plate sits
    exactly a holder's flange above the rail.  This replaces the guess
    `machine.py` used to make - resting the plate straight on the bearings -
    which was 4.1 mm low and was flagged as the softest number in the machine.
    """
    body = body or asmprim.part("bot/BOT_BEARING_MOUNT_Y_AXIS")
    return asmprim.datum(body, "PLATE").Placement.Base.y


def lm8uu_mounts(doc, asm, at_y, plate):
    """The four LM8UU holders under the alpha plate, and their bearings.

    Read off the plate rather than placed by hand: its M3 come in six clusters,
    four of them the 18 x 29 rectangle these mounts bolt on.  Those four land
    over the two Y rails, which is the check as well as the placement.
    """
    plain = asmprim.part("bot/BOT_BEARING_MOUNT_Y_AXIS")
    driven = asmprim.part("bot/BOT_BEARING_MOUNT_Y_AXIS_DRIVEN")
    found = rectangles(small_holes(plate), 29.0, 18.0)
    if len(found) != 4:
        raise SystemExit(f"the fixed plate has {len(found)} bearing clusters, "
                         f"not 4")

    made = []
    for cx, cz in found:
        driving = (cx < 0) == (DRIVEN_AT[0] < 0) and \
                  (cz < 0) == (DRIVEN_AT[1] < 0)
        body = driven if driving else plain
        # Local +X is the seat's axis and has to run along the rail.  Which
        # quarter turn decides which way the driven arm reaches, and it has to
        # reach the same way the clamp's tube does -- inboard.
        link = asmprim.link(
            asm, f"{body.Label} {cx:+.0f},{cz:+.0f}", body,
            Placement(Vector(cx, at_y, cz), Rotation(Vector(0, 1, 0), -90.0)))
        made.append(link)

        sleeve = stock.linear_bearing(doc, f"LM8UU Y {cx:+.0f},{cz:+.0f}")
        sleeve.Placement = Placement(
            Vector(cx, asmprim.frame(link, "BEARING").Base.y, cz - 12.0),
            Rotation())
        made.append(sleeve)
    doc.recompute()
    for link in made:
        asmprim.ground(asm, link)
    return [m for m in made if m.TypeId == "App::Link"]


def worm_drive(doc, asm, plate_top, plate):
    """The worm, its shaft, the two saddles that carry it and the handwheel.

    The saddles go on the plate's other two clusters -- the 20.3 x 12 pattern,
    the ones that exist on one side only -- and everything else follows from
    them.
    """
    long_body = asmprim.part("bot/BOT_ROD_HOLDER_ALPHA_AXIS")
    short_body = asmprim.part("bot/BOT_ROD_HOLDER_ALPHA_AXIS_SHORT")
    found = rectangles(small_holes(plate), 20.3, 12.0)
    if len(found) != 2:
        raise SystemExit(f"the fixed plate has {len(found)} saddle clusters, "
                         f"not 2")

    # The saddle is drawn with its bolted plate over the barrel; in the machine
    # that plate is underneath, so it goes in turned over, and the barrel then
    # runs inboard from whichever end of the plate it is bolted to.
    stand = asmprim.datum(long_body, "MOUNT").Placement.Base.y
    axis_y = plate_top + stand
    # The saddle's own head is 20 mm long with its bolts 4 mm in from each end,
    # so its outboard face is 10 mm beyond the cluster's centre.
    head = asmprim.part("bot/BOT_ROD_HOLDER_ALPHA_AXIS_SHORT")
    reach = head.Shape.BoundBox.XLength / 2.0
    made = []
    for cx, cz in found:
        body = long_body if (cz > 0) == (LONG_SADDLE_AT > 0) else short_body
        made.append(asmprim.link(
            asm, f"{body.Label} {cz:+.0f}", body,
            Placement(Vector(cx, axis_y, cz + math.copysign(reach, cz)),
                      ANTI_DIAGONAL if cz > 0 else DIAGONAL)))
    shaft_x = sum(c[0] for c in found) / 2.0

    # The shaft runs its full 270 and its plain end stops just past the short
    # saddle, so the handwheel lands where that leaves it -- well outboard of
    # the plate, which is where the manual's STEP_4_1 render has it.
    tail = -(max(abs(c[1]) for c in found) + reach + 10.0)
    # The other two wheels bear against something and the screw is cut to suit;
    # this one has only the end of a 270 shaft to sit on, so it is pushed on
    # until the shaft bottoms in its blind bore and its mouth is a bore's depth
    # short of the end.
    wheel_at = tail + SCREW_LENGTH - wheel_bore()
    shaft = stock.threaded_rod(doc, "M5x270 worm shaft", SCREW_D, SCREW_LENGTH)
    # Stock is drawn along its own +Z, which is already the way this one runs.
    shaft.Placement = Placement(Vector(shaft_x, axis_y, tail), Rotation())
    made.append(shaft)

    worm = asmprim.part("sr/SR_WORM_GEAR")
    # Drawn turning about +Y, so it lies down onto the shaft, and its own
    # `SHAFT` datum -- the middle of its thread -- goes on the ring's centre
    # plane at Z = 0, which is where it has to mesh.
    lie = Rotation(Vector(1, 0, 0), 90.0)
    middle = asmprim.datum(worm, "SHAFT").Placement.Base
    made.append(asmprim.link(
        asm, "SR_WORM_GEAR", worm,
        Placement(Vector(shaft_x, axis_y, 0.0) - lie.multVec(middle), lie)))
    made.append(handwheel(doc, asm, "worm",
                          Vector(shaft_x, axis_y, wheel_at), "-Z"))

    doc.recompute()
    for link in made:
        asmprim.ground(asm, link)
    return made, shaft_x, axis_y


TOWARDS = {"+X": Vector(1, 0, 0), "-X": Vector(-1, 0, 0),
           "+Z": Vector(0, 0, 1), "-Z": Vector(0, 0, -1)}


def wheel_bore():
    """How far a handwheel's bore reaches back from its open face.

    The bore is **blind**: it runs from the boss face in to the `SHAFT` datum
    and is open at that one end only, so this is also how much screw the wheel
    can swallow, and the length that has to be left for it.
    """
    body = asmprim.part("bot/BOT_HANDWHEEL")
    return (body.Shape.BoundBox.YLength
            - asmprim.datum(body, "SHAFT").Placement.Base.y)


def handwheel(doc, asm, what, at, towards):
    """One `BOT_HANDWHEEL`, its bore over the end of a screw.

    `at` is the face the wheel bears against and `towards` which way the screw
    runs away from it, so the wheel is always placed against whatever it turns
    against rather than at a coordinate.

    **Which way round matters, and only one way round can be assembled.**  The
    bore is blind, open at the boss end alone, so the boss has to face the
    screw: put the wheel on the other way and the screw arrives at 5 mm of
    solid plastic behind the bore's floor, the wheel sits on the end of it
    rather than over it, and it cannot go on at all.  Local +Y is the bore's
    axis running from floor to mouth, so it points along `towards`, and the
    body is set back from `at` by its own length -- which leaves the wheel in
    exactly the same place as before, turned round.
    """
    body = asmprim.part("bot/BOT_HANDWHEEL")
    axis = TOWARDS[towards]
    turn = Rotation(Vector(0, 1, 0), axis)
    length = body.Shape.BoundBox.YLength
    return asmprim.link(asm, f"BOT_HANDWHEEL {what}", body,
                        Placement(at - axis * length, turn))


def rail_clamps(doc, asm, mounts):
    """Step 7's four clamps, one on each of the carriage's four troughs.

    Each closes over a Y rail and pulls down into the trough it sits in, so
    every one of them is placed by the trough's own datum.
    """
    made = {}
    for name, where in CLAMPS.items():
        body = asmprim.part(name)
        for sx, sz in (where if isinstance(where[0], tuple) else (where,)):
            mount = trough(mounts, sx, sz)
            seat = asmprim.frame(mount, "TROUGH").Base
            # Local +X is the groove and has to lie along the rail.  Which way
            # round decides which side the arm reaches, and for the two parts
            # with an arm that is forced by what the arm has to reach.
            turn = -90.0
            made[(name, sx, sz)] = asmprim.link(
                asm, f"{body.Label} {sx:+.0f}{sz:+.0f}", body,
                Placement(Vector(seat.x, seat.y, seat.z),
                          Rotation(Vector(0, 1, 0), turn)))
    doc.recompute()
    for link in made.values():
        asmprim.ground(asm, link)
    return made


def trough(mounts, sx, sz):
    """The carriage mount on one corner, by the sign of where it sits."""
    for mount in mounts:
        at = asmprim.frame(mount, "TROUGH").Base
        if (at.x < 0) == (sx < 0) and (at.z < 0) == (sz < 0):
            return mount
    raise SystemExit(f"no carriage mount at {sx:+.0f}{sz:+.0f}")


def sprung_nuts(doc, asm, label, at, towards):
    """Two M5 nuts and the spring between them, inside an arm's own hollows.

    The pair is what makes the drive backlash free; see the docstring.
    """
    axis = Vector(*towards)
    turn = Rotation(Vector(0, 0, 1), axis)
    # Both nuts go inside the hollow rather than on its boundaries: a nut is
    # drawn from its own face along +Z, so the far one starts a nut back from
    # the far rib.
    ends = (NUT_AT[0], NUT_AT[1] - NUT_THICK)
    made = []
    for i, along in enumerate(ends):
        one = fasteners.nut(doc, "M5")
        one.Label = f"M5 nut {label} {i + 1}"
        one.Placement = Placement(at + axis * along, turn)
        made.append(one)
    coil = stock.spring(doc, f"spring {label}", SPRING_D, SPRING_WIRE,
                        ends[1] - ends[0] - NUT_THICK)
    coil.Placement = Placement(at + axis * (ends[0] + NUT_THICK), turn)
    made.append(coil)
    doc.recompute()
    for solid in made:
        asmprim.ground(asm, solid)
    return made


def x_screw(doc, asm, bracket, clamp):
    """The X screw: frame to carriage, handwheel outboard of the bracket.

    Its axis comes from the bracket and its nuts from the clamp, and those two
    were reconstructed from different meshes months apart -- so the first thing
    this does is ask whether they agree.
    """
    on_bracket = asmprim.frame(bracket, "SCREW")
    on_clamp = asmprim.frame(clamp, "SCREW")
    check_axes("the X screw", on_bracket, on_clamp, along="x")

    # The wheel goes against the bracket's outboard face and the screw runs its
    # full length inboard from the wheel's own bore floor.
    wheel_x = placed_box(bracket).XMin
    wheel = handwheel(doc, asm, "X", Vector(wheel_x, on_bracket.Base.y,
                                            on_bracket.Base.z), "+X")
    end = asmprim.frame(wheel, "SHAFT").Base.x

    rod = stock.threaded_rod(doc, "M5x270 X screw", SCREW_D, SCREW_LENGTH)
    rod.Placement = Placement(Vector(end, on_bracket.Base.y, on_bracket.Base.z),
                              Rotation(Vector(0, 1, 0), 90.0))
    asmprim.ground(asm, wheel)
    asmprim.ground(asm, rod)
    nuts = sprung_nuts(doc, asm, "X", on_clamp.Base, (0.0, 0.0, 1.0))
    doc.recompute()
    say(f"  the X screw runs x {end:.1f} .. {end + SCREW_LENGTH:.1f} "
        f"at y {on_bracket.Base.y:.1f}, z {on_bracket.Base.z:.1f}")
    return [wheel, rod] + nuts


def y_screw(doc, asm, driven, clamp):
    """The Y screw: carriage to alpha plate, handwheel outboard of the tube."""
    on_clamp = asmprim.frame(clamp, "SCREW")
    on_mount = asmprim.frame(driven, "SCREW")
    check_axes("the Y screw", on_clamp, on_mount, along="z")

    wheel_z = placed_box(clamp).ZMax
    wheel = handwheel(doc, asm, "Y", Vector(on_clamp.Base.x, on_clamp.Base.y,
                                            wheel_z), "-Z")
    end = asmprim.frame(wheel, "SHAFT").Base.z

    rod = stock.threaded_rod(doc, "M5x270 Y screw", SCREW_D, SCREW_LENGTH)
    rod.Placement = Placement(
        Vector(on_clamp.Base.x, on_clamp.Base.y, end - SCREW_LENGTH),
        Rotation())
    asmprim.ground(asm, wheel)
    asmprim.ground(asm, rod)
    nuts = sprung_nuts(doc, asm, "Y", on_mount.Base, (0.0, 0.0, 1.0))
    doc.recompute()
    say(f"  the Y screw runs z {end - SCREW_LENGTH:.1f} .. {end:.1f} "
        f"at x {on_clamp.Base.x:.1f}, y {on_clamp.Base.y:.1f}")
    return [wheel, rod] + nuts


def check_axes(what, a, b, along):
    """Two parts that carry the same screw have to put it in the same place."""
    across = [c for c in "xyz" if c != along]
    off = [abs(getattr(a.Base, c) - getattr(b.Base, c)) for c in across]
    say(f"  {what}: {', '.join(f'{c} {getattr(a.Base, c):+8.3f} against '
                               f'{getattr(b.Base, c):+8.3f}'
                               for c in across)}")
    if max(off) > 0.5:
        raise SystemExit(f"{what}'s two ends are {max(off):.2f} mm apart")
    say(f"  ok: the two parts agree on it to {max(off):.3f} mm")
    return max(off)


def check_mesh(shaft_x, axis_y, ring):
    """Does the worm actually mesh with the ring, and at the right distance?"""
    centre = abs(shaft_x)
    want = alpha.PITCH_R + 0.25 * (10.0 + 7.0)     # ring pitch + worm pitch
    say(f"  the saddles put the worm {centre:.2f} mm from the alpha axis; "
        f"two meshing pitch circles want {want:.2f}")
    if abs(centre - want) > 0.2:
        raise SystemExit(f"the worm is {centre - want:+.2f} mm out of mesh")

    box = ring.LinkedObject.Shape.copy()
    box.Placement = ring.Placement.multiply(box.Placement)
    band = box.BoundBox
    say(f"  the ring's teeth stand y {band.YMin:.1f} .. {band.YMax:.1f}, "
        f"the worm's thread y {axis_y - 5.0:.1f} .. {axis_y + 5.0:.1f}")
    if axis_y - 5.0 < band.YMin - TOL or axis_y + 5.0 > band.YMax + TOL:
        raise SystemExit("the worm does not lie inside the ring's tooth band")
    middle = 0.5 * (band.YMin + band.YMax)
    say(f"  ok: in mesh, {abs(axis_y - middle):.1f} mm off the teeth's own "
        f"mid height")


def check_travel(mounts, clamps):
    """How far the carriage and the alpha plate can actually go.

    Both axes are shorter than their rails, because what stops them is the
    clamp at one end and the bearing at the other rather than the rail's end.
    """
    rails = carriage.Y_RAIL_LENGTH
    say(f"  the Y rails are {rails:.0f} long, clamped at "
        f"z {carriage.RAIL_Z[0]:+.0f} and {carriage.RAIL_Z[1]:+.0f}")
    return rails


def build():
    doc, asm = asmprim.assembly("Drive")

    say("=== the frame and the XY carriage, as stages 1 and 3 leave them")
    members = frame.bottom_frame(doc, asm)
    frame.step1(doc, asm)
    frame.stands(doc, asm, members)
    holders = carriage.rail_holders(doc, asm)
    rods = carriage.rails(doc, asm)
    carriage.bearings(doc, asm, rods)
    mounts = carriage.bearing_mounts(doc, asm)
    carriage.print_plate(doc, asm, mounts)
    carriage.y_rails(doc, asm, mounts)

    say("=== step 7: the four clamps that hold the Y rails down")
    clamps = rail_clamps(doc, asm, mounts)
    say(f"  {len(clamps)} clamps, one on each trough")

    say("=== step 3: the alpha plate on its four LM8UU")
    seat = rail_y(mounts) + alpha_seat()
    say(f"  the plate's underside lands at y {seat:.1f}, which is the rail "
        f"plus a holder's flange")
    stack = alpha.place(doc, asm, seat)
    plate = asmprim.part("plate/ALPHA_BOT_PLATE")
    holders_y = lm8uu_mounts(doc, asm, rail_y(mounts), plate)
    say(f"  {len(holders_y)} LM8UU holders, on the plate's own clusters")

    say("=== step 3: the worm, its shaft and its handwheel")
    _, shaft_x, axis_y = worm_drive(doc, asm, alpha.plate_top(seat), plate)
    check_mesh(shaft_x, axis_y, stack["SR_OUTER_RING_W_GEAR"])

    say("=== steps 8 and 9: the X screw")
    bracket = [o for o in asm.Group
               if o.Label == "BOT_BRACKET_X_AXIS"][0]
    x_screw(doc, asm, bracket,
            clamps[("bot/BOT_RAIL_CLAMP_X_DRIVE", -1, -1)])

    say("=== steps 5 and 9: the Y screw")
    driven = [h for h in holders_y if "DRIVEN" in h.Label][0]
    y_screw(doc, asm, driven,
            clamps[("bot/BOT_RAIL_CLAMP_Y_AXIS_1", -1, 1)])

    asmprim.solve(asm, context="the drives")
    asmprim.save(doc)
    say("\nSTAGES 3 AND 4 COMPLETE -- three screws, and the worm in mesh")


if asmprim.is_entry(__file__):
    build()
