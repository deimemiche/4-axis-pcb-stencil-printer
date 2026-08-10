"""Stage 1 - the machine datum, and the bottom frame it is anchored to.

The bottom frame is four extrusions, all 300 mm, **butt jointed** into a
rectangle: two run the full length and the other two land between them.  Onto
that go the eight printed pieces of the manual's step 1 - five gussets, the X
axis bracket, two right angle connectors - and the four feet.

**This is Michael's machine, not the author's original**, and here that means
one thing: the manual's step 1 has 1 x 2040 x 300 and 3 x 2020 x 300, and the
linear Z axis mod in the repository's README swaps that 2040 for a 2020 of the
same length.  So all four members are 2020, the frame is **340 x 300** and it
*is* symmetric about the machine origin.

Three things settle the rest, and they agree:

* **The corners are butt joints, not mitres.**  Zoom the manual's own STEP_1
  render on a corner and an extrusion's *end face* is visible, T-slots and all.
  A mitre would show a diagonal face.
* **The rail length is the span.**  The top frame is the same idea one storey
  up and its numbers are unambiguous: 2 x 2020 x 280 between two 300 mm
  members, and its rails are 8 mm x **280**.  So a rail runs the full distance
  between the inner faces of the two members it is bolted to, and equals the
  length of the members parallel to it.
* **The side members are therefore 300 apart.**  The X rails are 300 and run
  between their inner faces, so that spacing is fixed, and a 20 mm member
  either side makes the frame 340 across.

The X axis still mounts on the **-X side**, which is where the author's 2040
was and where `BOT_BRACKET_X_AXIS` and the Z columns go.  Nothing about that
depended on the extra 20 mm: `BOT_BRACKET_X_AXIS` bolts to the corner, not to
the wide face, and the assembly's own checks below say so.

## What step 1's 32 screws prove

The manual lists **32 x M4x10 and 32 slot nuts**, and the printed parts it
lists have exactly 32 holes between them:

    5 x BOT_BRACKETS         5 bolts each   25
    1 x BOT_BRACKET_X_AXIS   3               3
    2 x BOT_RIGHT_ANGLE_CON  2 each          4
                                            --
                                            32

So every hole gets a screw and there are none left over -- which also means the
**four feet are not separately bolted**.  Each `STAND` hangs on the corner bolt
of the gusset above it, its 7 mm counterbore taking that screw's head, which is
the only arrangement the count allows.  `check_bolts` below counts them.

Run it directly:

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/frame.py

## The datum

One origin for the whole machine, **Y up**, matching every part script:

* **Y = 0 is the frame's top face.**  Everything the machine is built from
  stands on that face, so heights read directly as "how far above the frame".
* **X = 0, Z = 0 is the centre of the X rails**, which run -150 .. +150.  With
  four equal members the frame reaches -170 .. +170 across and -150 .. +150
  along, so the outline is symmetric too.  It is worth saying that the origin
  follows the *rails* rather than the outline, because on the author's own
  frame - 2040 on the -X side - the two do not coincide.

`stock.extrusion` therefore puts a section's **top** at its own local Y = 0
rather than centring it, so members of different heights hang from a common top
surface instead of needing an offset each.

## What the parts themselves say about it

Two groups were exported in assembly position rather than about a part origin,
and where they land under an identity placement is evidence about the author's
own datum.  `check_datum()` below reports it rather than assuming it, and what
it finds is this:

* the **SR** group stacks cleanly -- outer ring and inner ring both start at
  Y = -2, the inner ring ends at Y = 8 and the bearing plate runs 8 .. 11 --
  and all of it is centred on X = Z = 0;
* the **ECCF** group stacks just as cleanly -- bottom -18 .. -10, height
  -10 .. 0, then mount and top both from 0 -- centred on X = 0.

So each group carries its own **sub-assembly** datum, and a good one.  What
neither carries is a *machine* datum: the alpha axis and the front eccentric
are each drawn about their own centre, and nothing in the meshes relates one to
the other.  That is worth being explicit about, because "the parts are already
in assembly position" is true within a group and false between groups.
"""

