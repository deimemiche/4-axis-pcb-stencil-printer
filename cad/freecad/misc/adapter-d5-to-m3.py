"""ADAPTER_D5_TO_M3 - bushing that takes a 5 mm shaft into an M3 fitting.

Reconstructed from the original author's ADAPTER_D5_TO_M3.stl, in that mesh's
own coordinates: the smallest part in the machine, 52 mm3, spanning Y = 0 .. 3.5.

A 6.4 mm collar sits under a 5 mm spigot, bored 3.2 mm the whole way through.
The spigot's free end is chamfered 0.4 mm at 45 degrees so it starts into its
hole.  All of it is turned, so it is drawn once in section and swept.

    Section  sketch -> Revolution  the whole part, swept about Y
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

collar_d = 6.4
collar_height = 1.0

spigot_d = 5.0           # the 5 mm shaft this stands in for
total_height = 3.5
chamfer = 0.4            # 45 degrees off the spigot's free end

bore_d = 3.2

mesh_volume = 51.912


def adapter_d5_to_m3(doc):
    bdy = fcprim.body(doc, "ADAPTER_D5_TO_M3")

    # Half a section through the bushing; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (bore_d / 2, 0.0),
        (collar_d / 2, 0.0),
        (collar_d / 2, collar_height),
        (spigot_d / 2, collar_height),
        (spigot_d / 2, total_height - chamfer),
        (spigot_d / 2 - chamfer, total_height),
        (bore_d / 2, total_height),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    return bdy


fcprim.make(__file__, "ADAPTER_D5_TO_M3", adapter_d5_to_m3, mesh_volume)
