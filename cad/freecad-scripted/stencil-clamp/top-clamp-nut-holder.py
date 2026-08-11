"""TOP_CLAMP_NUT_HOLDER - carries the nut the stencil clamp's screw drives.

Reconstructed from the original author's TOP_CLAMP_NUT_HOLDER.stl, in that
mesh's own coordinates: 14 mm thick in Z, the screw running along Y.

Seen from the side it is a spine with a block hung off it, the gap between them
straddling whatever it slides on.  The spine's top ends in a 45 degree ramp, and
its foot spreads forward into an 8 mm barrel that runs out to both faces on
tangents - the only curve in the part.

An M3 drives the block, and its nut drops into a hexagonal seat open to the top
face, so it cannot turn.

Everything the part does not mate against is chamfered 1 mm on both faces: up the
block's front, over the ramp and down the spine's back.  It stops at the gap, the
foot and the block's underside.

    Body       sketch -> Pad      the whole side view, extruded across
    Base front sketch -> Pad      the barrel and its tangents, at the foot
    Edges              Chamfer    1 mm round the outside of both faces
    Screw      sketch -> Pocket   M3 clearance through the block
    Nut seat   sketch -> Pocket   its hexagon, and the slot it drops in through
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

half_z = 7.0             # the part's thickness, either side of the screw
edge_break = 1.0         # the 45 degree break round both faces and the corners

spine_x = (-11.4, -8.4)
spine_y = (-14.8, 15.2)
ramp_at = 12.2           # the spine's top slopes back at 45 degrees from here

block_x = (-5.0, 5.0)
block_y = (-7.3, 12.2)

base_y = -11.8           # the foot spreads forward below this
barrel_d = 8.0
barrel_x = 1.0           # the barrel's axis, on the screw's line
run_out_r = 1.0          # where its tangents land on the faces

screw_hole_d = 3.5       # M3 clearance
screw_y = (-7.3, 0.2)
nut_across_flats = 5.7
nut_y = (-5.3, -2.7)

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 4126.555


def broken(corner, towards, away, size):
    """The two points a 45 degree break puts where `corner` used to be."""
    def along(other):
        span = math.hypot(other[0] - corner[0], other[1] - corner[1])
        return (corner[0] + (other[0] - corner[0]) * size / span,
                corner[1] + (other[1] - corner[1]) * size / span)
    return [along(towards), along(away)]


def top_clamp_nut_holder(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_NUT_HOLDER")
    barrel_r = barrel_d / 2

    # Where the ramp meets the block's front face and the spine's top.
    ramp_low = (block_x[1], ramp_at - block_x[1])
    ramp_high = (ramp_at - spine_y[1], spine_y[1])

    # Drawn looking at the side; H is X, V is Y, and the pad runs across Z.
    # The foot is left at the spine's width here and spread forward afterwards.
    body = fcprim.sketch(bdy, "Body", "XY_Plane", offset=-half_z)
    fcprim.polyline(body, (
        broken((spine_x[0], spine_y[0]), (spine_x[0], spine_y[1]),
               (spine_x[1], spine_y[0]), edge_break)
        + [(spine_x[1], spine_y[0]), (spine_x[1], block_y[1]),
           (block_x[0], block_y[1])]
        + broken((block_x[0], block_y[0]), (block_x[0], block_y[1]),
                 (block_x[1], block_y[0]), edge_break)
        + broken((block_x[1], block_y[0]), (block_x[0], block_y[0]),
                 ramp_low, edge_break)
        + broken(ramp_low, (block_x[1], block_y[0]), ramp_high, edge_break)
        + broken(ramp_high, ramp_low, (spine_x[0], spine_y[1]), edge_break)
        + broken((spine_x[0], spine_y[1]), ramp_high,
                 (spine_x[0], spine_y[0]), edge_break)
    ), name="side")
    fcprim.pad(bdy, "Body", body, 2 * half_z)

    # The foot's front seen end on: the barrel, a 45 degree tangent off each
    # side of it, and a small radius where each tangent lands on a face.
    tangent = (barrel_x - barrel_r / math.sqrt(2), barrel_r / math.sqrt(2))
    run_out_x = (barrel_x - barrel_r * math.sqrt(2) + (half_z - run_out_r)
                 - run_out_r * math.sqrt(2))
    corner_x = barrel_x - barrel_r * math.sqrt(2) + half_z
    front = fcprim.sketch(bdy, "Base front", "XZ_Plane", offset=-base_y)
    fcprim.polyline(front, [
        (corner_x, -half_z),
        (tangent[0], -tangent[1]),
        (tangent[0], tangent[1]),
        (corner_x, half_z),
        (spine_x[0] + edge_break, half_z),
        (spine_x[0], half_z - edge_break),
        (spine_x[0], -half_z + edge_break),
        (spine_x[0] + edge_break, -half_z),
    ], name="front", arcs={1: -barrel_r},
        fillets={0: run_out_r, 3: run_out_r})
    fcprim.pad(bdy, "Base front", front, base_y - spine_y[0])

    # The foot's back corner is broken like every other, but the front pad has
    # just filled it back in, so it comes off again here.
    nick = fcprim.sketch(bdy, "Foot corner", "XY_Plane")
    starts, ends = broken((spine_x[0], spine_y[0]), (spine_x[0], spine_y[1]),
                          (spine_x[1], spine_y[0]), edge_break)
    fcprim.polyline(nick, [
        starts, ends,
        (ends[0], spine_y[0] - over),
        (spine_x[0] - over, spine_y[0] - over),
        (spine_x[0] - over, starts[1]),
    ], name="nick")
    fcprim.pocket(bdy, "Foot corner", nick, midplane=True)

    # The break runs right round the outside and stops wherever the part mates
    # with something: the gap it straddles, the foot, the block's underside.
    mates_at = (("x", spine_x[1]), ("x", block_x[0]), ("x", run_out_x),
                ("y", block_y[0]), ("y", block_y[1]),
                ("y", base_y), ("y", spine_y[0]))
    stays_sharp = ((spine_x[0], spine_y[0]), (block_x[0], block_y[0]),
                   (block_x[1], block_y[0]))

    def outside(edge):
        point = fcprim.midpoint(edge)
        if abs(abs(point.z) - half_z) > 1e-6:
            return False
        if any(abs({"x": point.x, "y": point.y}[axis] - value) < 1e-6
               for axis, value in mates_at):
            return False
        # The little breaks where the chamfer runs into a mating face stay put.
        return all(math.hypot(point.x - cx, point.y - cy) > edge_break
                   for cx, cy in stays_sharp)

    fcprim.chamfer(bdy, "Edges", edge_break, outside)

    screw = fcprim.sketch(bdy, "Screw", "XZ_Plane", offset=-screw_y[0])
    fcprim.circle(screw, (barrel_x, 0.0), screw_hole_d, name="screw")
    fcprim.pocket(bdy, "Screw clearance", screw, screw_y[1] - screw_y[0])

    # Half a hexagon closed off by a slot out to the top face, so the nut goes
    # in sideways and cannot turn.
    across_corners = nut_across_flats * 2 / math.sqrt(3)
    seat = fcprim.sketch(bdy, "Nut seat", "XZ_Plane", offset=-nut_y[1])
    fcprim.polyline(seat, [
        (barrel_x + nut_across_flats / 2, half_z + over),
        (barrel_x + nut_across_flats / 2, -across_corners / 4),
        (barrel_x, -across_corners / 2),
        (barrel_x - nut_across_flats / 2, -across_corners / 4),
        (barrel_x - nut_across_flats / 2, half_z + over),
    ], name="nut")
    fcprim.pocket(bdy, "Nut clearance", seat, nut_y[1] - nut_y[0],
                  reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  Both are on the
    # screw's own line: the block's front face, which the back bar is pulled
    # against, and the floor of the slot the nut drops into behind it.
    fcprim.lcs(bdy, "HOLDER_BACK", at=(barrel_x, screw_y[0], 0.0),
               axis=(0, -1, 0))
    fcprim.lcs(bdy, "NUT", at=(barrel_x, nut_y[0], 0.0), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "TOP_CLAMP_NUT_HOLDER", top_clamp_nut_holder,
            mesh_volume)
