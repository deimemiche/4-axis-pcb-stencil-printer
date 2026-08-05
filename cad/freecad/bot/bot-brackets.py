"""BOT_BRACKETS - corner gusset for the bottom frame.

Reconstructed from the original author's BOT_BRACKETS.stl, in that mesh's own
coordinates: a flat 60 x 60 plate 4 mm thick, sitting in the XZ plane between
Y = 0 and 4, that ties two extrusions together at a right angle.

The plate is an L, its inner corner swept out by a single 45 mm arc so the
gusset carries load without wasting material.  Five M4 clearance holes on a
10 mm grid bolt it down, three along one leg and three along the other, sharing
the hole in the corner.

    Outline  sketch -> Pad     the plate, arc and all
    Bolts    sketch -> Pocket  five M4 clearance holes, through
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

size = 60.0             # the plate is square before the corner is swept out
thickness = 4.0
leg_width = 20.0        # what is left of each leg beside the sweep
sweep_r = 22.5          # the arc taken out of the inner corner
sweep_from = 42.5       # where that arc meets each leg

bolt_hole_d = 4.5       # M4 clearance
bolt_pitch = 20.0       # matches the extrusion's own 20 mm grid
bolt_inset = 10.0       # from the outer faces
bolts_per_leg = 3

mesh_volume = 8117.645


def bot_brackets(doc):
    bdy = fcprim.body(doc, "BOT_BRACKETS")

    # Walked anticlockwise from the outer corner.  The negative radius on the
    # sixth segment puts the arc's centre on the outside of the walk, which is
    # what bites the corner out rather than bulging it.
    outline = fcprim.sketch(bdy, "Outline", "XZ_Plane", offset=-thickness)
    fcprim.polyline(outline, [
        (0.0, 0.0),
        (size, 0.0),
        (size, leg_width),
        (sweep_from, leg_width),
        (leg_width, sweep_from),
        (leg_width, size),
        (0.0, size),
    ], name="plate", arcs={3: -sweep_r})
    fcprim.pad(bdy, "Plate", outline, thickness)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane")
    for i in range(bolts_per_leg):
        fcprim.circle(bolts, (bolt_inset + i * bolt_pitch, bolt_inset),
                      bolt_hole_d, name=f"bolt_a{i}")
        if i:                                  # the corner hole is shared
            fcprim.circle(bolts, (bolt_inset, bolt_inset + i * bolt_pitch),
                          bolt_hole_d, name=f"bolt_b{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts)

    # Mounting datums for the assembly; see fcprim.lcs.  The gusset lies flat
    # on two members at a corner, so every datum is on its underside and the
    # five bolts are what tie the two together.
    fcprim.lcs(bdy, "MOUNT", axis=(0, -1, 0))
    at = [(bolt_inset + i * bolt_pitch, bolt_inset)
          for i in range(bolts_per_leg)]
    at += [(bolt_inset, bolt_inset + i * bolt_pitch)
           for i in range(1, bolts_per_leg)]
    for i, (x, z) in enumerate(at):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, 0.0, z), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "BOT_BRACKETS", bot_brackets, mesh_volume)
