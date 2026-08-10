"""Steps 11 and 18 - the eccentrics that press the stencil onto the boards.

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \\
        cad/freecad/asm/eccentric.py

Step 11 builds two at the front and step 18 two more at the back.  On the
author's machine the back pair are `ECCB_BODY`, `ECCB_LEVER` and `ECCB_SHIM`,
which he never published -- **on Michael's they are the same `ECCF_*` eccentric
as the front**, which is exactly what the README's linear Z axis mod says it
did, and which is why this file can build all four.

## The group knows its own stack

`ECCF_*` was exported in assembly position, so the four bodies stack
contiguously to the millimetre under an identity placement and only the group
as a whole has to be located:

| | its own Y |
|---|---|
| `ECCF_BOT` | -18 .. -10 | the plate that bolts to the frame |
| `ECCF_HEIGHT` | -10 .. 0 | the thumb nut that sets the height |
| `ECCF_MOUNT` | 0 .. 14 | the collar the eccenter body turns in |
| `ECCF_TOP` | 0 .. 27 | the block the M8 runs up |

So one number places the lot: `ECCF_BOT` lies on the bottom frame's top face,
which puts the group's own origin at **Y = 18** and the top of it at **45**.

## What that settles: the machine's working height

The eccentric is what the top frame comes down onto, so the top of the stack is
where the underside of the top frame ends up -- **Y = 45**, and the frame's
members are 20 deep, so the working pose is `z = 65`.

Two things agree with it and neither was used to get it:

* the alpha axis's top plate -- the work surface -- finishes at **Y = 40.2**,
  and the stencil clamp hangs its lowest part 16.9 mm below the rail.  Standing
  the frame at 68.1 leaves that clear by 1 mm and the foil 3 mm above the
  plate, which is the printer's **snap-off** -- and the eccentrics' own 45 mm
  stack is then **3.1 mm** below it, which is exactly the range `ECCF_HEIGHT`,
  the thumb nut on the eccentric's rod, exists to cover.
* the linear Z rod is 140 long from the frame's top face and the bearing is
  24 of it, so a frame underside at 45 is comfortably inside the travel.

## Where they go in plan

`ECCF_BOT` is 40 mm along its bolt line with two M4 at +-16, so it needs a slot
running that way.  They go on the two **side** members, two each: the front end
member is where the X screw runs at Y = 13, and the interference check found
the front pair standing in it.  Their stations along the member are read off
the manual's STEP_18 renders and are the softest thing here.

The hinges are not modelled: the manual lists two of them in step 12 and there
is no part for them in the repository, printed or drawn.
"""

import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asmprim  # noqa: E402
import column   # noqa: E402
import frame    # noqa: E402
import stencil  # noqa: E402
import stock    # noqa: E402
from asmprim import say  # noqa: E402

TOL = 1e-6

GROUP = ("ECCF_BOT", "ECCF_HEIGHT", "ECCF_MOUNT", "ECCF_TOP")
LEVER = "ECCF_LEVER"
LEVER_MIRROR = -13.2             # the plane the lever's two cheeks straddle

BOARD_Y = 40.2                   # ALPHA_TOP_PLATE's top face, the work surface
ROD_D = 8.0
ROD_LENGTH = 55.0                # M8 x 55, steps 11 and 18
SLOT_DEPTH = 5.0                 # how far into the extrusion's slot it starts
SPRING_D = 12.0                  # "ID > 9"
SPRING_WIRE = 1.2

# Two on each **side** member, whose top slots run the way ECCF_BOT's own two
# bolts do once it is turned a quarter turn.  Not on the end members: the X
# screw runs the length of the front one at Y = 13, and the interference check
# found the front pair standing in it.
AT_Z = (-70.0, 70.0)   # clear of the corner brackets, which reach 90
AT_SIDE = (-1, 1)


def group_lift():
    """How far the ECCF group rises to stand its plate on the frame."""
    return -asmprim.part(f"eccf/{GROUP[0]}").Shape.BoundBox.YMin


def top_of_stack():
    """Where the eccentric's own top face lands, once it is stood up."""
    return group_lift() + max(asmprim.part(f"eccf/{name}").Shape.BoundBox.YMax
                              for name in GROUP)


def working_height():
    """The top frame's Y when it is down on the eccentrics."""
    return top_of_stack() + column.MEMBER


def lever_pair(doc, asm, label, at, turn):
    """Both cheeks of one hand lever.

    `ECCF_LEVER.stl` holds two shells, not one: it is a printing pair of
    identical cheeks that go one either side of the eccenter and grip its shaft
    between their hubs, and `eccf/eccf-lever.py` builds the one at X = -30.4 ..
    -16.2 and says in as many words that the other is its mirror about
    X = -13.2.

    Only the first was ever placed here, so it touched nothing:
    `check.connected` found four hand levers hanging in the air and that is
    exactly what they were.

    The two are named by how the second is made rather than by which is
    inboard.  They were once "outer" and "inner", which stopped being true when
    the group started turning to face the side it is on: a half turn swaps
    which cheek is nearer the machine's middle, so the names swapped meaning on
    one side and stayed put on the other.

    **The pair straddles its own mirror plane, not the part's origin.**  The
    two cheeks sit either side of `LEVER_MIRROR`, so placing them both at the
    group's origin hangs the pair 13.2 mm off the eccenter they are supposed to
    grip -- which is what it did, and what put the levers out of line with the
    ECCF stack under them.  Shifting by the mirror plane in the group's *own*
    frame centres the gap on the eccenter whichever way the group faces.
    """
    body = asmprim.part(f"eccf/{LEVER}")
    # In the group's own frame, so it follows the quarter turn either way.
    place = Placement(at, turn).multiply(
        Placement(Vector(-LEVER_MIRROR, 0.0, 0.0), Rotation()))
    near = asmprim.link(asm, f"{LEVER} {label}", body, place)
    shape = body.Shape.copy().mirror(Vector(LEVER_MIRROR, 0.0, 0.0),
                                     Vector(1, 0, 0))
    far = doc.addObject("Part::Feature", "Mirrored")
    far.Label = f"{LEVER} mirrored {label}"
    far.Shape = shape
    far.Placement = place
    return near, far


