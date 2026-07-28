"""XY_PLATE - the print plate the boards sit on, carried by the X/Y carriage.

Drawn from the author's own 2D drawing, `technical-drawings/base-plate.dxf`,
which is dimensioned 257 x 162 x 2 and carries sixteen 3.2 mm holes.  This is
the plate the build page lists as "aluminium plate 257 x 162", so the drawing
and the build page agree.

Unlike everything in `bot/`, `sr/`, `top/` and `eccf/` this is not a
reconstruction of a mesh -- there is no STL for it, because it is not printed.
The drawing is the source, and the volume check below is arithmetic on the
drawing's own numbers rather than a measurement of somebody else's mesh.

The holes are the four corners of a rectangle repeated in both directions:
x = +-97.65 and +-124.35, z = +-59 and +-76, all sixteen combinations.

    Outline   sketch -> Pad     the plate
    Holes     sketch -> Pocket  16 x 3.2 mm, through

The plate lies in XZ with its thickness up the machine's Y, which is how every
plate in this machine is modelled -- `SR_BEARING_PLATE` is the same way round.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 257.0           # along X
width = 162.0            # along Z
thickness = 2.0

hole_d = 3.2
hole_x = (97.65, 124.35)
hole_z = (59.0, 76.0)


def holes():
    """Every hole centre, all four quadrants."""
    return [(sx * x, sz * z)
            for x in hole_x for z in hole_z
            for sx in (-1, 1) for sz in (-1, 1)]


def expected_volume():
    plain = length * width * thickness
    bored = len(holes()) * math.pi * (hole_d / 2.0) ** 2 * thickness
    return plain - bored


def plate(doc):
    bdy = fcprim.body(doc, "XY_PLATE")

    outline = fcprim.sketch(bdy, "Outline", "XZ_Plane")
    fcprim.polyline(outline, [
        (-length / 2, -width / 2),
        (length / 2, -width / 2),
        (length / 2, width / 2),
        (-length / 2, width / 2),
    ], name="plate")
    fcprim.pad(bdy, "Plate", outline, thickness, reversed_=True)

    drilling = fcprim.sketch(bdy, "Holes", "XZ_Plane")
    for i, (x, z) in enumerate(holes()):
        fcprim.circle(drilling, (x, z), hole_d, name=f"hole{i}")
    fcprim.pocket(bdy, "Holes", drilling, midplane=True)

    return bdy


fcprim.make(__file__, "XY_PLATE", plate, expected_volume())
