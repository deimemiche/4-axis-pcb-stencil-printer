"""Stage 6 - the stencil clamp: manual steps 13, 14 and 15.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/stencil.py

The lid's two 8 mm rails are not an axis of the machine: they are what the
**stencil clamp** slides on.  The stencil is a thin steel foil, and the clamp
grips it along **two opposite edges** and pulls them apart, so the foil is held
flat and in tension over the board.  All of it goes up when the lid does.

    step 13   2 rails 8 x 280, 4 LM8UU, 4 TOP_RAIL_HOLDER, 2 springs,
              2 TOP_CLAMP_BEARING_MOUNT_1, 2 x ..._2, 2 TOP_SPRING_PLATE,
              2 TOP_CLAMP_STOP
    step 14   **2** upper angles, 213.72 long, 12 x M3x10 and nuts
    step 15   **2** lower angles, 198 long, 8 x M3x10 and 6 TOP_CLAMP_NUT_HOLDER

## A clamp bar is a *pair* of angles with the foil between them

The part counts say it plainly: step 14 buys **two** of the long angle and step
15 **two** of the short one, and the drawings give the long one **6** holes
through its leg and the short one **4** - which is exactly the 12 and the 8
screws those steps list.  So there are four angles, not two, and they make
**two clamp bars**:

    nut holders   sitting in the channel, taking the M3s
    upper angle   213.72, its ends bolted to a bearing mount on each rail
    -- the foil --
    lower angle   198, hanging between the rails

One bar grips the foil's near edge and the other its far edge; the spring on
each rail pushes them apart and the foil comes taut.

## The bar sits *beside* the rail, not under it

This is the thing that was open, and `TOP_CLAMP_BEARING_MOUNT_1`'s own numbers
settle it.  The mount's plate reaches sideways off the rail, along the clamp
bar, and the angle is bolted to it three ways at once:

    two M3 up through the leg      9.2 apart along the rail
    one M3 along the rail          through the upright, near its top

Five of the mount's dimensions and the angle's drawing agree, and none of them
was used to guess any other:

* the mount's two cross bolts are at x -3.6 and +5.6, **9.2 apart**; the upper
  angle's two end holes are 6.4 and 15.6 from its corner, **9.2 apart**, and
  laying the corner on the mount's own end at x = -10 puts them at -3.6 and
  +5.6 exactly;
* the mount's end is flatted off for its **first 2 mm**, x -10 .. -8, "so that
  end sits against whatever it bolts to" -- and the angle's upright is **2 mm**
  thick;
* that flat is at **9.0** from the rail's axis, and the angle is 213.72 long,
  so its end face is 106.86 from its middle: the rail therefore runs
  **115.86** out.  Independently, the angle's end holes are 103.11 from its
  middle and the mount's bolt line is 12.75 in from the rail: 103.11 + 12.75 =
  **115.86** as well;
* the mount's plate ends 7.5 above the rail's axis, and standing the angle's
  upright flush with that puts its leg 12.5 below the axis, which puts the
  M3 through the upright at **6.14** below it.  The mount's own along-bolt is
  at **6.1385**.

So the upright stands **up**, past the rail's axis, but the bar stops 9 mm
short of the rail, and nothing of the clamp is ever under a rail.  An earlier
pass had the bar hanging centred under the rail and the upright driven through
it; that pair had to be printed as OPEN every build.  It is gone.

## What that settles: the working height, and the eccentrics

    rail          the lid's top face - 10
    upright top   rail + 7.5
    upper leg     rail - 12.5  .. - 10.5   bolted to the mounts
    the foil      rail - 12.65
    lower leg     rail - 14.65 .. - 12.65

Standing the lid so the lower angle clears the work surface by 1 mm puts the
foil 3 mm above the board, which is the printer's **snap-off** - the gap the
squeegee presses out of the way as it goes.

## What is read off the renders, and what is not

Forced by the parts: the rails' spacing, that a bar is a pair, the channel and
its nut holders, every height above.

Read off the pictures: the order of the parts along a rail (STEP_13_1), and how
far apart the two bars sit - which is a *pose*, not a dimension, because the
whole point of the clamp is that it slides.  `STENCIL` below is the foil this
one is holding.

**Still open**: `TOP_CLAMP_BEARING_MOUNT_2` is `..._1` mirrored, and a bar does
need one of each - the two ends of a bar are opposite hands, which is why the
author drew two parts where a rotation would have done for one.  Which of the
two goes on which rail is a coin toss here; nothing else depends on it.
"""

