"""TOP_SPRING_PLATE - seat the stencil clamp's spring bears on.

Reconstructed from the original author's TOP_SPRING_PLATE.stl, in that mesh's
own coordinates: a small turned washer spanning Y = 0 .. 4.4, 19.4 mm across
its widest.

Everything about it is a body of revolution, so it is drawn once in section
and swept: a flat 19.4 mm brim under a cone that tapers away at 45 degrees,
bored 9 mm at the bottom and opened out to 13 mm above the shoulder the spring
sits on.

    Section  sketch -> Revolution  the whole part, swept about Y
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

brim_d = 19.4            # widest, at the bottom
brim_height = 2.4
top_d = 15.4             # the cone tapers to this
total_height = 4.4

rod_clear_d = 9.0        # below the shoulder
spring_bore_d = 13.0     # above it, where the spring sits

mesh_volume = 768.864


def top_spring_plate(doc):
    bdy = fcprim.body(doc, "TOP_SPRING_PLATE")

    # Half a section through the part; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (rod_clear_d / 2, 0.0),
        (brim_d / 2, 0.0),
        (brim_d / 2, brim_height),
        (top_d / 2, total_height),
        (spring_bore_d / 2, total_height),
        (spring_bore_d / 2, brim_height),
        (rod_clear_d / 2, brim_height),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    # Mounting datums for the assembly; see fcprim.lcs.  The plate is turned,
    # so both are on its axis: the brim's underside, which lands on the clamp
    # bearing mount, and the shoulder inside it that the spring stands on.
    fcprim.lcs(bdy, "BEARING_MOUNT", axis=(0, -1, 0), roll=180.0)
    fcprim.lcs(bdy, "SPRING", at=(0.0, brim_height, 0.0), axis=(0, 1, 0))

    return bdy


fcprim.make(__file__, "TOP_SPRING_PLATE", top_spring_plate, mesh_volume)
