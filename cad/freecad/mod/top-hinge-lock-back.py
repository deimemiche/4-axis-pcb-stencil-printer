"""TOP_HINGE_LOCK_BACK - the hooked half of Michael's hinge lock.

Michael's own part, from the hinge lock mod in the repository's README, and
transcribed from the CadQuery in [`../../hinge-lock.py`](../../hinge-lock.py)
driven by [`../../settings.py`](../../settings.py) the same way `mod/`'s two Z
axis parts are transcribed from `z-axis.py`.  There is no mesh and no drawing to
check it against, so what checks it is the assembly.

What it is for, in his words: "the hinges I used still allowed for some play
between the back of the frame and the moving part... if you're looking for
repeatability across multiple applies, or just to increase overall rigidity of
the top frame when closed".  So it is what takes the slop out of the lid's
hinge, and there are two halves - this one and `TOP_HINGE_LOCK_FRONT` - drawn
together by one M3 that runs along the bars.

A block 39 x 19.9 x 28.1 with a **20.1 mm square channel** cut 24 deep into one
end and straight through its width, which is a 20 mm extrusion plus a tight
fit with a 4 mm wall above and below it.  It hooks over a bar.  What is left
past the channel is a 15 mm tail, and the M3 runs along the part's width
through that tail into a nut held in a pocket.

    Body       sketch -> Pad     the block
    Channel    sketch -> Pocket  what it hooks over, through the width
    Frame      sketch -> Pocket  two M4 through both walls
    Lock       sketch -> Pocket  the M3, along the width through the tail
    Nut        sketch -> Pocket  its nut, and the slot the nut drops through

**Two readings that could not be settled from the source** and are the things
to check first if this ever comes out wrong:

* the **two M4** at x -13.5 and -1.5 run through the top wall, the channel and
  the bottom wall.  Whatever they bolt to, it is not the bar in the channel:
  they straddle its centre line by 6 mm either side, where a 2020's slot is
  not.  They are drawn as the source draws them.
* the nut pocket's **side cut** opens upward here, so the nut drops in from the
  top face.  `nutcatchSidecut` puts it on one side of the part and the source
  does not say which; nothing else depends on it.

The cosmetic chamfers the CadQuery part carries are left off, as they are on
`top-z-axis-bracket.py`, and for the same reason: they change no fit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From cad/settings.py.
wall = 4.0               # Settings.wallThickness
tight_fit = 0.1          # Settings.tightFit
loose_fit = 0.5          # Settings.looseFit
bolt_fit = 0.2           # Settings.boltFit
ext = 20.0               # Settings.extD

# The two bolts, from cq_queryabolt's own tables.
frame_bolt_d = 4.0       # M4, Settings.frameBolt
frame_nut_across = 7.0   # an M4 nut, across the flats
lock_bolt_d = 3.0        # M3, Settings.bolt
lock_nut_across = 5.5
lock_nut_thick = 2.4

# hinge-lock.py's own three numbers, in its own order.
bolt_length = frame_bolt_d * 2 + 4 * wall        # 24, and the channel's depth
length = bolt_length + 2 * wall + frame_nut_across        # 39
height = ext + tight_fit + 2 * wall              # 28.1
width = ext - tight_fit                          # 19.9

channel = ext + tight_fit                        # 20.1 square
channel_end = -length / 2.0 + bolt_length        # +4.5, where it stops
floor = (height - channel) / 2.0                 # 4.0, the wall each side

channel_mid = channel_end - bolt_length / 2.0    # -7.5, the channel's centre
frame_hole_d = frame_bolt_d + bolt_fit           # 4.2
frame_at = (channel_mid - bolt_length / 4.0,
            channel_mid + bolt_length / 4.0)     # -13.5 and -1.5

lock_hole_d = lock_bolt_d + loose_fit            # 3.5
lock_at = bolt_length / 2.0                      # +12, out in the tail
lock_y = height / 2.0                            # 14.05, the channel's middle
nut_at = width / 2.0 - (ext - wall)              # -6.05, how far the nut is in
nut_thick = lock_nut_thick + bolt_fit            # 2.6

over = 2.0               # how far cutting profiles run past the part

# The CadQuery solid's own volume with its chamfers suppressed, which is
# what this transcription should come to exactly.
undressed = 11585.562


def hinge_lock_back(doc):
    bdy = fcprim.body(doc, "TOP_HINGE_LOCK_BACK")

    # Drawn in plan; H is X, the length, V is Y, the width.  The pad runs up Z.
    plan = fcprim.sketch(bdy, "Body", "XY_Plane")
    fcprim.polyline(plan, [
        (-length / 2.0, -width / 2.0),
        (length / 2.0, -width / 2.0),
        (length / 2.0, width / 2.0),
        (-length / 2.0, width / 2.0),
    ], name="body")
    fcprim.pad(bdy, "Body", plan, height)

    # The channel it hooks over: drawn in side view, cut right through the
    # width, and open at the -X end.
    hook = fcprim.sketch(bdy, "Channel", "XZ_Plane")
    fcprim.polyline(hook, [
        (-length / 2.0 - over, floor),
        (channel_end, floor),
        (channel_end, floor + channel),
        (-length / 2.0 - over, floor + channel),
    ], name="channel")
    fcprim.pocket(bdy, "Channel", hook, midplane=True)

    # Two M4 straight down through both walls; see the docstring.
    frame = fcprim.sketch(bdy, "Frame bolts", "XY_Plane")
    for i, x in enumerate(frame_at):
        fcprim.circle(frame, (x, 0.0), frame_hole_d, name=f"frame{i}")
    fcprim.pocket(bdy, "Frame bolts", frame, midplane=True)

    # The M3 that draws the two halves together, along the width.
    lock = fcprim.sketch(bdy, "Lock bolt", "XZ_Plane")
    fcprim.circle(lock, (lock_at, lock_y), lock_hole_d, name="lock")
    fcprim.pocket(bdy, "Lock bolt", lock, midplane=True)

    # Its nut, and the slot the nut drops down through.
    nut = fcprim.sketch(bdy, "Nut", "XZ_Plane", offset=-nut_at)
    fcprim.polygon(nut, (lock_at, lock_y), lock_nut_across, angle=30.0,
                   name="nut")
    fcprim.pocket(bdy, "Nut", nut, nut_thick)

    drop = fcprim.sketch(bdy, "Nut slot", "XZ_Plane", offset=-nut_at)
    fcprim.polyline(drop, [
        (lock_at - lock_nut_across / 2.0, lock_y),
        (lock_at + lock_nut_across / 2.0, lock_y),
        (lock_at + lock_nut_across / 2.0, height + over),
        (lock_at - lock_nut_across / 2.0, height + over),
    ], name="slot")
    fcprim.pocket(bdy, "Nut slot", drop, nut_thick)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   HOOK  the closed end of the channel, where the bar seats
    #   LOCK  the M3's axis, pointing along the part's width
    fcprim.lcs(bdy, "HOOK", at=(channel_end, 0.0, height / 2.0), axis=(-1, 0, 0))
    fcprim.lcs(bdy, "LOCK", at=(lock_at, 0.0, lock_y), axis=(0, 1, 0))

    return bdy


fcprim.make(__file__, "TOP_HINGE_LOCK_BACK", hinge_lock_back, undressed)
