"""ALPHA_BOT_PLATE - the fixed plate the slewing ring turns on.

Drawn from `technical-drawings/bottom-plate.pdf`, whose title block calls it
RAHMEN_BOTTOM_BOT_ALU_PLATE_XY_AXIS: 200 x 200 x 6, which is the "aluminium
plate 200 x 200 x 6" the build page lists under the alpha axis.

What the plate carries:

* **4 x M3 on a 122 mm bolt circle**, at 0, 90, 180 and 270 degrees.  The
  circle is drawn dashed and labelled  122; it is a bolt circle rather than a
  bore, which the four holes sitting exactly on it settle.
* **5 x 10 mm on a 150.9 mm bolt circle**, at 0 and +-72 and +-144 degrees.
  The drawing has only the one of them that lies on the centre line, at
  x = 75.45: that radius is where the worm meets the ring gear, and 10 mm is
  the worm's own diameter, so on the drawing it is the worm's clearance
  through the plate.  Michael's plate has all five, and the other four are the
  **worm gear's mounting**.  They sit at the same five stations as
  `ALPHA_TOP_PLATE`'s ring screws and `SR_OUTER_RING_W_GEAR`'s five bosses,
  and the ring hangs under the turning plate with its counterbores facing
  down, so its five M3 go in from below - through here.  The five are drawn
  as a bolt circle proper: a construction pentagon inscribed in a construction
  circle, one hole on each corner, so the sketch says how they are spaced
  instead of just landing them there.
* **M3 clusters** in two families.  Both are mirrored top to bottom, but only
  the *inner* family is mirrored left to right as well -- the corner family
  exists on the left of the plate only, which is worth knowing before anyone
  wonders whether the drawing is symmetric.  It is not.

    Outline    sketch -> Pad     the plate
    Ring bolts sketch -> Pocket  4 x M3 on the bolt circle
    Worm       sketch -> Pocket  5 x 10 mm on the 75.45 circle
    Mounting   sketch -> Pocket  the M3 clusters

M3 holes are drawn at the tapping drill, 2.5 mm, because the drawing calls
them threads rather than clearance.  What the assembly checks is where they
are, not how wide.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

side = 200.0
thickness = 6.0

m3_tap_d = 2.5           # M3 tapping drill; the drawing says "M3", not a size
bolt_circle_d = 122.0    # the 4 x M3 that hold the ring down
worm_d = 10.0
worm_r = 75.45           # where the worm meets the ring gear, and the
worm_count = 5           # ring's own screw circle, so five of them

corner_x = (-93.7, -73.4)          # left hand side only
corner_z = (84.0, 96.0)
inner_x = (53.0, 82.0)             # both sides
inner_z = (52.0, 70.0)


# Which four of the sixteen inner holes carry the Y axis bearing mounts, and
# what the assembly calls each.  They are not a symmetric four: the mounts run
# in pairs along Z and the drawing offers two holes for each end of a pair, so
# the machine uses one from each corner cluster.  The names are the plan's own,
# numbered along the plate.
bearing_mount_at = ((-inner_x[1], inner_z[1]), (-inner_x[0], -inner_z[0]),
                    (inner_x[0], inner_z[1]), (inner_x[1], -inner_z[0]))
bearing_mount_labels = ("BEARING_MOUNT_Y1", "BEARING_MOUNT_Y2",
                        "BEARING_MOUNT_Y3", "BEARING_MOUNT_Y_AXIS")


def ring_bolts():
    r = bolt_circle_d / 2.0
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
            for a in (0, 90, 180, 270)]


def mounting():
    """The two families of M3, mirrored as the drawing shows them."""
    out = [(x, sz * z) for x in corner_x for z in corner_z for sz in (-1, 1)]
    out += [(sx * x, sz * z) for x in inner_x for z in inner_z
            for sx in (-1, 1) for sz in (-1, 1)]
    return out


def expected_volume():
    plain = side * side * thickness
    m3 = len(ring_bolts()) + len(mounting())
    plain -= m3 * math.pi * (m3_tap_d / 2.0) ** 2 * thickness
    plain -= worm_count * math.pi * (worm_d / 2.0) ** 2 * thickness
    return plain


def plate(doc):
    bdy = fcprim.body(doc, "ALPHA_BOT_PLATE")

    outline = fcprim.sketch(bdy, "Outline", "XZ_Plane")
    fcprim.polyline(outline, [
        (-side / 2, -side / 2),
        (side / 2, -side / 2),
        (side / 2, side / 2),
        (-side / 2, side / 2),
    ], name="plate")
    fcprim.pad(bdy, "Plate", outline, thickness, reversed_=True)

    ring = fcprim.sketch(bdy, "Ring bolts", "XZ_Plane")
    for i, (x, z) in enumerate(ring_bolts()):
        fcprim.circle(ring, (x, z), m3_tap_d, name=f"ring{i}")
    fcprim.pocket(bdy, "Ring bolts", ring, midplane=True)

    worm = fcprim.sketch(bdy, "Worm", "XZ_Plane")
    fcprim.bolt_circle(worm, (0.0, 0.0), worm_r, worm_d, worm_count,
                       name="worm")
    fcprim.pocket(bdy, "Worm clearance", worm, midplane=True)

    mount = fcprim.sketch(bdy, "Mounting", "XZ_Plane")
    for i, (x, z) in enumerate(mounting()):
        fcprim.circle(mount, (x, z), m3_tap_d, name=f"mount{i}")
    fcprim.pocket(bdy, "Mounting holes", mount, midplane=True)

    # Mounting datums for the assembly; see fcprim.lcs.  Every one of them is
    # one of the holes above, on one face of the plate or the other -- the
    # plate is 200 square and drilled, and nothing else about it is a mounting
    # feature.  The four Y bearing mounts hang under it, so theirs are on the
    # underside; the ring, the two alpha rod holders and the plate itself sit
    # on top, so theirs are at `thickness`.
    for (x, z), label in zip(bearing_mount_at, bearing_mount_labels):
        fcprim.lcs(bdy, label, at=(x, 0.0, z), axis=(0, -1, 0))
    fcprim.lcs(bdy, "PLATE", at=(0.0, thickness, bolt_circle_d / 2.0),
               axis=(0, -1, 0))
    for z, label in ((-corner_z[1], "ROD_HOLDER_ALPHA"),
                     (corner_z[1], "ROD_HOLDER_ALPHA_AXIS")):
        fcprim.lcs(bdy, label, at=(corner_x[0], thickness, z), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "ALPHA_BOT_PLATE", plate, expected_volume(),
            made_of=fcprim.ALUMINIUM)
