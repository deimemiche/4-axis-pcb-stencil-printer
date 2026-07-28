"""SR_BEARING_PLATE - spider that carries the rotary axis bearing.

Reconstructed from the original author's SR_BEARING_PLATE.stl, in that mesh's
own coordinates: a 130 mm disc only 3 mm deep, spanning Y = 8 .. 11, directly
under the slewing ring.

Almost all of it is fresh air.  Only the outer rim runs the full circle, and
only for the topmost millimetre; below that a cross of narrow arms reaches out
to four bolt pads at the compass points.  Each tier is one pad off the same top
face, so the plate is described by how deep each feature reaches rather than by
cutting a disc away again.

    Bolt pads  sketch -> Pad     four bosses, the full 3 mm
    Cross      sketch -> Pad     the arms, 2 mm
    Rim        sketch -> Pad     the annulus, 1 mm
    Bolt holes sketch -> Pocket  M3 clearance through the pads
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

top_y = 11.0             # the plate's upper face, in machine coordinates

plate_d = 130.0
rim_inner_d = 114.0
rim_depth = 1.0          # how far down the full circle reaches

arm_width = 3.4          # the cross that spans the opening
arm_depth = 2.0

pad_circle_r = 61.0      # bolt pad centres
pad_d = 8.0
pad_depth = 3.0          # the pads go all the way down
bolt_hole_d = 3.4        # M3 clearance

mesh_volume = 4887.350


def sr_bearing_plate(doc):
    bdy = fcprim.body(doc, "SR_BEARING_PLATE")
    half = arm_width / 2
    reach = plate_d / 2

    pads = fcprim.sketch(bdy, "Bolt pads", "XZ_Plane", offset=-top_y)
    for i, (x, z) in enumerate(((pad_circle_r, 0.0), (-pad_circle_r, 0.0),
                                (0.0, pad_circle_r), (0.0, -pad_circle_r))):
        fcprim.circle(pads, (x, z), pad_d, name=f"pad{i}")
    fcprim.pad(bdy, "Bolt pads", pads, pad_depth)

    # One closed twelve sided outline rather than two crossing rectangles,
    # which PartDesign will not take in a single profile.
    cross = fcprim.sketch(bdy, "Cross", "XZ_Plane", offset=-top_y)
    fcprim.polyline(cross, [
        (reach, -half), (reach, half), (half, half), (half, reach),
        (-half, reach), (-half, half), (-reach, half), (-reach, -half),
        (-half, -half), (-half, -reach), (half, -reach), (half, -half),
    ], name="arm")
    fcprim.pad(bdy, "Cross", cross, arm_depth)

    rim = fcprim.sketch(bdy, "Rim", "XZ_Plane", offset=-top_y)
    fcprim.circle(rim, (0.0, 0.0), plate_d, name="outer")
    fcprim.circle(rim, (0.0, 0.0), rim_inner_d, name="inner")
    fcprim.pad(bdy, "Rim", rim, rim_depth)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane", offset=-top_y)
    for i, (x, z) in enumerate(((pad_circle_r, 0.0), (-pad_circle_r, 0.0),
                                (0.0, pad_circle_r), (0.0, -pad_circle_r))):
        fcprim.circle(bolts, (x, z), bolt_hole_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, reversed_=True)

    return bdy


fcprim.make(__file__, "SR_BEARING_PLATE", sr_bearing_plate, mesh_volume)
