"""ALPHA_TOP_PLATE_PLAIN - the alpha plate before the workholding grid.

`technical-drawings/top-plate-plain.dxf`: the same 240 x 200 x 6 outline and
the same five mounting holes as `alpha-top-plate.py`, without the 83 hole
grid.  The author drew both, so both are here; the machine uses the drilled
one, and this is what it is drilled from.

    Outline   sketch -> Pad     the plate
    Mounting  sketch -> Pocket  5 x M3 to the outer ring
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 240.0
width = 200.0
thickness = 6.0

mount_d = 3.5
mount_r = 75.45
mount_count = 5


def mounting():
    return [(mount_r * math.cos(math.radians(a)),
             mount_r * math.sin(math.radians(a)))
            for a in (i * 360.0 / mount_count for i in range(mount_count))]


def expected_volume():
    plain = length * width * thickness
    return plain - len(mounting()) * math.pi * (mount_d / 2.0) ** 2 * thickness


def plate(doc):
    bdy = fcprim.body(doc, "ALPHA_TOP_PLATE_PLAIN")

    outline = fcprim.sketch(bdy, "Outline", "XZ_Plane")
    fcprim.polyline(outline, [
        (-length / 2, -width / 2),
        (length / 2, -width / 2),
        (length / 2, width / 2),
        (-length / 2, width / 2),
    ], name="plate")
    fcprim.pad(bdy, "Plate", outline, thickness, reversed_=True)

    mount = fcprim.sketch(bdy, "Mounting", "XZ_Plane")
    for i, (x, z) in enumerate(mounting()):
        fcprim.circle(mount, (x, z), mount_d, name=f"mount{i}")
    fcprim.pocket(bdy, "Ring mounting", mount, midplane=True)

    return bdy


fcprim.make(__file__, "ALPHA_TOP_PLATE_PLAIN", plate, expected_volume(),
            made_of=fcprim.ALUMINIUM)
