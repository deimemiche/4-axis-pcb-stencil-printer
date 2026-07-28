"""BOT_ROD_HOLDER_ALPHA_AXIS - long saddle carrying the alpha axis rod.

Reconstructed from the original author's BOT_ROD_HOLDER_ALPHA_AXIS.stl, in that
mesh's own coordinates: X = 0 .. 68.6 along the rod.

Its first 20 mm are exactly BOT_ROD_HOLDER_ALPHA_AXIS_SHORT - the same bolted
plate over the same blended barrel, the same four M3 holes - and the rest is the
barrel alone, carrying on as a 1 degree cone that closes from 11.3 mm to 9.6 mm
at the free end.  The rod bore stays 5.3 mm the whole way.

    Profile     sketch -> Pad         the bolted head, extruded along X
    Tail        sketch -> Revolution  the tapered barrel beyond the head
    Rod bore    sketch -> Pocket      5.3 mm through both
    Bolt holes  sketch -> Pocket      four M3 clearance holes down through the plate
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

head_length = 20.0       # the bolted part, shared with the short holder
total_length = 68.622

plate_y = 2.65           # underside of the plate
plate_top_y = 6.5
half_z = 14.15

barrel_d = 11.3          # outside of the rod barrel, at the head
tip_d = 9.6              # what the taper closes to
blend_r = 1.5            # fillet from barrel to plate underside
rod_d = 5.3

bolt_x = (4.0, 16.0)
bolt_z = 10.15
bolt_hole_d = 3.5        # M3 clearance

mesh_volume = 6310.190


def bot_rod_holder_alpha_axis(doc):
    bdy = fcprim.body(doc, "BOT_ROD_HOLDER_ALPHA_AXIS")
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
    fcprim.pad(bdy, "Head", profile, head_length)

    # Half a section through the tail; H is along the rod, V is the radius.
    tail = fcprim.sketch(bdy, "Tail", "XY_Plane")
    fcprim.polyline(tail, [
        (head_length, 0.0),
        (head_length, barrel_r),
        (total_length, tip_d / 2),
        (total_length, 0.0),
    ], name="tail")
    fcprim.revolution(bdy, "Tapered barrel", tail, axis="H_Axis")

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


fcprim.make(__file__, "BOT_ROD_HOLDER_ALPHA_AXIS", bot_rod_holder_alpha_axis,
            mesh_volume)
