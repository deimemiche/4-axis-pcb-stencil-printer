"""Stage 4 - the alpha axis: the slewing ring between its two plates.

Manual step 4, "Alpha Axis Bearing": the 240 x 200 upper plate, 9 x M3x14,
4 bearings 14 x 7 x 5, `SR_BEARING_PLATE`, `SR_WORM_GEAR`, `SR_INNER_RING`,
`SR_OUTER_RING_W_GEAR` and 4 `ADAPTER_D5_TO_M3`.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/alpha.py

## The SR group is used upside down

This was the one thing stage 4 had to settle, and the parts settle it
themselves.  In the meshes' own coordinates `SR_BEARING_PLATE` sits *above* the
rings - Y 8 .. 11 against the rings' -2 .. 10 - which would drive it straight
through the rotating plate.  Turned over, everything lands at once:

| flipped | Y | |
|---|---|---|
| `SR_BEARING_PLATE` | -11 .. -8 | bolted flat to the fixed plate |
| `SR_INNER_RING` | -8 .. 2 | **seats on it exactly**, 0.0 mm gap |
| `SR_OUTER_RING_W_GEAR` | -10 .. 2 | **clears the fixed plate by 1 mm** |
| `ALPHA_TOP_PLATE` | 2 .. 8 | bolted to the outer ring |

Two things make that more than a coincidence of bounding boxes.

* **The rotating ring clears the fixed plate by exactly 1 mm** while the fixed
  ring seats on the bearing plate with exactly none.  A part that turns must
  not rub and a part that does not turn should be supported: the two rings
  differ by precisely the millimetre that arrangement needs, and only in this
  orientation.
* **Both screw lengths come out right.**  Step 3's **M3x8** goes through the
  3 mm bearing plate and 5 mm into the 6 mm fixed plate; step 4's **M3x14**
  goes through the 6 mm top plate and 8 mm into the 12 mm outer ring.  Neither
  works the other way up.

So the fixed side is bottom plate, bearing plate, inner ring; the turning side
is outer ring and top plate; and the worm drives the outer ring's teeth.

## What the interfaces already proved

Both bolted interfaces cross the boundary between work done by completely
different routes - the plates transcribed from the author's 2D drawings, the
rings reconstructed from his STLs - and both are exact: 4 x M3 on r = 61 and
5 x M3 on r = 75.45, same radius, same count, same spacing.

## The alpha axis does not go all the way round

`SR_OUTER_RING_W_GEAR` carries **29 teeth at 2.25 degrees**, and only over a
72 degree sector of the rim; the rest is plain.  It is not a gear that turns
continuously, it is a sector that rocks, and the travel is about **+-32.6
degrees** - which is what a stencil wants.  360 / 2.25 = **160** teeth for a
complete rim, so a single start worm gives 160:1 at the handwheel.

## Still to place

The worm itself and its M5 drive shaft, which belong with the lead screws and
handwheels of manual steps 7 to 9.  `ALPHA_BOT_PLATE` has the 10 mm hole for it
at r = 75.45, so the mesh radius is already known.
"""

import math
import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
from asmprim import say  # noqa: E402

TOL = 1e-6

# From the parts' own scripts, so a rebuild that moved them would show here.
RING_TEETH = 29
TOOTH_PITCH = 2.25               # degrees
TOOTH_SECTOR = (234.0, 306.0)
TIP_R = 79.9506                  # from sr-outer-ring-w-gear.py
ROOT_R = 78.5083
RING_R = 75.45                   # the plain ring's own outside radius
PITCH_R = 0.5 * (TIP_R + ROOT_R)  # where the worm's own pitch circle meets it
RIM_R = 0.5 * (RING_R + ROOT_R)  # between the two: solid across the sector

PLATE_THICKNESS = 6.0
BEARING_PLATE_SCREW = 8.0        # M3x8, step 3
TOP_PLATE_SCREW = 14.0           # M3x14, step 4

# The SR meshes are exported upside down; see the docstring.
SR_FLIP = Rotation(Vector(1, 0, 0), 180.0)

# How far the toothed ring is turned before it is bolted down.  Its five bosses
# have to land on ALPHA_TOP_PLATE's five holes, which leaves five clockings 72
# degrees apart, and only one of those points the teeth at the worm; see
# `check_clocking`.
RING_CLOCK = 270.0
TEETH_TOWARDS = 180.0            # -X, where the worm's saddles are
RING_TURN = Rotation(Vector(0, 1, 0), RING_CLOCK).multiply(SR_FLIP)


