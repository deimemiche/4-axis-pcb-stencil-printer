"""SCOPE_TOP - the cap on the extrusion's end, and the leadscrew's top bearing.

Michael's own part, transcribed from `top()` in
[`../../microscope-mount/microscope-mount.py`](../../microscope-mount/microscope-mount.py).
It closes the top of the column and does three things at once:

* a **28.5 mm square plate** with one 5.5 hole on the axis, which is an M5
  into the extrusion's own centre bore -- that single bolt is what holds the
  cap on.
* a **socket** standing 4 mm off its underside, 20.5 square inside, that slips
  over the extrusion and keeps the cap square to it.  The source calls it the
  indexing feature.  It is a U rather than a ring: the side the leadscrew is on
  is cut away, because that is where the nut boss of `SCOPE_SLIDER` runs.
* a **seat for a 605 bearing**, 14 bored through a 22 mm square boss, 18.25 off
  the axis -- the same 18.25 the slider carries its nut at.  The bearing is
  `../misc/BEARING_14X5X5`, 14 x 5 x 5, and the plate is 5 thick, so it goes in
  flush.

    Plate    sketch -> Pad     the plate and the bearing boss, bored for both
    Socket   sketch -> Pad     the U that goes over the extrusion, downwards

The press-fit backstop under the bearing is **left out**, because the source
leaves it out: it is there, commented, and putting it in would be designing
rather than transcribing.  Nothing holds the bearing in against the leadscrew
pulling down on it; a shoulder there is the first thing to add if it walks.

The edge breaks are left off, as everywhere in `scope/`; see `../STATUS.md`.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From ../../microscope-mount/settings.py.
wall = 4.0               # Settings.wall_t
loose_fit = 0.5          # Settings.loose_fit
v_slot = 20.0            # Settings.v_slot_d
frame_bolt_d = 5.0       # M5, Settings.frame_bolt

# The 605 bearing the leadscrew's top end turns in.
bearing_od = 14.0
bearing_t = 5.0

socket_id = v_slot + loose_fit           # 20.5, over the extrusion
plate_w = socket_id + 2 * wall           # 28.5, and the same as the slider's

rod_clearance = 8.0 / 2.0                # rod_nut_w / 2, the source's own
rod_y = plate_w / 2.0 + rod_clearance    # 18.25, the leadscrew off the axis
boss_w = bearing_od + 2 * wall           # 22, square about the bearing
boss_y = (plate_w + rod_clearance + wall) / 2.0    # 18.25, its own centre

bolt_hole_d = frame_bolt_d + loose_fit   # 5.5, into the extrusion's core

thickness = bearing_t                    # 5, so the bearing is flush in it
socket_h = wall                          # 4, how far the U reaches down


def plate_outline():
    """The plate and the bearing boss, which meet as one outline."""
    half = plate_w / 2.0
    return [
        (-half, -half), (half, -half), (half, half),
        (boss_w / 2.0, half), (boss_w / 2.0, boss_y + boss_w / 2.0),
        (-boss_w / 2.0, boss_y + boss_w / 2.0), (-boss_w / 2.0, half),
        (-half, half),
    ]


def socket_outline():
    """The U: the plate's own square, with the leadscrew's side cut out.

    The source cuts a 20.5 x 28.5 pocket offset 4 mm towards the leadscrew,
    which reaches past the far edge -- so what is left is three walls and an
    open side, not four.
    """
    half = plate_w / 2.0
    inner = socket_id / 2.0
    return [
        (-half, -half), (half, -half), (half, half),
        (inner, half), (inner, -inner), (-inner, -inner), (-inner, half),
        (-half, half),
    ]


def expected_volume():
    """Arithmetic on the numbers above; see `../STATUS.md`."""
    overlap = boss_w * (plate_w / 2.0 - (boss_y - boss_w / 2.0))
    plate = (plate_w ** 2 + boss_w ** 2 - overlap
             - math.pi / 4.0 * bolt_hole_d ** 2
             - math.pi / 4.0 * bearing_od ** 2) * thickness
    inner = socket_id / 2.0
    socket = (plate_w ** 2 - socket_id * (plate_w / 2.0 + inner)) * socket_h
    return plate + socket


def top(doc):
    bdy = fcprim.body(doc, "SCOPE_TOP")

    plate = fcprim.sketch(bdy, "Plate", "XY_Plane")
    fcprim.polyline(plate, plate_outline(), name="plate")
    fcprim.circle(plate, (0.0, 0.0), bolt_hole_d, name="bolt")
    fcprim.circle(plate, (0.0, rod_y), bearing_od, name="seat")
    fcprim.pad(bdy, "Plate", plate, thickness)

    socket = fcprim.sketch(bdy, "Socket", "XY_Plane")
    fcprim.polyline(socket, socket_outline(), name="socket")
    fcprim.pad(bdy, "Socket", socket, socket_h, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   MOUNT/BOLT  the extrusion's end face, and the M5 down into its core
    #   BEARING     the seat's axis, which the leadscrew turns on
    fcprim.lcs(bdy, "MOUNT", axis=(0, 0, -1))
    fcprim.lcs(bdy, "BOLT", axis=(0, 0, -1))
    fcprim.lcs(bdy, "SLOT", at=(0.0, 0.0, -socket_h), axis=(0, 0, -1))
    fcprim.lcs(bdy, "BEARING", at=(0.0, rod_y, 0.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "ROD", at=(0.0, rod_y, thickness), axis=(0, 0, 1))

    return bdy


fcprim.make(__file__, "SCOPE_TOP", top, expected_volume())
