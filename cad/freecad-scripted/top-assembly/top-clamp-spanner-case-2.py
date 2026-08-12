"""TOP_CLAMP_SPANNER_CASE_2 - deep half of the stencil clamp's spanner case.

Reconstructed from the original author's TOP_CLAMP_SPANNER_CASE_2.stl, in that
mesh's own coordinates: a 14 x 58 plate with rounded corners, spanning
X = 2 .. 11.  TOP_CLAMP_SPANNER_CASE_1 is the shallow lid that closes onto it
at X = 2.

Most of the plate's middle is hollowed out to a 38 mm round cavity that houses
the spanner, leaving material only at the two ends.  A 14 mm hub stands up from
the cavity floor for the spanner to turn on.  The two M4 bolts that hold the
case together are counterbored 8.2 mm from the back.

    Plate        sketch -> Pad     the outline, padded across the case
    Cavity       sketch -> Pocket  the round hollow, from the mating face
    Hub          sketch -> Pad     spigot standing on the cavity floor
    Bolt holes   sketch -> Pocket  M4 clearance, through
    Counterbores sketch -> Pocket  their heads, from the back
    Spindle      sketch -> Pocket  through the hub
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

face_x = 2.0             # the face CASE_1 mates against
back_x = 11.0

plate_half_y = 7.0
plate_half_z = 29.0
corner_r = 3.0

cavity_d = 38.0
cavity_depth = 6.0       # measured in from the mating face
hub_d = 14.0
hub_height = 1.0         # stands proud of the cavity floor

bolt_z = 24.0
bolt_hole_d = 4.5        # M4 clearance
head_d = 8.2
head_from_face = 4.6     # where the counterbore starts

spindle_d = 5.399        # the spanner's own shaft

mesh_volume = 3572.245


def top_clamp_spanner_case_2(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_SPANNER_CASE_2")
    floor_x = face_x + cavity_depth

    # Sketched on YZ, so every pad runs backwards along +X from its face.
    plate = fcprim.sketch(bdy, "Plate", "YZ_Plane", offset=face_x)
    fcprim.polyline(plate, [
        (-plate_half_y, -plate_half_z),
        (plate_half_y, -plate_half_z),
        (plate_half_y, plate_half_z),
        (-plate_half_y, plate_half_z),
    ], name="plate", fillets={0: corner_r, 1: corner_r,
                              2: corner_r, 3: corner_r})
    fcprim.pad(bdy, "Plate pad", plate, back_x - face_x)

    cavity = fcprim.sketch(bdy, "Cavity", "YZ_Plane", offset=face_x)
    fcprim.circle(cavity, (0.0, 0.0), cavity_d, name="cavity")
    fcprim.pocket(bdy, "Cavity cut", cavity, cavity_depth, reversed_=True)

    # Added after the cavity, since the cavity would otherwise swallow it.
    hub = fcprim.sketch(bdy, "Hub", "YZ_Plane", offset=floor_x - hub_height)
    fcprim.circle(hub, (0.0, 0.0), hub_d, name="hub")
    fcprim.pad(bdy, "Hub pad", hub, hub_height)

    bolts = fcprim.sketch(bdy, "Bolt holes", "YZ_Plane", offset=face_x)
    for side in (-1, 1):
        fcprim.circle(bolts, (0.0, side * bolt_z), bolt_hole_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, reversed_=True)

    heads = fcprim.sketch(bdy, "Counterbores", "YZ_Plane",
                          offset=face_x + head_from_face)
    for side in (-1, 1):
        fcprim.circle(heads, (0.0, side * bolt_z), head_d,
                      name=f"head{'np'[side > 0]}")
    fcprim.pocket(bdy, "Head clearance", heads,
                  back_x - face_x - head_from_face, reversed_=True)

    spindle = fcprim.sketch(bdy, "Spindle", "YZ_Plane",
                            offset=floor_x - hub_height)
    fcprim.circle(spindle, (0.0, 0.0), spindle_d, name="spindle")
    fcprim.pocket(bdy, "Spindle clearance", spindle, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `SPANNER_CASE` is the
    # bolt at -Z on the face CASE_1 closes against, and `SPANNER_HANDWHEEL` the
    # hub's own face, which is what the wheel runs on.
    fcprim.lcs(bdy, "SPANNER_CASE", at=(face_x, 0.0, -bolt_z), axis=(1, 0, 0),
               roll=90.0)
    fcprim.lcs(bdy, "SPANNER_HANDWHEEL", at=(floor_x - hub_height, 0.0, 0.0),
               axis=(1, 0, 0), roll=90.0)

    # `FRAME` is the plate's own top edge, and the assembly measured it on that
    # *face* -- whose frame sits at its centre of area, which the two corner
    # radii move off the middle.  The height and the depth are the part's; the
    # position along it is kept as measured.  See ASSEMBLY.md Part II, step 6.
    fcprim.lcs(bdy, "FRAME", at=(floor_x, plate_half_y, -17.6635),
               axis=(0, -1, 0), roll=90.0)

    return bdy


fcprim.make(__file__, "TOP_CLAMP_SPANNER_CASE_2", top_clamp_spanner_case_2,
            mesh_volume)
