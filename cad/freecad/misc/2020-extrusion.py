"""2020_<length> - T-slot aluminium extrusion, 20 x 20 mm, cut to length.

The one bought part the machine is mostly made of, and until now the only one
with no document of its own: `asm/stock.py` builds the extrusions as plain
`Part::Feature` booleans inside the assembly, which is fine for a solid to hang
joints off but is nothing anybody can open and edit.  This draws the same
section as a PartDesign body, so the profile has sketches and dimensions like
every other part here.

One script, several documents.  A stick of extrusion *is* its length -- the
section never changes -- so the length is the only parameter that varies and
each one is saved under its own name:

    2020_300.FCStd            x6   the four bottom frame members, the lid's
                                   back rail, and the hinge bar
    2020_300_TOP_FRONT.FCStd  x1   the lid's front rail, drilled for the
                                   stretcher
    2020_280.FCStd            x2   the lid's two sides, spanning between them

Adding a length is adding a number to `lengths` below.

    Section    sketch -> Pad           the 20 x 20 outside, run up +Z
    Slot       sketch -> Pocket        one T-slot, the whole length
                      -> PolarPattern  the other three, about the centre line
    Bore       sketch -> Pocket        the M5 core hole
    Stretcher  sketch -> Pocket        the cross hole, on the front rail only

**One of the seven 300s is drilled.**  The lid's front rail carries the stencil
stretcher: `M5_100_Stencil_Stretcher` runs from the spanner case through the
rail and out the far side, so that one stick needs a hole for the rod where the
others do not.  Cutting it into `2020_300` would put it in all seven -- the four
the bottom frame is made of included -- so the drilled stick is a document of
its own, built from the same `extrusion()` with `stretcher=True`.

5.4 mm, on the stick's own axis, at 150 of the 300.  That is where
`assembly/Top_Assembly.FCStd` already has the rod: it crosses the rail at
Z = 174.5 against the rail's own 24.5 to 324.5, dead centre.  The hole is drawn
through the +/-Y faces, but the section is four-fold symmetric so the pair of
faces is a free choice; its two mouths land on the `SLOT_YP` and `SLOT_YN`
datums, which sit at mid length already.

**The drill hardly meets the profile at all.**  At 5.4 it stays inside the
6 mm slot mouth, so there is no outer wall in its way and the cavity behind is
air: all it cuts is the two 1.9 mm thicknesses of boss between the centre bore
and the cavity floor, 115 mm3 in total.  That is 0.2 % of the stick, which is
why this one is checked at a tenth of the usual tolerance -- at 1 % a hole that
never got cut would pass unnoticed.

The section is **representative rather than a particular brand's**: a 6 mm slot
mouth opening into an 11 mm channel behind a 2 mm wall, with four diagonal ribs
carrying the centre boss out to the corners.  A supplier's own section differs
in the corner fillets and the exact web shape; the outside dimensions and the
slot positions -- the two things anything bolts to -- are right.

**The ribs are the whole of what makes this a section rather than a puzzle.**
Cut each cavity as a plain 11 mm rectangle and the four of them meet across the
diagonals, leaving the boss the centre bore runs through floating in mid air:
the profile comes out in five pieces and could not be extruded at all.  Sloping
the cavity flanks at 45 degrees leaves the ribs that hold it on.

That is what the volume check is for.  A real 20 x 20 slot 6 profile is
catalogued at 0.53 kg/m, which at 2.70 g/cm3 is 196 mm2 of section; this one
measures 196.1, and the number is sensitive to exactly the things that go
wrong -- a rib lost, a slot the polar pattern dropped, a bore that missed.

**This script lives beside the documents it writes, and has to.**
`fcprim.make` saves next to its own source, so a script in `bot/` writes
`bot/2020_300.FCStd` -- and `assembly/Bottom_Frame.FCStd` links
`../misc/2020_300.FCStd`.  Building in one place and copying to the other
swaps the file the assembly points at for one with a freshly generated element
map, which breaks every joint made against a face or an edge of it.  Build
where the assembly looks, and there is nothing to copy.

A name beginning with a digit is the one cost of naming these after the
profile.  FreeCAD's internal document *name* has to be an identifier, so it
sanitises `2020_300` to `_2020_300`; the label, the file and the body all keep
the plain name, and the underscore shows up only in `App.getDocument`.
`asmprim.part` looks a document up by its file's basename, which will not match
that, so it opens these by path.

Coordinates: the section is centred on the origin and the length runs along
**+Z** from zero, so the part's own Z is the axis of the stick.  `asm/stock.py`
puts its top face on Y = 0 instead, because there the members hang from a
common top surface; anything linking these documents into the assembly wants
that 10 mm.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

cell = 20.0              # 2020: one 20 mm cell, square
slot_mouth = 6.0         # the gap a slot nut drops through
slot_mouth_depth = 2.0   # and the outer wall it goes through
slot_channel = 11.0      # the widest the T gets, behind that wall
centre_bore = 4.2        # tapped M5 in most profiles
core = 8.0               # across the boss the centre bore is drilled through
rib = 2.0                # the four diagonal webs that hold that boss on
proud = 1.0              # how far the slot cutter stands outside the face

stretcher_hole = 5.4     # the M5 stretcher rod through the lid's front rail
stretcher_cut = 114.6    # and the little the drill takes out; see the docstring

# Catalogued 0.53 kg/m at 2.70 g/cm3; see the module docstring.
section_area = 196.0

# The lengths this machine is built from.
lengths = (300.0, 280.0)


def stick(length, stretcher=False):
    """What a stick of this length is called -- document, body and file."""
    return f"2020_{length:.0f}" + ("_TOP_FRONT" if stretcher else "")


def extrusion(doc, length, stretcher=False):
    """The section, run up +Z for `length`, drilled for the stretcher or not."""
    bdy = fcprim.body(doc, stick(length, stretcher))
    half = cell / 2.0

    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (-half, -half), (half, -half), (half, half), (-half, half),
    ], name="section")
    fcprim.pad(bdy, "Length", section, length)

    # One slot, drawn on the +Y face and walked from the mouth inwards: down
    # through the wall, out to the full width of the channel, then down the
    # sloping flanks to the boss and back out the other side.  It stands
    # `proud` outside the face so the cut has something to break out through.
    wide = slot_channel / 2.0
    front = half - slot_mouth_depth      # the wall's inner face
    back = core / 2.0                    # and the boss's own
    off = rib / math.sqrt(2.0)           # the ribs, measured off the diagonal
    mouth = slot_mouth / 2.0
    slot = fcprim.sketch(bdy, "Slot", "XY_Plane")
    fcprim.polyline(slot, [
        (-mouth, half + proud), (mouth, half + proud),
        (mouth, front), (wide, front), (wide, wide + off),
        (back - off, back), (-(back - off), back),
        (-wide, wide + off), (-wide, front), (-mouth, front),
    ], name="slot")
    # Symmetric and through all: the sketch sits on the near end face, so a
    # pocket that only ran one way would cut nothing at all.
    cut = fcprim.pocket(bdy, "Slot", slot, midplane=True)
    fcprim.polar_pattern(bdy, "Slots", [cut], 4, axis="Z_Axis")

    bore = fcprim.sketch(bdy, "Bore", "XY_Plane")
    fcprim.circle(bore, (0.0, 0.0), centre_bore, name="bore")
    fcprim.pocket(bdy, "Centre bore", bore, midplane=True)

    # Across the stick at mid length, on its axis: XZ draws in X and Z and the
    # pocket cuts along Y, symmetric and through all, so it opens on both faces.
    if stretcher:
        rod = fcprim.sketch(bdy, "Stretcher", "XZ_Plane")
        fcprim.circle(rod, (0.0, length / 2.0), stretcher_hole, name="rod")
        fcprim.pocket(bdy, "Stretcher hole", rod, midplane=True)

    # Mounting datums for the assembly; see fcprim.lcs.  Each datum's Z points
    # out of the face it names, which is the way a bolt goes in and the way a
    # butting member comes up against it.  The four slot faces take theirs at
    # mid length: a stick is the same all the way along and symmetric end to
    # end, so anything bolted at a particular place along it is located by its
    # own joint rather than by another datum here.
    fcprim.lcs(bdy, "END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))
    for label, (x, y) in (("SLOT_XP", (half, 0.0)), ("SLOT_YP", (0.0, half)),
                          ("SLOT_XN", (-half, 0.0)), ("SLOT_YN", (0.0, -half))):
        fcprim.lcs(bdy, label, at=(x, y, length / 2.0),
                   axis=(x / half, y / half, 0.0))
    return bdy


for cut_length in lengths:
    fcprim.make(__file__, stick(cut_length),
                lambda doc, length=cut_length: extrusion(doc, length),
                section_area * cut_length, made_of=fcprim.ALUMINIUM)

fcprim.make(__file__, stick(300.0, stretcher=True),
            lambda doc: extrusion(doc, 300.0, stretcher=True),
            section_area * 300.0 - stretcher_cut, tolerance=0.0015,
            made_of=fcprim.ALUMINIUM)
