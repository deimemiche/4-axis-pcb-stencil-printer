"""STAND - foot the machine rests on.

Reconstructed from the original author's STAND.stl, in that mesh's own
coordinates: a small turned foot spanning Y = 0 .. 7, 11.5 mm across the base.

Like the spring plate it is all turned, so it is drawn once in section and
swept.  The base flange is bored 4.5 mm for the bolt that holds it on; above
the flange the wall tapers gently inwards and the bore opens out to 7 mm, which
leaves room for the bolt head.

    Section  sketch -> Revolution  the whole part, swept about Y
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

base_d = 11.5
base_height = 1.0
top_d = 9.4              # the taper closes to this
total_height = 7.0

bolt_hole_d = 4.5        # M4 clearance, through the base
head_bore_d = 7.0        # above the base, clearing the bolt head

mesh_volume = 373.371


def stand(doc):
    bdy = fcprim.body(doc, "STAND")

    # Half a section through the foot; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (bolt_hole_d / 2, 0.0),
        (base_d / 2, 0.0),
        (base_d / 2, base_height),
        (top_d / 2, total_height),
        (head_bore_d / 2, total_height),
        (head_bore_d / 2, base_height),
        (bolt_hole_d / 2, base_height),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    return bdy


fcprim.make(__file__, "STAND", stand, mesh_volume)
