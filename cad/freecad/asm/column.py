"""Stage 5 - the Z columns, the hinge bar, and the lid that swings off it.

Manual steps 10, 12 and 13:

* step 10, 2 x `BOT_CLAMP_Z` and 2 threaded rods M8 x 140, 8 M4x10 into slot
  nuts -- **replaced here by the linear Z axis mod**, below;
* step 12, the top frame - **3** x 2020 x 300, 2 x 2020 x 280, 8 x
  `TOP_BRACKET`, 2 x `TOP_CLAMP_Z_AXIS`, and **2 hinges**;
* step 13, its axis - 2 rails 8 x **280**, 4 LM8UU, 4 x `TOP_RAIL_HOLDER`.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/column.py

## The top frame is a lid, and that is the whole of step 12

The thing this file got wrong for a long time, and the thing a photograph of
the machine settles at a glance: **the top frame is two bodies, not one.**

    hinge bar      one 2020 x 300, carried on the two Z rods
    -- 2 hinges, screwed to both top faces --
    the lid        2 x 2020 x 300 + 2 x 2020 x 280 + 8 x TOP_BRACKET,
                   and everything the stencil clamp is made of

That is what step 12's **third** 300 mm extrusion is for.  An earlier pass here
called it "most likely the bar the stencil clamp mounts to" and left it out;
the manual's own STEP_12 renders show it plainly, lying outboard of one side
member with the two hinges bridging their top faces and a `TOP_CLAMP_Z_AXIS` at
each of its ends.

It matters because it is how the machine is *used*.  A stencil printer needs
the stencil lifted clear to put a board in and take it out, and lowered onto
the board to print; the lid is what does that.  Without the hinge the model
says the frame is a rigid box 65 mm above a work surface you cannot reach.

`POSE["lid"]` in `machine.py` opens it.

## Where the top assembly sits in X, and why it is not centred

Nothing bolts the top assembly to the bottom frame: it hangs on two 8 mm rods,
so **the rods put it where it is**, and everything else follows.

    the bottom bracket's collar     stands the rod 11.55 out from the frame
    the bearing mount's flange      reaches 13.55 in from the rod's axis

The bottom frame's outer face is at 170, so the rod runs at 181.55 and the face
the bearing mount bolts to -- the hinge bar's outer face -- has to be at
**168.0**.  The hinge bar is 20 deep and the lid is 320 across, so the whole top
assembly spans -172 .. 168 against the bottom frame's -170 .. 170: it sits
**2 mm off flush**, and that 2 mm is the difference between Michael's own two
mod parts, each of which measures the rod from a different feature of itself.
`check_reach` reports it rather than hiding it.  Two millimetres is a washer.

## The linear Z axis, in place of step 10

This is Michael's machine, so the columns are the mod the README describes and
not the manual's step 10.  The two **M8 x 140 threaded rods become 8 mm linear
rods of the same length**, each stood up on a `BOT_Z_AXIS_BRACKET` at a corner
of the bottom frame, and the hinge bar rides them on an LM8UU in a
`TOP_Z_AXIS_BEARING_MOUNT` instead of being clamped to them.  Both of those
parts are Michael's: the bracket bolts to the bottom frame and so lives in
[`../bot/`](../bot/), the bearing mount rides the lid and stays in
[`../mod/`](../mod/).

What that changes, apart from the parts:

* **the Z axis slides instead of being undone and re-clamped.**  The author's
  `TOP_CLAMP_Z_AXIS` grips the rod, so the frame's height is only adjustable
  with a hex key; on a bearing it runs free and the eccentrics set the height.
  That is also why Michael's machine has four `ECCF_*` and the author's has two
  at the front only: with a sliding Z the hinge end needs a stop of its own.
* **there is more of it.**  A clamp has to grip 34 mm of rod and a bearing only
  has to sit on 24, and the bottom bracket's collar takes 24 rather than the
  bottom clamp's 40, so the travel goes from 66 mm to **92**.  `check_travel`
  works it out from the parts rather than asserting it.
* **the Z axis moves to the +X side**, opposite the drives.  The author's
  columns and his 2040 are both on -X, and so is `BOT_BRACKET_X_AXIS`; with the
  2040 gone and the bracket still there, a column at that corner runs straight
  into it, which is what the interference check said when it was tried.  The
  photograph in the README has the rods on the side away from the handwheels,
  which agrees, and it is also the side the lid hinges on.

## What is inferred rather than derived

The **stations of the two hinges along the bar**, and the hinge itself: it is
bought rather than printed or drawn, so `stock.hinge_leaf` is an ordinary 40 mm
butt hinge of the right sort of size, not a measurement of the author's.
Nothing else depends on either.
"""

