"""HINGE_40_LEAF - one leaf of the bought butt hinge the lid swings on.

Bought stock, like the rod and the studding, and the one part of the lid that
was never drawn at all: the two hinges bridge the top faces of the hinge bar
and the lid's side member, both 2020, and until now the only geometry for them
was a stand-in inside the retired `asm/stock.py`.

**One document, used twice.**  The hinge in
[`../../../docs/img/closed-top.jpg`](../../../docs/img/closed-top.jpg) has
**four knuckles**, two to a leaf, and an even knuckle count is what makes a
butt hinge out of two of *the same* part rather than a handed pair: this leaf
carries the first and third knuckle, and the second leaf is this one turned end
for end.  In the assembly that is a **180 degree rotation about X through
(0, 0, 20)** -- it swaps the knuckle stations, puts the plate on the far side
of the pivot, and leaves the plate in the same plane, which is the whole trick.

    Plate     sketch -> Pad     the leaf, 20 from the pivot, 1.5 thick
    Notches   sketch -> Pocket  cut back to the barrel at the other two stations
    Knuckle   sketch -> Pad     one barrel, at the first station
    Knuckles          Pattern   and the third, one station apart
    Pin       sketch -> Pocket  the bore, through
    Screws    sketch -> Pocket  two M4 clearance, over the extrusion's slot

**The pivot sits one sheet thickness above the mounting face**, which is where
`asm/stock.py` always had it, and it is not a free choice: it is the only place
a butt hinge can fold.  Closed, the two leaves lie face to face, so the pin has
to be in the plane where they meet; open flat, that same plane is one thickness
above the face each leaf is screwed to.  Put the pin a barrel radius up instead
-- tangent to the leaf, which is the other thing a rolled sheet suggests -- and
the leaves foul each other at about 45 degrees off flat.  That was drawn and
measured before this was: 192 mm3 of the two solids in the same place.

So the barrel straddles the leaf rather than sitting on it, and stands
`knuckle_d/2 - thick` = **1 mm proud of the mounting face**.  There is room for
it: the pivot is over the seam between two 2020 members, and their corner
radii leave a groove there.

The notches are what a leaf needs to let the other one's knuckles through: at
the second and fourth station this one is cut square back to the barrel's own
radius.  Zero clearance, like every other fit here: two of these placed as a
hinge touch at every angle and overlap at none, checked in 30 degree steps from
flat open to shut.

### What is measured and what is not

Read off the photograph: that it is a plain steel butt hinge, black finished;
four knuckles; two screws to a leaf, socket head with a washer under each,
landing in T nuts in the extrusion's slot; and that it is surface mounted
across the two top faces rather than let in.

**Everything with a number on it is the ordinary 40 mm butt hinge
[`../ASSEMBLY.md`](../ASSEMBLY.md) already assumed, not a measurement of
Michael's.**  40 long, 20 to a leaf so it covers one 20 mm face exactly, and a
5 mm barrel.  The photograph agrees with those to about the 10 % it can be read
to, and no better.  Every one of them is a name below; measure the real hinge
and the numbers move together.

The sheet is **1.5 mm** rather than the 2 the stand-in used, because for a
rolled hinge the sheet, the barrel and the pin are one number in three guises:
`pin_d = knuckle_d - 2 thick`.  At 2 mm sheet a 5 mm barrel would leave a 1 mm
pin, which no 40 mm hinge has.  1.5 leaves 2 mm, which they do.

Not drawn: the countersink under each screw head, the peened ends of the pin,
and any clearance between the leaves -- the same bargain the rest of the bought
stock makes.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 40.0            # along the pivot
leaf = 20.0              # from the pivot, which is one 2020 face exactly
thick = 1.5              # the sheet; has to stay under the barrel's radius
knuckle_d = 5.0          # the barrel, over the outside
pin_d = knuckle_d - 2.0 * thick   # what is left inside a sheet rolled round

knuckles = 4             # in the barrel, two to a leaf; see the docstring

hole_d = 4.5             # M4 clearance
hole_pitch = 20.0        # between the two in a leaf


def moment(x, radius):
    """The area under a circle of `radius` from its centre out to `x`.

    `int sqrt(R^2 - x^2) dx`, which is what the plate and the barrel sharing
    material comes down to; see `leaf_volume`.
    """
    return 0.5 * (x * math.sqrt(radius ** 2 - x ** 2)
                  + radius ** 2 * math.asin(x / radius))


def leaf_volume():
    """What the leaf comes to, from the same numbers the sketches use.

    Four terms and two corrections.  The plate less its notches, plus the two
    barrels -- and then **the barrels and the plate overlap**, because the
    plate runs in to the pivot rather than stopping at the tangent point, which
    is what a rolled sheet does where it meets itself.  That shared sliver is
    the strip of the barrel's circle between the plate's two faces, one station
    long, and it would otherwise be counted twice.  The pin's bore only ever
    meets material inside this leaf's own knuckles: at the other two stations
    the notch has already taken the plate back well past it.
    """
    radius, station = knuckle_d / 2.0, length / knuckles
    mine = knuckles // 2                   # knuckles on this leaf

    plate = leaf * length * thick
    notches = mine * radius * thick * station
    barrel = math.pi * radius ** 2 * station * mine
    shared = moment(thick, radius) * station * mine
    pin = math.pi * (pin_d / 2.0) ** 2 * station * mine
    screws = 2.0 * math.pi / 4.0 * hole_d ** 2 * thick
    return plate - notches + barrel - shared - pin - screws


def hinge_leaf(doc):
    """The leaf, its pivot on the origin and running up +Z."""
    bdy = fcprim.body(doc, "HINGE_40_LEAF")
    radius, station = knuckle_d / 2.0, length / knuckles

    # Drawn looking down the pivot: H is Y, V is Z, and the pad runs along +X,
    # from the plate's inner face out to the barrel's tangent.
    plate = fcprim.sketch(bdy, "Plate", "YZ_Plane", offset=-thick)
    fcprim.polyline(plate, [
        (0.0, 0.0), (leaf, 0.0), (leaf, length), (0.0, length),
    ], name="plate")
    fcprim.pad(bdy, "Plate", plate, thick)

    # Where the other leaf's knuckles go, this one is cut back to the barrel.
    # Square rather than round: it clears a cylinder either way, and it is what
    # the real one looks like.
    notches = fcprim.sketch(bdy, "Notches", "YZ_Plane", offset=-thick)
    for station_i in range(1, knuckles, 2):
        low, high = station_i * station, (station_i + 1) * station
        fcprim.polyline(notches, [
            (0.0, low), (radius, low), (radius, high), (0.0, high),
        ], name=f"notch{station_i}")
    fcprim.pocket(bdy, "Notches", notches, thick, reversed_=True)

    # One barrel at the first station, then the same again at the third.
    barrel = fcprim.sketch(bdy, "Knuckle", "XY_Plane")
    fcprim.circle(barrel, (0.0, 0.0), knuckle_d, name="knuckle")
    first = fcprim.pad(bdy, "Knuckle", barrel, station)
    fcprim.linear_pattern(bdy, "Knuckles", [first], knuckles // 2, 2 * station)

    # The pin, through everything; see `leaf_volume` for why that is only the
    # knuckles.
    pin = fcprim.sketch(bdy, "Pin", "XY_Plane")
    fcprim.circle(pin, (0.0, 0.0), pin_d, name="pin")
    fcprim.pocket(bdy, "Pin", pin, midplane=True)

    # The two screws, on the middle of the leaf, which is where the extrusion's
    # own slot runs once the pivot is over the seam between the two members.
    screws = fcprim.sketch(bdy, "Screws", "YZ_Plane", offset=-thick)
    for i, at in enumerate(((length - hole_pitch) / 2.0,
                            (length + hole_pitch) / 2.0)):
        fcprim.circle(screws, (leaf / 2.0, at), hole_d, name=f"screw{i + 1}")
    fcprim.pocket(bdy, "Screws", screws, thick, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `PIVOT` is the hinge
    # axis at mid length, which is what a `Revolute` joint turns about and what
    # the second leaf is rotated 180 degrees about X through.  `MOUNT` is on
    # the face that lies on the extrusion, pointing into it, and the two screws
    # are on the same face where the T nuts take them.
    fcprim.lcs(bdy, "PIVOT", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "MOUNT", at=(-thick, leaf / 2.0, length / 2.0),
               axis=(-1, 0, 0))
    for i, at in enumerate(((length - hole_pitch) / 2.0,
                            (length + hole_pitch) / 2.0)):
        fcprim.lcs(bdy, f"SCREW{i + 1}", at=(-thick, leaf / 2.0, at),
                   axis=(-1, 0, 0))

    # What the assembly joins to, on top of those.  `BORE`1 and 2 are on the
    # pivot where this leaf's two knuckles end -- the seam a knuckle of the
    # other leaf butts into -- and `BRACKET`1 and 2 are the two far corners of
    # the face that lies on the member, where the corner gussets come up
    # against it.  `FRAME2` is the middle of the leaf's outer edge, which is
    # the plate seen end on, so it is half the sheet's thickness in.
    for i in range(knuckles // 2):
        fcprim.lcs(bdy, f"BORE{i + 1}", at=(0.0, 0.0, (2 * i + 1) * station),
                   axis=(0, 0, 1))
    for i, at in enumerate((0.0, length)):
        fcprim.lcs(bdy, f"BRACKET{i + 1}", at=(-thick, leaf, at),
                   axis=(1, 0, 0), roll=180.0)
    fcprim.lcs(bdy, "FRAME2", at=(-thick / 2.0, leaf, length / 2.0),
               axis=(0, -1, 0), roll=90.0)

    # Three more the assembly measured on a *face* rather than on anything
    # drawn, and a face's own frame sits at its centre of area: the plate is
    # notched, so that centre is not the middle of the leaf and the numbers
    # below are not dimensions of anything.  They are kept as measured, because
    # the assembly is held against the machine Michael built and moving them
    # would move what hangs off them.  See ASSEMBLY_SCRIPT.md, step 6.
    fcprim.lcs(bdy, "FACE1", at=(0.0, 11.3095, length / 2.0),
               axis=(1, 0, 0), roll=180.0)
    fcprim.lcs(bdy, "FACE2", at=(0.0, 12.25, station), axis=(1, 0, 0),
               roll=180.0)
    fcprim.lcs(bdy, "FRAME1", at=(-thick, 11.1759, 19.9263), axis=(1, 0, 0),
               roll=180.0)
    return bdy


fcprim.make(__file__, "HINGE_40_LEAF", hinge_leaf, leaf_volume(),
            made_of=fcprim.STEEL)
