"""SCOPE_JOINER - the strap that ties two extrusions end to end.

Michael's own part, transcribed from `joiner()` in
[`../../microscope-mount/microscope-mount.py`](../../microscope-mount/microscope-mount.py),
and the simplest thing in `scope/`: an obround plate 116 x 13 x 4 with a
108 x 5.5 obround slot down the middle.

116 is `d * 2`, twice the collar's outside diameter, and the source says in as
many words why: "sometimes mechanical engineering isn't exact mechanical
engineering".  It is long enough to reach either side of a joint and that is
the whole specification.

The slot rather than two holes is the point of it.  An M5 anywhere along a
2020's slot will take it, so where the two sticks meet does not have to be
where a hole was drilled.

    Outline   sketch -> Pad   the obround, and the slot inside it
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From ../../microscope-mount/settings.py.
wall = 4.0               # Settings.wall_t
loose_fit = 0.5          # Settings.loose_fit
scope_d = 50.0           # Settings.scope_d
frame_bolt_d = 5.0       # M5, Settings.frame_bolt

collar_od = scope_d + 2 * wall           # 58, what the length is measured in
length = 2 * collar_od                   # 116
width = frame_bolt_d + 2 * wall          # 13
thickness = wall

slot_l = length - 2 * wall               # 108
slot_w = frame_bolt_d + loose_fit        # 5.5, so the bolt can slide in it


def obround(overall, across):
    """The two end centres of an obround `overall` long and `across` wide."""
    reach = (overall - across) / 2.0
    return (0.0, -reach), (0.0, reach)


def expected_volume():
    """Arithmetic on the numbers above; see `../STATUS.md`."""
    def area(overall, across):
        radius = across / 2.0
        return across * (overall - across) + math.pi * radius ** 2

    return (area(length, width) - area(slot_l, slot_w)) * thickness


def joiner(doc):
    bdy = fcprim.body(doc, "SCOPE_JOINER")

    outline = fcprim.sketch(bdy, "Outline", "XY_Plane")
    start, end = obround(length, width)
    fcprim.slot(outline, start, end, width, name="outline")
    start, end = obround(slot_l, slot_w)
    fcprim.slot(outline, start, end, slot_w, name="slot")
    fcprim.pad(bdy, "Plate", outline, thickness)

    # Mounting datums for the assembly; see fcprim.lcs.  The slot is where a
    # bolt can be rather than where one is, so the two ends of it are what
    # anything joining here has to work between.
    fcprim.lcs(bdy, "MOUNT", axis=(0, 0, -1))
    for i, (_, y) in enumerate(obround(slot_l, slot_w)):
        fcprim.lcs(bdy, f"SLOT_{'AB'[i]}", at=(0.0, y, 0.0), axis=(0, 0, -1))

    return bdy


fcprim.make(__file__, "SCOPE_JOINER", joiner, expected_volume())