import math
import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import check    # noqa: E402
import frame    # noqa: E402
import stock    # noqa: E402
from asmprim import say  # noqa: E402

RAIL_D = 8.0
TOP_RAIL_LENGTH = 280.0
SIDE_LENGTH = 300.0              # the three 300s: two sides and the hinge bar
MEMBER = 20.0

HALF_SPAN = TOP_RAIL_LENGTH / 2.0        # the side members' inner faces
HALF_DEPTH = SIDE_LENGTH / 2.0
OUTER_X = TOP_RAIL_LENGTH + 2 * MEMBER   # 320, the lid alone
OUTER_Z = SIDE_LENGTH                    # 300

# The Z columns: 8 mm linear rod, not the author's M8 studding.
ROD_D = 8.0
ROD_LENGTH = 140.0
BEARING_H = 24.0                 # an LM8UU, and the mount that holds it
COLLAR_H = 24.0                  # what the bottom bracket's collar grips

COLUMN_SIDE = 1                  # +X, opposite the drives; see the docstring
HINGE_AT = (-75.0, 75.0)         # the two hinges' stations along the bar

# Michael's hinge lock, from `mod/`.  Its channel's closed end sits on the face
# it hooks over; its own M3 is 14.05 up from the block's base, which is a
# member's mid height; and the two halves stand this far apart along the bar so
# that the bolt runs out of one and into the other.
LOCK_SEAT = 4.5                  # the channel's closed end, in the part
LOCK_MID = 14.05                 # the M3, up from the block's base
LOCK_APART = 33.95               # boss end to hook face, along the member
LOCK_AT = 0.0                    # the pair's station along the member
LOCK_CHANNEL = 24.0              # deep, for a 20 mm member: see hinge_locks

# Where the two top rails sit across the frame.  Derived rather than guessed,
# and see stencil.py for the whole chain: the upper stencil angle's end holes
# are 103.11 from its middle, and each lands on a clamp bearing mount's own
# bolt line, which is 12.75 in from the rail that mount rides.
END_HOLE = 103.11
MOUNT_BOLT = 12.75
TOP_RAIL_Z = (-(END_HOLE + MOUNT_BOLT), END_HOLE + MOUNT_BOLT)   # +-115.86

TOP_FRAME_Y = 100.0              # nominal, inside the range checked below

TOL = 1e-6


def rod_stand():
    """How far the bottom bracket's collar stands the rod off the frame."""
    return -asmprim.datum(asmprim.part("bot/BOT_Z_AXIS_BRACKET"),
                          "ROD").Placement.Base.z


def mount_reach():
    """And how far the bearing mount's flange is from the bearing's axis."""
    return asmprim.datum(asmprim.part("mod/TOP_Z_AXIS_BEARING_MOUNT"),
                         "MOUNT").Placement.Base.z


def rod_line():
    """The Z rod's own X, off the bottom frame's outer face."""
    return COLUMN_SIDE * (frame.HALF_SPAN + frame.NARROW + rod_stand())


def bar_face():
    """The outer face of the whole top assembly: the mount's reach in."""
    return rod_line() - COLUMN_SIDE * mount_reach()


def bar_x():
    """The hinge bar's own centre line."""
    return bar_face() - COLUMN_SIDE * MEMBER / 2.0


def pivot_x():
    """The hinge axis: where the bar and the lid's side member meet."""
    return bar_face() - COLUMN_SIDE * MEMBER