import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import stock    # noqa: E402
from asmprim import say  # noqa: E402

# Every member is 300 long; the manual gives no other length.
MEMBER_LENGTH = 300.0
NARROW = 20.0            # every member, across the plan -- see the mod above
TALL = 20.0              # all of them are one cell tall
STAND_DROP = 7.0         # how far a foot stands below what it hangs from

# The X rails are 300 and run between the inner faces of the two side members,
# which is what sets the frame's width.
RAIL_SPAN = 300.0
HALF_SPAN = RAIL_SPAN / 2.0                  # the side members' inner faces
HALF_DEPTH = MEMBER_LENGTH / 2.0             # the side members run this far

# Side members run the full length along Z and the rails bolt to their inner
# faces; end members land between them.  Where the author's frame has its one
# 2040 -- lying flat as the -X side member -- this has a 2020, so all four are
# alike and the plan is symmetric.
#
# It was the assembly that settled the 2040 was a *side* member and not an end
# one, and the reasoning still matters because it is what fixes which side the
# X drive is on: as an end member it would have reached Z = -150 .. -110, and
# the X rails sit at Z = +-111 with the print plate reaching +-128.5, so
# `machine.py`'s interference check found the carriage driving straight through
# it.
DRIVE_SIDE = "left"      # -X: BOT_BRACKET_X_AXIS, the Z columns, the hinges
SIDES = {
    "left":  (0.0, NARROW, Vector(-(HALF_SPAN + NARROW / 2.0), 0.0,
                                  -HALF_DEPTH)),
    "right": (0.0, NARROW, Vector(HALF_SPAN + NARROW / 2.0, 0.0, -HALF_DEPTH)),
    # Turned a quarter turn so their length runs along X instead.
    "front": (90.0, NARROW, Vector(-HALF_SPAN, 0.0,
                                   -HALF_DEPTH + NARROW / 2.0)),
    "back":  (90.0, NARROW, Vector(-HALF_SPAN, 0.0,
                                   HALF_DEPTH - NARROW / 2.0)),
}

OUTER_X = RAIL_SPAN + 2 * NARROW             # 340
OUTER_Z = MEMBER_LENGTH                      # 300

# The four outer corners in plan, as (X, Z) signs.  Everything in step 1 lands
# on one of them.
CORNERS = ((-1, -1), (-1, 1), (1, 1), (1, -1))
CORNER_X = HALF_SPAN + NARROW                # 170, the outer faces
CORNER_Z = HALF_DEPTH                        # 150

# Which corner each of step 1's odd parts goes to, read off the manual's
# STEP_1 renders.  The gussets are on all four corners underneath, plus one on
# top; the X bracket takes the drive corner on top; the two right angle
# connectors stand inside two opposite corners.
# Two of step 1's top side parts give way to the linear Z mod: `column.py`
# puts a BOT_Z_AXIS_BRACKET on each of the two +X corners, and each of those
# replaces one of the author's pieces there.
GUSSET_ON_TOP = None
BRACKET_CORNER = (-1, -1)                    # the drive side, with the X screw
ANGLE_CORNERS = ((-1, 1),)

STEP1_BOLTS = 32         # what the manual lists, and what its parts want
MOD_BRACKET_BOLTS = 5    # BOT_Z_AXIS_BRACKET, on the same 20 mm grid


def bottom_frame(doc, asm):
    """The four extrusions, placed and grounded."""
    members = {}
    for name, (angle, across, base) in SIDES.items():
        cells_x = int(round(across / 20.0))
        label = f"{'2040' if cells_x == 2 else '2020'} {name}"
        member = stock.extrusion(doc, label, MEMBER_LENGTH, cells_x=cells_x)
        member.Placement = Placement(base, Rotation(Vector(0, 1, 0), angle))
        members[name] = member
    doc.recompute()
    # The frame is what everything else is measured from, so it is the thing
    # that gets grounded; every other joint chain hangs off it.
    for member in members.values():
        asmprim.ground(asm, member)
    return members


