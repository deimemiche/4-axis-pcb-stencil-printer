"""STENCIL_HOLDER_BACK_2 - the shorter angle that closes the back of the clamp.

A 20 x 20 x 2 aluminium angle, 198 mm long, drawn from
`technical-drawings/stencil-holder-bottom.pdf`, which is titled TOP_FRAME like
the other sheet and named "bottom" in the repository, and is neither: it draws
the clamp's *short* angle, the one that pinches the foil against a long bar.

    Section  sketch -> Pad     the angle, run along X
    Face     sketch -> Pocket  4 x  3.4, through the horizontal leg

There are two of these short angles and they follow the long bars they close
on: this one and `STENCIL_HOLDER_BACK` are plain, while
`stencil-holder-front-2.py` and `STENCIL_HOLDER_FRONT` both carry a 5.4 through
the upright at the middle of the bar.

    length     198, against the long bars' 213.72 -- the short angle carries no
               bearing mount, so it stops short of their +-106.86
    face holes +-25 and +-75, which is where the long bars' row of four is

Those agreements are why this sheet is read as the clamp's other angle rather
than as a bar of its own: every hole in it lands on a hole already in the
machine.

**Part measured, part still off the sheet.**  Unlike the two long bars, whose
figures came off the built machine, this one started as the sheet drew it.  Two
of its figures disagreed with the long bars and Michael has settled both:

    diameters       the sheet's 4 x  5 are **3.4 M3 clearance**, as every hole
                    in both long bars is; the 5.4 in the front hand stands
    row across leg  the sheet's 10, i.e. the leg's centre line, stands, against
                    the long bars' 12 from the free edge -- so the two legs do
                    not sit with their free edges flush.  He is checking it
                    against the machine.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 198.0           # along X
leg = 20.0
wall = 2.0

face_d = 3.4             # M3 clearance, through the horizontal leg
face_x = (-75.0, -25.0, 25.0, 75.0)
face_from_edge = 10.0    # from the leg's free edge, i.e. its centre line


def expected_volume():
    section = leg * wall * 2 - wall * wall
    return (section * length
            - len(face_x) * math.pi * (face_d / 2.0) ** 2 * wall)


def angle(doc, name, middle=None):
    """The short bar.  `middle` drills one more hole through the upright at
    x = 0, as (diameter, distance down from the top of the upright)."""
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
    for i, x in enumerate(face_x):
        fcprim.circle(face, (x, leg - face_from_edge), face_d, name=f"face{i}")
    fcprim.pocket(bdy, "Face holes", face, midplane=True)

    # Through the upright, so drilled along Y: H is +X, V is +Z.
    if middle:
        diameter, from_edge = middle
        edge = fcprim.sketch(bdy, "Edge hole", "XZ_Plane")
        fcprim.circle(edge, (0.0, leg - from_edge), diameter, name="middle")
        fcprim.pocket(bdy, "Edge hole", edge, midplane=True)

    return bdy


def stencil_holder_back_2(doc):
    return angle(doc, "STENCIL_HOLDER_BACK_2")


# Set by stencil-holder-front-2.py, which runs this file for `angle` and builds
# the bar with the middle hole itself.
if not globals().get("as_library"):
    fcprim.make(__file__, "STENCIL_HOLDER_BACK_2", stencil_holder_back_2,
                expected_volume(), made_of=fcprim.ALUMINIUM)