def frame_x():
    """The lid's centre, which is a member and a half off the machine's."""
    return bar_face() - COLUMN_SIDE * (MEMBER + OUTER_X / 2.0)


def lid_placement(at_y, angle=0.0):
    """The transform that swings the lid up about its hinge.

    Zero is closed.  Positive lifts the free side, which is the side away from
    the columns, so the sign follows `COLUMN_SIDE`.
    """
    pivot = Vector(pivot_x(), at_y + stock.HINGE_THICK, 0.0)
    return Placement(Vector(), Rotation(Vector(0, 0, 1),
                                        -COLUMN_SIDE * angle), pivot)


def top_frame(doc, asm, at_y=TOP_FRAME_Y, lid=None):
    """The lid's four members, hung from `at_y` as their common top face."""
    lid = lid or Placement()
    cx = frame_x()
    sides = {
        "left":  (0.0, MEMBER, SIDE_LENGTH,
                  Vector(cx - (HALF_SPAN + MEMBER / 2.0), at_y, -HALF_DEPTH)),
        "right": (0.0, MEMBER, SIDE_LENGTH,
                  Vector(cx + (HALF_SPAN + MEMBER / 2.0), at_y, -HALF_DEPTH)),
        "front": (90.0, MEMBER, TOP_RAIL_LENGTH,
                  Vector(cx - HALF_SPAN, at_y, -HALF_DEPTH + MEMBER / 2.0)),
        "back":  (90.0, MEMBER, TOP_RAIL_LENGTH,
                  Vector(cx - HALF_SPAN, at_y, HALF_DEPTH - MEMBER / 2.0)),
    }
    members = {}
    for name, (angle, across, length, base) in sides.items():
        member = stock.extrusion(doc, f"lid 2020 {name}", length,
                                 cells_x=int(round(across / 20.0)))
        member.Placement = lid.multiply(
            Placement(base, Rotation(Vector(0, 1, 0), angle)))
        members[name] = member
    doc.recompute()
    for member in members.values():
        asmprim.ground(asm, member)
    return members


def hinge_bar(doc, asm, at_y=TOP_FRAME_Y):
    """Step 12's third 300 mm extrusion: what the Z rods actually carry."""
    bar = stock.extrusion(doc, "top 2020 hinge bar", SIDE_LENGTH)
    bar.Placement = Placement(Vector(bar_x(), at_y, -HALF_DEPTH), Rotation())
    doc.recompute()
    asmprim.ground(asm, bar)
    return bar


def hinges(doc, asm, at_y=TOP_FRAME_Y, lid=None):
    """Step 12's two, screwed across the bar and the lid's top faces.

    Two leaves each, because they are the one place in the machine where two
    parts have to move relative to each other and a single solid could not.
    """
    lid = lid or Placement()
    half = stock.HINGE_LENGTH / 2.0
    third = stock.HINGE_LENGTH / 6.0
    fixed, swinging = [], []
    for z in HINGE_AT:
        at = Placement(Vector(pivot_x(), at_y, z), Rotation())
        fixed.append(stock.hinge_leaf(
            doc, f"hinge bar leaf {z:+.0f}",
            [(-half, -third), (third, half)], hand=COLUMN_SIDE))
        fixed[-1].Placement = at
        swinging.append(stock.hinge_leaf(
            doc, f"hinge lid leaf {z:+.0f}",
            [(-third, third)], hand=-COLUMN_SIDE))
        swinging[-1].Placement = lid.multiply(at)
    doc.recompute()
    for leaf in fixed + swinging:
        asmprim.ground(asm, leaf)
    return fixed, swinging