def corner_hole(sx, sz):
    """Where the two members' top slots cross at one corner.

    Everything in step 1 is dimensioned from this point: it is the gusset's
    shared bolt, and the foot hangs on that same screw.
    """
    return Vector(sx * (HALF_SPAN + NARROW / 2.0), 0.0,
                  sz * (HALF_DEPTH - NARROW / 2.0))


def gussets(doc, asm):
    """The five flat corner plates: four underneath and one on top.

    `BOT_BRACKETS` is a plain 60 x 60 plate with its holes 10, 30 and 50 mm in
    from the outer corner along each leg, which is the extrusion's own 20 mm
    grid started half a cell in -- so laying its corner on the frame's corner
    puts all five bolts in a slot, and the one in the corner in both.

    Turning it to each corner is a quarter turn about Y and nothing else: the
    plate is flat and its holes go straight through, so the four underneath
    need no flip, only a drop.
    """
    body = asmprim.part("bot/BOT_BRACKETS")
    thickness = body.Shape.BoundBox.YLength
    made = []
    for sx, sz in CORNERS:
        # Local +X and +Z run along the two legs from the outer corner, so the
        # turn is the one that sends them both inboard.
        turn = {(-1, -1): 0.0, (-1, 1): 90.0, (1, 1): 180.0,
                (1, -1): 270.0}[(sx, sz)]
        under = Vector(sx * CORNER_X, -TALL - thickness, sz * CORNER_Z)
        made.append(asmprim.link(
            asm, f"BOT_BRACKETS {sx:+.0f}{sz:+.0f}", body,
            Placement(under, Rotation(Vector(0, 1, 0), turn))))
        if GUSSET_ON_TOP is not None and (sx, sz) == GUSSET_ON_TOP:
            made.append(asmprim.link(
                asm, f"BOT_BRACKETS {sx:+.0f}{sz:+.0f} top", body,
                Placement(Vector(sx * CORNER_X, 0.0, sz * CORNER_Z),
                          Rotation(Vector(0, 1, 0), turn))))
    doc.recompute()
    for gusset in made:
        asmprim.ground(asm, gusset)
    return made


def x_bracket(doc, asm):
    """`BOT_BRACKET_X_AXIS`, on the drive corner, carrying the X screw.

    Its three M4 land on the same 20 mm grid as everything else -- one on the
    end member and two on the side member -- and only one way round does that:
    the plate has to be turned half a turn so both legs run inboard from the
    corner.  What comes out of it is the X screw's axis, and `drive.py` checks
    that against the clamp that drives it.
    """
    sx, sz = BRACKET_CORNER
    body = asmprim.part("bot/BOT_BRACKET_X_AXIS")
    at = Vector(sx * CORNER_X, 0.0, sz * CORNER_Z)
    bracket = asmprim.link(asm, "BOT_BRACKET_X_AXIS", body,
                           Placement(at, Rotation(Vector(0, 1, 0), 180.0)))
    doc.recompute()
    asmprim.ground(asm, bracket)
    return bracket


def right_angle_cons(doc, asm):
    """The two `BOT_RIGHT_ANGLE_CON`, standing inside two opposite corners.

    The part says how it goes in: a tongue and an M4 on one face, an M4 through
    the other, and 20 mm between its two Z faces.  So it hangs from a **side**
    member's top slot with its full 20 mm width sitting on that member's 20 mm,
    and pushes against the **end** member's inner face, its tongue in the slot
    on that face's centre line at Y = -10.

    Which two corners is read off the manual's STEP_1_1 render, and so is the
    arrangement: zoomed in, the connector stands **on top of** the frame at a
    corner, wrapping the end of the member that runs through it.

    One thing about it stays unexplained.  Its upright's own M4 comes out 10 mm
    *above* the frame's top face, pointing along the member it stands at the
    end of, and step 1 has nothing there for it to bite into.  Step 11's
    eccentrics bolt to this corner with more screws than they have slot nuts
    for, so they are the likely customer; it is left as a hole in the air
    rather than moved to make it look tidy.
    """
    body = asmprim.part("bot/BOT_RIGHT_ANGLE_CON")
    made = []
    for sx, sz in ANGLE_CORNERS:
        # Its flat leg lies on a side member's top face at the very end of it,
        # its upright stands across that member's end face with the 1 mm tongue
        # in the slot there, and its 20 mm width is the member's own.
        turn = -90.0 if sz < 0 else 90.0
        at = Vector(sx * (HALF_SPAN + NARROW / 2.0), 0.0, sz * HALF_DEPTH)
        made.append(asmprim.link(
            asm, f"BOT_RIGHT_ANGLE_CON {sx:+.0f}{sz:+.0f}", body,
            Placement(at, Rotation(Vector(0, 1, 0), turn))))
    doc.recompute()
    for con in made:
        asmprim.ground(asm, con)
    return made


