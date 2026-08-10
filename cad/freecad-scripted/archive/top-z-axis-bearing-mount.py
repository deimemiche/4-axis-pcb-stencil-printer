"""TOP_Z_AXIS_BEARING_MOUNT - what the top frame rides the Z rod on.

The other half of Michael's linear Z axis mod, and transcribed from
[`../../archive/z-axis.py`](../../archive/z-axis.py) the same way `top-z-axis-bracket.py` is.

There is no mesh or drawing to check it against, so the check is the
assembly's: the rod has to pass this seat and the bracket's bore on one axis.

It replaces the author's `TOP_CLAMP_Z_AXIS`, and the difference is the whole
point of the mod: his part *clamps* an M8 threaded rod and so has to be undone
to move, while this one holds an **LM8UU** and slides.  The top frame's height
is then set by the eccentrics rather than by a clamp, and the frame runs up and
down freely in between.

    Tube    sketch -> Pad     23.1 outside, 24 tall
    Flange  sketch -> Pad     what bolts to the extrusion
    Bore    sketch -> Pocket  15.1 for the LM8UU, through
    Bolts   sketch -> Pocket  two M4 through the flange
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From cad/settings.py and cad/z-axis.py.
wall = 4.0               # Settings.wallThickness
bearing_d = 15.0         # Settings.bearingD, an LM8UU
bearing_fit = 0.1        # Settings.tightFit
bearing_h = 24.0         # Settings.bearingH
fit = 0.2                # Settings.fit
head_d = 7.5             # Settings.frameBoltHeadD

seat_d = bearing_d + bearing_fit         # 15.1
tube_d = seat_d + 2 * wall               # 23.1
flange_width = bearing_d + 3 * wall + 2 * head_d + fit   # 42.2
flange_thickness = wall
flange_at = (seat_d + wall) / 2.0        # 9.55, off the bearing's own axis

bolt_hole_d = 4.2                        # M4 plus Settings.boltFit
bolt_pitch = flange_width - fit - head_d - wall / 2.0    # 32.5


def bearing_mount(doc):
    bdy = fcprim.body(doc, "TOP_Z_AXIS_BEARING_MOUNT")

    tube = fcprim.sketch(bdy, "Tube", "XZ_Plane")
    fcprim.circle(tube, (0.0, 0.0), tube_d, name="tube")
    fcprim.pad(bdy, "Tube", tube, bearing_h, reversed_=True)

    flange = fcprim.sketch(bdy, "Flange", "XZ_Plane")
    fcprim.polyline(flange, [
        (-flange_width / 2.0, flange_at),
        (flange_width / 2.0, flange_at),
        (flange_width / 2.0, flange_at + flange_thickness),
        (-flange_width / 2.0, flange_at + flange_thickness),
    ], name="flange")
    fcprim.pad(bdy, "Flange", flange, bearing_h, reversed_=True)

    bore = fcprim.sketch(bdy, "Bearing seat", "XZ_Plane")
    fcprim.circle(bore, (0.0, 0.0), seat_d, name="seat")
    fcprim.pocket(bdy, "Bearing clearance", bore, bearing_h, reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XY_Plane",
                          offset=-(flange_at + flange_thickness))
    for i, x in enumerate((-bolt_pitch / 2.0, bolt_pitch / 2.0)):
        fcprim.circle(bolts, (x, -bearing_h / 2.0), bolt_hole_d,
                      name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, flange_thickness)

    # Mounting datums for the assembly; see fcprim.lcs.
    fcprim.lcs(bdy, "BEARING", axis=(0, 1, 0))
    fcprim.lcs(bdy, "MOUNT", at=(0.0, 0.0, flange_at + flange_thickness),
               axis=(0, 0, 1))
    for i, x in enumerate((-bolt_pitch / 2.0, bolt_pitch / 2.0)):
        fcprim.lcs(bdy, f"BOLT{i + 1}",
                   at=(x, -bearing_h / 2.0, flange_at + flange_thickness),
                   axis=(0, 0, 1))

    return bdy


fcprim.make(__file__, "TOP_Z_AXIS_BEARING_MOUNT", bearing_mount)