def flipped(body):
    """Where a SR part's own bounding box lands once it is turned over."""
    bb = body.Shape.BoundBox
    return (-bb.YMax, -bb.YMin)


def stack(doc, asm):
    """The five layers, fixed side and turning side."""
    names = ("sr/SR_BEARING_PLATE", "sr/SR_INNER_RING",
             "sr/SR_OUTER_RING_W_GEAR")
    made = {}
    for name in names:
        body = asmprim.part(name)
        # Only the toothed ring cares which way round it goes: the other two
        # are turned parts, and the bearing plate's four pads are 90 degrees
        # apart, so the flip alone leaves them right.
        turn = RING_TURN if name.endswith("OUTER_RING_W_GEAR") else SR_FLIP
        link = asmprim.link(asm, os.path.basename(name), body,
                            Placement(Vector(), turn))
        made[os.path.basename(name)] = link

    low = min(flipped(asmprim.part(n))[0] for n in names)
    high = max(flipped(asmprim.part(n))[1] for n in names)

    # The fixed plate's top face meets the bearing plate's underside.
    bot = asmprim.part("plate/ALPHA_BOT_PLATE")
    made["ALPHA_BOT_PLATE"] = asmprim.link(
        asm, "ALPHA_BOT_PLATE", bot,
        Placement(Vector(0, low - PLATE_THICKNESS, 0), Rotation()))

    # The turning plate sits on the outer ring's top face.
    top = asmprim.part("plate/ALPHA_TOP_PLATE")
    made["ALPHA_TOP_PLATE"] = asmprim.link(
        asm, "ALPHA_TOP_PLATE", top, Placement(Vector(0, high, 0), Rotation()))

    doc.recompute()
    for link in made.values():
        asmprim.ground(asm, link)
    return made, low, high


# What turns with the alpha axis, and what stays still.
TURNING = ("SR_OUTER_RING_W_GEAR", "ALPHA_TOP_PLATE")


def place(doc, asm, at_y, turn=0.0):
    """The whole stack, with the fixed plate's **underside** at `at_y`.

    `turn` is the alpha pose in degrees; only the outer ring and the top plate
    take it, which is the whole point of the slewing ring.
    """
    made, low, high = stack(doc, asm)
    lift = at_y - (low - PLATE_THICKNESS)
    spin = Rotation(Vector(0, 1, 0), turn)
    for name, link in made.items():
        link.Placement = Placement(
            Vector(0, lift, 0),
            spin if name in TURNING else Rotation()).multiply(link.Placement)
    doc.recompute()
    return made


def plate_top(at_y):
    """The fixed plate's top face, which is what the worm's saddles sit on."""
    return at_y + PLATE_THICKNESS


def placed_holes(link, max_r=3.0):
    """Small round holes in a *placed* part, as (radius, angle) about Y.

    `holes` reads a body in its own coordinates; this reads a link in the
    machine's, which is what a clocking check needs.
    """
    found = {}
    for face in link.LinkedObject.Shape.Faces:
        surface = face.Surface
        if surface.TypeId != "Part::GeomCylinder" or surface.Radius > max_r:
            continue
        centre = link.Placement.multVec(surface.Center)
        found[(round(centre.x, 3), round(centre.z, 3))] = surface.Radius
    return [(math.hypot(x, z), math.degrees(math.atan2(z, x)) % 360.0)
            for x, z in found]


