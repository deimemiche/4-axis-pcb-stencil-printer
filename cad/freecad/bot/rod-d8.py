"""ROD_D8_<length> - ground linear rod, 8 mm, cut to length.

The rails everything slides on.  Bought, like the extrusion, and like the
extrusion it lived only inside `asm/stock.py` as a `Part::Feature` cylinder
until now; this draws it as a PartDesign body so it opens with a sketch and a
dimension in it.

One script, a document per length -- a rod is its diameter and how far it runs,
and every one in this machine is 8 mm:

    ROD_D8_300.FCStd   x2   the X rails, across the bottom frame
    ROD_D8_280.FCStd   x2   the stencil rails, along the lid
    ROD_D8_244.FCStd   x2   the Y rails, under the alpha plate
    ROD_D8_140.FCStd   x2   the Z columns of the linear Z mod

Adding a length is adding a number to `lengths` below.

    Section  sketch -> Pad   an 8 mm circle, run up +Z

**Drawn plain.**  Real ground rod has a small lead-in chamfer at each end and
is hardened to a depth; neither is modelled, because nothing in the machine
locates on either -- an LM8UU rides the ground diameter and a clamp grips it,
and both of those are here.  The same reasoning `asm/stock.py` gives for
drawing studding without its thread.

That makes the volume exactly pi/4 d^2 L, which is what the build checks: it is
a thin check, but it is the whole part, and it catches a pad that ran the wrong
way or a diameter typed as a radius.

Coordinates: the axis is the part's own **+Z**, running from zero, which is the
convention `asm/stock.py` uses too -- a joint axis is always the part's Z, which
is what `Cylindrical` expects.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

diameter = 8.0           # what an LM8UU bores for, and every rail here

# The lengths this machine is built from.
lengths = (300.0, 280.0, 244.0, 140.0)


def rod(doc, length):
    """A circle, run up +Z for `length`."""
    bdy = fcprim.body(doc, f"ROD_D8_{length:.0f}")

    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.circle(section, (0.0, 0.0), diameter, name="rod")
    fcprim.pad(bdy, "Length", section, length)

    # Mounting datums for the assembly; see fcprim.lcs.  A rod is joined about
    # its axis and slid along it, so `AXIS` is the one that matters and it sits
    # at mid length, where a `Cylindrical` joint can go either way from it.
    # The two ends are for whatever butts against them -- a bracket's counter
    # bore, a collar.
    fcprim.lcs(bdy, "AXIS", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))
    return bdy


for cut_length in lengths:
    fcprim.make(__file__, f"ROD_D8_{cut_length:.0f}",
                lambda doc, length=cut_length: rod(doc, length),
                math.pi * (diameter / 2.0) ** 2 * cut_length,
                made_of=fcprim.STEEL)
