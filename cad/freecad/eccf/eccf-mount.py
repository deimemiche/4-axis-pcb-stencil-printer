"""ECCF_MOUNT - collar the front eccenter turns in.

Reconstructed from the original author's ECCF_MOUNT.stl, in that mesh's own
coordinates: a plain collar spanning Y = 0 .. 14, bored 18.4 mm for the
eccenter body.

Two flat sided lugs stand proud of the collar on the +X and -X faces, joined by
a single 3.5 mm cross bolt.  Both come from one obround drawn in the YZ plane
and padded right across: the prism only shows where it overreaches the collar's
own diameter, which is what gives the lugs their flats and their rounded tops.

    Collar     sketch -> Pad     the barrel
    Lugs       sketch -> Pad     obround padded across, symmetric in X
    Bore       sketch -> Pocket  through, and back out of the lugs
    Cross bolt sketch -> Pocket  through both lugs
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

collar_d = 26.4
collar_height = 14.0
bore_d = 18.4            # the eccenter runs in this

lug_width = 8.0          # across the flats of a lug, measured in Z
lug_y = 5.25             # height of the cross bolt, and of the lugs' round top
lug_span = 26.4          # tip to tip across X, the lugs' flats

bolt_hole_d = 3.5        # M3 clearance

mesh_volume = 3887.896


def eccf_mount(doc):
    bdy = fcprim.body(doc, "ECCF_MOUNT")

    collar = fcprim.sketch(bdy, "Collar", "XZ_Plane", offset=-collar_height)
    fcprim.circle(collar, (0.0, 0.0), collar_d, name="collar")
    fcprim.pad(bdy, "Collar pad", collar, collar_height)

    # Drawn side on, then padded across the whole part.  Everything inside the
    # collar's diameter is already solid, so only the two lugs come of it.
    # Body and nose are padded separately so the lug can sit flat on the
    # collar's bottom face while its top stays a true half round.
    lugs = fcprim.sketch(bdy, "Lugs", "YZ_Plane")
    fcprim.polyline(lugs, [
        (0.0, -lug_width / 2),
        (lug_y, -lug_width / 2),
        (lug_y, lug_width / 2),
        (0.0, lug_width / 2),
    ], name="lug")
    fcprim.pad(bdy, "Lug pad", lugs, lug_span, midplane=True)

    noses = fcprim.sketch(bdy, "Lug noses", "YZ_Plane")
    fcprim.circle(noses, (lug_y, 0.0), lug_width, name="nose")
    fcprim.pad(bdy, "Lug nose pad", noses, lug_span, midplane=True)

    # Cut last, so it clears the lug prism out of the middle again.
    bore = fcprim.sketch(bdy, "Bore", "XZ_Plane")
    fcprim.circle(bore, (0.0, 0.0), bore_d, name="bore")
    fcprim.pocket(bdy, "Bore cut", bore)

    bolt = fcprim.sketch(bdy, "Cross bolt", "YZ_Plane")
    fcprim.circle(bolt, (lug_y, 0.0), bolt_hole_d, name="bolt")
    fcprim.pocket(bdy, "Cross bolt cut", bolt, midplane=True)

    return bdy


fcprim.make(__file__, "ECCF_MOUNT", eccf_mount, mesh_volume)
