"""STENCIL_HOLDER_BOT - the lower L profile of the stencil frame.

Drawn from `technical-drawings/stencil-holder-bottom.pdf`, titled TOP_FRAME:
a 20 x 20 x 2 aluminium angle, 198 mm long.  This is one of the "L profile"
items the build page lists under the top frame.

    Section  sketch -> Pad     the angle, run along X
    Face     sketch -> Pocket  4 x  5, through the horizontal leg
    Edge     sketch -> Pocket  1 x  5.4, through the upright

The two legs are dimensioned from opposite edges on the drawing, which is easy
to misread: the four  5 sit 10 mm from the *outer* edge of their leg, so they
land on its centre line, while the single  5.4 sits 8.5 mm from the outer edge
of the upright and is therefore off centre.

The profile is modelled with its corner on the origin and its length centred
on X, so the four holes come out at +-25 and +-75 as the drawing dimensions
them from the middle.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 198.0           # along X
leg = 20.0
wall = 2.0

face_d = 5.0             # through the horizontal leg
face_x = (-75.0, -25.0, 25.0, 75.0)
face_from_edge = 10.0    # from the leg's outer edge, i.e. its centre line

edge_d = 5.4             # through the upright
edge_from_edge = 8.5     # from the upright's outer edge -- not its centre


def expected_volume():
    section = leg * wall * 2 - wall * wall
    solid = section * length
    solid -= len(face_x) * math.pi * (face_d / 2.0) ** 2 * wall
    solid -= math.pi * (edge_d / 2.0) ** 2 * wall
    return solid


def profile(doc):
    bdy = fcprim.body(doc, "STENCIL_HOLDER_BOT")

    # The angle, drawn in section: H is +Y, V is +Z, and the pad runs along X.
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
    edge = fcprim.sketch(bdy, "Edge hole", "XZ_Plane")
    fcprim.circle(edge, (0.0, leg - edge_from_edge), edge_d, name="edge")
    fcprim.pocket(bdy, "Edge hole", edge, midplane=True)

    return bdy


fcprim.make(__file__, "STENCIL_HOLDER_BOT", profile, expected_volume())
