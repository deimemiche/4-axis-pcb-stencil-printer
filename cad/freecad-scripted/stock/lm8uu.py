"""LM8UU - linear ball bearing, 8 mm bore, for the 8 mm rod.

The machine has fourteen: four on the X rails, four on the Y, four on the
stencil rails in the lid, and two on the Z columns of the linear Z mod.  The
manual's step 2 buys eight of them; the rest arrive with the steps that need
them.

    Outside  sketch -> Pad     the 15 mm sleeve, 24 long
    Bore     sketch -> Pocket  the 8 mm bore, through

Only one document, because unlike the rod and the extrusion an LM8UU is a
catalogue part with one size: 8 mm bore, 15 mm outside, 24 mm long, which is
what the printed holders here are cut for -- `drive.py` reads
`BOT_BEARING_MOUNT_Y_AXIS`'s seat as 15.2 mm with 13.2 mm lips and concludes
it is an LM8UU holder rather than a screw bearing's.

**Drawn as a plain sleeve.**  A real LM8UU is a steel shell with a plastic
cage, recirculating ball tracks, a seal at each end and a snap ring groove near
each; none of that is here, and the volume is a plain annulus.  What the
machine cares about is the bore it slides on, the outside its holder grips and
the length between the lips -- all three are right -- and the internals would
add several hundred faces to a part that appears fourteen times in a check that
already has to boolean the whole machine.  Held against a catalogue mass the
number would be badly out for the same reason: 3035 mm^3 of steel is 23.8 g
where a real LM8UU weighs about 16, because most of the middle is cage and air.

This is the same simplification `asm/stock.py` makes, and the solids agree to
zero volume; it is drawn here as sketches rather than booleans so it can be
opened and edited.

Coordinates: the bore's axis is the part's own **+Z**, running from zero, as
everything joined by a `Cylindrical` here is.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

bore = 8.0               # the rod it rides
outside = 15.0           # what the holder grips
length = 24.0            # and how long it is


def lm8uu(doc):
    bdy = fcprim.body(doc, "LM8UU")

    shell = fcprim.sketch(bdy, "Outside", "XY_Plane")
    fcprim.circle(shell, (0.0, 0.0), outside, name="shell")
    fcprim.pad(bdy, "Length", shell, length)

    # Symmetric and through all: the sketch sits on the near end face, so a
    # pocket that only ran one way would cut nothing at all.
    hole = fcprim.sketch(bdy, "Bore", "XY_Plane")
    fcprim.circle(hole, (0.0, 0.0), bore, name="bore")
    fcprim.pocket(bdy, "Bore", hole, midplane=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `BORE` is the axis it
    # slides on and `SEAT` the middle of the outside, which is what a printed
    # holder closes around; they are the same line, named for the two different
    # things that are joined to it.
    fcprim.lcs(bdy, "BORE", axis=(0, 0, 1))
    fcprim.lcs(bdy, "SEAT", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))
    return bdy


fcprim.make(__file__, "LM8UU", lm8uu,
            math.pi / 4.0 * (outside ** 2 - bore ** 2) * length,
            made_of=fcprim.STEEL)
