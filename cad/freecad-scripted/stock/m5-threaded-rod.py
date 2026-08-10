"""M5_270 - M5 threaded rod: the sticks that drive the machine, and one more.

Bought stock, like the extrusion and the linear rod, and like them it existed
only inside `asm/stock.py` as a `Part::Feature` cylinder -- fine as a solid to
hang a joint off, but nothing anybody can open and edit.  This draws the same
studding as PartDesign bodies, so it opens with a sketch and a dimension in it.

The manual buys **three** M5 x 270 and each one does a different job, so this is
one document holding a body per stick rather than one part used three times.
The three have counterparts in [`asm/drive.py`](../asm/drive.py), which is
where the machine's own copies are built and placed.  Michael's machine has a
**fourth**, an M5 x 100 for the stencil stretcher, which he drew into the
document in the GUI:

    M5_270_WORM_SHAFT          the alpha axis: worm, thrust nuts, handwheel
    M5_270_X_SCREW             the X carriage screw, through the bracket's eye
    M5_270_Y_SCREW             the Y carriage screw, through the driven arm
    M5_100_Stencil_Stretcher   Michael's, and the only one not 270 long

    Section  sketch -> Pad   a 5 mm circle, run up +Z

Adding a stick is adding a line to `rods` below -- a name and a length.

**Drawn plain, at the nominal major diameter, exactly as `asm/stock.py` draws
it.**  Modelling a real M5 thread here would be 0.8 mm of pitch over 270 mm --
some 337 turns of swept profile per stick -- to represent a surface nothing in
the machine locates on: every one of these runs in a printed nut or a clearance
hole, and the parts that matter are already drawn.  Both documents therefore
give the same solid, and agree to **zero volume**.  Michael wants them threaded
for real in the end; see the note at the bottom.

That makes each stick exactly pi/4 d^2 L, which is what the build checks, over
all four together: it is a thin check, but it is the whole of the part, and it
catches a pad that ran the wrong way, a diameter typed as a radius, or one of
them left short.

Coordinates: each stick's axis is its own **+Z**, running from zero, which is
what `asm/stock.py` uses and what a `Cylindrical` joint expects.  They then
stand side by side, `spacing` apart along +X -- that offset is the body's own
`Placement`, document layout and no part of the geometry, so that opening the
file shows four sticks rather than four coincident ones.  Every sketch and
every datum is drawn at the origin regardless.

**The datums carry the stick's name**, `X_SCREW_AXIS` where a one-part document
would say `AXIS`.  Labels are unique per *document*, not per body, so three
bodies each with an `AXIS` come out as `AXIS`, `AXIS001` and `AXIS002` -- and
`asmprim.datum` finds a datum by its label, so a joint would be asking for a
suffix that means nothing and moves with the build order.

`asmprim.part` hands back the *first* body in a document, so
`part("misc/M5_270")` is the worm shaft.  Among the three 270s that does not
matter -- they are the same stick -- but the stretcher is not, so anything
wanting a particular one picks it by label.

**Left to do, and this script has not been run against the document beside it.**
`M5_270.FCStd` is Michael's own GUI edit, and a rebuild regenerates the element
map: `assembly/Bottom_Assembly.FCStd` and `assembly/Rotation_Table.FCStd` both
link it for the screws, so every joint made against a face or an edge of one
would break.  The rebuild therefore waits, and waits for both notes below at
once.  What this script says and what the document holds differ in exactly
three places until it happens, all three of them the stretcher's and all three
artefacts of its having been copied from `M5_270_Y_SCREW`:

    datum labels    `Stencil_Stretcher_AXIS`, `_END_A`, `_END_B` here;
                    `Y_SCREW_AXIS001`, `_END_A001`, `_END_B001` there
    datum heights   50 and 100 here, its own mid length and far end;
                    135 and 270 there, a *270*'s, off the end of this stick
    Placement       `3 * spacing` here; x = 40 there, on top of the Y screw

    TODO rename, when this is cleaned up.  Three names no longer say what they
    mean.  The **document** is `M5_270` and holds a stick that is not 270; the
    **body** is `M5_100_Stencil_Stretcher` where every other part here is upper
    case throughout; and the stretcher's **datums** are the Y screw's, as
    above.  A document's name is its file name too, and the two assemblies link
    that file, so renaming it is a relink as well -- which is why it belongs
    with the cleanup rather than happening on its own.

    TODO draw these with their real thread, as
    [`m8-threaded-rod.py`](m8-threaded-rod.py) does, so they are actual
    threaded rod rather than plain cylinders at the major diameter.  What has
    stopped it is only the sweep: 0.8 mm of pitch is 337 turns over 270 mm
    against the M8's 44, and the reasoning for leaving them plain is above.
    The stretcher at 125 turns is the cheap one to do first.
"""

import math
import os
import sys

from FreeCAD import Placement, Rotation, Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

diameter = 5.0           # M5, nominal major diameter; see the module docstring

spacing = 20.0           # between sticks, laid out along +X

# What each stick is for and how long it is.  The three 270s are the manual's,
# in the order asm/drive.py builds them; the 100 is Michael's stretcher rod,
# and its mixed case name is his -- see the rename note in the docstring.
rods = (
    ("WORM_SHAFT", 270.0),
    ("X_SCREW", 270.0),
    ("Y_SCREW", 270.0),
    ("Stencil_Stretcher", 100.0),
)


def studding(doc, role, length, at_x):
    """A circle, run up +Z for `length`, standing at `at_x`."""
    bdy = fcprim.body(doc, f"M5_{length:.0f}_{role}")

    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.circle(section, (0.0, 0.0), diameter, name="rod")
    fcprim.pad(bdy, "Length", section, length)

    # Mounting datums for the assembly; see fcprim.lcs, and the module
    # docstring for why they are named after the stick.  A screw is joined
    # about its axis and turns in it, so the axis is the one that matters and
    # it sits at mid length, where a `Cylindrical` joint can go either way from
    # it.  The ends are for whatever the plain end runs into -- a handwheel
    # pushed on, a nut run up against a face.
    fcprim.lcs(bdy, f"{role}_AXIS", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, f"{role}_END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, f"{role}_END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))

    bdy.Placement = Placement(Vector(at_x, 0.0, 0.0), Rotation())
    return bdy


def sticks(doc):
    """All four, side by side."""
    return [studding(doc, role, length, i * spacing)
            for i, (role, length) in enumerate(rods)]


fcprim.make(__file__, "M5_270", sticks,
            sum(math.pi * (diameter / 2.0) ** 2 * length
                for _, length in rods),
            made_of=fcprim.STEEL)
