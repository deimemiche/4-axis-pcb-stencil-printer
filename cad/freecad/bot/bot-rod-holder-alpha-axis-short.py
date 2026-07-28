"""BOT_ROD_HOLDER_ALPHA_AXIS_SHORT - short saddle carrying the alpha axis rod.

Reconstructed from the original author's BOT_ROD_HOLDER_ALPHA_AXIS_SHORT.stl,
in that mesh's own coordinates: 20 mm of extrusion along X, bolted down through
a flat top plate with the rod running along X below it.

The rod sits in a 5.3 mm bore whose 11.3 mm barrel hangs under the plate and
blends into its underside with a 1.5 mm fillet each side.  The bore's top just
touches the underside, so the barrel is a little over half a circle.

    Profile     sketch -> Pad     the whole cross section, extruded along X
    Rod bore    sketch -> Pocket  5.3 mm through, on the barrel's axis
    Bolt holes  sketch -> Pocket  four M3 clearance holes down through the plate
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 20.0            # along the rod

plate_y = 2.65           # underside of the plate
plate_top_y = 6.5
half_z = 14.15

barrel_d = 11.3          # outside of the rod barrel
blend_r = 1.5            # fillet from barrel to plate underside
rod_d = 5.3

bolt_x = (4.0, 16.0)
bolt_z = 10.15
bolt_hole_d = 3.5        # M3 clearance

mesh_volume = 3203.725


def bot_rod_holder_alpha_axis_short(doc):
    bdy = fcprim.body(doc, "BOT_ROD_HOLDER_ALPHA_AXIS_SHORT")
    barrel_r = barrel_d / 2

    # Where the fillet leaves the plate's underside, and where it meets the
    # barrel: its centre stands blend_r below the plate and blend_r + barrel_r
    # out from the barrel's axis.
    centre = (plate_y - blend_r,
              math.sqrt((barrel_r + blend_r) ** 2 - (plate_y - blend_r) ** 2))
    reach = barrel_r / (barrel_r + blend_r)
    meet = (centre[0] * reach, centre[1] * reach)

    # The barrel takes whatever is left of the circle once the fillets have
    # eaten into its top on both sides.
    barrel_sweep = 360.0 - 2 * math.degrees(math.atan2(meet[1], meet[0]))

    # Drawn looking along the rod; H is Y, V is Z.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (plate_y, -half_z),
        (plate_top_y, -half_z),
        (plate_top_y, half_z),
        (plate_y, half_z),
        (plate_y, centre[1]),
        (meet[0], meet[1]),
        (meet[0], -meet[1]),
        (plate_y, -centre[1]),
    ], name="holder",
        arcs={4: -blend_r, 5: (barrel_r, barrel_sweep), 6: -blend_r})
    fcprim.pad(bdy, "Body", profile, length)

    rod = fcprim.sketch(bdy, "Rod bore", "YZ_Plane")
    fcprim.circle(rod, (0.0, 0.0), rod_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance", rod, reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane", offset=-plate_top_y)
    for x in bolt_x:
        for z in (-bolt_z, bolt_z):
            fcprim.circle(bolts, (x, z), bolt_hole_d,
                          name=f"bolt_{x:.0f}_{'np'[z > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, plate_top_y - plate_y,
                  reversed_=True)

    return bdy


fcprim.make(__file__, "BOT_ROD_HOLDER_ALPHA_AXIS_SHORT",
            bot_rod_holder_alpha_axis_short, mesh_volume)
