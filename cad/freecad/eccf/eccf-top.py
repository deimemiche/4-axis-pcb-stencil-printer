"""ECCF_TOP - top body of the front eccenter.

Reconstructed from the original author's ECCF_TOP.stl, in that mesh's own
coordinates: the block spanning Y = 0 .. 27 that the eccenter's threaded rod
passes through, with a round boss reaching down to meet ECCF_HEIGHT below.

The upper block is chamfered off at both top corners, which is why it is drawn
lying in the XY plane and padded across the machine rather than sketched flat.
An M8 nut sits in the hexagonal bore running the whole way up; the bottom 2 mm
opens out to plain rod clearance.

    Block        sketch -> Pad     chamfered body, padded symmetric in Z
    Wings        sketch -> Pad     the two narrower shoulders beneath it
    Boss         sketch -> Pad     round spigot reaching down to Y = 0
    Nut bore     sketch -> Pocket  hexagonal, all the way up
    Rod clear    sketch -> Pocket  the plain bottom of that bore
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

block_half_x = 22.0
block_half_z = 13.2
block_bottom_y = 14.0
block_top_y = 27.0
chamfer = 8.0            # 45 degrees off both top corners

wing_inner_x = 17.6      # the shoulders only exist outboard of this
wing_bottom_y = 11.0
wing_bottom_half_z = 10.2  # they taper out to the block's own width by Y = 14

boss_d = 18.0            # spigot down onto the height adjuster

nut_across_flats = 13.3  # M8
nut_bottom_y = 2.0
rod_clear_d = 8.4        # M8 threaded rod clearance

mesh_volume = 13649.486


def eccf_top(doc):
    bdy = fcprim.body(doc, "ECCF_TOP")

    # Drawn as a cross section through the machine's width, so both chamfers
    # are ordinary sketch geometry rather than solid edge operations.
    block = fcprim.sketch(bdy, "Block", "XY_Plane")
    fcprim.polyline(block, [
        (-block_half_x, block_bottom_y),
        (block_half_x, block_bottom_y),
        (block_half_x, block_top_y - chamfer),
        (block_half_x - chamfer, block_top_y),
        (-block_half_x + chamfer, block_top_y),
        (-block_half_x, block_top_y - chamfer),
    ], name="block")
    fcprim.pad(bdy, "Block pad", block, 2 * block_half_z, midplane=True)

    # Drawn end on this time, because each shoulder is chamfered: it starts as
    # wide as the block at Y = 14 and tapers in to Y = 11.  Seen from above
    # that reads as a plain rectangle, so it is easy to miss.
    for side, start in ((-1, -block_half_x), (1, wing_inner_x)):
        wing = fcprim.sketch(bdy, f"Wing {'-+'[side > 0]}X", "YZ_Plane",
                             offset=start)
        fcprim.polyline(wing, [
            (wing_bottom_y, -wing_bottom_half_z),
            (block_bottom_y, -block_half_z),
            (block_bottom_y, block_half_z),
            (wing_bottom_y, wing_bottom_half_z),
        ], name="wing")
        fcprim.pad(bdy, f"Wing {'-+'[side > 0]}X pad", wing,
                   block_half_x - wing_inner_x)

    boss = fcprim.sketch(bdy, "Boss", "XZ_Plane", offset=-block_bottom_y)
    fcprim.circle(boss, (0.0, 0.0), boss_d, name="boss")
    fcprim.pad(bdy, "Boss pad", boss, block_bottom_y)

    # Cut upwards from the shoulder, so the bore follows the block however tall
    # it is made.
    nut = fcprim.sketch(bdy, "Nut bore", "XZ_Plane", offset=-nut_bottom_y)
    fcprim.polygon(nut, (0.0, 0.0), nut_across_flats, 6, angle=0.0, name="nut")
    fcprim.pocket(bdy, "Nut clearance", nut)

    rod = fcprim.sketch(bdy, "Rod clearance", "XZ_Plane")
    fcprim.circle(rod, (0.0, 0.0), rod_clear_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance cut", rod, nut_bottom_y)

    return bdy


fcprim.make(__file__, "ECCF_TOP", eccf_top, mesh_volume)
