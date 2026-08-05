"""BOT_BRACKET_X_AXIS - corner bracket carrying the X axis screw.

Reconstructed from the original author's BOT_BRACKET_X_AXIS.stl, in that mesh's
own coordinates: X = -36 .. 0, Z = -60 .. 0, lying flat on the bottom frame with
Y up.

A 4 mm plate bolts down through three M4 holes.  It is an L, and the inside of
the L is not a corner but a 22.5 mm sweep that runs tangentially off the long
leg and finishes on the short leg's end.

Standing on the plate is a web that carries the screw: a 13.5 mm barrel bored
5.5 mm, with straight flanks running tangentially down off it and a 3.5 mm
fillet into the plate on each side.

    Plate       sketch -> Pad     the L, padded down from its top face
    Web         sketch -> Pad     the screw barrel and its flanks
    Screw bore  sketch -> Pocket  5.5 mm through the barrel
    Bolt holes  sketch -> Pocket  three M4 clearance holes through the plate
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

plate_thickness = 4.0
long_leg_x = -20.0       # the inside edge of the leg running along Z
long_leg_z = -60.0
short_leg_x = -36.0
short_leg_z = -20.0      # the inside edge of the leg running along X
sweep_r = 22.5           # the sweep between them

barrel_d = 13.5
screw_d = 5.5
screw_y = 13.0           # the screw's height above the plate's underside
screw_z = -10.0
web_x = (-20.0, 0.0)     # how much of the plate the web stands on
web_fillet_r = 3.5

bolt_hole_d = 4.5        # M4 clearance
bolt_at = ((-30.0, -10.0), (-10.0, -30.0), (-10.0, -50.0))

mesh_volume = 9745.755


def bot_bracket_x_axis(doc):
    bdy = fcprim.body(doc, "BOT_BRACKET_X_AXIS")
    barrel_r = barrel_d / 2

    # The sweep runs tangentially off the long leg's inside edge and is pulled
    # round until it reaches the short leg's far corner, which fixes its centre.
    sweep_x = long_leg_x - sweep_r
    sweep_z = short_leg_z - math.sqrt(sweep_r ** 2 - (short_leg_x - sweep_x) ** 2)

    # Drawn looking down on the plate; H is X, V is Z, and the pad runs down.
    plate = fcprim.sketch(bdy, "Plate", "XZ_Plane", offset=-plate_thickness)
    fcprim.polyline(plate, [
        (0.0, 0.0),
        (short_leg_x, 0.0),
        (short_leg_x, short_leg_z),
        (long_leg_x, sweep_z),
        (long_leg_x, long_leg_z),
        (0.0, long_leg_z),
    ], name="plate", arcs={2: -sweep_r})
    fcprim.pad(bdy, "Plate", plate, plate_thickness)

    # Drawn looking along the screw; H is Y, V is Z.  The flanks leave the
    # barrel where it is widest, so that half of it is an exact semicircle.
    #
    # The upper fillet would come down 0.25 mm past the plate's end, so it is
    # cut off there; that leaves a sliver of a face along the plate's edge.
    web = fcprim.sketch(bdy, "Web", "YZ_Plane", offset=web_x[0])
    flank_z = (screw_z - barrel_r, screw_z + barrel_r)
    foot = plate_thickness + web_fillet_r
    clipped = foot - math.sqrt(web_fillet_r ** 2
                               - (flank_z[1] + web_fillet_r) ** 2)
    fcprim.polyline(web, [
        (plate_thickness, flank_z[0] - web_fillet_r),
        (foot, flank_z[0]),
        (screw_y, flank_z[0]),
        (screw_y, flank_z[1]),
        (foot, flank_z[1]),
        (clipped, 0.0),
        (plate_thickness, 0.0),
    ], name="web", arcs={0: -web_fillet_r, 2: barrel_r, 4: -web_fillet_r})
    fcprim.pad(bdy, "Web", web, web_x[1] - web_x[0])

    bore = fcprim.sketch(bdy, "Screw bore", "YZ_Plane", offset=web_x[0])
    fcprim.circle(bore, (screw_y, screw_z), screw_d, name="screw")
    fcprim.pocket(bdy, "Screw clearance", bore, web_x[1] - web_x[0],
                  reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane",
                          offset=-plate_thickness)
    for i, (x, z) in enumerate(bolt_at):
        fcprim.circle(bolts, (x, z), bolt_hole_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, plate_thickness, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `SCREW` is the X axis
    # screw's own axis, 13 mm above the frame's top face -- which is the number
    # BOT_RAIL_CLAMP_X_DRIVE's eye has to agree with, and does.
    fcprim.lcs(bdy, "SCREW", at=(0.0, screw_y, screw_z), axis=(1, 0, 0))
    fcprim.lcs(bdy, "MOUNT", axis=(0, -1, 0))
    for i, (x, z) in enumerate(bolt_at):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, 0.0, z), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "BOT_BRACKET_X_AXIS", bot_bracket_x_axis, mesh_volume)
