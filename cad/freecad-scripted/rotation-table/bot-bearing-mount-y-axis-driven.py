"""BOT_BEARING_MOUNT_Y_AXIS_DRIVEN - carries the driven end of the Y axis screw.

Reconstructed from the original author's BOT_BEARING_MOUNT_Y_AXIS_DRIVEN.stl,
in that mesh's own coordinates: 27 mm along the screw, the same bearing seat and
flange as BOT_BEARING_MOUNT_Y_AXIS, with an arm hung off one side of it to carry
the motor's own shaft.

The seat is identical to the idle end's, lip and all - see that script for why it
is a revolved groove.  What is new is the arm: it reaches down to a 5.3 mm bore
and is hollowed out from both faces, leaving a 2 mm skin at each end and one
2 mm rib near the far end.

Both hollows are laid out round the bore.  The deep one is simply a 5.5 mm half
round with the walls carried straight down.  The shallow ones, which sit against
a skin, are the same idea drawn 4.25 mm out and roofed by a 120 degree vee
instead, so that they print without support.

    Profile      sketch -> Pad     the whole side view, padded along the screw
    Bearing      sketch -> Groove  the seat, its lip and lead in
    Shaft        sketch -> Pocket  the 5.3 mm bore at the end of the arm
    Web near/far sketch -> Pocket  the vee roofed hollows beside the ribs
    Web deep     sketch -> Pocket  the half round hollow between them
    Bolts        sketch -> Pocket  four M3 clearance holes through the flange
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

arm_y = -3.25            # the arm's far face; the near one is the flange's
arm_z = -30.907          # how far down it reaches
ledge_z = -17.628        # where it stops following the flange's underside
taper_y = 4.0            # and falls away at this angle to its own face
taper_angle = 30.0
taper_blend = 5.0

shaft = (4.0, -26.0)     # the motor shaft's bore, in (Y, Z)
shaft_d = 5.3

web_deep_r = 5.5         # the hollow between the ribs, a half round
web_vee_r = 4.25         # and the vee roofed one either side of them
web_vee_slope = 30.0     # its roof, measured from the horizontal
web_near = (-11.5, -9.5)  # what is left solid: skin, rib, skin
web_deep = (-9.5, 5.1)
web_far = (7.1, 11.5)

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 9014.048


def bot_bearing_mount_y_axis_driven(doc):
    bdy = fcprim.body(doc, "BOT_BEARING_MOUNT_Y_AXIS_DRIVEN")
    seat_r, wall_r, lip_r = seat_d / 2, wall_d / 2, lip_d / 2
    flange_y = flange_top_y - flange_thickness
    half_z, half_x = flange_z / 2, width / 2

    # Where the wall's outer face meets the flange's underside, and where the
    # wall is cut off at each side.
    meet_z = math.sqrt(wall_r ** 2 - flange_y ** 2)
    turn = math.radians(wall_angle)
    outer = (wall_r * math.cos(turn), wall_r * math.sin(turn))

    # Where the arm's taper lands on its own face.
    fall = (taper_y - arm_y) * math.tan(math.radians(taper_angle))

    # Drawn looking along the screw; H is Y, V is Z.  As on the idle end the
    # seat is left solid and bored out afterwards, so the wall is a wedge
    # closing on the centre rather than an open arc.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (flange_y, -meet_z),
        (flange_y, ledge_z),
        (taper_y, ledge_z),
        (arm_y, ledge_z - fall),
        (arm_y, arm_z),
        (flange_top_y, arm_z),
        (flange_top_y, half_z),
        (flange_y, half_z),
        (flange_y, meet_z),
        (outer[0], outer[1]),
        (0.0, 0.0),
        (outer[0], -outer[1]),
    ], name="mount", arcs={8: wall_r, 11: wall_r},
        fillets={2: taper_blend, 3: taper_blend})
    fcprim.pad(bdy, "Body", profile, width, midplane=True)

    # Half the bore's longitudinal section, revolved about the screw axis.
    bore = fcprim.sketch(bdy, "Bearing", "XY_Plane")
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

    shaft_bore = fcprim.sketch(bdy, "Shaft", "YZ_Plane", offset=-half_x)
    fcprim.circle(shaft_bore, shaft, shaft_d, name="shaft")
    fcprim.pocket(bdy, "Shaft clearance", shaft_bore, width, reversed_=True)

    # The vee roofed hollow: walls a tangent's reach either side of the bore,
    # closed by a roof of two more tangents to the same circle.
    def vee(label, span):
        slope = math.radians(web_vee_slope)
        apex = shaft[1] + web_vee_r / math.cos(slope)
        drop = web_vee_r * math.tan(slope)
        sk = fcprim.sketch(bdy, label, "YZ_Plane", offset=span[0])
        fcprim.polyline(sk, [
            (shaft[0] - web_vee_r, apex - drop),
            (shaft[0], apex),
            (shaft[0] + web_vee_r, apex - drop),
            (shaft[0] + web_vee_r, arm_z - over),
            (shaft[0] - web_vee_r, arm_z - over),
        ], name="web")
        fcprim.pocket(bdy, label, sk, span[1] - span[0], reversed_=True)

    vee("Web near", web_near)
    vee("Web far", web_far)

    deep = fcprim.sketch(bdy, "Web deep", "YZ_Plane", offset=web_deep[0])
    fcprim.polyline(deep, [
        (shaft[0] - web_deep_r, shaft[1]),
        (shaft[0], shaft[1] + web_deep_r),
        (shaft[0] + web_deep_r, shaft[1]),
        (shaft[0] + web_deep_r, arm_z - over),
        (shaft[0] - web_deep_r, arm_z - over),
    ], name="web", arcs={0: -web_deep_r, 1: -web_deep_r})
    fcprim.pocket(bdy, "Web deep", deep, web_deep[1] - web_deep[0],
                  reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane", offset=-flange_top_y)
    for i, (x, z) in enumerate(((bolt_x, bolt_z), (bolt_x, -bolt_z),
                                (-bolt_x, bolt_z), (-bolt_x, -bolt_z))):
        fcprim.circle(bolts, (x, z), bolt_hole_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, flange_thickness,
                  reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  The seat and the
    # flange are the idle end's exactly, and `SCREW` is what this part adds:
    # the arm's eye, which carries the Y axis screw parallel to the rail.
    fcprim.lcs(bdy, "BEARING", axis=(1, 0, 0))
    fcprim.lcs(bdy, "PLATE", at=(0.0, flange_top_y, 0.0), axis=(0, 1, 0))
    for i, (x, z) in enumerate(((bolt_x, bolt_z), (bolt_x, -bolt_z),
                                (-bolt_x, bolt_z), (-bolt_x, -bolt_z))):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, flange_top_y, z), axis=(0, 1, 0))
    fcprim.lcs(bdy, "SCREW", at=(0.0, shaft[0], shaft[1]), axis=(1, 0, 0))

    return bdy


fcprim.make(__file__, "BOT_BEARING_MOUNT_Y_AXIS_DRIVEN",
            bot_bearing_mount_y_axis_driven, mesh_volume)