import os
import sys

import Part
from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import column   # noqa: E402
import stock    # noqa: E402
from asmprim import basis, say  # noqa: E402

TOL = 1e-6

RAIL_Z = column.TOP_RAIL_Z

ANGLE = 20.0                     # the L's outside, both ways
LEG = 2.0                        # its wall
HALF_LENGTH = 213.72 / 2.0       # the upper angle's own half length
END_HOLE = column.END_HOLE       # 103.11, its end holes
UPPER_LINE = 6.4                 # its bolt line, from its corner
LOWER_LINE = 10.0                # the lower angle's, from its own
CHANNEL = UPPER_LINE + LOWER_LINE                # 16.4, corner to corner

# TOP_CLAMP_BEARING_MOUNT_1's own numbers, from `top-clamp-bearing-mount-1.py`.
MOUNT_BOLT = column.MOUNT_BOLT   # 12.75, the bolt line in from the rail's axis
MOUNT_SEAT = 9.0                 # the flat its end presents to the upright
MOUNT_TOP = 7.5                  # its plate's top edge, above the rail's axis
MOUNT_END = 10.0                 # from its origin back to that flat
MOUNT_LENGTH = 26.0              # the whole of it, along the rail
MOUNT_EDGE = 6.1385              # the along-the-rail bolt, below the axis

# Where the angle ends up, off the rail's axis.
UPRIGHT_TOP = MOUNT_TOP                  # +7.5
LEG_BOTTOM = ANGLE - UPRIGHT_TOP         # 12.5 below the axis
LEG_TOP = LEG_BOTTOM - LEG               # 10.5

SPRING_D = 11.0                  # step 13's "ID > 9"
SPRING_WIRE = 1.2
SPRING_FREE = 25.0
PLATE_THICK = 4.4                # TOP_SPRING_PLATE, along the rail

# The foil this clamp is holding, and where its two gripped edges sit.  A pose
# rather than a dimension: the bars slide, and a different stencil moves them.
STENCIL = {"span": 150.0, "across": 190.0, "thick": 0.15, "grip": 12.0}

NUT_HOLDER_AT = (-75.0, 0.0, 75.0)       # three to a bar, on the shared holes

# An angle drawn along its own X: length along the bar, leg lying flat, upright
# standing up.  -120 degrees about (1,1,1) sends its X to the machine's Z, its
# Y to X and its Z to Y, which is exactly that.
STANDING = Rotation(Vector(1, 1, 1), -120.0)
# And its partner, turned in plan so the two uprights end up back to back.
MIRRORED = Rotation(Vector(0, 1, 0), 180.0).multiply(STANDING)


def profile(name):
    return asmprim.part(f"plate/{name}")


def foil_drop():
    """How far the foil's own underside hangs below the rail's axis."""
    return LEG_BOTTOM + STENCIL["thick"]


def clamp_drop():
    """And how far the *lowest* part of the clamp hangs below it.

    The lower angle's leg is under the foil, so it is what has to clear the
    work surface -- the foil cannot simply be laid on the plate or the angle
    that grips it would be inside it.
    """
    return foil_drop() + LEG


def working_height(board, clear=1.0):
    """The lid's Y that leaves the clamp `clear` above the work surface.

    That is the constraint that actually sets the machine's height, and what
    falls out of it is the **snap-off**: the gap between the stencil and the
    board, which every stencil printer has.
    """
    return board + clear + clamp_drop() + column.MEMBER / 2.0


def snap_off(top_y, board):
    """The gap the working height leaves between the foil and the board."""
    return (top_y - column.MEMBER / 2.0 - foil_drop()) - board


def bar_stations():
    """Where the two clamp bars' corners sit, and which way each leg points.

    The corner is the upper angle's upright, which is what lands on a mount's
    flatted end; the leg runs from there along the rail, and the two bars face
    each other so the foil is gripped between their two bolt lines.
    """
    half = STENCIL["span"] / 2.0
    cx = column.frame_x()
    return {"sprung": (cx - half, 1), "fixed": (cx + half, -1)}


