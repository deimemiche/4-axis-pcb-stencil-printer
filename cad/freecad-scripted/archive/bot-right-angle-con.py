"""BOT_RIGHT_ANGLE_CON - right angle connector for 20 mm extrusion.

Reconstructed from the original author's BOT_RIGHT_ANGLE_CON.stl.  Every
dimension below was measured off that mesh (planar faces clustered by normal,
least squares fits on the curved facet groups); the resulting solid matches
the mesh volume to within the faceting error of the two bolt holes.

The part is an L bracket lying in the XY plane, padded symmetrically over the
full 20 mm extrusion width in Z.  Both outer 4 mm slices carry a triangular
gusset across the inner corner, leaving the middle 12 mm open.  A 1 mm tongue
on the -X face locates the bracket in the extrusion slot.

Modelled as a PartDesign Body:

    Profile   sketch -> Pad     legs and tongue, midplane over the full width
    Gusset    sketch -> Pad     one gusset, 4 mm off the bottom face
                      -> Mirror the second gusset, across the XY plane
    Bolt hole X sketch -> Pocket through the tongue and the Y leg
    Bolt hole Y sketch -> Pocket through the X leg

Run with:

    freecadcmd cad/freecad-scripted/code/pipeline/build.py archive/bot-right-angle-con.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# Extrusion the bracket bolts to.
ext_width = 20.0        # 2020 extrusion, also the bracket's width in Z
slot_width = 5.0        # width of the locating tongue
slot_depth = 1.0        # how far the tongue stands proud of the -X face

leg_length = 20.0       # both legs, measured from the outer corner
leg_thickness = 4.0

gusset_thickness = 4.0  # per gusset; one on each Z face

bolt_hole_d = 4.5       # M4 clearance
bolt_x = 10.0           # -X bolt, on the tongue centreline
bolt_y = 14.0           # -Y bolt, measured from the outer corner

# Volume of the original mesh, for the reconstruction check in finish().
mesh_volume = 3861.008


def right_angle_con(doc):
    bdy = fcprim.body(doc, "BOT_RIGHT_ANGLE_CON")
    inner = leg_length - leg_thickness
    tongue_y0 = bolt_x - slot_width / 2
    tongue_y1 = bolt_x + slot_width / 2

    # The L profile, walked anticlockwise from the outer corner, with the
    # locating tongue picked up as part of the same closed wire.
    profile = fcprim.sketch(bdy, "Profile", "XY_Plane")
    fcprim.polyline(profile, [
        (0.0, 0.0),
        (leg_length, 0.0),
        (leg_length, leg_thickness),
        (leg_thickness, leg_thickness),
        (leg_thickness, leg_length),
        (0.0, leg_length),
        (0.0, tongue_y1),
        (-slot_depth, tongue_y1),
        (-slot_depth, tongue_y0),
        (0.0, tongue_y0),
    ], name="leg")
    fcprim.pad(bdy, "Legs and tongue", profile, ext_width, midplane=True)

    # Gusset across the inner corner.  Its hypotenuse runs between the two leg
    # ends, so the triangle only ever adds material inside the corner.
    gusset = fcprim.sketch(bdy, "Gusset", "XY_Plane", offset=-ext_width / 2)
    fcprim.polyline(gusset, [
        (leg_thickness, leg_thickness),
        (leg_length, leg_thickness),
        (leg_thickness, leg_length),
    ], name="gusset")
    gusset_pad = fcprim.pad(bdy, "Gusset bottom", gusset, gusset_thickness)
    fcprim.mirrored(bdy, "Gusset top", [gusset_pad], "XY_Plane")

    # Bolt holes, one per leg.  The -X hole also passes through the tongue.
    hole_x = fcprim.sketch(bdy, "Bolt hole X", "YZ_Plane")
    fcprim.circle(hole_x, (bolt_x, 0.0), bolt_hole_d, name="bolt_x")
    fcprim.pocket(bdy, "Bolt hole X cut", hole_x, midplane=True)

    hole_y = fcprim.sketch(bdy, "Bolt hole Y", "XZ_Plane")
    fcprim.circle(hole_y, (bolt_y, 0.0), bolt_hole_d, name="bolt_y")
    fcprim.pocket(bdy, "Bolt hole Y cut", hole_y, midplane=True)

    fcprim.check_sketches(bdy)
    return bdy


here = os.path.dirname(os.path.abspath(__file__))
doc = fcprim.document("BOT_RIGHT_ANGLE_CON")
part = right_angle_con(doc)
fcprim.finish(doc, part,
              os.path.join(here, "BOT_RIGHT_ANGLE_CON.FCStd"),
              expect_volume=mesh_volume)
