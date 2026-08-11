"""BEARING_14X5X5 - ball bearing, 14 outside, 5 bore, 5 wide: a 605.

Bought stock.  The alpha axis runs on four of them, and they are what the
printed slewing ring turns on.

**The bore is 5.**  It is worth writing down how that is known, because it was
briefly drawn as a 7.  Three parts the author did publish agree, and none of
them is a note in a table:

* `ADAPTER_D5_TO_M3` is a bushing with a **5.0 mm spigot** and a 3.2 mm bore.
  Its whole job is to let an M3 screw carry this bearing -- which is what its
  name says, D5 to M3.  Its 6.4 mm collar clamps the inner ring; against a 7 mm
  bore that collar would fall straight through.
* `SR_BEARING_PLATE` carries **four 3.4 mm holes** -- M3 clearance -- on a
  61 mm radius, each on its own 8 mm pad.  Four screws, four adapters, four
  bearings; the count comes from the holes rather than from any list.
* `SR_INNER_RING` has a 136 mm bore, r 68, running y = 3 .. 8: a race **5 mm
  tall**, which is the bearing's width.  61 + 14/2 = 68, so a 14 mm bearing on
  that bolt circle rolls exactly on that race.

    Section  sketch -> Revolution  one ring, swept about Z

**Drawn as a single ring**, bore straight through to the outside: no separate
races, no balls, no cage, no shields.  Michael's simplification, and it is
enough for what this is for -- the three dimensions anything mates to are the
bore that goes on the adapter's spigot, the outside that rolls on the race, and
the width it is clamped across, and all three are the part.  Nothing in the
machine touches what is between them.

That makes the volume `pi w (Ro^2 - Ri^2)`, which is what the build checks:
thin, but it is the whole part, and it catches a radius typed as a diameter.

Coordinates: the axis is the part's own **+Z**, running from zero, which is
what a `Cylindrical` joint expects.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

bore = 5.0               # the adapter's spigot, and the M3 screw behind it
outer = 14.0             # what rolls on the inner ring's race
width = 5.0              # and the race is exactly this tall


def bearing(doc):
    """A rectangle in section, swept about the axis into one ring."""
    bdy = fcprim.body(doc, "BEARING_14X5X5")

    # Drawn on XZ, where the sketch's V axis *is* the global Z, so the sweep
    # comes out about the part's own axis.  H is the radius, V is the width.
    section = fcprim.sketch(bdy, "Section", "XZ_Plane")
    fcprim.polyline(section, [
        (bore / 2.0, 0.0), (outer / 2.0, 0.0),
        (outer / 2.0, width), (bore / 2.0, width),
    ], name="ring")
    fcprim.revolution(bdy, "Ring", section, axis="V_Axis")

    # Mounting datums for the assembly; see fcprim.lcs.  A bearing is joined
    # about its axis, so `AXIS` sits at mid width where a `Cylindrical` joint
    # can go either way from it; the two faces are what it is clamped between
    # -- here the adapter's collar on one side and the plate's pad on the other.
    fcprim.lcs(bdy, "AXIS", at=(0.0, 0.0, width / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "FACE_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "FACE_B", at=(0.0, 0.0, width), axis=(0, 0, 1))
    # The adapter's spigot goes *into* the bore from the A face, so its datum
    # is that face's own point looking up the axis rather than out of it.
    fcprim.lcs(bdy, "ADAPTER", axis=(0, 0, 1))
    return bdy


fcprim.make(__file__, "BEARING_14X5X5", bearing,
            math.pi * width * ((outer / 2.0) ** 2 - (bore / 2.0) ** 2),
            made_of=fcprim.STEEL)
