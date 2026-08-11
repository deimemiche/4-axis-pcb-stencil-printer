"""STAND - foot the machine rests on.

Reconstructed from the original author's STAND.stl, in that mesh's own
coordinates: a small turned foot spanning Y = 0 .. 7, 11.5 mm across the base.

Like the spring plate it is all turned, so it is drawn once in section and
swept.  The base flange is bored 4.5 mm for the bolt that holds it on; above
the flange the wall tapers gently inwards and the bore opens out to 7 mm, which
leaves room for the bolt head.

    Section  sketch -> Revolution  the whole part, swept about Y

**Mounting datums**, which this part went without until the four feet in
`assembly/Bottom_Frame.FCStd` lost their joints over it.  A joint made against
`Revolution.Edge10` is stored under an element name the build regenerates every
time, so it dies whenever the part is rebuilt; a datum placed by this script is
parametric and survives one.  See `fcprim.lcs`.

    SEAT   the flange's outer face, Y = 0, Z pointing out of it
    AXIS   the bolt hole, at mid height, Z up the part -- a Cylindrical joint
    TIP    the small end, Y = 7, Z pointing out of it

`SEAT` is the mating face and `TIP` the one that meets the table, as far as the
section says: a bolt goes in from the small end, down the 7 mm bore, and its
head lands on the shoulder above the flange, which leaves the thread to come
out through `SEAT`.  Nothing here depends on that reading -- a datum is a named
coordinate system either way, so joint against `TIP` instead if the foot in
fact stands the other way up.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

base_d = 11.5
base_height = 1.0
top_d = 9.4              # the taper closes to this
total_height = 7.0

bolt_hole_d = 4.5        # M4 clearance, through the base
head_bore_d = 7.0        # above the base, clearing the bolt head

mesh_volume = 373.371


def stand(doc):
    bdy = fcprim.body(doc, "STAND")

    # Half a section through the foot; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (bolt_hole_d / 2, 0.0),
        (base_d / 2, 0.0),
        (base_d / 2, base_height),
        (top_d / 2, total_height),
        (head_bore_d / 2, total_height),
        (head_bore_d / 2, base_height),
        (bolt_hole_d / 2, base_height),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    # Mounting datums for the assembly; see fcprim.lcs and the module
    # docstring.  The part is turned about +Y, so that is the axis every one of
    # these points along, and each end datum's Z points out of the face it
    # names -- the way a bolt goes in and the way a butting part comes up
    # against it.
    fcprim.lcs(bdy, "SEAT", axis=(0, -1, 0))
    fcprim.lcs(bdy, "AXIS", at=(0.0, total_height / 2.0, 0.0), axis=(0, 1, 0))
    fcprim.lcs(bdy, "TIP", at=(0.0, total_height, 0.0), axis=(0, 1, 0))

    # And the two the assembly joins to.  The gusset lands on the seat looking
    # up the foot rather than down onto it, so `BRACKET` is `SEAT`'s point with
    # its Z the other way.  `BOLT` is the M4's own axis at the step the base
    # ends on, which is where the counterbore above it begins and so where the
    # head is seated.
    fcprim.lcs(bdy, "BRACKET", axis=(0, 1, 0))
    fcprim.lcs(bdy, "BOLT", at=(0.0, base_height, 0.0), axis=(0, 1, 0))

    return bdy


fcprim.make(__file__, "STAND", stand, mesh_volume)