def hinge_locks(doc, asm, at_y=TOP_FRAME_Y, lid=None, angle=0.0):
    """Michael's own hinge lock, a hooked half and a plated half on one M3.

    Another mod from the repository's README, and the one part of the machine
    that exists *because* the lid does: "the hinges I used still allowed for
    some play between the back of the frame and the moving part... if you're
    looking for repeatability across multiple applies".  Both halves are in
    [`../mod/`](../mod/), transcribed from `hinge-lock.py` and checked against
    that source's own solid to the last cubic millimetre.

    **How it grips is in one number: the channel is 24 deep for a 20 mm
    member.**  Those extra 4 mm are not slop, they are the whole mechanism.
    The hook goes over the lid's own side member *and laps 4 mm onto the hinge
    bar beyond it*, so it spans the joint; the M3 then pulls the hook back
    against the front half, which is bolted flat to the lid's member.  Tighten
    it and the two bars are clamped together across the hinge, which is exactly
    "repeatability across multiple applies".

    Two more of the source's numbers agree and neither was used to get that:

    * the back half's M3 is **7.5 mm** beyond the channel's closed end and the
      front half's is **7.5 mm** out from the face its plate bolts to, so the
      two are one bolt only when the closed end lands on that same face -- and
      it does, on the lid member's inboard face;
    * its two M4 are **24 long**, which is a 4 mm wall and a 20 mm extrusion
      exactly, so they bolt the hook on straight through the member.

    Which is also why **a fitted lock is not placed with the lid open**: 4 mm
    of the hook lies across the hinge line, so the lid cannot rise until the
    lock is undone.  That is the lock working, not the model failing, and
    leaving it out of the open pose says so.
    """
    lid = lid or Placement()
    if angle:
        say("  the lock spans the hinge line, so it comes off to open the lid")
        return None, None
    back = asmprim.part("mod/TOP_HINGE_LOCK_BACK")
    front = asmprim.part("mod/TOP_HINGE_LOCK_FRONT")
    face = frame_x() + COLUMN_SIDE * HALF_SPAN       # the member's inner face
    mid = at_y - MEMBER / 2.0                        # and its mid height

    # Its X runs inboard off that face, its Y along the member, its Z up.
    turn = asmprim.basis(Vector(-COLUMN_SIDE, 0, 0), Vector(0, 0, 1),
                         Vector(0, 1, 0))
    hook = asmprim.link(asm, "TOP_HINGE_LOCK_BACK", back, lid.multiply(
        Placement(Vector(face + COLUMN_SIDE * LOCK_SEAT,
                         mid - LOCK_MID, LOCK_AT + LOCK_APART / 2.0), turn)))
    plate = asmprim.link(asm, "TOP_HINGE_LOCK_FRONT", front, lid.multiply(
        Placement(Vector(face, at_y - MEMBER, LOCK_AT - LOCK_APART / 2.0),
                  turn)))
    doc.recompute()
    for link in (hook, plate):
        asmprim.ground(asm, link)
    return hook, plate


def check_lap(hook):
    """How far the hook laps onto the hinge bar -- which is the lock itself."""
    if hook is None:
        return None
    lap = abs(hook.Shape.BoundBox.XMax if COLUMN_SIDE > 0
              else hook.Shape.BoundBox.XMin) - abs(pivot_x())
    say(f"  its channel is {LOCK_CHANNEL:.1f} deep for a {MEMBER:.0f} mm "
        f"member, so it laps {lap:.1f} mm past the hinge line")
    if abs(lap - (LOCK_CHANNEL - MEMBER)) > 0.05:
        raise SystemExit("the hinge lock does not span the joint it locks")
    say("  ok: it has hold of both bars, which is what locks them together")
    return lap


def check_lock(hook, plate):
    """The lock's one M3 has to be one axis through both halves."""
    if hook is None or plate is None:
        return None
    frames = [(item.Label, asmprim.frame(item, "LOCK"))
              for item in (hook, plate)]
    for label, at in frames:
        say(f"  {label:22s} M3 at x {at.Base.x:7.2f}, y {at.Base.y:6.2f}, "
            f"z {at.Base.z:7.2f}")
    if not check.collinear(frames, say):
        raise SystemExit("the hinge lock's two halves are not on one bolt")


