"""SCOPE_ROLLER_WHEEL - the tyre a 608 bearing wears to run on an extrusion.

Michael's own part, transcribed from `wheel()` in
[`../microscope-mount/roller.py`](../microscope-mount/roller.py).

A ring 28 outside and 22 bored, 7 wide -- 22 and 7 being a 608 bearing's own
outside and width, so the wheel is pressed on to one and the bearing does the
turning.  `SCOPE_ROLLER_MOUNT` hangs it off an M8.

Its rim is broken 0.875 either side, and that break is drawn where the rest of
`scope/`'s are left off: it is the surface that meets the extrusion, so it is
the part rather than a finish on it.

    Ring   sketch -> Pad      the 28 over the 22, 7 wide
    Rim    edges  -> Chamfer  0.875 off both outer corners

**It is a plain cylinder, not a V.**  The name in the source is `roller` and a
wheel that runs in a V-slot usually carries a 90 degree groove; this one has
0.875 breaks on a flat 28 mm face instead, so it rides the face of the
extrusion rather than the slot's vee.  That is what the source draws.
"""

import math
import os
import sys

import Part

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

bearing_od = 22.0        # a 608, which the wheel is pressed on to
bearing_t = 7.0
tyre = 3.0               # wheel_t, how much rubber-equivalent is over it

wheel_od = bearing_od + 2 * tyre         # 28
break_off = bearing_t / 8.0              # 0.875, off each rim corner


def expected_volume():
    """Arithmetic on the numbers above; see `../STATUS.md`.

    The two rim breaks are rings of triangular section, so Pappus settles
    them: the section's area times the circle its centroid travels.
    """
    ring = math.pi / 4.0 * (wheel_od ** 2 - bearing_od ** 2) * bearing_t
    section = break_off ** 2 / 2.0
    centroid = wheel_od / 2.0 - break_off / 3.0
    return ring - 2 * section * 2 * math.pi * centroid


def wheel(doc):
    bdy = fcprim.body(doc, "SCOPE_ROLLER_WHEEL")

    # Drawn on YZ, so the wheel's axis is X and the pad runs along it -- the
    # way the source's own Workplane("YZ") has it.
    ring = fcprim.sketch(bdy, "Ring", "YZ_Plane")
    fcprim.circle(ring, (0.0, 0.0), wheel_od, name="tyre")
    fcprim.circle(ring, (0.0, 0.0), bearing_od, name="bore")
    fcprim.pad(bdy, "Ring", ring, bearing_t)

    # Both rim circles, and only those: the outer cylinder's seam runs at the
    # same radius and is a straight edge, which a chamfer cannot take.
    def rim(edge):
        point = fcprim.midpoint(edge)
        return (isinstance(edge.Curve, Part.Circle)
                and abs(math.hypot(point.y, point.z) - wheel_od / 2.0) < 1e-6)

    fcprim.chamfer(bdy, "Rim", break_off, rim)

    # Mounting datums for the assembly; see fcprim.lcs.  A wheel is joined
    # about its axis and lands on a face, the same as `misc/BEARING_14X5X5`.
    fcprim.lcs(bdy, "AXIS", at=(bearing_t / 2.0, 0.0, 0.0), axis=(1, 0, 0))
    fcprim.lcs(bdy, "FACE_A", axis=(-1, 0, 0))
    fcprim.lcs(bdy, "FACE_B", at=(bearing_t, 0.0, 0.0), axis=(1, 0, 0))

    return bdy


fcprim.make(__file__, "SCOPE_ROLLER_WHEEL", wheel, expected_volume())
