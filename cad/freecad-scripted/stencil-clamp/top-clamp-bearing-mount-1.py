"""TOP_CLAMP_BEARING_MOUNT_1 - carries one end of the stencil clamp's screw.

Reconstructed from the original author's TOP_CLAMP_BEARING_MOUNT_1.stl, in that
mesh's own coordinates: X = -10 .. 16 along the screw, the bearing barrel on the
axis and a mounting plate standing off it.

The barrel takes a 15.2 mm bearing, opened out 1.5 mm at 45 degrees where it is
pressed in.  A plate runs off it tangentially and is bolted three ways at once -
one M3 along the screw, two across it - and every one of those bolts has its nut
in a slot dropped in from the top face.  Each slot ends in a 90 degree vee on the
bolt's own axis, so it prints without support.

For the first 2 mm the barrel is cut back flat: that end sits against whatever it
bolts to, and the plate does not start until past it.

TOP_CLAMP_BEARING_MOUNT_2.stl is this part mirrored in Z, vertex for vertex, so
`top-clamp-bearing-mount-2.py` reuses `bearing_mount` from here rather than
repeating it.

    Body       sketch -> Pad     barrel and plate, extruded along the screw
    Seated end sketch -> Pocket  the flat the mount sits on, and the plate's end
    Bearing    sketch -> Groove  the bore and the 45 degree lead in
    Bolts      sketch -> Pocket  three M3 clearance holes, one along, two across
    Nut slots  sketch -> Pocket  their seats, dropped in from the top face
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

screw_x = (-10.0, 16.0)  # the whole part, along the screw

barrel_d = 21.0
bore_d = 15.2            # the bearing
lead_in = 1.5            # 45 degrees, at the far end

plate_y = 16.5           # how far the plate reaches off the axis
plate_z = (-7.5, 10.5)   # the second edge is the one tangent to the barrel
plate_from_x = -8.0      # the plate starts here, not at the barrel's end

seat_y = 9.0             # the barrel is cut back to this before the plate starts

bolt_y = 12.75
bolt_hole_d = 3.5        # M3 clearance
along_z = 6.1385         # the bolt that runs along the screw
along_depth = 8.0
across_x = (-3.6, 5.6)   # the two that run across it
across_depth = 7.0

nut_across = 5.6         # the slot the nut drops down
nut_thick = 2.6
nut_from_face = 2.0      # how far in from the face the bolt enters
nut_floor = 11.1334      # where the vee starts, at the slot's edges

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 7142.368


def bearing_mount(doc, name, hand=1):
    """Build the mount; `hand` = -1 mirrors it in Z, which is the other one."""
    bdy = fcprim.body(doc, name)
    barrel_r, length = barrel_d / 2, screw_x[1] - screw_x[0]
    chord, tangent = (hand * z for z in plate_z)

    # Where the plate's far edge crosses the barrel, and how far round the
    # barrel is left over between there and the tangent edge.  Mirroring turns
    # the profile inside out, so the sweep changes hand with it.
    meets = math.sqrt(barrel_r ** 2 - plate_z[0] ** 2)
    sweep = hand * (360.0 + math.degrees(math.atan2(plate_z[0], meets)) - 90.0)

    # Drawn looking along the screw; H is Y, V is Z.
    body = fcprim.sketch(bdy, "Body", "YZ_Plane", offset=screw_x[0])
    fcprim.polyline(body, [
        (meets, chord),
        (plate_y, chord),
        (plate_y, tangent),
        (0.0, tangent),
    ], name="mount", arcs={3: (barrel_r, sweep)})
    fcprim.pad(bdy, "Body", body, length)

    # The first 2 mm are the seat: no plate there, and the barrel flatted off.
    seat = fcprim.sketch(bdy, "Seated end", "XY_Plane")
    fcprim.polyline(seat, [
        (screw_x[0] - over, seat_y),
        (plate_from_x, seat_y),
        (plate_from_x, plate_y + over),
        (screw_x[0] - over, plate_y + over),
    ], name="seat")
    fcprim.pocket(bdy, "Seated end", seat, midplane=True)

    # Half the bore's section, revolved about the screw.
    bore = fcprim.sketch(bdy, "Bearing", "XY_Plane")
    fcprim.polyline(bore, [
        (screw_x[0], 0.0),
        (screw_x[0], bore_d / 2),
        (screw_x[1] - lead_in, bore_d / 2),
        (screw_x[1], bore_d / 2 + lead_in),
        (screw_x[1], 0.0),
    ], name="bore")
    fcprim.groove(bdy, "Bearing seat", bore, axis="H_Axis")

    along = fcprim.sketch(bdy, "Bolt along", "YZ_Plane", offset=plate_from_x)
    fcprim.circle(along, (bolt_y, hand * along_z), bolt_hole_d, name="bolt")
    fcprim.pocket(bdy, "Bolt along", along, along_depth, reversed_=True)

    across = fcprim.sketch(bdy, "Bolts across", "XY_Plane", offset=chord)
    for i, x in enumerate(across_x):
        fcprim.circle(across, (x, bolt_y), bolt_hole_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolts across", across, across_depth,
                  reversed_=(hand > 0))

    # Every slot is the same shape seen from its own bolt's direction: a 5.6 mm
    # channel down from the top face, closed off by a vee on the bolt's axis.
    def slot(across_at, swap):
        points = [
            (plate_y + over, across_at - nut_across / 2),
            (nut_floor, across_at - nut_across / 2),
            (nut_floor - nut_across / 2, across_at),
            (nut_floor, across_at + nut_across / 2),
            (plate_y + over, across_at + nut_across / 2),
        ]
        return [(p[1], p[0]) for p in points] if swap else points

    # The one along the screw is 5.6 mm wide in Z and thick along X.
    slot_along = fcprim.sketch(bdy, "Nut slot along", "YZ_Plane",
                               offset=plate_from_x + nut_from_face)
    fcprim.polyline(slot_along, slot(hand * along_z, swap=False), name="along")
    fcprim.pocket(bdy, "Nut slot along", slot_along, nut_thick, reversed_=True)

    # The two across it are 5.6 mm wide in X and thick along Z.
    slots_across = fcprim.sketch(bdy, "Nut slots across", "XY_Plane",
                                 offset=chord + hand * nut_from_face)
    for x in across_x:
        fcprim.polyline(slots_across, slot(x, swap=True), name=f"across{x:.0f}")
    fcprim.pocket(bdy, "Nut slots across", slots_across, nut_thick,
                  reversed_=(hand > 0))

    return bdy


def top_clamp_bearing_mount_1(doc):
    return bearing_mount(doc, "TOP_CLAMP_BEARING_MOUNT_1")


# Set by top-clamp-bearing-mount-2.py, which runs this file for `bearing_mount`
# and builds the mirrored part itself.
if not globals().get("as_library"):
    fcprim.make(__file__, "TOP_CLAMP_BEARING_MOUNT_1",
                top_clamp_bearing_mount_1, mesh_volume)
