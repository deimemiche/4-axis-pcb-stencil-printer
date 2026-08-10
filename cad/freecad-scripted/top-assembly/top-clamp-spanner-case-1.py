"""TOP_CLAMP_SPANNER_CASE_1 - shallow lid of the stencil clamp's spanner case.

Reconstructed from the original author's TOP_CLAMP_SPANNER_CASE_1.stl, in that
mesh's own coordinates: the 2 mm plate spanning X = 0 .. 2 that closes onto
TOP_CLAMP_SPANNER_CASE_2's cavity, sharing its outline exactly.

A 5 mm rib stands proud of the outer face along the plate's whole length,
stiffening the lid against the spanner pushing back at it.  Front to back run
the spanner's own spindle and the two M4 bolts that clamp the case shut.

    Plate     sketch -> Pad     the lid, same outline as the deep half
    Rib       sketch -> Pad     the stiffener on the outer face
    Spindle   sketch -> Pocket  through both
    Bolt holes sketch -> Pocket through both
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

face_x = 0.0             # the face that mates with CASE_2
plate_thickness = 2.0
rib_height = 1.2         # stands out the other way, to X = -1.2
rib_half_y = 2.5

plate_half_y = 7.0
plate_half_z = 29.0
corner_r = 3.0

bolt_z = 24.0
bolt_hole_d = 4.5        # M4 clearance
spindle_d = 5.399        # the spanner's own shaft

mesh_volume = 1782.273


def top_clamp_spanner_case_1(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_SPANNER_CASE_1")

    plate = fcprim.sketch(bdy, "Plate", "YZ_Plane", offset=face_x)
    fcprim.polyline(plate, [
        (-plate_half_y, -plate_half_z),
        (plate_half_y, -plate_half_z),
        (plate_half_y, plate_half_z),
        (-plate_half_y, plate_half_z),
    ], name="plate", fillets={0: corner_r, 1: corner_r,
                              2: corner_r, 3: corner_r})
    fcprim.pad(bdy, "Plate pad", plate, plate_thickness)

    rib = fcprim.sketch(bdy, "Rib", "YZ_Plane", offset=face_x - rib_height)
    fcprim.polyline(rib, [
        (-rib_half_y, -plate_half_z),
        (rib_half_y, -plate_half_z),
        (rib_half_y, plate_half_z),
        (-rib_half_y, plate_half_z),
    ], name="rib")
    fcprim.pad(bdy, "Rib pad", rib, rib_height)

    spindle = fcprim.sketch(bdy, "Spindle", "YZ_Plane",
                            offset=face_x - rib_height)
    fcprim.circle(spindle, (0.0, 0.0), spindle_d, name="spindle")
    fcprim.pocket(bdy, "Spindle clearance", spindle, reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "YZ_Plane",
                          offset=face_x - rib_height)
    for side in (-1, 1):
        fcprim.circle(bolts, (0.0, side * bolt_z), bolt_hole_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, reversed_=True)

    return bdy


fcprim.make(__file__, "TOP_CLAMP_SPANNER_CASE_1", top_clamp_spanner_case_1,
            mesh_volume)