def grip_lines(bars):
    """Where each bar actually holds the foil, along the rails."""
    return {key: at + hand * UPPER_LINE for key, (at, hand) in bars.items()}


def running_gear(doc, asm, at_y, bars, lid=None):
    """Step 13, twice: what rides each of the lid's two rails.

    A bearing mount at each end of each bar, a stop clamped to the rail beyond
    the sliding one, and a spring between them pushing the two bars apart,
    which is what tensions the foil.

    A bar's two ends are opposite hands -- the mount's plate has to reach
    *inboard* from both rails -- so one takes `..._1` and the other `..._2`,
    which is why the author drew a mirrored pair.
    """
    lid = lid or Placement()
    hands = {1: asmprim.part("top/TOP_CLAMP_BEARING_MOUNT_1"),
             -1: asmprim.part("top/TOP_CLAMP_BEARING_MOUNT_2")}
    stop_body = asmprim.part("top/TOP_CLAMP_STOP")
    plate_body = asmprim.part("top/TOP_SPRING_PLATE")

    rail_y = at_y - column.MEMBER / 2.0          # the inner face's slot centre
    made = {key: [] for key in bars}
    for z in RAIL_Z:
        inboard = -1.0 if z > 0 else 1.0         # which way the plate reaches
        for key, (at, hand) in bars.items():
            # Unmirrored where the plate's reach and the leg agree in hand,
            # mirrored where they do not; the mirror is in the part's own
            # vertical, so the turned copy takes its Z the other way up.
            same = (inboard > 0) == (hand > 0)
            body = hands[1 if same else -1]
            turn = basis(Vector(hand, 0, 0), Vector(0, 0, inboard),
                         Vector(0, -1 if same else 1, 0))
            made[key].append(asmprim.link(
                asm, f"{body.Label} {key} {z:+.0f}", body,
                lid.multiply(Placement(
                    Vector(at + hand * MOUNT_END, rail_y, z), turn))))
            sleeve = stock.linear_bearing(doc, f"LM8UU stencil {key} {z:+.0f}")
            sleeve.Placement = lid.multiply(Placement(
                Vector(at + hand * (MOUNT_END - 1.0), rail_y, z),
                Rotation(Vector(0, 1, 0), 90.0 * hand)))
            asmprim.ground(asm, sleeve)

        # The stop sits beyond the sliding bar and the spring pushes it off.
        sprung, hand = bars["sprung"]
        nose = sprung                            # its mount's outer end
        stop = asmprim.link(
            asm, f"TOP_CLAMP_STOP {z:+.0f}", stop_body,
            lid.multiply(Placement(
                Vector(nose - hand * SPRING_FREE, rail_y, z), Rotation())))
        # The plate's own thickness runs along the rail; it goes outboard of
        # the bar's upright rather than into it.
        seat = asmprim.link(
            asm, f"TOP_SPRING_PLATE {z:+.0f}", plate_body,
            lid.multiply(Placement(
                Vector(nose - (PLATE_THICK if hand > 0 else 0.0), rail_y, z),
                Rotation(Vector(0, 0, 1), -90.0))))
        coil = stock.spring(doc, f"stencil spring {z:+.0f}", SPRING_D,
                            SPRING_WIRE, SPRING_FREE)
        coil.Placement = lid.multiply(Placement(
            Vector(nose - hand * SPRING_FREE, rail_y, z),
            Rotation(Vector(0, 1, 0), 90.0 * hand)))
        for solid in (stop, seat, coil):
            asmprim.ground(asm, solid)

    doc.recompute()
    for group in made.values():
        for item in group:
            asmprim.ground(asm, item)
    return made, rail_y


