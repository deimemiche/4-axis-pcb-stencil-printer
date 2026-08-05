"""ECCF_MOUNT - collar the front eccenter turns in.

Reconstructed from the original author's ECCF_MOUNT.stl, in that mesh's own
coordinates: a plain collar spanning Y = 0 .. 14, bored 18.4 mm for the
eccenter body.

Two flat sided lugs stand proud of the collar on the +X and -X faces, joined by
a single cross bolt.  Both come from one obround drawn in the YZ plane and
padded right across: the prism only shows where it overreaches the collar's own
diameter, which is what gives the lugs their flats and their rounded tops.

    Collar     sketch -> Pad     the barrel
    Lugs       sketch -> Pad     obround padded across, symmetric in X
    Bore       sketch -> Pocket  through, and back out of the lugs
    Cross bolt sketch -> Pocket  through both lugs

**The cross bolt hole is Michael's, not the author's**: 5.7 mm for a heat set
threaded insert where the original is 3.5 mm, plain M3 clearance.  It is the
one dimension here that does not come off `ECCF_MOUNT.stl`, so this is the one
part in `eccf/` that is meant to differ from the mesh it was reconstructed
from, and both of the repository's checks have to be told about it:

* the **volume** check no longer expects the mesh's own figure but
  `mesh_volume - insert_relief()`, the second being what the wider hole takes
  out of the collar wall, worked out below from the same numbers the sketches
  use.  It cannot catch a mistyped `bolt_hole_d`, since that number drives the
  hole and the allowance alike -- what it still catches is the whole of the
  rest of the part, and a cross bolt pocket that ran the wrong way, missed the
  lugs or cut into the bore.
* `verify.py` **will report mismatches** for this part, and that is correct
  rather than a regression: 184 of 20000 samples, every one of them
  `solid=False mesh=True` and inside the enlarged hole, which is what 132 mm3
  of missing material comes to in the box it samples.  Nothing else in `eccf/`
  should ever come back with a mismatch.

The lug is `lug_width` across, so a 5.7 mm hole leaves 1.15 mm of wall either
side of the insert.
"""

import math
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

bolt_hole_d = 5.7        # for a heat set threaded insert; see the docstring
author_bolt_hole_d = 3.5  # what the mesh has, plain M3 clearance

mesh_volume = 3887.896


def insert_relief():
    """How much more the insert's hole takes out than the author's does.

    The hole is a cylinder along X through the lugs, and every bit of it lies
    inside the nose's own radius, so what it passes through is only the collar
    wall: from the bore out to the lug's flat, on each side.  At height `z` in
    the hole that wall is `lug_span/2 - sqrt((bore_d/2)^2 - z^2)` thick, and
    the hole is `2 sqrt(r^2 - z^2)` tall there, which leaves

        4 r^2 . int cos^2 t . (lug_span/2 - sqrt((bore_d/2)^2 - r^2 sin^2 t)) dt

    over a half turn, substituting z = r sin t so the integrand stays smooth to
    the ends.  Simpson's rule settles by a few hundred steps; it runs with a
    few thousand because it costs nothing and this is the number the build is
    checked against.
    """
    def cut(diameter, steps=2000):
        radius, out, bore = diameter / 2.0, lug_span / 2.0, bore_d / 2.0
        step = math.pi / steps
        total = 0.0
        for i in range(steps + 1):
            angle = -math.pi / 2.0 + i * step
            wall = out - math.sqrt(bore ** 2 - (radius * math.sin(angle)) ** 2)
            weight = 1 if i in (0, steps) else (4 if i % 2 else 2)
            total += weight * math.cos(angle) ** 2 * wall
        return 4.0 * radius ** 2 * total * step / 3.0

    return cut(bolt_hole_d) - cut(author_bolt_hole_d)


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


fcprim.make(__file__, "ECCF_MOUNT", eccf_mount, mesh_volume - insert_relief())
