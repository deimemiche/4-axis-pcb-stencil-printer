"""BOT_RAIL_CLAMP_X_DRIVE - takes the X axis nut and reaches back to the rail.

Reconstructed from the original author's BOT_RAIL_CLAMP_X_DRIVE.stl, in that
mesh's own coordinates: 27 mm across Z, the whole side view extruded along it.

A block at one end takes two M3 up into the nut; a tapered arm carries the other
end over to a 5.5 mm bore.  Everything joining the block to the arm is a 10 mm
radius, so the side view is a plain polyline with four fillets on it and nothing
else.

The arm is hollowed from both faces the same way `bot-bearing-mount-y-axis-driven`
is, over exactly the same spans: a 2 mm skin at each end, one 2 mm rib, a deep
half round hollow between them and a vee roofed one beside each skin.

    Body     sketch -> Pad     the side view, extruded across
    Bore     sketch -> Pocket  5.5 mm through the arm's eye
    Channel  sketch -> Groove  the half round the screw runs in
    Web ...  sketch -> Pocket  the three hollows, open to the arm's end
    Shanks   sketch -> Pocket  two M3 clearance holes up into the nut
    Heads    sketch -> Pocket  their counterbores
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

depth = 27.0             # across the rail

block_x = 10.5           # the nut block, symmetric about the screw
low_y = 0.0
arm_y = 7.0              # the top of the block, and the arm's underside
step_y = 2.25            # the arm's underside where it meets the eye
top_y = 16.55
left_x = -33.4136        # the far end of the arm
waist_x = -24.4936       # where the arm's two tapers land on the eye
blend_r = 10.0           # every corner between block and arm

boss = (-28.622, 9.4)    # the eye, in (X, Y)
bore_d = 5.5

web_deep_r = 5.5         # the hollow between the ribs, a half round
web_vee_r = 4.15         # and the vee roofed one either side of them
web_vee_slope = 30.0     # its roof, measured from the arm's own axis
web_near = (-11.5, -9.5)  # what is left solid: skin, rib, skin
web_deep = (-9.5, 5.1)
web_far = (7.1, 11.5)

groove_r = 4.05          # a channel up the underside, on the screw's own line
groove_far = (-25.414, 2.25)   # where it tapers out, level with the arm's face

bolt_z = 9.0             # two M3 up into the nut
shank_d = 3.5
shank_y = 3.0
head_d = 6.0

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 8417.646


def bot_rail_clamp_x_drive(doc):
    bdy = fcprim.body(doc, "BOT_RAIL_CLAMP_X_DRIVE")
    half_z = depth / 2

    # Drawn looking at the side; H is X, V is Y, and the pad runs across Z.
    body = fcprim.sketch(bdy, "Body", "XY_Plane")
    fcprim.polyline(body, [
        (block_x, low_y),
        (block_x, arm_y),
        (-block_x, arm_y),
        (waist_x, top_y),
        (left_x, top_y),
        (left_x, step_y),
        (waist_x, step_y),
        (-block_x, low_y),
    ], name="side",
        fillets={2: blend_r, 3: blend_r, 6: blend_r, 7: blend_r})
    fcprim.pad(bdy, "Body", body, depth, midplane=True)

    bore = fcprim.sketch(bdy, "Bore", "XY_Plane", offset=-half_z)
    fcprim.circle(bore, boss, bore_d, name="eye")
    fcprim.pocket(bdy, "Bore", bore, depth, reversed_=True)

    # The vee roofed hollow: walls a tangent's reach either side of the eye,
    # closed by a roof of two more tangents to the same circle.
    def vee(label, span):
        slope = math.radians(web_vee_slope)
        apex = boss[0] + web_vee_r / math.cos(slope)
        drop = web_vee_r * math.tan(slope)
        sk = fcprim.sketch(bdy, label, "XY_Plane", offset=span[0])
        fcprim.polyline(sk, [
            (left_x - over, boss[1] - web_vee_r),
            (apex - drop, boss[1] - web_vee_r),
            (apex, boss[1]),
            (apex - drop, boss[1] + web_vee_r),
            (left_x - over, boss[1] + web_vee_r),
        ], name="web")
        fcprim.pocket(bdy, label, sk, span[1] - span[0], reversed_=True)

    vee("Web near", web_near)
    vee("Web far", web_far)

    deep = fcprim.sketch(bdy, "Web deep", "XY_Plane", offset=web_deep[0])
    fcprim.polyline(deep, [
        (left_x - over, boss[1] - web_deep_r),
        (boss[0], boss[1] - web_deep_r),
        (boss[0] + web_deep_r, boss[1]),
        (boss[0], boss[1] + web_deep_r),
        (left_x - over, boss[1] + web_deep_r),
    ], name="web", arcs={1: web_deep_r, 2: web_deep_r})
    fcprim.pocket(bdy, "Web deep", deep, web_deep[1] - web_deep[0],
                  reversed_=True)

    # The channel the screw itself runs in: a half round on the screw's line,
    # tapering out to nothing where the arm's underside rises to meet it.  Cut
    # as a revolved groove, since its lower half is in fresh air anyway.
    channel = fcprim.sketch(bdy, "Channel", "XY_Plane")
    fcprim.polyline(channel, [
        (groove_far[0], 0.0),
        (groove_far[0], groove_far[1]),
        (-block_x, groove_r),
        (block_x + over, groove_r),
        (block_x + over, 0.0),
    ], name="channel")
    fcprim.groove(bdy, "Channel", channel, axis="H_Axis")

    shanks = fcprim.sketch(bdy, "Shanks", "XZ_Plane")
    for side in (-1, 1):
        fcprim.circle(shanks, (0.0, side * bolt_z), shank_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Shanks", shanks, shank_y)

    heads = fcprim.sketch(bdy, "Heads", "XZ_Plane", offset=-shank_y)
    for side in (-1, 1):
        fcprim.circle(heads, (0.0, side * bolt_z), head_d,
                      name=f"head{'np'[side > 0]}")
    fcprim.pocket(bdy, "Heads", heads, arm_y - shank_y)

    # Mounting datums for the assembly; see fcprim.lcs.  This part is the cap
    # for BOT_BEARING_MOUNT_X_AXIS's trough: the rod lies along the block's own
    # X at the underside, and the two M3 straddle it 18 mm apart, which is
    # exactly the mount's own cap bolt spacing.
    fcprim.lcs(bdy, "ROD", axis=(1, 0, 0))
    for i, z in enumerate((-bolt_z, bolt_z)):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(0.0, 0.0, z), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "BOT_RAIL_CLAMP_X_DRIVE", bot_rail_clamp_x_drive,
            mesh_volume)
