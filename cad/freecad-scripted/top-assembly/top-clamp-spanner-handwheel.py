"""TOP_CLAMP_SPANNER_HANDWHEEL - thumbwheel that drives the stencil clamp.

Reconstructed from the original author's TOP_CLAMP_SPANNER_HANDWHEEL.stl, in
that mesh's own coordinates: a flat 34 mm wheel only 5 mm deep, turned about
the X axis.

Eleven scallops around the rim give the grip.  Eleven is an odd number in both
senses - the wheel has no mirror symmetry, which is why its bounding box is
very slightly lopsided in Y.  An M5 nut drops into the hexagonal pocket behind
the boss and is trapped by the plain rod clearance at the back.

    Boss     sketch -> Pad          the raised hub
    Wheel    sketch -> Pad          the rim
    Flute    sketch -> Pocket       one scallop
                    -> PolarPattern the other ten
    Nut      sketch -> Pocket       captive M5 nut
    Rod      sketch -> Pocket       clearance out of the back
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

boss_d = 14.0
boss_thickness = 1.0
wheel_d = 34.0
wheel_thickness = 4.0

flute_d = 5.0            # grip scallops, centres on the rim itself
flute_count = 11

nut_across_flats = 8.2   # M5
nut_depth = 4.0          # measured from the front face, through the boss
rod_clear_d = 5.398

mesh_volume = 3111.484


def top_clamp_spanner_handwheel(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_SPANNER_HANDWHEEL")

    # Sketched on YZ, so every pad runs backwards along +X from its face.
    boss = fcprim.sketch(bdy, "Boss", "YZ_Plane")
    fcprim.circle(boss, (0.0, 0.0), boss_d, name="boss")
    fcprim.pad(bdy, "Boss pad", boss, boss_thickness)

    wheel = fcprim.sketch(bdy, "Wheel", "YZ_Plane", offset=boss_thickness)
    fcprim.circle(wheel, (0.0, 0.0), wheel_d, name="wheel")
    fcprim.pad(bdy, "Wheel pad", wheel, wheel_thickness)

    flute = fcprim.sketch(bdy, "Flute", "YZ_Plane", offset=boss_thickness)
    fcprim.circle(flute, (wheel_d / 2, 0.0), flute_d, name="flute")
    cut = fcprim.pocket(bdy, "Flute cut", flute, wheel_thickness, reversed_=True)
    fcprim.polar_pattern(bdy, "Flutes", [cut], flute_count, axis="X_Axis")

    nut = fcprim.sketch(bdy, "Nut pocket", "YZ_Plane")
    fcprim.polygon(nut, (0.0, 0.0), nut_across_flats, 6, angle=0.0, name="nut")
    fcprim.pocket(bdy, "Nut clearance", nut, nut_depth, reversed_=True)

    rod = fcprim.sketch(bdy, "Rod clearance", "YZ_Plane")
    fcprim.circle(rod, (0.0, 0.0), rod_clear_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance cut", rod, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  Both are on the
    # wheel's axis: the floor of the nut pocket, and the wheel's back face,
    # which is what runs on the case's hub.
    fcprim.lcs(bdy, "NUT", at=(nut_depth, 0.0, 0.0), axis=(-1, 0, 0))
    fcprim.lcs(bdy, "SPANNER_CASE",
               at=(boss_thickness + wheel_thickness, 0.0, 0.0),
               axis=(-1, 0, 0), roll=90.0)

    return bdy


fcprim.make(__file__, "TOP_CLAMP_SPANNER_HANDWHEEL",
            top_clamp_spanner_handwheel, mesh_volume)
