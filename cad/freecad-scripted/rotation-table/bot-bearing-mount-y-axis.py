"""BOT_BEARING_MOUNT_Y_AXIS - carries the idle end of the Y axis screw.

Reconstructed from the original author's BOT_BEARING_MOUNT_Y_AXIS.stl, in that
mesh's own coordinates: a 27 mm wide block bolted flat under the frame, with a
15.2 mm bearing seat hanging below it.

The seat is not a closed bore.  Its wall stops 127.5 degrees either side of
straight up, so the bearing drops in from underneath rather than being pressed
in from the end.  Both ends of the seat narrow to a 13.2 mm lip that stops the
bearing pushing straight through, reached over a 1 mm 45 degree lead in - so
the bore is cut as a revolved groove rather than a pocket, a pocket having only
one section to give.

    Profile  sketch -> Pad     flange and the solid seat body, padded across
    Bore     sketch -> Groove  the stepped seat, revolved about the screw
    Bolts    sketch -> Pocket  four M3 clearance holes through the flange
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

width = 27.0             # along the screw
flange_z = 38.0          # across the frame
flange_top_y = 11.6
flange_thickness = 4.0

seat_d = 15.2            # bearing outside diameter
wall_d = 21.0            # outside of the seat's wall
wall_angle = 127.5       # where the wall stops, measured from straight up

lip_d = 13.2             # retains the bearing at each end
lip_land = 0.2           # flat part of the lip
lip_lead = 1.0           # 45 degree lead in behind it

bolt_x = 9.0
bolt_z = 14.5
bolt_hole_d = 3.5        # M3 clearance

mesh_volume = 6369.140


def bot_bearing_mount_y_axis(doc):
    bdy = fcprim.body(doc, "BOT_BEARING_MOUNT_Y_AXIS")
    seat_r, wall_r, lip_r = seat_d / 2, wall_d / 2, lip_d / 2
    flange_y = flange_top_y - flange_thickness
    half_z, half_x = flange_z / 2, width / 2

    # Where the wall's outer face meets the flange's underside, and where the
    # wall is cut off at each side.
    meet_z = math.sqrt(wall_r ** 2 - flange_y ** 2)
    turn = math.radians(wall_angle)
    outer = (wall_r * math.cos(turn), wall_r * math.sin(turn))

    # Drawn looking along the screw; H is Y, V is Z.  The seat is left solid
    # here and bored out afterwards, so the wall is a wedge closing on the
    # centre rather than an open arc.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (flange_y, -meet_z),
        (flange_y, -half_z),
        (flange_top_y, -half_z),
        (flange_top_y, half_z),
        (flange_y, half_z),
        (flange_y, meet_z),
        (outer[0], outer[1]),
        (0.0, 0.0),
        (outer[0], -outer[1]),
    ], name="mount", arcs={5: wall_r, 8: wall_r})
    fcprim.pad(bdy, "Body", profile, width, midplane=True)

    # Half the bore's longitudinal section, revolved about the screw axis.
    bore = fcprim.sketch(bdy, "Bore", "XY_Plane")
    fcprim.polyline(bore, [
        (-half_x, 0.0),
        (-half_x, lip_r),
        (-half_x + lip_land, lip_r),
        (-half_x + lip_land + lip_lead, seat_r),
        (half_x - lip_land - lip_lead, seat_r),
        (half_x - lip_land, lip_r),
        (half_x, lip_r),
        (half_x, 0.0),
    ], name="bore")
    fcprim.groove(bdy, "Bearing seat", bore, axis="H_Axis")

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane", offset=-flange_top_y)
    for i, (x, z) in enumerate(((bolt_x, bolt_z), (bolt_x, -bolt_z),
                                (-bolt_x, bolt_z), (-bolt_x, -bolt_z))):
        fcprim.circle(bolts, (x, z), bolt_hole_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, flange_thickness, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  The seat's axis is the
    # rail the bearing rides, and the flange's top face is what bolts up
    # against the plate above it -- which is what fixes the plate's height.
    fcprim.lcs(bdy, "BEARING", axis=(1, 0, 0))
    fcprim.lcs(bdy, "PLATE", at=(0.0, flange_top_y, 0.0), axis=(0, 1, 0))
    for i, (x, z) in enumerate(((bolt_x, bolt_z), (bolt_x, -bolt_z),
                                (-bolt_x, bolt_z), (-bolt_x, -bolt_z))):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, flange_top_y, z), axis=(0, 1, 0))

    # Each of the four bolts goes right through the flange, so each has a
    # second datum on its underside, where the head seats -- numbered along the
    # part, which is what sorting the centres does.
    seats = sorted((sx * bolt_x, sz * bolt_z)
                   for sx in (-1, 1) for sz in (-1, 1))
    for i, (x, z) in enumerate(seats):
        fcprim.lcs(bdy, f"BOLT{i + 5}",
                   at=(x, flange_top_y - flange_thickness, z), axis=(0, -1, 0))

    # Three of the four bolt tops are where the alpha plate is clamped down.
    # The fourth -- the one at +X, -Z -- is left to the joint at the other end
    # of the pair, so it is the one dropped here.
    clamped = [c for c in seats if c != (bolt_x, -bolt_z)]
    for i, (x, z) in enumerate(clamped):
        fcprim.lcs(bdy, f"BOT_PLATE{i + 1}", at=(x, flange_top_y, z),
                   axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "BOT_BEARING_MOUNT_Y_AXIS", bot_bearing_mount_y_axis,
            mesh_volume)
