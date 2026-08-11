"""TOP_CLAMP_SPANNER_COUNTER - the long rail the stencil clamp's spanner works against.

Reconstructed from the original author's TOP_CLAMP_SPANNER_COUNTER.stl, in that
mesh's own coordinates: 58 mm along Z, with the same side view as
TOP_CLAMP_NUT_HOLDER - a spine, a block hung off it, and a gap between them - so
the two run on the same thing.

An 8.4 mm slot up the middle of the block is where the spanner swings; its
bottom closes in a 120 degree vee so it prints unsupported.  The 5.6 mm screw
bore runs through the whole length underneath it.

Under the foot the front sweeps back to nothing at each end over an 8 mm nose.
An M3 comes up into the block at each end, and its nut slides in along a slot
that a 90 degree vee closes off.

    Body         sketch -> Pad      the side view, extruded the whole length
    Edges                Chamfer    1 mm round the outside of both end faces
    Nose         sketch -> Pocket   sweeps the foot's front back at each end
    Spanner slot sketch -> Pocket   what the spanner swings in
    Screw bore   sketch -> Pocket   5.6 mm through
    Bolts        sketch -> Pocket   two M3 up into the block
    Nut slots    sketch -> Pocket   their nuts, in from each end
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

half_z = 29.0            # the whole length, either side of the middle
edge_break = 1.0

spine_x = (-11.4, -8.4)
spine_y = (-14.8, 15.2)
block_x = (-5.0, 5.0)
block_y = (-7.3, 15.2)
gap_top = 12.2           # the gap between spine and block closes here
base_y = -11.8           # the foot fills it in below this

nose_r = 4.0             # the foot's front sweeps back over this
nose_at = (1.0, 25.0)    # its centre, mirrored in Z
nose_ends = -3.2         # where the sweep has got to at the end face
nose_meets = 15.972      # where it leaves the foot's front face

screw_d = 5.6
slot_z = 4.2             # the spanner's slot, either side of the middle
slot_x = (-1.2, 3.0)
slot_root = -4.85        # where its 120 degree vee bottom closes

bolt_hole_d = 3.5        # M3 clearance, up into the nuts
bolt_z = 25.0
bolt_y = (-7.3, 0.2)

slot_across = 5.7        # the nut slot in from each end
slot_y = (-5.3, -2.7)
slot_apex = 20.5         # where its vee closes

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 19314.972


def broken(corner, towards, away, size):
    """The two points a 45 degree break puts where `corner` used to be."""
    def along(other):
        span = math.hypot(other[0] - corner[0], other[1] - corner[1])
        return (corner[0] + (other[0] - corner[0]) * size / span,
                corner[1] + (other[1] - corner[1]) * size / span)
    return [along(towards), along(away)]


def tangent_from(point, centre, radius, hand):
    """Where a tangent drawn from `point` touches the circle."""
    span = math.hypot(point[0] - centre[0], point[1] - centre[1])
    angle = (math.atan2(point[1] - centre[1], point[0] - centre[0])
             + hand * math.acos(radius / span))
    return (centre[0] + radius * math.cos(angle),
            centre[1] + radius * math.sin(angle))


def top_clamp_spanner_counter(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_SPANNER_COUNTER")

    # Drawn looking at the side; H is X, V is Y, and the pad runs along Z.
    # The foot is left square here and swept back at the ends afterwards.
    body = fcprim.sketch(bdy, "Body", "XY_Plane", offset=-half_z)
    fcprim.polyline(body, (
        broken((spine_x[0], spine_y[0]), (spine_x[0], spine_y[1]),
               (block_x[1], spine_y[0]), edge_break)
        + broken((block_x[1], spine_y[0]), (spine_x[0], spine_y[0]),
                 (block_x[1], base_y), edge_break)
        + broken((block_x[1], base_y), (block_x[1], spine_y[0]),
                 (spine_x[1], base_y), edge_break)
        + [(spine_x[1], base_y), (spine_x[1], gap_top),
           (block_x[0], gap_top)]
        + broken((block_x[0], block_y[0]), (block_x[0], gap_top),
                 (block_x[1], block_y[0]), edge_break)
        + broken((block_x[1], block_y[0]), (block_x[0], block_y[0]),
                 (block_x[1], block_y[1]), edge_break)
        + broken((block_x[1], block_y[1]), (block_x[1], block_y[0]),
                 (spine_x[0], block_y[1]), edge_break)
        + broken((spine_x[0], spine_y[1]), (block_x[1], spine_y[1]),
                 (spine_x[0], spine_y[0]), edge_break)
    ), name="side")
    fcprim.pad(bdy, "Body", body, 2 * half_z)

    # Both end faces are broken 1 mm round the outside, stopping where the part
    # mates: the gap it straddles, the foot, the block's underside.
    mates_at = (("x", spine_x[1]), ("x", block_x[0]),
                ("y", block_y[0]), ("y", gap_top),
                ("y", base_y), ("y", spine_y[0]))
    stays_sharp = ((spine_x[0], spine_y[0]), (block_x[0], block_y[0]),
                   (block_x[1], block_y[0]), (block_x[1], spine_y[0]),
                   (block_x[1], base_y))

    def outside(edge):
        point = fcprim.midpoint(edge)
        if abs(abs(point.z) - half_z) > 1e-6:
            return False
        # Nothing in the foot: the nose sweeps all of it away at the ends, and
        # its front face is only as tall as the break itself.
        if point.y < base_y:
            return False
        if any(abs({"x": point.x, "y": point.y}[axis] - value) < 1e-6
               for axis, value in mates_at):
            return False
        return all(math.hypot(point.x - cx, point.y - cy) > edge_break
                   for cx, cy in stays_sharp)

    fcprim.chamfer(bdy, "Edges", edge_break, outside)

    # The nose: a tangent in from the end face, round the radius, and a tangent
    # back out to the foot's front.  Drawn looking down; H is X, V is Z.
    low = tangent_from((nose_ends, -half_z), (nose_at[0], -nose_at[1]),
                       nose_r, -1)
    high = tangent_from((block_x[1], -nose_meets), (nose_at[0], -nose_at[1]),
                        nose_r, 1)
    nose = fcprim.sketch(bdy, "Nose", "XZ_Plane", offset=-base_y)
    fcprim.polyline(nose, [
        (nose_ends, -half_z),
        low, high,
        (block_x[1], -nose_meets),
        (block_x[1], nose_meets),
        (high[0], -high[1]), (low[0], -low[1]),
        (nose_ends, half_z),
        (block_x[1] + over, half_z + over),
        (block_x[1] + over, -half_z - over),
    ], name="nose", arcs={1: -nose_r, 5: -nose_r})
    fcprim.pocket(bdy, "Nose", nose, base_y - spine_y[0], reversed_=True)

    # The slot the spanner swings in.  Drawn end on; H is Y, V is Z.  Its
    # bottom closes to a point in a 120 degree vee, so it prints unsupported.
    opens = slot_root + slot_z / math.tan(math.radians(60.0))
    slot = fcprim.sketch(bdy, "Spanner slot", "YZ_Plane", offset=slot_x[0])
    fcprim.polyline(slot, [
        (slot_root, 0.0),
        (opens, slot_z),
        (block_y[1] + over, slot_z),
        (block_y[1] + over, -slot_z),
        (opens, -slot_z),
    ], name="slot")
    fcprim.pocket(bdy, "Spanner slot", slot, slot_x[1] - slot_x[0],
                  reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolts", "XZ_Plane", offset=-bolt_y[0])
    for side in (-1, 1):
        fcprim.circle(bolts, (nose_at[0], side * bolt_z), bolt_hole_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, bolt_y[1] - bolt_y[0])

    bore = fcprim.sketch(bdy, "Screw bore", "YZ_Plane", offset=spine_x[0])
    fcprim.circle(bore, (0.0, 0.0), screw_d, name="screw")
    fcprim.pocket(bdy, "Screw clearance", bore, block_x[1] - spine_x[0],
                  reversed_=True)

    # A nut slot in from each end, closed by a 90 degree vee.
    slots = fcprim.sketch(bdy, "Nut slots", "XZ_Plane", offset=-slot_y[1])
    for side in (-1, 1):
        fcprim.polyline(slots, [
            (nose_at[0] - slot_across / 2, side * (half_z + over)),
            (nose_at[0] - slot_across / 2,
             side * (slot_apex + slot_across / 2)),
            (nose_at[0], side * slot_apex),
            (nose_at[0] + slot_across / 2,
             side * (slot_apex + slot_across / 2)),
            (nose_at[0] + slot_across / 2, side * (half_z + over)),
        ], name=f"slot{'np'[side > 0]}")
    fcprim.pocket(bdy, "Nut slots", slots, slot_y[1] - slot_y[0],
                  reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  All three are on the
    # spanner screw's own axis, and what tells them apart is which face they
    # are on: the spine's front, where the stencil holder is pulled against;
    # the near wall of the spanner's slot, where the nut sits; and the block's
    # far face, where the studding comes out.
    fcprim.lcs(bdy, "HOLDER_FRONT", at=(spine_x[1], 0.0, 0.0), axis=(-1, 0, 0),
               roll=90.0)
    fcprim.lcs(bdy, "NUT", at=(slot_x[0], 0.0, 0.0), axis=(-1, 0, 0))
    fcprim.lcs(bdy, "STUD", at=(block_x[1], 0.0, 0.0), axis=(1, 0, 0),
               roll=90.0)

    return bdy


fcprim.make(__file__, "TOP_CLAMP_SPANNER_COUNTER", top_clamp_spanner_counter,
            mesh_volume)
