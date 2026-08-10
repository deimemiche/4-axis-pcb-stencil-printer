"""BOT_Z_AXIS_COUNTER_HOLDER - takes the reaction of the Z axis screw.

Reconstructed from the original author's BOT_Z_AXIS_COUNTER_HOLDER.stl, in that
mesh's own coordinates: a 40 x 14 plate bolted flat to the bottom frame, with a
20 mm tower standing on it, Y up.

The screw runs up the tower's 8.4 mm bore, which stops 1 mm short of the bottom.
Nine millimetres up sits an M8 nut, in a hexagonal seat that is open sideways so
the nut goes in from the front rather than being trapped.

The tower blends into the plate two ways at once: a 2 mm fillet in plan, where
its barrel runs into the plate's long edges, and a 2 mm fillet in section, where
it stands off the plate's top face.  The second one is a surface, not an
extrusion, so it is swept rather than drawn, and then cut back to the plate's
long edges - past those the barrel stands on its own and has nothing to blend
into.

    Plate       sketch -> Pad         the plate and the tower's footprint
    Tower       sketch -> Pad         the barrel, full height
    Tower root  sketch -> Revolution  the fillet where it meets the plate
    Root trim   sketch -> Pocket      and off again where there is no plate
    Screw bore  sketch -> Pocket      8.4 mm, stopping short of the bottom
    Nut seat    sketch -> Pocket      the hexagon and the slot it slides in by
    Bolt holes  sketch -> Pocket      two M4 clearance holes through the plate
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

plate_x = 40.0
plate_z = 14.0
plate_thickness = 5.0
corner_r = 2.0

tower_d = 20.0
tower_height = 24.0
blend_r = 2.0            # barrel into the plate's long edges, and off its face

bore_d = 8.4
bore_floor = 1.0         # how much of the plate is left under the screw

nut_across_flats = 13.3  # M8
nut_y = (13.0, 22.0)

bolt_x = 16.0
bolt_hole_d = 4.5        # M4 clearance

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 6348.698


def bot_z_axis_counter_holder(doc):
    bdy = fcprim.body(doc, "BOT_Z_AXIS_COUNTER_HOLDER")
    half_x, half_z, tower_r = plate_x / 2, plate_z / 2, tower_d / 2

    # The blend rolls along the plate's long edge, so its centre stands one
    # radius outside that edge and one radius plus tower_r off the axis.
    blend_x = math.sqrt((tower_r + blend_r) ** 2 - (half_z + blend_r) ** 2)
    reach = tower_r / (tower_r + blend_r)
    on_tower = (blend_x * reach, (half_z + blend_r) * reach)

    # Drawn looking down on the plate; H is X, V is Z, and the pad runs down.
    plate = fcprim.sketch(bdy, "Plate", "XZ_Plane", offset=-plate_thickness)
    fcprim.polyline(plate, [
        (half_x, -half_z),
        (half_x, half_z),
        (blend_x, half_z),
        on_tower,
        (-on_tower[0], on_tower[1]),
        (-blend_x, half_z),
        (-half_x, half_z),
        (-half_x, -half_z),
        (-blend_x, -half_z),
        (-on_tower[0], -on_tower[1]),
        (on_tower[0], -on_tower[1]),
        (blend_x, -half_z),
    ], name="plate",
        fillets={0: corner_r, 1: corner_r, 6: corner_r, 7: corner_r},
        arcs={2: -blend_r, 3: tower_r, 4: -blend_r,
              8: -blend_r, 9: tower_r, 10: -blend_r})
    fcprim.pad(bdy, "Plate", plate, plate_thickness)

    tower = fcprim.sketch(bdy, "Tower", "XZ_Plane", offset=-tower_height)
    fcprim.circle(tower, (0.0, 0.0), tower_d, name="tower")
    fcprim.pad(bdy, "Tower", tower, tower_height)

    # The root fillet, drawn once in section and swept all the way round.
    root = fcprim.sketch(bdy, "Tower root", "XY_Plane")
    fcprim.polyline(root, [
        (tower_r, plate_thickness),
        (tower_r + blend_r, plate_thickness),
        (tower_r, plate_thickness + blend_r),
    ], name="root", arcs={1: -blend_r})
    fcprim.revolution(bdy, "Tower root", root, axis="V_Axis")

    # Sweeping it all the way round puts fillet where the barrel has no plate
    # to stand on - out past the plate's long edges, where it sticks out on its
    # own - so that much is taken straight back off again.  Everything beyond
    # the edge goes except the barrel itself, which the arc here keeps.
    out = tower_r + blend_r + over
    crosses = math.sqrt(tower_r ** 2 - half_z ** 2)
    trim = fcprim.sketch(bdy, "Root trim", "XZ_Plane",
                         offset=-(plate_thickness + blend_r))
    for side in (1, -1):
        fcprim.polyline(trim, [
            (-side * out, side * half_z),
            (-side * crosses, side * half_z),
            (side * crosses, side * half_z),
            (side * out, side * half_z),
            (side * out, side * out),
            (-side * out, side * out),
        ], name=f"trim{'np'[side > 0]}", arcs={1: -tower_r})
    fcprim.pocket(bdy, "Root trim", trim, blend_r, reversed_=True)

    bore = fcprim.sketch(bdy, "Screw bore", "XZ_Plane", offset=-tower_height)
    fcprim.circle(bore, (0.0, 0.0), bore_d, name="screw")
    fcprim.pocket(bdy, "Screw clearance", bore, tower_height - bore_floor,
                  reversed_=True)

    # Half a hexagon closed off by a slot running out past the barrel, so the
    # nut can be pushed in from the side.
    seat = fcprim.sketch(bdy, "Nut seat", "XZ_Plane", offset=-nut_y[1])
    across_corners = nut_across_flats * 2 / math.sqrt(3)
    fcprim.polyline(seat, [
        (nut_across_flats / 2, tower_r + over),
        (nut_across_flats / 2, -across_corners / 4),
        (0.0, -across_corners / 2),
        (-nut_across_flats / 2, -across_corners / 4),
        (-nut_across_flats / 2, tower_r + over),
    ], name="nut")
    fcprim.pocket(bdy, "Nut clearance", seat, nut_y[1] - nut_y[0],
                  reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane",
                          offset=-plate_thickness)
    for x in (-bolt_x, bolt_x):
        fcprim.circle(bolts, (x, 0.0), bolt_hole_d,
                      name=f"bolt{'np'[x > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, plate_thickness, reversed_=True)

    return bdy


fcprim.make(__file__, "BOT_Z_AXIS_COUNTER_HOLDER", bot_z_axis_counter_holder,
            mesh_volume)