def top_rails(doc, asm, at_y, lid=None):
    """The two 280 mm rails and the four collars that hold them.

    Same arrangement as the bottom frame's X rails: the collar bolts flat to a
    side member's inner face with both screws in one slot, and the rail leaves
    that face at right angles.  They belong to the lid and go up with it.
    """
    lid = lid or Placement()
    body = asmprim.part("top/TOP_RAIL_HOLDER")
    foot = -asmprim.datum(body, "MOUNT").Placement.Base.x
    slot_y = at_y - MEMBER / 2.0             # the inner face's slot centre
    cx = frame_x()

    holders, rods = [], []
    for z in TOP_RAIL_Z:
        for side in (-1, 1):
            turn = 0.0 if side < 0 else 180.0
            at = Vector(cx + (-HALF_SPAN + foot if side < 0
                              else HALF_SPAN - foot), slot_y, z)
            holder = asmprim.link(
                asm, f"TOP_RAIL_HOLDER {'L' if side < 0 else 'R'}{z:+.0f}",
                body, lid.multiply(Placement(at,
                                             Rotation(Vector(0, 1, 0), turn))))
            asmprim.ground(asm, holder)
            holders.append(holder)

        rod = stock.rod(doc, f"top rail {z:+.0f}", RAIL_D, TOP_RAIL_LENGTH)
        rod.Placement = lid.multiply(Placement(
            Vector(cx - TOP_RAIL_LENGTH / 2.0, slot_y, z),
            Rotation(Vector(0, 1, 0), 90)))
        asmprim.ground(asm, rod)
        rods.append(rod)
    doc.recompute()
    return holders, rods


def columns(doc, asm, at_y):
    """Two 8 mm linear rods on their corner brackets, and the bearings on the
    hinge bar that ride them.

    The bracket is chiral -- an L plate with the rod hung off one leg -- so the
    two are **mirror images**, the way `TOP_CLAMP_BEARING_MOUNT_2` is `..._1`
    mirrored.  Only mirrored do both rods come out on the same side of the
    machine.  Each hand is its own document, so what the assembly shows is what
    would be printed; this used to mirror the shape here at build time, which
    put a solid in the machine that no part in the repository answered to.

    The mount is placed by its flange rather than by its bore: the flange is
    what is bolted, so it is the joint that has to be exact, and the bore then
    lands on the rod because `bar_face` was worked out from that same reach.
    """
    hands = {-1: asmprim.part("bot/BOT_Z_AXIS_BRACKET"),
             1: asmprim.part("bot/BOT_Z_AXIS_BRACKET_MIRRORED")}
    seat = asmprim.part("mod/TOP_Z_AXIS_BEARING_MOUNT")
    corner_x = frame.HALF_SPAN + frame.NARROW        # 170, the outer face
    corner_z = frame.HALF_DEPTH
    # The flange bolts into the bar's outer face slot, whose centre is halfway
    # down it, and the flange's own holes are halfway along the tube.
    hang = at_y - MEMBER / 2.0 + BEARING_H / 2.0
    turn = Rotation(Vector(0, 1, 0), 90.0 if COLUMN_SIDE < 0 else 270.0)

    rods, mounts, brackets = [], [], []
    for sz in (-1, 1):
        # Both corners take the same quarter turn; what differs is the hand.
        stand = Rotation(Vector(0, 1, 0), 270.0)
        at = Vector(COLUMN_SIDE * corner_x, 0.0, sz * corner_z)
        body = hands[sz]
        bracket = asmprim.link(asm, f"{body.Label} {sz:+.0f}", body,
                               Placement(at, stand))
        brackets.append(bracket)

        axis = rod_axis(bracket, body)
        rod = stock.rod(doc, f"8x140 column {sz:+.0f}", ROD_D, ROD_LENGTH)
        rod.Placement = Placement(Vector(axis.x, 0.0, axis.z),
                                  Rotation(Vector(1, 0, 0), -90.0))
        asmprim.ground(asm, rod)
        rods.append(rod)

        # The LM8UU in its mount rides the rod, and the hinge bar hangs on it.
        holder = asmprim.link(
            asm, f"TOP_Z_AXIS_BEARING_MOUNT {sz:+.0f}", seat,
            Placement(Vector(rod_line(), hang, axis.z), turn))
        mounts.append(holder)
        sleeve = stock.linear_bearing(doc, f"LM8UU column {sz:+.0f}")
        sleeve.Placement = Placement(
            Vector(rod_line(), hang - BEARING_H, axis.z),
            Rotation(Vector(1, 0, 0), -90.0))
        asmprim.ground(asm, sleeve)
        mounts.append(sleeve)

    doc.recompute()
    for link in brackets:
        asmprim.ground(asm, link)
    for link in mounts:
        if link.TypeId == "App::Link":
            asmprim.ground(asm, link)
    return rods, brackets + mounts


