"""STENCIL_HOLDER_BACK - the back L profile of the stencil clamp.

A 20 x 20 x 2 aluminium angle, 213.72 mm long.  `stencil-holder-front.py` is
the other one and is the same bar with one hole more; the drawings call the
pair BOT and TOP, which is not where they sit - both lie flat in the top frame,
one behind the other.

    Section  sketch -> Pad     the angle, run along X
    Face     sketch -> Pocket  the row of four, plus the mount's pair at each
                               end, through the horizontal leg
    Edge     sketch -> Pocket  the mount's third bolt at each end, through the
                               upright

**The figures here are Michael's, measured off the built machine.**
`technical-drawings/stencil-holder-top.pdf` is titled TOP_FRAME and does
describe a 213.72 angle, but it is not a description of this part: it draws a
row of six rather than four, dimensions holes the sheets never drill, and gives
5 and 5.4 where every hole in the bar is 3.4 M3 clearance.  Do not "correct"
anything below against that sheet.

Across the legs a hole is dimensioned from the **free edge of the leg it is
in**, so `row_from_edge` and the rest are subtracted from `leg`.  The three at
each end bolt to a `TOP_CLAMP_BEARING_MOUNT_1` / `_2`, and that part is what
confirms them: its two cross bolts sit at -3.6 and 5.6 with the horizontal
leg's free edge at 10, which is 13.6 and 4.4 from that edge, and its bolt along
the rod sits at 6.1385 with the upright's free edge at 10.5, which is 4.3615
down from the top of the upright.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 213.72          # along X
leg = 20.0
wall = 2.0

hole_d = 3.4             # M3 clearance, which every hole in this bar is

row_x = (-75.0, -25.0, 25.0, 75.0)
row_from_edge = 12.0     # from the horizontal leg's free edge

mount_x = (-103.11, 103.11)
mount_from_edge = (13.6, 4.4)   # the mount's cross bolts, through the leg
mount_edge_from_edge = 4.36     # its bolt along the rod, through the upright


def expected_volume():
    holes = len(row_x) + len(mount_x) * (len(mount_from_edge) + 1)
    section = leg * wall * 2 - wall * wall
    return section * length - holes * math.pi * (hole_d / 2.0) ** 2 * wall


def angle(doc, name, middle=None):
    """The bar.  `middle` drills one more hole through the upright at x = 0,
    as (diameter, distance down from the top of the upright)."""
    bdy = fcprim.body(doc, name)

    # Drawn in section: H is +Y, V is +Z, and the pad runs along X.
    section = fcprim.sketch(bdy, "Section", "YZ_Plane")
    fcprim.polyline(section, [
        (0.0, 0.0),
        (leg, 0.0),
        (leg, wall),
        (wall, wall),
        (wall, leg),
        (0.0, leg),
    ], name="angle")
    fcprim.pad(bdy, "Angle", section, length, midplane=True)

    # Through the horizontal leg, so drilled down Z: H is +X, V is +Y.
    face = fcprim.sketch(bdy, "Face holes", "XY_Plane")
    for i, x in enumerate(row_x):
        fcprim.circle(face, (x, leg - row_from_edge), hole_d, name=f"row{i}")
    for i, x in enumerate(mount_x):
        for j, from_edge in enumerate(mount_from_edge):
            fcprim.circle(face, (x, leg - from_edge), hole_d,
                          name=f"mount{i}{j}")
    fcprim.pocket(bdy, "Face holes", face, midplane=True)

    # Through the upright, so drilled along Y: H is +X, V is +Z.
    edge = fcprim.sketch(bdy, "Edge holes", "XZ_Plane")
    for i, x in enumerate(mount_x):
        fcprim.circle(edge, (x, leg - mount_edge_from_edge), hole_d,
                      name=f"mountedge{i}")
    if middle:
        diameter, from_edge = middle
        fcprim.circle(edge, (0.0, leg - from_edge), diameter, name="middle")
    fcprim.pocket(bdy, "Edge holes", edge, midplane=True)

    return bdy


def stencil_holder_back(doc):
    return angle(doc, "STENCIL_HOLDER_BACK")


# Set by stencil-holder-front.py, which runs this file for `angle` and builds
# the bar with the middle hole itself.
if not globals().get("as_library"):
    fcprim.make(__file__, "STENCIL_HOLDER_BACK", stencil_holder_back,
                expected_volume(), made_of=fcprim.ALUMINIUM)