def clamp_bars(doc, asm, bars, rail_y, lid=None):
    """Steps 14 and 15: two bars, each a pair of angles with the foil between.

    The upper angle's leg goes under the bearing mounts and the lower one hangs
    under it, turned in plan so their uprights stand back to back with the nut
    holders' channel between them.
    """
    lid = lid or Placement()
    upper_y = rail_y - LEG_BOTTOM                # the upper leg's underside
    lower_y = upper_y - STENCIL["thick"] - LEG
    made = {}
    for key, (at, hand) in bars.items():
        up = STANDING if hand > 0 else MIRRORED
        down = MIRRORED if hand > 0 else STANDING
        made[f"upper {key}"] = asmprim.link(
            asm, f"STENCIL_HOLDER_BACK {key}", profile("STENCIL_HOLDER_BACK"),
            lid.multiply(Placement(Vector(at, upper_y, 0.0), up)))
        made[f"lower {key}"] = asmprim.link(
            asm, f"STENCIL_HOLDER_FRONT {key}", profile("STENCIL_HOLDER_FRONT"),
            lid.multiply(Placement(Vector(at + hand * CHANNEL, lower_y, 0.0),
                                   down)))
    doc.recompute()
    for item in made.values():
        asmprim.ground(asm, item)
    return made, upper_y


def nut_holders(doc, asm, bars, rail_y, lid=None):
    """Step 15's six, three to a bar, dropped into the channel.

    They sit on the upper angle's leg between the two uprights, and the M3 that
    clamps the foil comes up from underneath into the nut each one holds.
    """
    lid = lid or Placement()
    body = asmprim.part("top/TOP_CLAMP_NUT_HOLDER")
    box = body.Shape.BoundBox
    on_top = rail_y - LEG_TOP                    # the upper leg's own top face
    made = []
    for key, (at, hand) in bars.items():
        # Centred on the channel between the two corners, standing on the leg.
        middle = at + hand * CHANNEL / 2.0
        stand = Vector(middle - box.Center.x, on_top - box.YMin, 0.0)
        for z in NUT_HOLDER_AT:
            made.append(asmprim.link(
                asm, f"TOP_CLAMP_NUT_HOLDER {key} {z:+.0f}", body,
                lid.multiply(Placement(stand + Vector(0.0, 0.0, z),
                                       Rotation()))))
    doc.recompute()
    for item in made:
        asmprim.ground(asm, item)
    return made


def foil(doc, asm, bars, rail_y, lid=None):
    """The stencil itself: a steel sheet gripped along both of its edges.

    It is the only thing in the machine that is neither printed, bought nor cut
    from the author's drawings -- it is the workpiece the whole thing exists to
    hold, and putting it in is what makes the clamp legible.
    """
    lid = lid or Placement()
    lines = grip_lines(bars)
    lo, hi = min(lines.values()), max(lines.values())
    at_y = rail_y - foil_drop()
    sheet = Part.makeBox(hi - lo + 2 * STENCIL["grip"], STENCIL["thick"],
                         STENCIL["across"],
                         Vector(lo - STENCIL["grip"], at_y,
                                -STENCIL["across"] / 2.0))
    obj = doc.addObject("Part::Feature", "Stencil")
    obj.Label = "stencil foil"
    obj.Shape = sheet
    obj.Placement = lid
    asmprim.ground(asm, obj)
    doc.recompute()
    return obj


def check_pair():
    """The two angles have to bolt to each other and to the mounts."""
    top = profile("STENCIL_HOLDER_BACK")
    bot = profile("STENCIL_HOLDER_FRONT")

    def holes(part, radius):
        return sorted({round(f.Surface.Center.x, 2)
                       for f in part.Shape.Faces
                       if f.Surface.TypeId == "Part::GeomCylinder"
                       and abs(f.Surface.Radius - radius) < 0.01})

    holes_t, holes_b = holes(top, 2.5), holes(bot, 2.5)
    say(f"  upper angle: {len(holes_t)} holes at "
        f"{', '.join(f'{h:g}' for h in holes_t)}")
    say(f"  lower angle: {len(holes_b)} holes at "
        f"{', '.join(f'{h:g}' for h in holes_b)}")
    shared = [h for h in holes_b if any(abs(h - t) < 0.01 for t in holes_t)]
    if len(shared) != len(holes_b):
        raise SystemExit("the lower angle's holes do not land on the upper's")
    ends = [h for h in holes_t if abs(abs(h) - END_HOLE) < 0.01]
    say(f"  ok: all {len(shared)} of the lower angle's holes are the upper's "
        f"too, and the {len(ends)} left over are its ends, on the mounts")

    holder = asmprim.part("top/TOP_CLAMP_NUT_HOLDER").Shape.BoundBox
    say(f"  the two uprights leave a {CHANNEL:.1f} mm channel and "
        f"TOP_CLAMP_NUT_HOLDER is {holder.XLength:.1f} wide")
    if abs(holder.XLength - CHANNEL) > 0.05:
        raise SystemExit("the nut holder does not fit the channel")
    say("  ok: it drops into it")


