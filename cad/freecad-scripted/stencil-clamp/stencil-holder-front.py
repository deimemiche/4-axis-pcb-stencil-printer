"""STENCIL_HOLDER_FRONT - the front L profile of the stencil clamp.

The same 20 x 20 x 2 aluminium angle as `stencil-holder-back.py`, 213.72 mm
long, with the same row of four and the same three at each end - and one hole
more: a 5.4 through the upright at the middle of the bar, which the back one
does not have.  So this builds the same body with that hole turned on rather
than repeating it.

Editing the bar means editing `stencil-holder-back.py`; both parts follow.  The
one figure that lives here is the middle hole, 8.5 down from the top of the
upright, which puts it off the upright's centre line.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import fcprim

# Run the other script for its `angle`, telling it not to build its own part
# while we do.  Importing it would not do: its filename is not an identifier,
# and the module-level build would fire on the way past.
back = {"__file__": os.path.join(HERE, "stencil-holder-back.py"),
        "as_library": True}
with open(back["__file__"]) as handle:
    exec(compile(handle.read(), back["__file__"], "exec"), back)

middle_d = 5.4
middle_from_edge = 8.5   # from the top of the upright -- not its centre


def expected_volume():
    import math
    return (back["expected_volume"]()
            - math.pi * (middle_d / 2.0) ** 2 * back["wall"])


def stencil_holder_front(doc):
    bdy = back["angle"](doc, "STENCIL_HOLDER_FRONT",
                        middle=(middle_d, middle_from_edge))
    # The front bar carries a clamp bearing mount at each end, and they are not
    # the same joint: at -X the mount is bolted to the upright's outer face, at
    # +X to the leg's upper face.  Only the two outer row holes take a nut
    # holder here -- the two in the middle are the back bar's -- and the near
    # one is also where the short bar closes on this one.
    fcprim.lcs(bdy, "BEARING_MOUNT1",
               at=back["edge_hole"](back["mount_x"][0], back["wall"]),
               axis=(0, -1, 0))
    fcprim.lcs(bdy, "BEARING_MOUNT2",
               at=back["face_hole"](back["mount_x"][1],
                                    back["mount_from_edge"][1], back["wall"]),
               axis=(0, 0, 1))
    for i, x in enumerate((back["row_x"][0], back["row_x"][-1])):
        fcprim.lcs(bdy, f"NUT_HOLDER{i + 1}",
                   at=back["face_hole"](x, back["row_from_edge"],
                                        back["wall"]), axis=(0, 0, 1))
    fcprim.lcs(bdy, "HOLDER_FRONT",
               at=back["face_hole"](back["row_x"][0], back["row_from_edge"]),
               axis=(0, 0, 1))
    return bdy


fcprim.make(__file__, "STENCIL_HOLDER_FRONT", stencil_holder_front,
            expected_volume(), made_of=fcprim.ALUMINIUM)
