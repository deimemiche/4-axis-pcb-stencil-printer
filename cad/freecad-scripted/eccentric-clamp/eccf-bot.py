"""ECCF_BOT - bottom plate of the front eccenter.

Reconstructed from the original author's ECCF_BOT.stl, in that mesh's own
coordinates, so the part sits where it belongs in the machine: a 40 x 20 plate
lying flat, 8 mm thick, spanning Y = -18 .. -10 under the eccenter body.

The centre hole carries the eccenter shaft: an 8 mm bore from the top meeting a
nut pocket from the bottom, so the shaft can be drawn up against a captive nut.
The two mounting bolts sit on the centreline at X = +-16, their heads sunk into
open slots that run out to the plate edge.

    Outline           sketch -> Pad     the plate
    Bolt head slots   sketch -> Pocket  open counterbores, from the top
    Shaft bore        sketch -> Pocket  from the top, halfway down
    Nut pocket        sketch -> Pocket  from the bottom, meeting the bore
    Bolt holes        sketch -> Pocket  from the bottom, into the slots
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

plate_x = 40.0          # across the machine
plate_z = 20.0          # front to back
plate_thickness = 8.0

top_y = -10.0           # the plate's upper face, in machine coordinates

shaft_d = 8.0           # eccenter shaft clearance
shaft_depth = 4.0       # bored halfway, the nut pocket meets it
nut_across_flats = 13.3  # M8 nut
nut_depth = 4.0

bolt_x = 16.0           # mounting bolts, one either side of the shaft
bolt_hole_d = 4.5       # M4 clearance
bolt_hole_depth = 3.5
head_d = 8.0            # bolt head clearance
head_depth = 4.5

mesh_volume = 4961.116


def eccf_bot(doc):
    bdy = fcprim.body(doc, "ECCF_BOT")

    # Sketched on XZ, so the pad runs down from the top face into the machine.
    outline = fcprim.sketch(bdy, "Outline", "XZ_Plane", offset=-top_y)
    fcprim.polyline(outline, [
        (-plate_x / 2, -plate_z / 2),
        (plate_x / 2, -plate_z / 2),
        (plate_x / 2, plate_z / 2),
        (-plate_x / 2, plate_z / 2),
    ], name="plate")
    fcprim.pad(bdy, "Plate", outline, plate_thickness)

    # Bolt head clearance, cut from the top.  Each slot runs from the bolt out
    # through the edge of the plate, so the plate can be slid onto its bolts
    # rather than lifted over them.
    heads = fcprim.sketch(bdy, "Bolt head slots", "XZ_Plane", offset=-top_y)
    for side in (-1, 1):
        fcprim.slot(heads, (side * bolt_x, 0.0), (side * plate_x / 2, 0.0),
                    head_d, name=f"head{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolt head clearance", heads, head_depth, reversed_=True)

    bore = fcprim.sketch(bdy, "Shaft bore", "XZ_Plane", offset=-top_y)
    fcprim.circle(bore, (0.0, 0.0), shaft_d, name="shaft")
    fcprim.pocket(bdy, "Shaft clearance", bore, shaft_depth, reversed_=True)

    # From the underside: the nut pocket meets the bore halfway through.
    nut = fcprim.sketch(bdy, "Nut pocket", "XZ_Plane",
                        offset=-(top_y - plate_thickness))
    # Corners on the X axis, flats front and back, as the original has it.
    fcprim.polygon(nut, (0.0, 0.0), nut_across_flats, 6, angle=0.0, name="nut")
    fcprim.pocket(bdy, "Nut clearance", nut, nut_depth)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane",
                          offset=-(top_y - plate_thickness))
    for side in (-1, 1):
        fcprim.circle(bolts, (side * bolt_x, 0.0), bolt_hole_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, bolt_hole_depth)

    # Mounting datums for the assembly; see fcprim.lcs.  The plate is bolted
    # down onto three brackets at once, so it takes a datum at each of the
    # corners they reach -- two of them the same corner, once each way up,
    # because two brackets meet there.  `NUT` and `STUD` are on the shaft's own
    # axis: the top face, where the eccenter's stud enters, and the floor of
    # the bore, where the nut behind it stops.  The two mounting bolts have
    # theirs on the floor of the slot cut for their heads.
    for side, label in ((-1, "BOLT1"), (1, "BOLT2")):
        fcprim.lcs(bdy, label, at=(side * bolt_x, top_y - head_depth, 0.0),
                   axis=(0, -1, 0))
    fcprim.lcs(bdy, "NUT", at=(0.0, top_y, 0.0), axis=(0, -1, 0))
    fcprim.lcs(bdy, "STUD", at=(0.0, top_y - shaft_depth, 0.0), axis=(0, -1, 0))
    under = top_y - plate_thickness
    fcprim.lcs(bdy, "BRACKET", at=(plate_x / 2, under, plate_z / 2),
               axis=(0, -1, 0), roll=270.0)
    fcprim.lcs(bdy, "BRACKET_X", at=(-plate_x / 2, under, plate_z / 2),
               axis=(0, 1, 0), roll=270.0)
    fcprim.lcs(bdy, "Z_AXIS_BRACKET", at=(-plate_x / 2, under, plate_z / 2),
               axis=(0, -1, 0), roll=270.0)

    return bdy


fcprim.make(__file__, "ECCF_BOT", eccf_bot, mesh_volume)
