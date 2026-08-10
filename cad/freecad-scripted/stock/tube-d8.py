"""TUBE_D8_<length> - drawn aluminium tube, 8 mm outside, cut to length.

Bought stock, like the extrusion, the ground rod and the studding, and drawn
the same way: one script, a document per length, so adding a length is adding a
number to `lengths` below.

    TUBE_D8_170.FCStd   8 x 1 mm tube, 170 long

    Outside  sketch -> Pad     the 8 mm barrel, run up +Z
    Bore     sketch -> Pocket  the 6 mm bore, through

**The 6 mm bore is the stock size, not a choice.** Drawn aluminium tube comes
in whole millimetre walls, and 8 x 1 - 8 mm outside, 1 mm wall, 6 mm bore - is
the one every supplier of EN 754 / DIN 1748 round tube carries in 8 mm, and the
one 6 mm pneumatic push fit is sized on. The thinner 8 x 0.5 (7 mm bore) and
the heavier 8 x 1.5 (5 mm bore) exist; they are a special order next to this
one. Changing it is changing `wall` below, and the volume check follows.

The outside is the **same 8 mm as `bot/rod-d8.py`**, so everything in the
machine that grips or slides on ground rod - an LM8UU, a rail clamp, a rod
holder - takes this too. What it will not take is the rod's load: a 1 mm wall
has about 44 % of the solid rod's second moment of area, and none of the
hardened surface an LM8UU wants to run on.

Coordinates: the axis is the part's own **+Z**, running from zero, which is
what a `Cylindrical` joint expects and what the rod and the studding use.

**Drawn plain**, like the rod: no chamfer at either end, no draw marks. The
volume is therefore exactly the annulus, `pi/4 (D^2 - d^2) L`, which is what
the build checks -- a thin check, but it is the whole of the part, and it
catches a bore that missed, a pad that ran the wrong way, or a wall typed as a
diameter.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

outside = 8.0            # the same as the ground rod, so the same parts fit
wall = 1.0               # stock 8 x 1; see the module docstring
bore = outside - 2.0 * wall

# The lengths this machine is built from.
lengths = (170.0,)


def tube(doc, length):
    """An annulus, run up +Z for `length`."""
    bdy = fcprim.body(doc, f"TUBE_D8_{length:.0f}")

    barrel = fcprim.sketch(bdy, "Outside", "XY_Plane")
    fcprim.circle(barrel, (0.0, 0.0), outside, name="tube")
    fcprim.pad(bdy, "Length", barrel, length)

    # Symmetric and through all: the sketch sits on the near end face, so a
    # pocket that only ran one way would cut nothing at all.
    hole = fcprim.sketch(bdy, "Bore", "XY_Plane")
    fcprim.circle(hole, (0.0, 0.0), bore, name="bore")
    fcprim.pocket(bdy, "Bore", hole, midplane=True)

    # Mounting datums for the assembly; see fcprim.lcs.  A tube is joined about
    # its axis and slid along it, so `AXIS` is the one that matters and it sits
    # at mid length, where a `Cylindrical` joint can go either way from it.
    # `BORE` is the same line named for what goes *inside* it, and the two ends
    # are for whatever butts against them.
    fcprim.lcs(bdy, "AXIS", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "BORE", axis=(0, 0, 1))
    fcprim.lcs(bdy, "END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))
    return bdy


for cut_length in lengths:
    fcprim.make(__file__, f"TUBE_D8_{cut_length:.0f}",
                lambda doc, length=cut_length: tube(doc, length),
                math.pi / 4.0 * (outside ** 2 - bore ** 2) * cut_length,
                made_of=fcprim.ALUMINIUM)
