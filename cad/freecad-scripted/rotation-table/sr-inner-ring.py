"""SR_INNER_RING - the fixed inner race of the slewing ring.

Reconstructed from the original author's SR_INNER_RING.stl, in that mesh's own
coordinates: the machine's largest ring at 140 mm across, spanning Y = -2 .. 8.

It is a plain turned ring with one step in its bore: 132 mm for the first 5 mm
and 136 mm above that, so the balls run on the shoulder the step leaves.

    Section  sketch -> Revolution  the whole ring, swept about Y
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

outer_d = 140.0
bottom_y = -2.0
top_y = 8.0

lower_bore_d = 132.0
upper_bore_d = 136.0
step_y = 3.0             # where the bore opens out

mesh_volume = 12886.514


def sr_inner_ring(doc):
    bdy = fcprim.body(doc, "SR_INNER_RING")

    # Half a section through the ring; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (lower_bore_d / 2, bottom_y),
        (outer_d / 2, bottom_y),
        (outer_d / 2, top_y),
        (upper_bore_d / 2, top_y),
        (upper_bore_d / 2, step_y),
        (lower_bore_d / 2, step_y),
    ], name="section")
    fcprim.revolution(bdy, "Turned ring", section, axis="V_Axis")

    # Mounting datums for the assembly; see fcprim.lcs.  The ring is turned, so
    # every one of them is on its axis and what tells them apart is the height:
    # the two ends, the step the bore opens out at -- which is what the ball
    # bearing drops onto -- and the middle of the upper bore, which is the face
    # the bearing plate is a fit in and so where that face's own frame sits.
    fcprim.lcs(bdy, "STUD", at=(0.0, bottom_y, 0.0), axis=(0, 1, 0))
    fcprim.lcs(bdy, "BEARING", at=(0.0, step_y, 0.0), axis=(0, 1, 0))
    fcprim.lcs(bdy, "PLATE", at=(0.0, (step_y + top_y) / 2.0, 0.0),
               axis=(0, 1, 0))
    fcprim.lcs(bdy, "RING", at=(0.0, top_y, 0.0), axis=(0, 1, 0))

    return bdy


fcprim.make(__file__, "SR_INNER_RING", sr_inner_ring, mesh_volume)