def check_seat():
    """Where the bar meets its mounts: the two chains that fix the rails.

    Both of these arrive at the rail spacing from a different end of the same
    joint, and they have to agree or the bar is not on the mount.
    """
    by_hole = END_HOLE + MOUNT_BOLT
    by_end = HALF_LENGTH + MOUNT_SEAT
    say(f"  end holes {END_HOLE:.2f} + the mount's bolt line "
        f"{MOUNT_BOLT:.2f} = {by_hole:.2f}")
    say(f"  half the angle {HALF_LENGTH:.2f} + its flatted seat "
        f"{MOUNT_SEAT:.2f} = {by_end:.2f}")
    if abs(by_hole - by_end) > 0.01:
        raise SystemExit("the clamp bar does not reach its bearing mounts")
    if abs(abs(RAIL_Z[0]) - by_hole) > 0.01:
        raise SystemExit(f"the rails are at {RAIL_Z[0]}, not {-by_hole}")
    say(f"  ok: the rails run at +-{by_hole:.2f}, and the bar stops "
        f"{MOUNT_SEAT:.1f} mm short of each")

    # And the third bolt, the one along the rail through the upright.
    upright = LEG_BOTTOM - (LEG + 4.36)          # the drawing's own 4.36
    say(f"  the M3 through the upright lands {upright:.2f} below the rail's "
        f"axis; the mount's own bolt is at {MOUNT_EDGE:.4f}")
    if abs(upright - MOUNT_EDGE) > 0.25:
        raise SystemExit("the upright's bolt does not line up with the mount")
    say("  ok: standing the upright flush with the plate's top edge puts it "
        "there")


def check_foil(bars, rail_y, board=None):
    """Where the foil ends up, which is the machine's whole purpose."""
    at_y = rail_y - foil_drop()
    lines = grip_lines(bars)
    span = abs(max(lines.values()) - min(lines.values()))
    say(f"  the foil is gripped {span:.0f} mm apart and lies at y {at_y:.2f}")
    if board is not None:
        say(f"  the work surface is at y {board:.2f}: snap-off "
            f"{at_y - board:.2f} mm, and the clamp itself clears it by "
            f"{rail_y - clamp_drop() - board:.2f}")
        if rail_y - clamp_drop() < board:
            raise SystemExit("the clamp's lower angle is inside the plate")
    return at_y


def build():
    doc, asm = asmprim.assembly("Stencil")

    say("=== the lid and its two rails")
    lid = column.lid_placement(column.TOP_FRAME_Y, 0.0)
    top = column.top_frame(doc, asm, column.TOP_FRAME_Y, lid)
    bar = column.hinge_bar(doc, asm, column.TOP_FRAME_Y)
    column.hinges(doc, asm, column.TOP_FRAME_Y, lid)
    column.check_size(top, bar, lid)
    holders, rails = column.top_rails(doc, asm, column.TOP_FRAME_Y, lid)
    column.check_collinear(holders)

    say("=== where the bar meets its mounts")
    check_seat()
    check_pair()

    say("=== step 13: what rides the rails")
    bars = bar_stations()
    gear, rail_y = running_gear(doc, asm, column.TOP_FRAME_Y, bars, lid)
    say(f"  two mounts, a spring, a plate and a stop on each rail, at "
        f"y {rail_y:.1f}")

    say("=== steps 14 and 15: two bars, four angles, six nut holders")
    clamp_bars(doc, asm, bars, rail_y, lid)
    nut_holders(doc, asm, bars, rail_y, lid)
    foil(doc, asm, bars, rail_y, lid)
    check_foil(bars, rail_y)

    asmprim.solve(asm, context="the stencil clamp")
    asmprim.save(doc)
    say("\nSTAGE 6 -- a clamp bar is a pair of angles, bolted beside the "
        "rails and not under them")


if asmprim.is_entry(__file__):
    build()