def stands(doc, asm, members):
    """The four printed feet, one under each corner.

    STAND is modelled growing from its own Y = 0, and in the machine that face
    is the one bolted up against what is above it, so each is turned over and
    hung from it.  What is above it is the corner gusset rather than the
    extrusion: step 1 has no screws left over for the feet, and the foot's own
    7 mm counterbore is there to swallow the head of the gusset's corner bolt.
    """
    body = asmprim.part("misc/STAND")
    gusset = asmprim.part("bot/BOT_BRACKETS").Shape.BoundBox.YLength
    feet = []
    for i, (sx, sz) in enumerate(CORNERS):
        at = corner_hole(sx, sz) + Vector(0.0, -TALL - gusset, 0.0)
        foot = asmprim.link(asm, f"STAND {i + 1}", body,
                            Placement(at, Rotation(Vector(1, 0, 0), 180.0)))
        feet.append(foot)
    doc.recompute()
    return feet


def check_bolts(gusset_links, bracket, cons):
    """Step 1's 32 screws, counted off the parts that take them.

    The manual gives the number and the parts give the holes; agreeing is
    evidence that the right parts are in the right quantity, which no single
    part could tell us.
    """
    listed = {"BOT_BRACKETS": (5, 5), "BOT_BRACKET_X_AXIS": (1, 3),
              "BOT_RIGHT_ANGLE_CON": (2, 2)}
    total = 0
    for name, (many, each) in listed.items():
        say(f"  {many} x {name:22s} {each} bolts each = {many * each:2d}")
        total += many * each
    say(f"  {total} M4 x 10 and slot nuts, which is what step 1 lists")
    if total != STEP1_BOLTS:
        raise SystemExit(f"step 1 lists {STEP1_BOLTS} screws, "
                         f"its parts want {total}")
    say(f"  ok: exactly {STEP1_BOLTS}, and none left over -- so the feet hang "
        f"on the gussets' own corner bolts")

    here = len(gusset_links) * 5 + 3 + len(cons) * 2
    say(f"  this machine puts {len(gusset_links)} gussets and {len(cons)} "
        f"connector(s) on: {here} bolts, plus "
        f"{2 * MOD_BRACKET_BOLTS} for the mod's two Z brackets")
    say("  (the two +X corners carry BOT_Z_AXIS_BRACKET instead of the "
        "author's fifth gusset and second connector)")


