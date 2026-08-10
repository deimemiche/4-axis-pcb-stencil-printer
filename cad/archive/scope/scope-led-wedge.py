"""SCOPE_LED_WEDGE - a strip of LEDs held at 45 degrees along a frame member.

Michael's own part, transcribed from `led_wedge()` in
[`../microscope-mount/led-wedge.py`](../microscope-mount/led-wedge.py).
It bolts flat under a 2020 and holds an 8.5 mm LED strip on a 45 degree face,
so the light comes in across the board rather than straight down at it -- which
is what makes solder joints and part outlines show up under the microscope.

145 mm of triangle with a 20 mm wide flange over it:

    Wedge            sketch -> Pad     the 8.5 x 8.5 triangle, 145 long
    Flange           sketch -> Pad     the obround that bolts to the member
    Frame bolts      sketch -> Pocket  two 5.5, 149.8 apart
    Head clearance   sketch -> Pocket  15 dia, so a driver can reach them
    Zip ties         sketch -> Pocket  four 2 mm slots, two either side

Its walls are 2.4 rather than the 4 everything else here uses, and the source
says why in one word: "not structural".

**The two 15 mm clearances are why this part has no closed form.**  They are
bored down through the sloping wedge, so what they take out is a cylinder
meeting a prism at an angle.  Everything else is rectangles and obrounds and
comes out of arithmetic exactly, so the check keeps that shape and asks
`Part` for the one term it cannot state: a cylinder common with the wedge.
That is still a second, independent description of the solid -- primitives and
a boolean, against sketches and pads -- rather than a measurement of this one.

The 1 mm break along the wedge's knife edge is left off, as everywhere in
`scope/`; see `../STATUS.md`.
"""

import math
import os
import sys

import Part
from FreeCAD import Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From ../microscope-mount/settings.py.
loose_fit = 0.5          # Settings.loose_fit
v_slot = 20.0            # Settings.v_slot_d
frame_bolt_d = 5.0       # M5, Settings.frame_bolt

wall = 4.0 * 3.0 / 5.0   # 2.4; "not structural"
strip_w = 8.5            # led_strip_w, and the wedge is that square
zip_tie_d = 2.0

length = 145.0           # the default the source is drawn at

flange_l = length + 4 * wall + 2 * frame_bolt_d        # 164.6 overall
flange_w = v_slot                                      # 20
flange_z = strip_w                                     # 8.5, on top of it
flange_mid = length / 2.0                              # 72.5, and the wedge's
flange_across = strip_w / 2.0                          # 4.25, its own middle

bolt_hole_d = frame_bolt_d + loose_fit                 # 5.5
bolt_span = length + 2 * wall                          # 149.8
bolt_at = (flange_mid - bolt_span / 2.0, flange_mid + bolt_span / 2.0)

head_d = 3.0 * frame_bolt_d                            # 15, for a driver
head_deep = v_slot                                     # 20, down past the wedge

tie_l = length / 3.0                                   # 48.333
tie_at = (flange_mid - length / 4.0, flange_mid + length / 4.0)
tie_across = (flange_across - (strip_w + 2 * zip_tie_d) / 2.0,
              flange_across + (strip_w + 2 * zip_tie_d) / 2.0)


def wedge_section():
    """The triangle, in the plane across the strip: upright, roof, slope."""
    return [(0.0, 0.0), (0.0, strip_w), (strip_w, strip_w)]


def clearance_loss():
    """How much of the wedge the two head clearances take out.

    The one term arithmetic cannot state here; see the module docstring.
    """
    section = Part.Face(Part.makePolygon(
        [Vector(0.0, y, z) for y, z in wedge_section()]
        + [Vector(0.0, 0.0, 0.0)]))
    wedge = section.extrude(Vector(length, 0.0, 0.0))
    lost = 0.0
    for x in bolt_at:
        bore = Part.makeCylinder(head_d / 2.0, head_deep,
                                 Vector(x, flange_across, flange_z),
                                 Vector(0.0, 0.0, -1.0))
        lost += wedge.common(bore).Volume
    return lost


def expected_volume():
    """Arithmetic on the numbers above, and one boolean; see `../STATUS.md`."""
    wedge = strip_w ** 2 / 2.0 * length
    flange = (flange_w * (flange_l - flange_w)
              + math.pi * (flange_w / 2.0) ** 2) * wall

    bolts = 2 * math.pi / 4.0 * bolt_hole_d ** 2 * wall
    # The ties are in the flange's overhang, either side of the wedge, so each
    # takes out its own obround's worth of it and nothing else.
    ties = 4 * (zip_tie_d * (tie_l - zip_tie_d)
                + math.pi * (zip_tie_d / 2.0) ** 2) * wall

    return wedge + flange - bolts - ties - clearance_loss()


def led_wedge(doc):
    bdy = fcprim.body(doc, "SCOPE_LED_WEDGE")

    # Drawn on YZ so the section is across the strip and the pad runs along
    # it, the way the source's own Workplane("YZ") has it.
    section = fcprim.sketch(bdy, "Wedge", "YZ_Plane")
    fcprim.polyline(section, wedge_section(), name="wedge")
    fcprim.pad(bdy, "Wedge", section, length)

    flange = fcprim.sketch(bdy, "Flange", "XY_Plane", offset=flange_z)
    reach = (flange_l - flange_w) / 2.0
    fcprim.slot(flange, (flange_mid - reach, flange_across),
                (flange_mid + reach, flange_across), flange_w, name="flange")
    fcprim.pad(bdy, "Flange", flange, wall)

    bolts = fcprim.sketch(bdy, "Frame bolts", "XY_Plane", offset=flange_z + wall)
    for i, x in enumerate(bolt_at):
        fcprim.circle(bolts, (x, flange_across), bolt_hole_d, name=f"bolt{i + 1}")
    fcprim.pocket(bdy, "Frame bolts", bolts)

    # Bored down from under the flange, so a driver reaches the bolt heads.
    heads = fcprim.sketch(bdy, "Head clearance", "XY_Plane", offset=flange_z)
    for i, x in enumerate(bolt_at):
        fcprim.circle(heads, (x, flange_across), head_d, name=f"head{i + 1}")
    fcprim.pocket(bdy, "Head clearance", heads, head_deep)

    ties = fcprim.sketch(bdy, "Zip ties", "XY_Plane", offset=flange_z + wall)
    for i, x in enumerate(tie_at):
        for j, y in enumerate(tie_across):
            fcprim.slot(ties, (x - (tie_l - zip_tie_d) / 2.0, y),
                        (x + (tie_l - zip_tie_d) / 2.0, y), zip_tie_d,
                        name=f"tie{i + 1}{'ab'[j]}")
    fcprim.pocket(bdy, "Zip ties", ties)

    # Mounting datums for the assembly; see fcprim.lcs.  The flange's top face
    # is what lies against the member, so its datums look up out of it.
    fcprim.lcs(bdy, "MOUNT", at=(flange_mid, flange_across, flange_z + wall),
               axis=(0, 0, 1))
    for i, x in enumerate(bolt_at):
        fcprim.lcs(bdy, f"BOLT{i + 1}",
                   at=(x, flange_across, flange_z + wall), axis=(0, 0, 1))

    return bdy


fcprim.make(__file__, "SCOPE_LED_WEDGE", led_wedge, expected_volume())
