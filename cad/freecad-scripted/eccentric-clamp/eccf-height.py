"""ECCF_HEIGHT - height adjustment thumb nut of the front eccenter.

Reconstructed from the original author's ECCF_HEIGHT.stl, in that mesh's own
coordinates: a two step knob spanning Y = -10 .. 0, turned by hand to set the
eccenter's height.

The wide lower flange is scalloped with ten semicircular flutes for grip.  An
M8 nut drops into the hexagonal pocket from underneath and is trapped by the
narrower 8.5 mm clearance at the top, so turning the knob drives the nut along
the threaded rod.

    Grip flange  sketch -> Pad          the wide lower disc
    Collar       sketch -> Pad          the narrow upper disc
    Flute        sketch -> Pocket       one scallop
                        -> PolarPattern the other nine
    Nut pocket   sketch -> Pocket       captive M8 nut, from below
    Rod clear    sketch -> Pocket       through the collar
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

top_y = 0.0             # the knob's upper face, in machine coordinates

flange_d = 44.0
flange_thickness = 5.0
collar_d = 35.0
collar_thickness = 5.0

flute_d = 7.0           # the grip scallops
flute_count = 10
flute_radius = flange_d / 2   # centres ride on the flange's own rim

nut_across_flats = 13.2  # M8
nut_depth = 8.0
rod_clear_d = 8.5        # M8 threaded rod clearance
rod_clear_depth = 2.0

mesh_volume = 10162.354


def eccf_height(doc):
    bdy = fcprim.body(doc, "ECCF_HEIGHT")
    flange_top = top_y - collar_thickness

    # Sketched on XZ, so every pad runs downwards from the face it sits on.
    flange = fcprim.sketch(bdy, "Grip flange", "XZ_Plane", offset=-flange_top)
    fcprim.circle(flange, (0.0, 0.0), flange_d, name="flange")
    fcprim.pad(bdy, "Flange", flange, flange_thickness)

    collar = fcprim.sketch(bdy, "Collar", "XZ_Plane", offset=-top_y)
    fcprim.circle(collar, (0.0, 0.0), collar_d, name="collar")
    fcprim.pad(bdy, "Collar", collar, collar_thickness)

    # One flute, then let the pattern put the rest round the rim.
    flute = fcprim.sketch(bdy, "Flute", "XZ_Plane", offset=-flange_top)
    fcprim.circle(flute, (0.0, flute_radius), flute_d, name="flute")
    cut = fcprim.pocket(bdy, "Flute cut", flute, flange_thickness, reversed_=True)
    fcprim.polar_pattern(bdy, "Flutes", [cut], flute_count, axis="Y_Axis")

    nut = fcprim.sketch(bdy, "Nut pocket", "XZ_Plane",
                        offset=-(top_y - rod_clear_depth))
    fcprim.polygon(nut, (0.0, 0.0), nut_across_flats, 6, angle=0.0, name="nut")
    fcprim.pocket(bdy, "Nut clearance", nut, nut_depth, reversed_=True)

    rod = fcprim.sketch(bdy, "Rod clearance", "XZ_Plane", offset=-top_y)
    fcprim.circle(rod, (0.0, 0.0), rod_clear_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance cut", rod, rod_clear_depth, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  The knob is turned, so
    # both are on its axis: the top face it screws up against, and the floor of
    # the clearance bored for the rod, which is where the nut inside it sits.
    fcprim.lcs(bdy, "ECC_MOUNT", at=(0.0, top_y, 0.0), axis=(0, 1, 0),
               roll=270.0)
    fcprim.lcs(bdy, "NUT", at=(0.0, top_y - rod_clear_depth, 0.0),
               axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "ECCF_HEIGHT", eccf_height, mesh_volume)
