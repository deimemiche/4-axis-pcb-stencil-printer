"""M8_<length> - M8 threaded rod, cut to length, drawn with its real thread.

Bought stock, like the extrusion and the linear rod.  The machine uses one
length of it:

    M8_55.FCStd   x4   the eccenter rods, two on each side member

Each stands in a slot of the bottom frame's side extrusion on a pair of nuts,
runs up through `ECCF_HEIGHT` and `ECCF_TOP`, and carries the nut that sets the
working height.  Adding a length is adding a number to `lengths` below -- the
original author's Z axis hung on two M8 x 140, which the linear Z mod does away
with, so 55 is the only one this build buys.

    Core     sketch -> Pad     a circle at the minor diameter, run up +Z
    Thread   sketch -> Helix   the ISO profile, swept past both ends
    Trim     sketch -> Pocket  square, back to length at each end

**The thread is real geometry here**, where [`m5-threaded-rod.py`] draws its
studding as a plain 5 mm cylinder.  The reason that one is plain is length: a
0.8 mm pitch over 270 mm is some 337 turns of swept profile per stick, to show
a surface that only ever runs in a printed nut or a clearance hole.  The same
thread over 55 mm is 44 turns, which costs nothing to sweep and is what anyone
opening the file expects to see, since this rod is the one you actually take
hold of and turn to level the machine.

The profile is ISO 68-1 metric coarse, simplified the usual way: a 60 degree V
truncated to a `pitch/8` land at the crest and a `pitch/4` land at the root,
which puts the flanks at 30 degrees off the axis and leaves the flat root minor
diameter `d - 1.0825 P` = 6.647 mm.  The rounded root and the tolerance class's
allowance are not drawn -- both are smaller than a printed nut cares about, and
every nut on this rod is a bought one running on a real thread anyway.

**Both ends are cut square**, through the thread, which is what a hacksaw
leaves and what the eccenter needs: the bottom face beds on the nuts down in
the extrusion's slot and the top one is free.  No lead-in chamfer is drawn.

That squareness is also what makes the build's check exact.  A thread is a screw
sweep, so moving up the rod by any distance is the same as turning it -- which
means the **cross section is the same area at every height**, and the volume of
a piece cut square at both ends is that area times the length, with no end
effects to account for.  `section_area` works it out from the profile: the
minor circle, plus each ring between minor and major radius taking the share of
the pitch the rib is wide there.  It is arithmetic on the same numbers the
sketches use, so it catches a pad that ran the wrong way or a thread swept at
the wrong pitch, but not a mistyped pitch itself.

**Ignore the bounding box the build prints.** A swept thread is a B-spline
surface, and `Shape.BoundBox` measures those by their control points rather
than by the surface, so this rod reports something like X[-7.4, 4.0],
Z[-1.3, 56.3] for a solid that really runs 8 mm across and 0 .. 55 long. The
volume is exact regardless, and `export.py` then `stlmeasure.py` gives the true
extents off the tessellation if they are ever in doubt.

Coordinates: the axis is the part's own **+Z**, running from zero, which is
what a `Cylindrical` joint expects and what the plain rod and the M5 studding
already use.

[`m5-threaded-rod.py`]: m5-threaded-rod.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

diameter = 8.0           # M8, nominal major diameter, over the crests
pitch = 1.25             # metric coarse
flank = 30.0             # degrees off the axis -- 60 included

# The lengths this machine is built from; see the module docstring.
lengths = (55.0,)

# ISO 68-1, truncated to flats at crest and root.  The full V stands
# H = sqrt(3)/2 P tall; an external thread keeps the middle 5/8 of it, so the
# rib is that much deep and its width runs from pitch/8 at the crest to
# 3/4 pitch at the root.
depth = 5.0 / 8.0 * math.sqrt(3.0) / 2.0 * pitch
half_crest = pitch / 16.0
half_root = 3.0 * pitch / 8.0

bury = 0.1               # how far the rib's inner edge sits inside the core
overrun = 2.0 * pitch    # how far the sweep runs past each end, to be trimmed
over = 2.0               # how far the trimming profiles clear the crests

# Where FreeCAD puts the origin of a cut end's face -- measured, not designed;
# see the datums at the foot of `studding`.
end_face_centre = 0.3606


def section_area():
    """The rod's cross section -- the same at every height; see the docstring.

    The core's circle, plus the rib: at radius `r` it is
    `2 (major - r) tan(flank)` wider than its crest land, and takes that
    fraction of the pitch out of the ring there.
    """
    major, minor = diameter / 2.0, diameter / 2.0 - depth
    tangent = math.tan(math.radians(flank))
    span, cube = major ** 2 - minor ** 2, major ** 3 - minor ** 3
    rib = (2.0 * math.pi / pitch) * (2.0 * half_crest * span / 2.0
                                     + 2.0 * tangent * (major * span / 2.0
                                                        - cube / 3.0))
    return math.pi * minor ** 2 + rib


def studding(doc, length):
    """A cored cylinder with the thread swept onto it, cut square to length."""
    bdy = fcprim.body(doc, f"M8_{length:.0f}")
    major, minor = diameter / 2.0, diameter / 2.0 - depth

    core = fcprim.sketch(bdy, "Core", "XY_Plane")
    fcprim.circle(core, (0.0, 0.0), 2.0 * minor, name="core")
    fcprim.pad(bdy, "Length", core, length)

    # The thread's axial section, drawn where the sweep starts -- a whole
    # `overrun` below the cut end, so that the first full turn is already up to
    # section by the time the rod begins.  The root side is sunk into the core
    # rather than laid on it, so the two share material instead of a face.
    thread = fcprim.sketch(bdy, "Thread", "XZ_Plane")
    fcprim.polyline(thread, [
        (minor - bury, -overrun - half_root),
        (minor, -overrun - half_root),
        (major, -overrun - half_crest),
        (major, -overrun + half_crest),
        (minor, -overrun + half_root),
        (minor - bury, -overrun + half_root),
    ], name="thread")
    fcprim.helix(bdy, "Thread", thread, pitch, length + 2.0 * overrun)

    # Back to length: the overhanging turn at each end, taken off square.  H is
    # X and V is Y on XY_Plane, and each pocket runs away from the rod.
    for label, at, away in (("Trim bottom", 0.0, False),
                            ("Trim top", length, True)):
        square = fcprim.sketch(bdy, label, "XY_Plane", offset=at)
        reach = major + over
        fcprim.polyline(square, [
            (-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach),
        ], name="trim")
        fcprim.pocket(bdy, label, square, overrun + pitch, reversed_=away)

    # Mounting datums for the assembly; see fcprim.lcs.  A rod is joined about
    # its axis, so `AXIS` is the one that matters and it sits at mid length,
    # where a `Cylindrical` joint can go either way from it.  The ends are for
    # whatever runs up against them -- a nut, a washer, the slot's floor.
    fcprim.lcs(bdy, "AXIS", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))

    # The eccenter hangs on this stick and grips it at both cut ends.  Those
    # two datums are `end_face_centre` out along X, and that number is not a
    # dimension of anything: the hand-built assembly picked the end *face*, and
    # a thread trimmed square leaves an end face that is not symmetric about
    # the rod's axis, so FreeCAD's own frame for it sits a third of a
    # millimetre off centre.  It is kept as measured, because moving it onto
    # the axis would move both eccenter halves by that much.  See
    # ASSEMBLY_SCRIPT.md, step 6.
    fcprim.lcs(bdy, "ECC_BOT", at=(end_face_centre, 0.0, 0.0), axis=(0, 0, -1),
               roll=180.0)
    fcprim.lcs(bdy, "ECC_TOP", at=(end_face_centre, 0.0, length), axis=(0, 0, 1))
    return bdy


for cut_length in lengths:
    fcprim.make(__file__, f"M8_{cut_length:.0f}",
                lambda doc, length=cut_length: studding(doc, length),
                section_area() * cut_length, made_of=fcprim.STEEL)
