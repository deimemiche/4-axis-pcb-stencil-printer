"""ADAPTER_D5_TO_M3 - bushing that lets an M3 screw carry a 5 mm bore.

That is the way round the name reads: **D5 to M3**, a 5 mm outside over an M3
inside.  It goes on the alpha axis, one per bearing, four in all.  The spigot
fills the 5 mm bore of a `BEARING_14X5X5`, the collar clamps that bearing's
inner ring, and the M3 screw runs through the middle of both and into
`SR_BEARING_PLATE`, whose four 3.4 mm holes sit on a 61 mm radius -- which is
where the count of four comes from.  The collar is 6.4 across for the same
reason: wider than the 5 mm bore so it has something to clamp, and narrow
enough to keep clear of the ring that has to turn.

Reconstructed from the original author's ADAPTER_D5_TO_M3.stl, in that mesh's
own coordinates: the smallest part in the machine, 52 mm3, spanning Y = 0 .. 3.5.

A 6.4 mm collar sits under a 5 mm spigot, bored 3.2 mm the whole way through.
The spigot's free end is chamfered 0.4 mm at 45 degrees so it starts into its
hole.  All of it is turned, so it is drawn once in section and swept.

    Section  sketch -> Revolution  the whole part, swept about Y

The reconstruction is exact: `verify.py` classifies 20000 random points against
both shapes and finds no disagreement at all, and the solid is 51.919 mm3
against the mesh's 51.912, which is the mesh's own faceting.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

collar_d = 6.4
collar_height = 1.0

spigot_d = 5.0           # the bearing bore it fills
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
