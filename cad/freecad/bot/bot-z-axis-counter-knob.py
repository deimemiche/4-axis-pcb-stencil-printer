"""BOT_Z_AXIS_COUNTER_KNOB - the knob on the Z axis counter screw.

Reconstructed from the original author's BOT_Z_AXIS_COUNTER_KNOB.stl, in that
mesh's own coordinates: Y = 0 .. 17, turned about Y.

A 24 mm barrel with nine 5 mm flutes round it to grip by, bored 8 mm nearly all
the way through, and a small tapered spigot on top.

Both ends are broken 1 mm, and the break follows the whole silhouette - round the
flutes as well as the barrel - so it is a chamfer on the rim rather than anything
the section could carry.

    Section  sketch -> Revolution    the barrel, its bore and the spigot
    Flute    sketch -> Pocket        one grip flute
                    -> PolarPattern  the other eight
    Rims             Chamfer         1 mm round both ends
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

barrel_d = 24.0
barrel_y = (0.0, 15.0)
edge_break = 1.0         # 45 degrees off both ends

bore_d = 8.0
bore_floor = 14.0        # the bore stops here

spigot_y = 17.0
spigot_d = (5.0, 4.6536)  # it tapers slightly

flutes = 9
flute_d = 5.0            # cut on the barrel's own diameter

mesh_volume = 4761.615


def bot_z_axis_counter_knob(doc):
    bdy = fcprim.body(doc, "BOT_Z_AXIS_COUNTER_KNOB")
    barrel_r = barrel_d / 2

    # Half a section through the knob; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (bore_d / 2, barrel_y[0]),
        (barrel_r, barrel_y[0]),
        (barrel_r, barrel_y[1]),
        (spigot_d[0] / 2, barrel_y[1]),
        (spigot_d[1] / 2, spigot_y),
        (0.0, spigot_y),
        (0.0, bore_floor),
        (bore_d / 2, bore_floor),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    # One flute, cut on the barrel's own diameter so it bites 0.26 mm in, then
    # repeated round.
    flute = fcprim.sketch(bdy, "Flute", "XZ_Plane", offset=-spigot_y)
    fcprim.circle(flute, (0.0, -barrel_r), flute_d, name="flute")
    cut = fcprim.pocket(bdy, "Flute", flute, spigot_y, reversed_=True)
    fcprim.polar_pattern(bdy, "Grip", [cut], flutes, axis="Y_Axis")

    # The break round both ends, taken after the flutes so that it follows them.
    def rim(edge):
        point = fcprim.midpoint(edge)
        if min(abs(point.y - end) for end in barrel_y) > 1e-6:
            return False
        return math.hypot(point.x, point.z) > bore_d   # not bore or spigot

    fcprim.chamfer(bdy, "Rims", edge_break, rim)

    return bdy


fcprim.make(__file__, "BOT_Z_AXIS_COUNTER_KNOB", bot_z_axis_counter_knob,
            mesh_volume)
