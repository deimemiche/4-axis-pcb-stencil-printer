"""BOT_RAIL_CLAMP_Y_AXIS - clamps the Y axis rod down onto the frame.

Reconstructed from the original author's BOT_RAIL_CLAMP_Y_AXIS.stl, in that
mesh's own coordinates: a 21 x 27 block 7 mm tall with a half round groove
along its underside that closes over an 8 mm linear rod.

Two M3 bolts either side of the rod pull the clamp down; their heads sit in
counterbores so the top face stays clear.

    Profile  sketch -> Pad     block and rod groove, padded across the rod
    Heads    sketch -> Pocket  M3 counterbores from the top
    Shanks   sketch -> Pocket  M3 clearance the rest of the way
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 21.0            # along the rod
width = 27.0             # across it
height = 7.0

groove_r = 4.05          # 8 mm rod plus a little clearance

bolt_z = 9.0             # bolt centres either side of the rod
bolt_hole_d = 3.5        # M3 clearance
head_d = 6.0
head_depth = 4.0         # leaves 3 mm of shank below

mesh_volume = 3144.570


def bot_rail_clamp_y_axis(doc):
    bdy = fcprim.body(doc, "BOT_RAIL_CLAMP_Y_AXIS")

    # Drawn looking along the rod, then padded across it.  The groove is one
    # segment of the outline, so its radius drives the rod size directly.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (0.0, -groove_r),
        (0.0, -width / 2),
        (height, -width / 2),
        (height, width / 2),
        (0.0, width / 2),
        (0.0, groove_r),
    ], name="clamp", arcs={5: -groove_r})
    fcprim.pad(bdy, "Body", profile, length, midplane=True)

    heads = fcprim.sketch(bdy, "Bolt heads", "XZ_Plane", offset=-height)
    for side in (-1, 1):
        fcprim.circle(heads, (0.0, side * bolt_z), head_d,
                      name=f"head{'np'[side > 0]}")
    fcprim.pocket(bdy, "Head clearance", heads, head_depth, reversed_=True)

    shanks = fcprim.sketch(bdy, "Bolt shanks", "XZ_Plane")
    for side in (-1, 1):
        fcprim.circle(shanks, (0.0, side * bolt_z), bolt_hole_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", shanks)

    # Mounting datums for the assembly; see fcprim.lcs.  `ROD` is the rod the
    # groove closes on and `MOUNT` the underside that meets the trough it is
    # pulled down against, which is the same plane -- the groove is a half
    # round, so the rod's axis lies in the joint face.
    fcprim.lcs(bdy, "ROD", axis=(1, 0, 0))
    fcprim.lcs(bdy, "MOUNT", axis=(0, -1, 0))
    for i, side in enumerate((-1, 1)):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(0.0, 0.0, side * bolt_z),
                   axis=(0, -1, 0))
    # Both bolts are counterbored from the top, so each has a second datum on
    # the floor of that bore, which is where its head seats.
    for i, side in enumerate((-1, 1)):
        fcprim.lcs(bdy, f"BOLT{i + 1}_HEAD",
                   at=(0.0, height - head_depth, side * bolt_z),
                   axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "BOT_RAIL_CLAMP_Y_AXIS", bot_rail_clamp_y_axis,
            mesh_volume)
