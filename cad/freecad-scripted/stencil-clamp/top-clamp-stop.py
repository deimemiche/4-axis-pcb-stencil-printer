"""TOP_CLAMP_STOP - split collar that sets how far the stencil clamp travels.

Reconstructed from the original author's TOP_CLAMP_STOP.stl, in that mesh's own
coordinates: 10 mm of extrusion along X, the rod running along X through the
middle of it.

A 15.6 mm barrel clamps an 8.2 mm rod.  A tongue runs off it tangentially, split
from the bore by a 2 mm saw cut, and an M3 bolt across the cut pulls the two
halves of the tongue together.  Its nut drops into a hexagonal pocket that is
open to one end, so the nut slides in sideways and cannot turn.

Only the tongue's far corners break the extrusion: both are chamfered 3 mm at 45
degrees, in a plane the layer scan never sees.

    Body      sketch -> Pad     barrel and tongue, extruded along the rod
    Chamfers  sketch -> Pocket  the two corners off the tongue's end
    Rod bore  sketch -> Pocket  8.2 mm, through
    Saw cut   sketch -> Pocket  2 mm, from the bore out through the tongue
    Bolt hole sketch -> Pocket  M3 clearance, across the cut
    Nut       sketch -> Pocket  its hexagonal seat, open to one end
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 10.0            # along the rod
barrel_d = 15.6
rod_d = 8.2

tongue_y = 12.987        # how far the tongue reaches
tongue_top_z = 5.0       # the barrel's tangent point sets its other end
chamfer = 3.0            # 45 degrees off both far corners

cut_width = 2.0          # the saw cut between bore and tongue

bolt_y = 8.987
bolt_hole_d = 3.4        # M3 clearance
nut_across_flats = 5.7
nut_z = (-5.8, -3.2)     # where the nut sits along the bolt

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 1749.942


def top_clamp_stop(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_STOP")
    barrel_r = barrel_d / 2

    # The tongue leaves the barrel tangentially at the bottom and is cut off
    # level with tongue_top_z at the other end, where the barrel is still round.
    meet_y = math.sqrt(barrel_r ** 2 - tongue_top_z ** 2)
    sweep = 270.0 - math.degrees(math.atan2(tongue_top_z, meet_y))

    # Drawn looking along the rod; H is Y, V is Z.
    body = fcprim.sketch(bdy, "Body", "YZ_Plane")
    fcprim.polyline(body, [
        (0.0, -barrel_r),
        (tongue_y, -barrel_r),
        (tongue_y, tongue_top_z),
        (meet_y, tongue_top_z),
    ], name="stop", arcs={3: (barrel_r, sweep)})
    fcprim.pad(bdy, "Body", body, length)

    # Both chamfers are the same 45 degree line, mirrored end for end; each
    # profile is drawn well outside the part except along that line.
    chamfers = fcprim.sketch(bdy, "Chamfers", "XY_Plane")
    for side, edge in ((1, 0.0), (-1, length)):
        fcprim.polyline(chamfers, [
            (edge - side * over, tongue_y - chamfer - over),
            (edge + side * (chamfer + over), tongue_y + over),
            (edge - side * over, tongue_y + over),
        ], name=f"chamfer{'np'[side > 0]}")
    fcprim.pocket(bdy, "Chamfer cut", chamfers, midplane=True)

    bore = fcprim.sketch(bdy, "Rod bore", "YZ_Plane")
    fcprim.circle(bore, (0.0, 0.0), rod_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance", bore, reversed_=True)

    # Starts inside the bore, so the cut only ever opens what is already open.
    cut = fcprim.sketch(bdy, "Saw cut", "YZ_Plane")
    fcprim.polyline(cut, [
        (0.0, -cut_width / 2), (tongue_y + over, -cut_width / 2),
        (tongue_y + over, cut_width / 2), (0.0, cut_width / 2),
    ], name="cut")
    fcprim.pocket(bdy, "Saw cut", cut, reversed_=True)

    bolt = fcprim.sketch(bdy, "Bolt hole", "XY_Plane")
    fcprim.circle(bolt, (length / 2, bolt_y), bolt_hole_d, name="bolt")
    fcprim.pocket(bdy, "Bolt clearance", bolt, midplane=True)

    # Half a hexagon closed off by a slot running out to the end face, so the
    # nut can be pushed in from the side.
    nut = fcprim.sketch(bdy, "Nut", "XY_Plane", offset=nut_z[0])
    across_corners = nut_across_flats * 2 / math.sqrt(3)
    fcprim.polyline(nut, [
        (length / 2 - across_corners / 4, bolt_y - nut_across_flats / 2),
        (length / 2 - across_corners / 2, bolt_y),
        (length / 2 - across_corners / 4, bolt_y + nut_across_flats / 2),
        (length + over, bolt_y + nut_across_flats / 2),
        (length + over, bolt_y - nut_across_flats / 2),
    ], name="nut")
    fcprim.pocket(bdy, "Nut seat", nut, nut_z[1] - nut_z[0], reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `SPRING` is the
    # barrel's own axis at the near end face, which is what the spring pushes
    # on.  The pinch bolt crosses the saw cut, so it takes one at each end of
    # what it reaches: the far face it enters through, and the floor of its
    # nut seat.
    fcprim.lcs(bdy, "SPRING", axis=(1, 0, 0), roll=90.0)
    fcprim.lcs(bdy, "BOLT", at=(length / 2, bolt_y, length / 2), axis=(0, 0, 1))
    fcprim.lcs(bdy, "NUT", at=(length / 2, bolt_y, nut_z[1]), axis=(0, 0, 1))

    return bdy


fcprim.make(__file__, "TOP_CLAMP_STOP", top_clamp_stop, mesh_volume)
