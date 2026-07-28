"""BOT_BEARING_MOUNT_X_AXIS - carries the driven end of the X axis screw.

Reconstructed from the original author's BOT_BEARING_MOUNT_X_AXIS.stl, in that
mesh's own coordinates: 27 mm along the screw, standing on a plate that bolts
down to the frame.

Seen end on it is a T - a 4 mm plate with a housing standing on it - and the
15.2 mm bearing seat is bored straight through the housing, opening out into a
1.5 mm 45 degree mouth at each end so the bearing leads in.

The housing's top carries a rod in a half round trough that opens on 45 degree
tangents, with an M3 either side of it to pull a cap down.  Each of those nuts
slides in along a slot from the end face that a 90 degree vee closes off, the
same trick as the spanner counter uses.

The plate's own four bolts come up from underneath, and their nuts drop into
hexagonal seats in its top face, which the housing is too narrow to cover.

    Profile     sketch -> Pad     the T, padded along the screw
    Bearing     sketch -> Groove  the seat and its two lead ins
    Trough      sketch -> Pocket  the rod's seat in the top
    Cap bolts   sketch -> Pocket  two M3 down into the bearing seat
    Cap nuts    sketch -> Pocket  their slots, in from each end face
    Plate bolts sketch -> Pocket  four M3 up through the plate
    Plate nuts  sketch -> Pocket  their hexagons, open to the plate's top
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

width = 27.0             # along the screw

plate_y = (-11.6, -7.6)
plate_z = 17.5           # either side of the screw
house_y = 14.6           # the top of the housing
house_z = 10.5

seat_d = 15.2            # bearing outside diameter
seat_lead = 1.5          # 45 degrees, opening out to each end face

trough_r = 4.05          # the rod's seat, centred on the top face
trough_flare = 45.0      # how its sides open out

cap_bolt_x = 9.0         # an M3 either side of the trough
cap_bolt_d = 3.5
cap_bolt_floor = 6.0     # anything past here is inside the bearing seat
cap_nut_across = 5.7
cap_nut_y = (9.6, 12.6)
cap_nut_apex = 4.505     # where the slot's vee closes

plate_bolt = (8.5, 13.35)
plate_bolt_d = 3.6
plate_bolt_y = -9.6      # up from the plate's underside to here
plate_nut_across = 5.7   # and the hexagon above it, open to the plate's top

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 10097.752


def bot_bearing_mount_x_axis(doc):
    bdy = fcprim.body(doc, "BOT_BEARING_MOUNT_X_AXIS")
    half_x, seat_r = width / 2, seat_d / 2
    mouth_r = seat_r + seat_lead

    # Drawn looking along the screw; H is Y, V is Z, and the pad runs along X.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (plate_y[0], -plate_z),
        (plate_y[1], -plate_z),
        (plate_y[1], -house_z),
        (house_y, -house_z),
        (house_y, house_z),
        (plate_y[1], house_z),
        (plate_y[1], plate_z),
        (plate_y[0], plate_z),
    ], name="mount")
    fcprim.pad(bdy, "Body", profile, width, midplane=True)

    # Half the seat's longitudinal section, revolved about the screw.  H is X,
    # V is the radius.
    bore = fcprim.sketch(bdy, "Bearing", "XY_Plane")
    fcprim.polyline(bore, [
        (-half_x, 0.0),
        (-half_x, mouth_r),
        (-half_x + seat_lead, seat_r),
        (half_x - seat_lead, seat_r),
        (half_x, mouth_r),
        (half_x, 0.0),
    ], name="seat")
    fcprim.groove(bdy, "Bearing seat", bore, axis="H_Axis")

    # The trough, drawn on the same plane: a half round centred on the top face
    # with a tangent off each side.  Its sides are carried up past the top so
    # the profile closes in fresh air rather than on the face itself.
    reach = trough_r * math.cos(math.radians(trough_flare))
    touch = (reach, house_y - reach)
    trough = fcprim.sketch(bdy, "Trough", "XY_Plane")
    fcprim.polyline(trough, [
        (-2 * reach, house_y + over),
        (-2 * reach, house_y),
        (-touch[0], touch[1]),
        (touch[0], touch[1]),
        (2 * reach, house_y),
        (2 * reach, house_y + over),
    ], name="trough", arcs={2: trough_r})
    fcprim.pocket(bdy, "Trough", trough, 2 * (house_z + over), midplane=True)

    # Two M3 straight down into the seat, and the nut slots that cross them.
    # Drawn looking down; H is X, V is Z.
    bolts = fcprim.sketch(bdy, "Cap bolts", "XZ_Plane", offset=-house_y)
    for side in (-1, 1):
        fcprim.circle(bolts, (side * cap_bolt_x, 0.0), cap_bolt_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Cap bolts", bolts, house_y - cap_bolt_floor,
                  reversed_=True)

    opens = cap_nut_apex + cap_nut_across / 2
    slots = fcprim.sketch(bdy, "Cap nuts", "XZ_Plane", offset=-cap_nut_y[1])
    for side in (-1, 1):
        fcprim.polyline(slots, [
            (side * (half_x + over), cap_nut_across / 2),
            (side * opens, cap_nut_across / 2),
            (side * cap_nut_apex, 0.0),
            (side * opens, -cap_nut_across / 2),
            (side * (half_x + over), -cap_nut_across / 2),
        ], name=f"slot{'np'[side > 0]}")
    fcprim.pocket(bdy, "Cap nuts", slots, cap_nut_y[1] - cap_nut_y[0],
                  reversed_=True)

    corners = [(x * plate_bolt[0], z * plate_bolt[1])
               for x in (-1, 1) for z in (-1, 1)]

    holes = fcprim.sketch(bdy, "Plate bolts", "XZ_Plane", offset=-plate_y[0])
    for i, corner in enumerate(corners):
        fcprim.circle(holes, corner, plate_bolt_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Plate bolts", holes, plate_bolt_y - plate_y[0])

    seats = fcprim.sketch(bdy, "Plate nuts", "XZ_Plane", offset=-plate_bolt_y)
    for i, corner in enumerate(corners):
        fcprim.polygon(seats, corner, plate_nut_across, name=f"nut{i}")
    fcprim.pocket(bdy, "Plate nuts", seats, plate_y[1] - plate_bolt_y)

    # Mounting datums for the assembly; see fcprim.lcs.  This part is the
    # corner of the XY stage, so it carries three axes at right angles: the
    # bearing rides the X rail, the trough clamps the Y rail across it, and the
    # plate bolts down to the print plate underneath.
    fcprim.lcs(bdy, "RAIL", axis=(1, 0, 0))
    fcprim.lcs(bdy, "TROUGH", at=(0.0, house_y, 0.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "PLATE", at=(0.0, plate_y[0], 0.0), axis=(0, -1, 0))
    for i, (x, z) in enumerate(corners):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, plate_y[0], z), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "BOT_BEARING_MOUNT_X_AXIS", bot_bearing_mount_x_axis,
            mesh_volume)