def eccentrics(doc, asm):
    """All four, placed as whole groups on the frame's end members."""
    lift = group_lift()
    made = []
    for side in AT_SIDE:
        # The plate's bolt line runs along its own X, and on a side member the
        # slot runs along Z, so the whole group turns a quarter turn -- and
        # **which quarter turn depends on the side it is on**.  The lever is
        # the reason: it is a hand lever, so its arm has to come out towards
        # whoever is working the machine rather than in under the print plate,
        # and the group carries the lever.  Turned the same way on both sides,
        # one side's levers reach outward and the other side's reach in, which
        # is what they did.  This is a rotation and not a mirror: it is the
        # same eccentric, stood the other way round, not a second hand of it.
        turn = Rotation(Vector(0, 1, 0), 90.0 if side < 0 else 270.0)
        for z in AT_Z:
            at = Vector(side * (frame.HALF_SPAN + frame.NARROW / 2.0),
                        lift, z)
            for name in GROUP:
                body = asmprim.part(f"eccf/{name}")
                made.append(asmprim.link(
                    asm, f"{name} {side:+.0f}{z:+.0f}", body,
                    Placement(at, turn)))
            made.extend(lever_pair(doc, asm, f"{side:+.0f}{z:+.0f}", at, turn))

            # The rod is M8 x 55 and its bottom nuts are in the extrusion's own
            # slot, so it starts below the frame's top face rather than on it.
            rod = stock.threaded_rod(doc, f"M8x55 eccenter {side:+.0f}{z:+.0f}",
                                     ROD_D, ROD_LENGTH)
            rod.Placement = Placement(
                Vector(at.x, -SLOT_DEPTH, at.z),
                Rotation(Vector(1, 0, 0), -90.0))
            asmprim.ground(asm, rod)
            made.append(rod)
    doc.recompute()
    for link in made:
        if link.TypeId == "App::Link":
            asmprim.ground(asm, link)
    return made


def check_stack():
    """The four bodies have to stack without a gap or an overlap."""
    spans = [(name, asmprim.part(f"eccf/{name}").Shape.BoundBox)
             for name in GROUP]
    lift = group_lift()
    for name, bb in spans:
        say(f"  {name:12s} y {bb.YMin + lift:6.1f} .. {bb.YMax + lift:6.1f}")
    say(f"  the eccentric stands {top_of_stack():.0f} mm tall, so the top "
        f"frame works at y {working_height():.0f}")
    return top_of_stack()


def check_gap(top_y=None):
    """Where the eccentrics put the stencil, relative to the board.

    This is the check the whole machine comes down to, and the two chains that
    meet in it were worked out from opposite ends: the eccentric's own stack of
    four printed parts, and the clamp's chain of bearing mount, angle and foil.
    """
    top_y = working_height() if top_y is None else top_y
    rail = top_y - column.MEMBER / 2.0
    foil = rail - stencil.foil_drop()
    say(f"  work surface   y {BOARD_Y:.2f}")
    say(f"  stencil foil   y {foil:.2f}")
    gap = foil - BOARD_Y
    say(f"  so the snap-off is {gap:.2f} mm, and a board sits in it")
    if gap < 0:
        raise SystemExit("the foil would be inside the work surface")
    return gap


def check_reach(top_y):
    """Do the eccentrics reach the frame they press?

    They do, and getting here took one correction.  The eccentric stacks to 45
    and puts the top frame's underside there; the stencil clamp, with its
    angles' uprights standing up the way the machine's own video shows,
    reaches 14.9 mm below the rail and so wants the frame at 65.1.  An earlier
    pass had the angles hanging their legs downwards instead, which asked for
    84 and made these two disagree by 19 mm.  Nothing else changed.
    """
    stands = top_of_stack()
    say(f"  the eccentrics stand to y {stands:.1f} with their thumb nuts down")
    say(f"  the top frame's underside is at y {top_y - column.MEMBER:.1f}")
    short = (top_y - column.MEMBER) - stands
    say(f"  so ECCF_HEIGHT has to be wound up {short:.1f} mm, which is what "
        f"it is for")
    if not 0.0 <= short <= 10.0:
        say(f"  NOTE {short:+.1f} mm is outside the thumb nut's own 10 mm")
    return short


def build():
    doc, asm = asmprim.assembly("Eccentric")
    say("=== the bottom frame, to stand them on")
    members = frame.bottom_frame(doc, asm)
    frame.check_size(members)

    say("=== four eccentrics, two at each end")
    made = eccentrics(doc, asm)
    say(f"  {len([m for m in made if m.TypeId == 'App::Link'])} printed parts "
        f"and 4 rods")
    check_stack()

    say("=== what that means for the machine")
    # The height the machine actually works at is the clamp's, not the
    # eccentric's own stack; the difference is what the thumb nut takes up.
    working = stencil.working_height(BOARD_Y)
    check_gap(working)
    check_reach(working)

    asmprim.solve(asm, context="the eccentrics")
    asmprim.save(doc)
    say("\nSTEPS 11 AND 18 -- four eccentrics, standing 45 mm with their "
        "thumb nuts down")


if asmprim.is_entry(__file__):
    build()
