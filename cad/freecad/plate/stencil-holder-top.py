"""STENCIL_HOLDER_TOP - the upper L profile of the stencil frame.

Drawn from `technical-drawings/stencil-holder-top.pdf`, also titled TOP_FRAME:
the same 20 x 20 x 2 angle as `stencil-holder-bot.py`, 213.72 mm long rather
than 198.

    Section  sketch -> Pad     the angle, run along X
    Face     sketch -> Pocket  the row along the horizontal leg, plus a second
                               hole at each end
    Edge     sketch -> Pocket  one through the upright at each end

The odd 213.72 length is not arbitrary: the end holes are dimensioned 103.11
from the middle and 3.75 from the end, and 103.11 + 3.75 is half of 213.72, so
the length follows from where the end holes had to go.

**Read with care.**  This drawing dimensions its holes across the legs from the
*inner* face of the opposite leg rather than from an outer edge, which is the
opposite convention to the lower profile, and the two views show different legs
at the same station.  The along-the-length positions (+-25, +-75, +-103.11) and
the section are certain; the across-the-leg positions below are the best
reading of the drawing and are the thing to check first if this part ever comes
out looking wrong.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 213.72          # along X
leg = 20.0
wall = 2.0

face_d = 5.0
face_x = (-103.11, -75.0, -25.0, 25.0, 75.0, 103.11)
face_from_inner = 4.4    # from the inner face of the upright

end_x = (-103.11, 103.11)
end_from_inner = 13.6    # the second hole at each end

edge_d = 5.4
edge_x = (-103.11, 103.11)
edge_from_inner = 4.36


def expected_volume():
    section = leg * wall * 2 - wall * wall
    solid = section * length
    holes = len(face_x) + len(end_x)
    solid -= holes * math.pi * (face_d / 2.0) ** 2 * wall
    solid -= len(edge_x) * math.pi * (edge_d / 2.0) ** 2 * wall
    return solid


def profile(doc):
    bdy = fcprim.body(doc, "STENCIL_HOLDER_TOP")

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

    face = fcprim.sketch(bdy, "Face holes", "XY_Plane")
    for i, x in enumerate(face_x):
        fcprim.circle(face, (x, wall + face_from_inner), face_d,
                      name=f"face{i}")
    for i, x in enumerate(end_x):
        fcprim.circle(face, (x, wall + end_from_inner), face_d, name=f"end{i}")
    fcprim.pocket(bdy, "Face holes", face, midplane=True)

    edge = fcprim.sketch(bdy, "Edge holes", "XZ_Plane")
    for i, x in enumerate(edge_x):
        fcprim.circle(edge, (x, wall + edge_from_inner), edge_d,
                      name=f"edge{i}")
    fcprim.pocket(bdy, "Edge holes", edge, midplane=True)

    return bdy


fcprim.make(__file__, "STENCIL_HOLDER_TOP", profile, expected_volume())