def check_clocking(ring, top):
    """Which of the five ways round the toothed ring goes on.

    Its bosses are 72 degrees apart and so are the plate's holes, so five
    clockings bolt up.  Only one of them points the toothed sector at the worm,
    and that is what settles it -- the ring's own teeth and the fixed plate's
    saddle holes have to agree, and they were drawn from a mesh and a 2D
    drawing respectively.
    """
    on_ring = sorted(a for r, a in placed_holes(ring) if abs(r - 75.45) < 0.5)
    on_plate = sorted(a for r, a in placed_holes(top) if abs(r - 75.45) < 0.5)
    say(f"  ring bosses at  {', '.join(f'{a:6.1f}' for a in on_ring)}")
    say(f"  plate holes at  {', '.join(f'{a:6.1f}' for a in on_plate)}")
    if len(on_ring) != 5 or len(on_plate) != 5:
        raise SystemExit("the ring and the plate do not have five holes each")
    worst = max(abs(a - b) for a, b in zip(on_ring, on_plate))
    if worst > 0.01:
        raise SystemExit(f"the ring's bosses miss the plate's holes by "
                         f"{worst:.2f} degrees")
    say(f"  ok: bolted up, worst hole out by {worst:.3f} degrees")

    # Which way the teeth point, asked of the solid rather than of a bounding
    # box: a box cannot tell a tooth from a boss, and the bosses stand 80.7 mm
    # out against the teeth's 79.95.  So probe the pitch circle instead --
    # there is material there only where there are teeth.
    shape = ring.LinkedObject.Shape.copy()
    shape.Placement = ring.Placement.multiply(shape.Placement)
    middle = 0.5 * (shape.BoundBox.YMin + shape.BoundBox.YMax)
    # Probe the **rim** the teeth stand on rather than the teeth themselves:
    # at the pitch circle a gear is half air, so a comb of teeth gives no run
    # at all, whereas the rim under them is solid right across the sector.
    solid = [a for a in range(360)
             if shape.isInside(Vector(RIM_R * math.cos(math.radians(a)),
                                      middle,
                                      RIM_R * math.sin(math.radians(a))),
                               1e-6, True)]
    # The five bosses reach past this radius too, so take the longest run of
    # material rather than any material at all.
    runs, run = [], []
    for a in solid + [s + 360 for s in solid]:
        if run and a != run[-1] + 1:
            runs.append(run)
            run = []
        run.append(a)
    runs.append(run)
    sector = max(runs, key=len)
    centre = (0.5 * (sector[0] + sector[-1])) % 360.0
    say(f"  the longest run of material at r = {RIM_R:.2f} is "
        f"{len(sector)} degrees wide, centred on {centre:.0f}")
    if abs(centre - TEETH_TOWARDS) > 1.0:
        raise SystemExit(f"the teeth face {centre:.0f} degrees, not the worm "
                         f"at {TEETH_TOWARDS:.0f}")
    say(f"  ok: the teeth face {TEETH_TOWARDS:.0f} degrees, which is where "
        f"the worm's saddles are")


def check_stack(low):
    """The seating and the clearance, which is what fixes the orientation."""
    bearing = flipped(asmprim.part("sr/SR_BEARING_PLATE"))
    inner = flipped(asmprim.part("sr/SR_INNER_RING"))
    outer = flipped(asmprim.part("sr/SR_OUTER_RING_W_GEAR"))
    say(f"  bearing plate {bearing[0]:6.1f} .. {bearing[1]:6.1f}   (fixed)")
    say(f"  inner ring    {inner[0]:6.1f} .. {inner[1]:6.1f}   (fixed)")
    say(f"  outer ring    {outer[0]:6.1f} .. {outer[1]:6.1f}   (turns)")

    seat = inner[0] - bearing[1]
    clear = outer[0] - low
    say(f"  the fixed ring seats on the bearing plate with a {seat:.1f} mm gap")
    say(f"  the turning ring clears the fixed plate by {clear:.1f} mm")
    if abs(seat) > TOL:
        raise SystemExit("the fixed ring does not seat on the bearing plate")
    if clear <= TOL:
        raise SystemExit("the turning ring would rub on the fixed plate")
    say("  ok: what does not turn is supported, what turns is clear")


def check_screws():
    """Both screw lengths have to reach, and neither does the other way up."""
    bearing = flipped(asmprim.part("sr/SR_BEARING_PLATE"))
    outer = flipped(asmprim.part("sr/SR_OUTER_RING_W_GEAR"))
    plate = bearing[1] - bearing[0]
    ring = outer[1] - outer[0]

    into_plate = BEARING_PLATE_SCREW - plate
    into_ring = TOP_PLATE_SCREW - PLATE_THICKNESS
    say(f"  M3x{BEARING_PLATE_SCREW:.0f} through the {plate:.0f} mm bearing "
        f"plate bites {into_plate:.0f} mm into the {PLATE_THICKNESS:.0f} mm "
        f"fixed plate")
    say(f"  M3x{TOP_PLATE_SCREW:.0f} through the {PLATE_THICKNESS:.0f} mm top "
        f"plate bites {into_ring:.0f} mm into the {ring:.0f} mm outer ring")
    ok = 0 < into_plate <= PLATE_THICKNESS and 0 < into_ring <= ring
    if not ok:
        raise SystemExit("the manual's screw lengths do not fit this stack")
    say("  ok: both of the manual's screw lengths land inside their part")


