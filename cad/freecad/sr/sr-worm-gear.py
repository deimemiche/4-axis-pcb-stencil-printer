"""SR_WORM_GEAR - the worm that drives the slewing ring.

Reconstructed from the original author's SR_WORM_GEAR.stl, in that mesh's own
coordinates: Y = 0 .. 20, turned about Y.

A 5 mm bore through a 7 mm core, with a single start thread standing 1.5 mm
proud of it.  The thread is trapezoidal - 60 degrees included, equal lands at
crest and root - and its 3.0699 mm pitch is what `SR_OUTER_RING_W_GEAR`'s
2.25 degree tooth spacing works out to on the wheel's pitch circle.

This is the only part here that a revolve cannot make: a helix advances along
its axis as it turns.  `PartDesign::AdditiveHelix` sweeps the thread's axial
section along one, which is exactly the right primitive and needs the same
fully constrained sketch as everything else.

The thread starts and stops at the part's own ends rather than running through
them, so its first and last turn are only partly there - it takes a full 1.2 mm,
half the profile's height, to come up to section. That is what the original does
too, and it is worth 10 mm3, so the sweep is not run long. The two trims only
take off the overhang of the start and end profiles themselves, which stand
1.2 mm proud of the sweep at each end.

    Core     sketch -> Revolution  the bored tube, run long at both ends
    Thread   sketch -> Helix       the thread's axial section, swept
    Trim     sketch -> Pocket      back to length at each end
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

worm_y = (0.0, 20.0)
core_d = 7.0
bore_d = 5.0

thread_d = 10.0          # over the crests
pitch = 3.06986          # one turn, and one tooth of the wheel
flank = 30.0             # degrees off the radial - 60 included

over = 2.0               # how far the trimming profiles run past the part

mesh_volume = 754.281


def sr_worm_gear(doc):
    bdy = fcprim.body(doc, "SR_WORM_GEAR")
    core_r, crest_r = core_d / 2, thread_d / 2

    section = fcprim.sketch(bdy, "Core", "XY_Plane")
    fcprim.polyline(section, [
        (bore_d / 2, worm_y[0]),
        (core_r, worm_y[0]),
        (core_r, worm_y[1]),
        (bore_d / 2, worm_y[1]),
    ], name="core")
    fcprim.revolution(bdy, "Core", section, axis="V_Axis")

    # The thread's axial section, drawn where the sweep starts.  Crest and root
    # get equal lands, which is what is left of the pitch once both flanks have
    # had their run.  The root side is sunk into the core rather than laid on
    # it, so the two share material instead of a face.
    run = (crest_r - core_r) * math.tan(math.radians(flank))
    land = (pitch - 2 * run) / 2
    sunk = core_r - 0.1
    thread = fcprim.sketch(bdy, "Thread", "XY_Plane")
    fcprim.polyline(thread, [
        (sunk, worm_y[0] - land / 2 - run),
        (core_r, worm_y[0] - land / 2 - run),
        (crest_r, worm_y[0] - land / 2),
        (crest_r, worm_y[0] + land / 2),
        (core_r, worm_y[0] + land / 2 + run),
        (sunk, worm_y[0] + land / 2 + run),
    ], name="thread")
    fcprim.helix(bdy, "Thread", thread, pitch, worm_y[1] - worm_y[0])

    # Back to length.  H is X, V is Z, and each pocket runs away from the part.
    for label, at, away in (("Trim bottom", worm_y[0], True),
                            ("Trim top", worm_y[1], False)):
        square = fcprim.sketch(bdy, label, "XZ_Plane", offset=-at)
        reach = crest_r + over
        fcprim.polyline(square, [
            (-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach),
        ], name="trim")
        fcprim.pocket(bdy, label, square, pitch + over, reversed_=away)

    return bdy


fcprim.make(__file__, "SR_WORM_GEAR", sr_worm_gear, mesh_volume)
