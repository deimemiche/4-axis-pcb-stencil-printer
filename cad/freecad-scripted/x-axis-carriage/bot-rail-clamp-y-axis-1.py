"""BOT_RAIL_CLAMP_Y_AXIS_1 - clamps the Y axis rod and reaches out to the alpha rod.

Reconstructed from the original author's BOT_RAIL_CLAMP_Y_AXIS_1.stl, in that
mesh's own coordinates: the rod clamp along X at the origin, the arm reaching
out to X = 38.622.

Two parts of it are other parts of this machine:

* the clamp block is `BOT_RAIL_CLAMP_Y_AXIS` exactly - 21 mm long, a 4.05 mm
  groove closing over the 8 mm rod, two M3 counterbored from the top;
* the far end is `BOT_ROD_HOLDER_ALPHA_AXIS`'s barrel - an 11.3 mm tube bored
  5.3 mm, on an axis along X at (Y 4, Z -26).

The gusset between them is one prism and one revolved cut, and nothing else.

Seen end on it never changes: from each of the block's two front corners a line
runs tangent to the tube, rounded into the corner on a 10 mm radius.  That
section is simply padded the whole length.

What tapers it is the cut.  Its outer surface is a torus - a 33.5 mm arc turned
about the tube's own axis - so it comes off as a revolved groove, the same
primitive the bearing seats use.  Two dimensions fall out of that arc rather
than being chosen: it reaches furthest out exactly where the block ends, and it
runs down onto the tube's own diameter exactly where the part stops.

    Block       sketch -> Pad     the clamp, square for now
    Gusset      sketch -> Pad     the end on section, the whole length
    Sweep       sketch -> Groove  the torus, turned about the tube
    Rod         sketch -> Pocket  the 4.05 mm groove the rod closes into
    Bore        sketch -> Pocket  5.3 mm through the tube
    Heads       sketch -> Pocket  two M3 counterbores
    Shanks      sketch -> Pocket  and their clearance holes
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

block_x = 10.5           # the clamp block, symmetric about the rod
half_z = 13.5
block_y = 7.0
groove_r = 4.05          # 8 mm rod plus a little clearance

tube = (4.0, -26.0)      # the alpha rod's holder, in (Y, Z)
tube_d = 11.3
bore_d = 5.3
tube_x = (-2.5, 38.622)

corner_blend = 10.0      # where each tangent runs into the block's front face
sweep_r = 33.5           # the arc that is turned about the tube to shape the gusset

bolt_z = 9.0             # as on the sibling part
bolt_hole_d = 3.5        # M3 clearance
head_d = 6.0
head_depth = 4.0         # leaves 3 mm of shank below

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 9094.455


def bot_rail_clamp_y_axis_1(doc):
    bdy = fcprim.body(doc, "BOT_RAIL_CLAMP_Y_AXIS_1")
    tube_r, front = tube_d / 2, -half_z

    def tangent(corner, hand):
        """Where a line from `corner` touches the tube, and at what angle."""
        span = math.hypot(corner[0] - tube[0], corner[1] - tube[1])
        turn = (math.atan2(corner[1] - tube[1], corner[0] - tube[0])
                + hand * math.acos(tube_r / span))
        return ((tube[0] + tube_r * math.cos(turn),
                 tube[1] + tube_r * math.sin(turn)), math.degrees(turn))

    low, low_at = tangent((0.0, front), 1)
    high, high_at = tangent((block_y, front), -1)

    block = fcprim.sketch(bdy, "Block", "YZ_Plane", offset=-block_x)
    fcprim.polyline(block, [
        (0.0, -half_z), (block_y, -half_z), (block_y, half_z), (0.0, half_z),
    ], name="block")
    fcprim.pad(bdy, "Block", block, 2 * block_x)

    # The gusset, drawn looking along the arm; H is Y, V is Z.  Its two flanks
    # are tangent to the tube, and the tube's own underside closes the profile,
    # so the barrel comes out of the same pad.
    gusset = fcprim.sketch(bdy, "Gusset", "YZ_Plane", offset=tube_x[0])
    fcprim.polyline(gusset, [
        (0.0, half_z),
        (0.0, front),
        low,
        high,
        (block_y, front),
        (block_y, half_z),
    ], name="gusset",
        arcs={2: (tube_r, (high_at - low_at) % 360.0)},
        fillets={1: corner_blend, 4: corner_blend})
    fcprim.pad(bdy, "Gusset", gusset, tube_x[1] - tube_x[0])

    # What tapers it.  H is X and V is the radius from the tube's axis, so the
    # sketch is shifted onto that axis and turned about its own H.
    reach = math.sqrt(sweep_r ** 2 - (tube_x[1] - block_x - sweep_r) ** 2) \
        + tube_r
    sweep = fcprim.sketch(bdy, "Sweep", "XY_Plane", offset=tube[1],
                          shift=(0.0, tube[0]))
    fcprim.polyline(sweep, [
        (block_x, reach),
        (tube_x[1], tube_r),
        (tube_x[1] + over, tube_r),
        (tube_x[1] + over, reach + over),
        (block_x, reach + over),
    ], name="sweep", arcs={0: sweep_r})
    fcprim.groove(bdy, "Sweep", sweep, axis="H_Axis")

    # The rod's groove.  It is cut after the gusset, so that the gusset does not
    # fill it in, and it runs the whole length rather than stopping with the
    # block: past the block the sweep has already taken everything near it away.
    rod = fcprim.sketch(bdy, "Rod", "YZ_Plane", offset=-block_x)
    fcprim.polyline(rod, [
        (0.0, -groove_r),
        (-over, -groove_r),
        (-over, groove_r),
        (0.0, groove_r),
    ], name="rod", arcs={3: -groove_r})
    fcprim.pocket(bdy, "Rod", rod, tube_x[1] + block_x, reversed_=True)

    bore = fcprim.sketch(bdy, "Bore", "YZ_Plane", offset=tube_x[0])
    fcprim.circle(bore, tube, bore_d, name="bore")
    fcprim.pocket(bdy, "Bore", bore, tube_x[1] - tube_x[0], reversed_=True)

    heads = fcprim.sketch(bdy, "Heads", "XZ_Plane", offset=-block_y)
    for side in (-1, 1):
        fcprim.circle(heads, (0.0, side * bolt_z), head_d,
                      name=f"head{'np'[side > 0]}")
    fcprim.pocket(bdy, "Heads", heads, head_depth, reversed_=True)

    shanks = fcprim.sketch(bdy, "Shanks", "XZ_Plane")
    for side in (-1, 1):
        fcprim.circle(shanks, (0.0, side * bolt_z), bolt_hole_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Shanks", shanks, block_y - head_depth)

    # Mounting datums for the assembly; see fcprim.lcs.  The clamp half is
    # BOT_RAIL_CLAMP_Y_AXIS's, datums and all; `SCREW` is the tube on the end
    # of the gusset, which is where the Y axis screw's nuts bear.
    fcprim.lcs(bdy, "ROD", axis=(1, 0, 0))
    fcprim.lcs(bdy, "MOUNT", axis=(0, -1, 0))
    for i, side in enumerate((-1, 1)):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(0.0, 0.0, side * bolt_z),
                   axis=(0, -1, 0))
    fcprim.lcs(bdy, "SCREW", at=(0.0, tube[0], tube[1]), axis=(1, 0, 0))
    # The counterbore floor under each bolt head, and the far end of the tube,
    # which is where the handwheel comes up against it.
    for i, side in enumerate((-1, 1)):
        fcprim.lcs(bdy, f"BOLT{i + 1}_HEAD",
                   at=(0.0, block_y - head_depth, side * bolt_z),
                   axis=(0, -1, 0))
    fcprim.lcs(bdy, "HANDWHEEL", at=(tube_x[1], tube[0], tube[1]),
               axis=(1, 0, 0), roll=90.0)

    return bdy


fcprim.make(__file__, "BOT_RAIL_CLAMP_Y_AXIS_1", bot_rail_clamp_y_axis_1,
            mesh_volume)