def holes(body, max_r=3.0):
    """Every small round hole's centre, as (radius from the axis, angle)."""
    found = {}
    for face in body.Shape.Faces:
        surface = face.Surface
        if surface.TypeId != "Part::GeomCylinder" or surface.Radius > max_r:
            continue
        centre = surface.Center
        found[(round(centre.x, 3), round(centre.z, 3))] = surface.Radius
    return [(math.hypot(x, z), math.degrees(math.atan2(z, x)) % 360.0)
            for x, z in found]


def check_circle(name, a_body, b_body, count, radius):
    """Two parts' bolt circles have to be the same circle."""
    a = [h for h in holes(a_body) if abs(h[0] - radius) < 0.5]
    b = [h for h in holes(b_body) if abs(h[0] - radius) < 0.5]
    say(f"  {name}")
    ok = len(a) == count and len(b) == count
    if not ok:
        say(f"    FAIL expected {count} holes on each, got "
            f"{len(a)} and {len(b)}")
    for holes_here, body in ((a, a_body), (b, b_body)):
        for r, _ in holes_here:
            if abs(r - radius) > 0.01:
                say(f"    FAIL {body.Label} has a hole at r = {r:.3f}")
                ok = False
        angles = sorted(h[1] for h in holes_here)
        gaps = {round((angles[(i + 1) % len(angles)] - angles[i]) % 360.0, 3)
                for i in range(len(angles))}
        if len(gaps) != 1:
            say(f"    FAIL {body.Label}'s holes are not evenly spaced")
            ok = False
        else:
            say(f"    {body.Label}: {len(holes_here)} at r = {radius}, "
                f"{gaps.pop():.0f} deg apart")
    if not ok:
        raise SystemExit(f"{name} does not line up")
    say("    ok: same radius, same count, same spacing")


def check_gear():
    span = RING_TEETH * TOOTH_PITCH
    full = 360.0 / TOOTH_PITCH
    sector = TOOTH_SECTOR[1] - TOOTH_SECTOR[0]
    say(f"  {RING_TEETH} teeth at {TOOTH_PITCH} deg = {span:.2f} deg of teeth, "
        f"in a {sector:.0f} deg sector")
    say(f"  a complete rim would be {full:.0f} teeth, so a single start worm "
        f"gives {full:.0f}:1")
    say(f"  travel is about +-{span / 2:.1f} deg -- the alpha axis rocks, "
        f"it does not revolve")
    if abs(full - round(full)) > TOL or span > sector + TOL:
        raise SystemExit("the ring's teeth do not add up")
    say("  ok: the pitch divides the circle and the teeth fit their sector")


def build():
    doc, asm = asmprim.assembly("Alpha")

    say("=== the stack, with the SR group turned over")
    made, low, high = stack(doc, asm)
    check_stack(low)

    say("=== the manual's screw lengths, which is what fixes the orientation")
    check_screws()

    say("=== the two bolted interfaces")
    check_circle("fixed plate to bearing plate, 4 x M3 on 122",
                 asmprim.part("plate/ALPHA_BOT_PLATE"),
                 asmprim.part("sr/SR_BEARING_PLATE"), 4, 61.0)
    check_circle("turning plate to toothed ring, 5 x M3 on 150.9",
                 asmprim.part("plate/ALPHA_TOP_PLATE"),
                 asmprim.part("sr/SR_OUTER_RING_W_GEAR"), 5, 75.45)

    say("=== which way round the ring goes on")
    check_clocking(made["SR_OUTER_RING_W_GEAR"], made["ALPHA_TOP_PLATE"])

    say("=== the ring gear")
    check_gear()

    asmprim.solve(asm, context="the alpha stack")
    asmprim.save(doc)
    total = made["ALPHA_TOP_PLATE"].Shape.BoundBox
    say(f"  the whole axis stands {total.YMax - (low - PLATE_THICKNESS):.0f} mm "
        f"tall")
    say("\nSTAGE 4 PASSED -- the SR group goes in upside down, and every "
        "number\n   in the manual agrees once it does")


if asmprim.is_entry(__file__):
    build()