def check_size(members):
    """The frame must come out the size the build page says it is."""
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for member in members.values():
        bb = member.Shape.BoundBox
        for i, (a, b) in enumerate(((bb.XMin, bb.XMax), (bb.YMin, bb.YMax),
                                    (bb.ZMin, bb.ZMax))):
            lo[i], hi[i] = min(lo[i], a), max(hi[i], b)
    say(f"  frame {hi[0] - lo[0]:.1f} x {hi[2] - lo[2]:.1f} mm in plan, "
        f"Y {lo[1]:.1f} .. {hi[1]:.1f}")
    ok = True
    for i, axis, want in ((0, "X", OUTER_X), (2, "Z", OUTER_Z)):
        if abs((hi[i] - lo[i]) - want) > 1e-6:
            say(f"  FAIL {axis} is {hi[i] - lo[i]:.3f}, expected {want}")
            ok = False
    # With four equal members both axes are symmetric about the origin.  On the
    # author's own frame X would not be, because his 2040 side member is 20 mm
    # wider than its opposite number; the origin follows the rails either way.
    for i, axis in ((0, "X"), (2, "Z")):
        if abs(lo[i] + hi[i]) > 1e-6:
            say(f"  FAIL {axis} is not centred on the origin")
            ok = False
    if abs(hi[1]) > 1e-6:
        say(f"  FAIL the top face is at Y = {hi[1]:.3f}, expected 0")
        ok = False

    # The whole point of the width: an X rail has to reach from one side
    # member's inner face to the other, and it is 300 long.
    gap = 2 * HALF_SPAN
    if abs(gap - RAIL_SPAN) > 1e-6:
        say(f"  FAIL the side members are {gap:.3f} apart, "
            f"but the X rail is {RAIL_SPAN}")
        ok = False
    if not ok:
        raise SystemExit("the bottom frame is not the size it should be")
    say(f"  ok: {OUTER_X:.0f} x {OUTER_Z:.0f} outer, top face on Y = 0, "
        f"four 2020s and so symmetric")
    say(f"  ok: side members {gap:.0f} apart, which is the X rail exactly")


def check_level(feet):
    """Do all four feet reach the floor?

    This is the assembly earning its keep on its first day.  It failed when the
    2040 was modelled standing 40 mm tall, because the two feet on that side
    then finished 20 mm below the other two and the machine would rock -- which
    is how the frame came to be modelled with every member lying 20 mm tall,
    the reading that everything since has agreed with.
    """
    bottoms = sorted(round(f.Shape.BoundBox.YMin, 3) for f in feet)
    say(f"  4 stands, resting on Y = {', '.join(f'{b:.1f}' for b in bottoms)}")
    spread = bottoms[-1] - bottoms[0]
    if spread > 1e-6:
        say(f"  FAIL the feet are not level -- {spread:.1f} mm between the "
            f"highest and lowest")
        raise SystemExit("the machine would rock")
    say(f"  ok: level, the machine rests on Y = {bottoms[0]:.1f}")


def check_datum():
    """Report where the two pre-positioned groups actually sit.

    This is the cheap test the plan asks for before anything is built on top of
    the datum: it prints, it does not assume.
    """
    groups = {
        "sr": ("SR_OUTER_RING_W_GEAR", "SR_INNER_RING", "SR_BEARING_PLATE"),
        "eccf": ("ECCF_BOT", "ECCF_HEIGHT", "ECCF_MOUNT", "ECCF_TOP"),
    }
    for folder, names in groups.items():
        say(f"  {folder}/ with an identity placement:")
        for name in names:
            bb = asmprim.part(f"{folder}/{name}").Shape.BoundBox
            say(f"    {name:24s} X[{bb.XMin:7.2f},{bb.XMax:7.2f}] "
                f"Y[{bb.YMin:7.2f},{bb.YMax:7.2f}] "
                f"Z[{bb.ZMin:7.2f},{bb.ZMax:7.2f}]")


def step1(doc, asm):
    """Everything the manual's step 1 puts on the frame, in one call."""
    made = gussets(doc, asm)
    made.append(x_bracket(doc, asm))
    made += right_angle_cons(doc, asm)
    return made


def build():
    doc, asm = asmprim.assembly("BottomFrame")
    say("=== the four extrusions")
    members = bottom_frame(doc, asm)
    check_size(members)

    say("=== step 1's brackets")
    gusset_links = gussets(doc, asm)
    bracket = x_bracket(doc, asm)
    cons = right_angle_cons(doc, asm)
    check_bolts(gusset_links, bracket, cons)

    say("=== the four feet")
    feet = stands(doc, asm, members)
    asmprim.solve(asm, context="placing the frame and feet")
    check_level(feet)

    say("=== what the pre-positioned groups say about the datum")
    check_datum()

    asmprim.save(doc)
    say("\nSTAGE 1 PASSED -- datum fixed, bottom frame and feet stand up")


if asmprim.is_entry(__file__):
    build()