def rod_axis(bracket, body):
    """Where a bracket's collar puts its rod, in machine coordinates.

    The mirrored hand is a document of its own and carries its own `ROD` datum,
    already on the other side of the plate's corner, so there is nothing to
    negate here: both hands are read the same way.
    """
    return bracket.Placement.multVec(
        asmprim.datum(body, "ROD").Placement.Base)


def check_size(members, bar, lid=None):
    """The lid on its own, and the whole top assembly with the bar.

    Measured in the lid's own frame rather than the machine's, so that it
    means the same thing with the lid open as with it shut: a bounding box
    swung 60 degrees up is 177 across and says nothing about the frame.
    """
    back = (lid or Placement()).inverse()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for member in members.values():
        shape = member.Shape.copy()
        shape.Placement = back.multiply(shape.Placement)
        bb = shape.BoundBox
        for i, (a, b) in enumerate(((bb.XMin, bb.XMax), (bb.YMin, bb.YMax),
                                    (bb.ZMin, bb.ZMax))):
            lo[i], hi[i] = min(lo[i], a), max(hi[i], b)
    say(f"  lid {hi[0] - lo[0]:.1f} x {hi[2] - lo[2]:.1f} in plan, "
        f"Y {lo[1]:.1f} .. {hi[1]:.1f}")
    ok = True
    for i, axis, want in ((0, "X", OUTER_X), (2, "Z", OUTER_Z)):
        if abs((hi[i] - lo[i]) - want) > 1e-6:
            say(f"  FAIL {axis} is {hi[i] - lo[i]:.3f}, expected {want}")
            ok = False
    if abs(2 * HALF_SPAN - TOP_RAIL_LENGTH) > TOL:
        say("  FAIL the side members are not a rail apart")
        ok = False

    box = bar.Shape.BoundBox
    across = max(hi[0], box.XMax) - min(lo[0], box.XMin)
    say(f"  with the hinge bar the top assembly is {across:.1f} across, "
        f"against the bottom frame's {frame.OUTER_X:.0f}")
    if abs(across - (OUTER_X + MEMBER)) > TOL:
        say("  FAIL the bar does not lie alongside the lid")
        ok = False
    if not ok:
        raise SystemExit("the top frame is not the size it should be")
    say(f"  ok: lid {OUTER_X:.0f} x {OUTER_Z:.0f}, side members "
        f"{2 * HALF_SPAN:.0f} apart = the rail exactly")
    say(f"  ok: it hinges about x {pivot_x():.1f}, and swings clear of "
        f"everything inboard of that")


def check_collinear(holders):
    """Both top rails' collars have to share an axis, as the X rails did."""
    ok = True
    for z in TOP_RAIL_Z:
        pair = [h for h in holders if f"{z:+.0f}" in h.Label]
        a, b = (asmprim.frame(h, "RAIL") for h in pair)
        axis = asmprim.axis_of(pair[0], "RAIL")
        tilt = math.degrees(axis.getAngle(asmprim.axis_of(pair[1], "RAIL")))
        tilt = min(tilt, 180.0 - tilt)
        off = (b.Base - a.Base).cross(axis).Length / axis.Length
        say(f"  rail {z:+6.1f}: parallel to {tilt:.2e} deg, "
            f"offset {off:.2e} mm")
        if tilt > TOL or off > TOL:
            ok = False
    if not ok:
        raise SystemExit("the top rail bores do not line up")
    say("  ok: both top rails' bores are collinear")


