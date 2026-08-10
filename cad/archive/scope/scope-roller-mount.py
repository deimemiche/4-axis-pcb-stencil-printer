"""SCOPE_ROLLER_MOUNT - what hangs a roller wheel off a frame member.

Michael's own part, transcribed from `roller_mount()` in
[`../microscope-mount/roller.py`](../microscope-mount/roller.py).

A 53.5 x 20 x 4 plate with two M5 counterbored through it 20 apart -- one
extrusion cell -- and a block hanging 25 below one end.  The block holds an M8
nyloc across it and `SCOPE_ROLLER_WHEEL` runs on the bolt, 16.25 under the
plate, which puts the wheel's own rim 2.25 clear of it.

Three of the source's "chamfers" are shape rather than finish, and they are
drawn here as what they are:

* the block's two bottom corners are broken **5 mm**, a quarter of the plate's
  width, so it comes to a foot rather than a slab.  Drawn into the block's own
  section.
* the corner between the plate's underside and the block is broken **4 mm**,
  and that break *adds* material -- it is the gusset that stops the block
  folding.  A `PartDesign::Chamfer` can only take material away, so it is a
  tapered pad's worth of triangle in section; see `../README.md`.
* everything else is a 0.5 edge break and is left off, as everywhere here.

    Plate      sketch -> Pad     53.5 x 20 x 4
    Block      sketch -> Pad     what hangs off it, feet and all
    Gusset     sketch -> Pad     the 4 mm triangle between the two
    Axle nut   sketch -> Pocket  the M8 nyloc, 9.5 into the block's inner face
    Axle       sketch -> Pocket  and the M8 itself, through
    Frame      sketch -> Pocket  two 5.5 through the plate
    Spotfaces  sketch -> Pocket  9.1 x 0.1 under each head

**The nut pocket is drawn 6.8 deep and the nut is 9.5.**  That is the source:
`nutcatchParallel` defaults to a plain hexagon nut, and the `hexagon_lock` it
reads `nut_l` from is used only to work out how long the block is.  So the
pocket is a plain M8 nut's 6.8 and the nyloc's collar stands 2.7 proud of it,
in the 4 mm the block was made longer for.  It is transcribed as drawn.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From ../microscope-mount/settings.py.
wall = 4.0               # Settings.wall_t
loose_fit = 0.5          # Settings.loose_fit
v_slot = 20.0            # Settings.v_slot_d
frame_bolt_d = 5.0       # M5, Settings.frame_bolt
frame_head_d = 8.5       # its socket head

# The M8 the wheel turns on, from cq_queryabolt's own tables.
axle_d = 8.0
axle_nut_w = 13.0        # across the flats
axle_nut_t = 6.8         # a plain hexagon M8; see the docstring
nyloc_t = 9.5            # what the block is made long enough for

wheel_od = 22.0 + 2 * 3.0                # 28, SCOPE_ROLLER_WHEEL's own

plate_l = 2 * v_slot + nyloc_t + wall    # 53.5
plate_w = v_slot                         # 20
plate_t = wall                           # 4

block_l = nyloc_t + wall                 # 13.5, along the plate
block_h = wheel_od / 2.0 + axle_nut_w / 2.0 + wall + loose_fit    # 25
block_x = (plate_l / 2.0 - block_l, plate_l / 2.0)                # 13.25, 26.75

foot = v_slot / 4.0                      # 5, off each bottom corner
gusset = wall                            # 4, between plate and block

# Where the axle sits: the source measures it down from the block's own middle.
axle_z = -block_h / 2.0 - wall / 2.0 - ((wheel_od + loose_fit) - block_h) / 2.0

frame_hole_d = frame_bolt_d + loose_fit          # 5.5
spot_d = frame_head_d + loose_fit + 0.1          # 9.1, head plus clearances
spot_deep = 0.1
# Two bolts a cell apart, centred on what the plate has left over -- which is
# the underside as far as the block, and not the plate as a whole.
frame_mid = (-plate_l / 2.0 + block_x[0]) / 2.0          # -6.75
frame_at = (frame_mid - v_slot / 2.0, frame_mid + v_slot / 2.0)


def block_section():
    """The block looking along the plate: 20 wide, 25 deep, feet broken 5."""
    half = plate_w / 2.0
    return [
        (-half, 0.0), (-half, -(block_h - foot)), (-(half - foot), -block_h),
        (half - foot, -block_h), (half, -(block_h - foot)), (half, 0.0),
    ]


def expected_volume():
    """Arithmetic on the numbers above; see `../STATUS.md`."""
    plate = plate_l * plate_w * plate_t
    block = (plate_w * block_h - foot ** 2) * block_l
    web = gusset ** 2 / 2.0 * plate_w

    nut = math.sqrt(3.0) / 2.0 * axle_nut_w ** 2 * axle_nut_t
    axle = math.pi / 4.0 * axle_d ** 2 * block_l
    shared = math.pi / 4.0 * axle_d ** 2 * axle_nut_t      # counted twice

    frame = 2 * math.pi / 4.0 * frame_hole_d ** 2 * plate_t
    spot = 2 * math.pi / 4.0 * (spot_d ** 2 - frame_hole_d ** 2) * spot_deep

    return plate + block + web - nut - axle + shared - frame - spot


def mount(doc):
    bdy = fcprim.body(doc, "SCOPE_ROLLER_MOUNT")

    plate = fcprim.sketch(bdy, "Plate", "XY_Plane")
    fcprim.polyline(plate, [
        (-plate_l / 2.0, -plate_w / 2.0), (plate_l / 2.0, -plate_w / 2.0),
        (plate_l / 2.0, plate_w / 2.0), (-plate_l / 2.0, plate_w / 2.0),
    ], name="plate")
    fcprim.pad(bdy, "Plate", plate, plate_t)

    # The block is a prism along X, so it is drawn on YZ and padded that way.
    block = fcprim.sketch(bdy, "Block", "YZ_Plane", offset=block_x[0])
    fcprim.polyline(block, block_section(), name="block")
    fcprim.pad(bdy, "Block", block, block_l)

    # The gusset adds material, so it is a pad and not a chamfer.
    web = fcprim.sketch(bdy, "Gusset", "XZ_Plane")
    fcprim.polyline(web, [
        (block_x[0] - gusset, 0.0), (block_x[0], 0.0), (block_x[0], -gusset),
    ], name="gusset")
    fcprim.pad(bdy, "Gusset", web, plate_w, midplane=True)

    # Both the nut and the bolt enter the block's inner face, which is where
    # the wheel runs, so both are drawn on it and cut away from it.
    nut = fcprim.sketch(bdy, "Axle nut", "YZ_Plane", offset=block_x[0])
    fcprim.polygon(nut, (0.0, axle_z), axle_nut_w, name="nut")
    fcprim.pocket(bdy, "Axle nut", nut, axle_nut_t, reversed_=True)

    axle = fcprim.sketch(bdy, "Axle", "YZ_Plane", offset=block_x[0])
    fcprim.circle(axle, (0.0, axle_z), axle_d, name="axle")
    fcprim.pocket(bdy, "Axle", axle, midplane=True)

    frame = fcprim.sketch(bdy, "Frame bolts", "XY_Plane")
    for i, x in enumerate(frame_at):
        fcprim.circle(frame, (x, 0.0), frame_hole_d, name=f"bolt{i + 1}")
    fcprim.pocket(bdy, "Frame bolts", frame, midplane=True)

    spot = fcprim.sketch(bdy, "Spotfaces", "XY_Plane")
    for i, x in enumerate(frame_at):
        fcprim.circle(spot, (x, 0.0), spot_d, name=f"spot{i + 1}")
    fcprim.pocket(bdy, "Spotfaces", spot, spot_deep, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   MOUNT/BOLT  the plate's top face, and the two M5 up into the member
    #   AXLE        the face the wheel runs against, looking out of it
    fcprim.lcs(bdy, "MOUNT", at=(frame_mid, 0.0, plate_t), axis=(0, 0, 1))
    for i, x in enumerate(frame_at):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, 0.0, plate_t), axis=(0, 0, 1))
    fcprim.lcs(bdy, "AXLE", at=(block_x[0], 0.0, axle_z), axis=(-1, 0, 0))

    return bdy


fcprim.make(__file__, "SCOPE_ROLLER_MOUNT", mount, expected_volume())
