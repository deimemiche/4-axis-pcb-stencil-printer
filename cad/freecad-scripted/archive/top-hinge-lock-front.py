"""TOP_HINGE_LOCK_FRONT - the plated half of Michael's hinge lock.

The other half of `top-hinge-lock-back.py`, and transcribed from the same
CadQuery in [`../../archive/hinge-lock.py`](../../archive/hinge-lock.py).  Read that file's
docstring first: it says what the lock is for and what could not be settled
from the source.

A 4 mm plate, 48 long and **20 tall** - one extrusion's face - bolted flat to
that face with two M4 fourteen apart, and a 20 x 20 x 11 boss standing off it
at one end.  The M3 runs along the boss, counterbored so its head sinks in, and
lands in the nut the back half holds.

    Plate    sketch -> Pad     the 4 mm plate, up the face
    Boss     sketch -> Pad     what stands off it at one end
    Lock     sketch -> Pocket  the M3, along the length
    Head     sketch -> Pocket  its counterbore, 16 deep
    Frame    sketch -> Pocket  two M4 through the plate

Only the chamfers and fillets are left off, which is the bargain the rest of
`mod/` makes; everything that is a hole is here, so the finished solid's
volume can be held against the CadQuery one with its dressups suppressed,
and it is - `undressed` below.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From cad/settings.py.
wall = 4.0               # Settings.wallThickness
loose_fit = 0.5          # Settings.looseFit
bolt_fit = 0.2           # Settings.boltFit
ext = 20.0               # Settings.extD

frame_bolt_d = 4.0       # M4, Settings.frameBolt
frame_nut_across = 7.0
lock_bolt_d = 3.0        # M3, Settings.bolt
lock_head_d = 5.5        # its socket head

# hinge-lock.py's own numbers, in its own order.
bolt_length = frame_bolt_d * 2 + 5 * wall        # 28
length = bolt_length + ext                       # 48, along the extrusion
plate = wall                                     # 4, off the face
tall = ext                                       # 20, the face's own height

boss = ext                                       # 20 square
boss_out = wall + frame_nut_across               # 11, how far it stands off
boss_from = length / 2.0 - boss                  # +4, where it starts

lock_hole_d = lock_bolt_d + loose_fit            # 3.5
lock_head_hole = lock_head_d + 2 * loose_fit     # 6.5
lock_head_deep = ext - wall                      # 16
lock_out = plate + boss_out / 2.0 - wall / 2.0   # 7.5, the boss's own middle
lock_up = tall / 2.0                             # 10, the face's mid height

frame_hole_d = frame_bolt_d + bolt_fit           # 4.2
exposed = (-length / 2.0 + boss_from) / 2.0      # -10, the clear plate's
frame_mid = exposed - wall / 2.0                 # -12, its own middle
frame_at = (frame_mid - bolt_length / 4.0,
            frame_mid + bolt_length / 4.0)       # -19 and -5

spotface_d = 7.3         # under each M4 head, 0.2 deep
spotface_deep = 0.2

over = 2.0               # how far cutting profiles run past the part

# The CadQuery solid's own volume with its chamfers and fillets suppressed,
# which is what this transcription should come to exactly.
undressed = 7548.551


def hinge_lock_front(doc):
    bdy = fcprim.body(doc, "TOP_HINGE_LOCK_FRONT")

    # Drawn in plan; H is X, off the face it bolts to, V is Y, along it.  The
    # pad runs up Z, which is the extrusion's own height.
    face = fcprim.sketch(bdy, "Plate", "XY_Plane")
    fcprim.polyline(face, [
        (0.0, -length / 2.0),
        (plate, -length / 2.0),
        (plate, length / 2.0),
        (0.0, length / 2.0),
    ], name="plate")
    fcprim.pad(bdy, "Plate", face, tall)

    stand = fcprim.sketch(bdy, "Boss", "XY_Plane")
    fcprim.polyline(stand, [
        (plate, boss_from),
        (plate + boss_out, boss_from),
        (plate + boss_out, boss_from + boss),
        (plate, boss_from + boss),
    ], name="boss")
    fcprim.pad(bdy, "Boss", stand, tall)

    # The M3 runs along the boss, so it is drawn on the face it enters.
    lock = fcprim.sketch(bdy, "Lock bolt", "XZ_Plane")
    fcprim.circle(lock, (lock_out, lock_up), lock_hole_d, name="lock")
    fcprim.pocket(bdy, "Lock bolt", lock, midplane=True)

    head = fcprim.sketch(bdy, "Head", "XZ_Plane",
                         offset=-(boss_from + lock_head_deep / 2.0))
    fcprim.circle(head, (lock_out, lock_up), lock_head_hole, name="head")
    fcprim.pocket(bdy, "Head", head, lock_head_deep, midplane=True)

    # And the two M4 through the plate, into the extrusion's own slot.
    frame = fcprim.sketch(bdy, "Frame bolts", "YZ_Plane")
    for i, y in enumerate(frame_at):
        fcprim.circle(frame, (y, lock_up), frame_hole_d, name=f"frame{i}")
    fcprim.pocket(bdy, "Frame bolts", frame, midplane=True)

    spot = fcprim.sketch(bdy, "Spotfaces", "YZ_Plane",
                         offset=plate - spotface_deep / 2.0)
    for i, y in enumerate(frame_at):
        fcprim.circle(spot, (y, lock_up), spotface_d, name=f"spot{i}")
    fcprim.pocket(bdy, "Spotfaces", spot, spotface_deep, midplane=True)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   MOUNT  the face the plate lies against, looking out of it
    #   LOCK   the M3's axis, pointing along the extrusion
    fcprim.lcs(bdy, "MOUNT", at=(0.0, 0.0, lock_up), axis=(-1, 0, 0))
    fcprim.lcs(bdy, "LOCK", at=(lock_out, 0.0, lock_up), axis=(0, 1, 0))
    for i, y in enumerate(frame_at):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(0.0, y, lock_up), axis=(-1, 0, 0))

    return bdy


fcprim.make(__file__, "TOP_HINGE_LOCK_FRONT", hinge_lock_front, undressed)