def check_travel(rods, parts):
    """How much height the linear Z gives, worked out from the parts.

    The collar takes some of the rod at the bottom and the bearing takes some
    of it wherever the frame happens to be, so what is left is the travel.  On
    the author's own Z axis the two clamps take 40 and 34 of the 140; the mod's
    collar and bearing take 24 each, and that is where the extra travel comes
    from.
    """
    free = ROD_LENGTH - COLLAR_H - BEARING_H
    say(f"  8 mm rod {ROD_LENGTH:.0f}, {COLLAR_H:.0f} of it in the bracket's "
        f"collar and {BEARING_H:.0f} in the bearing")
    say(f"  so the top assembly runs over {free:.0f} mm; the author's clamped "
        f"Z axis gives 66")
    if free <= 0:
        raise SystemExit("the collar and the bearing take up the whole rod")
    for rod in rods:
        bb = rod.Shape.BoundBox
        if abs(bb.YLength - ROD_LENGTH) > TOL:
            say(f"  FAIL {rod.Label} is {bb.YLength:.1f} long")
            raise SystemExit("a column rod is the wrong length")
    say(f"  ok: {len(rods)} columns, {free:.0f} mm of Z travel")
    return free


def check_reach(rods, bar):
    """Does the bearing on the hinge bar sit on the rod the bracket stood up?

    The two ends of the linear Z mod are Michael's own parts and each measures
    the rod from a different feature of itself -- the bracket from the frame
    face its plate lies on, the mount from the flange it bolts through -- so
    they differ by a fixed 2 mm.  That difference cannot be split: the flange
    has to lie on the bar and the bore has to be on the rod, so it comes out as
    the top assembly sitting 2 mm inboard of the bottom frame instead.
    """
    axis = rods[0].Shape.BoundBox.XMin + ROD_D / 2.0
    face = bar.Shape.BoundBox.XMax if COLUMN_SIDE > 0 \
        else bar.Shape.BoundBox.XMin
    say(f"  the bracket stands the rod {rod_stand():.2f} out from the bottom "
        f"frame, so it runs at x {axis:+.2f}")
    say(f"  the mount reaches {mount_reach():.2f} in from its bore, so the "
        f"bar's face lands at x {face:+.2f}")
    if abs(abs(axis - face) - mount_reach()) > 0.01:
        say("  FAIL the flange does not lie on the bar")
        raise SystemExit("the Z bearing mount is not bolted to anything")
    off = abs(face) - (frame.HALF_SPAN + frame.NARROW)
    say(f"  ok: the flange is on the bar and the bore is on the rod")
    say(f"  NOTE that puts the top assembly {abs(off):.2f} mm "
        f"{'out past' if off > 0 else 'inboard of'} the bottom frame's "
        f"own face -- see the docstring; it is a washer's worth")
    return off


def build():
    doc, asm = asmprim.assembly("Column")
    say("=== the bottom frame, to hang the columns off")
    members = frame.bottom_frame(doc, asm)
    frame.check_size(members)

    say("=== the hinge bar, and the lid that swings off it")
    bar = hinge_bar(doc, asm, TOP_FRAME_Y)
    lid = lid_placement(TOP_FRAME_Y, 0.0)
    top = top_frame(doc, asm, TOP_FRAME_Y, lid)
    hinges(doc, asm, TOP_FRAME_Y, lid)
    check_size(top, bar, lid)

    say("=== its two 280 mm rails")
    holders, rods_top = top_rails(doc, asm, TOP_FRAME_Y, lid)
    check_collinear(holders)

    say("=== the hinge lock")
    hook, plate = hinge_locks(doc, asm, TOP_FRAME_Y, lid)
    check_lock(hook, plate)
    check_lap(hook)

    say("=== the two Z columns")
    rods, parts = columns(doc, asm, TOP_FRAME_Y)
    check_travel(rods, parts)
    check_reach(rods, bar)

    asmprim.solve(asm, context="the top frame and columns")
    asmprim.save(doc)
    say("\nSTAGE 5 PASSED -- a hinge bar on 92 mm of linear Z, and a lid "
        "that opens off it")


if asmprim.is_entry(__file__):
    build()
