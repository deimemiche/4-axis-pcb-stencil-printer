"""STENCIL_HOLDER_FRONT_2 - the shorter angle that closes the front of the clamp.

The same 198 mm angle as `stencil-holder-back-2.py`, with one hole more: a 5.4
through the upright at the middle of the bar.  So this builds the same body
with that hole turned on rather than repeating it.

It is the short angle to `STENCIL_HOLDER_FRONT`, and the two of them carry that
5.4 at the same place, 8.5 down from the top of the upright.  The back hand of
both lengths goes without it.

Editing the bar means editing `stencil-holder-back-2.py`; both parts follow.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import fcprim

# Run the other script for its `angle`, telling it not to build its own part
# while we do.  Importing it would not do: its filename is not an identifier,
# and the module-level build would fire on the way past.
back = {"__file__": os.path.join(HERE, "stencil-holder-back-2.py"),
        "as_library": True}
with open(back["__file__"]) as handle:
    exec(compile(handle.read(), back["__file__"], "exec"), back)

middle_d = 5.4
middle_from_edge = 8.5   # from the top of the upright -- not its centre


def expected_volume():
    import math
    return (back["expected_volume"]()
            - math.pi * (middle_d / 2.0) ** 2 * back["wall"])


def stencil_holder_front_2(doc):
    return back["angle"](doc, "STENCIL_HOLDER_FRONT_2",
                         middle=(middle_d, middle_from_edge))


fcprim.make(__file__, "STENCIL_HOLDER_FRONT_2", stencil_holder_front_2,
            expected_volume(), made_of=fcprim.ALUMINIUM)
