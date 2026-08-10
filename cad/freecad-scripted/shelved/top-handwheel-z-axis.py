"""TOP_HANDWHEEL_Z_AXIS - the wheel that raises and lowers the top frame.

Reconstructed from the original author's TOP_HANDWHEEL_Z_AXIS.stl, in that
mesh's own coordinates: Y = 0 .. 17, turned about Y.

A 38 mm wheel with ten 6 mm flutes to grip by, standing on a 16 mm boss.  An
8.4 mm bore runs up from the boss and opens out into a socket for an M8 nut,
which is what actually drives the screw.

Both faces of the wheel are broken 1 mm, and the break follows the flutes as
well as the rim, so it is a chamfer taken after they are cut rather than
anything the turned section could carry.  The boss's own face is left square.

    Section  sketch -> Revolution    boss, wheel and bore
    Flute    sketch -> Pocket        one grip flute
                    -> PolarPattern  the other nine
    Rims             Chamfer         1 mm round both faces of the wheel
    Nut      sketch -> Pocket        the M8 nut's socket, down to the bore
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

rim_d = 38.0
rim_y = (5.0, 17.0)
edge_break = 1.0         # 45 degrees off both faces of the wheel

boss_d = 16.0
boss_y = 5.0             # the boss runs from Y = 0 up to the wheel

bore_d = 8.4             # M8 clearance, all the way up inside the socket

flutes = 10
flute_d = 6.0            # cut on the wheel's own diameter

nut_across_flats = 13.3  # M8
nut_floor = 9.0          # how far down the socket goes

mesh_volume = 11107.886


def top_handwheel_z_axis(doc):
    bdy = fcprim.body(doc, "TOP_HANDWHEEL_Z_AXIS")
    bore_r = bore_d / 2

    # Half a section through the wheel; H is the radius, V is height.  The bore
    # is taken right through: above the socket's floor it is inside the socket
    # anyway, and drawing it that way keeps the section to one closed profile.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (bore_r, 0.0),
        (boss_d / 2, 0.0),
        (boss_d / 2, boss_y),
        (rim_d / 2, rim_y[0]),
        (rim_d / 2, rim_y[1]),
        (bore_r, rim_y[1]),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    # One flute, cut on the wheel's own diameter, then repeated round.
    flute = fcprim.sketch(bdy, "Flute", "XZ_Plane", offset=-rim_y[1])
    fcprim.circle(flute, (0.0, -rim_d / 2), flute_d, name="flute")
    cut = fcprim.pocket(bdy, "Flute", flute, rim_y[1] - rim_y[0],
                        reversed_=True)
    fcprim.polar_pattern(bdy, "Grip", [cut], flutes, axis="Y_Axis")

    # The break round both faces of the wheel, taken after the flutes so that
    # it follows them.  Nothing else out at that radius: the boss's rim and the
    # bore's mouth are the only other edges in those two planes.
    def rim(edge):
        point = fcprim.midpoint(edge)
        if min(abs(point.y - end) for end in rim_y) > 1e-6:
            return False
        return math.hypot(point.x, point.z) > boss_d / 2 + 1e-6

    fcprim.chamfer(bdy, "Rims", edge_break, rim)

    nut = fcprim.sketch(bdy, "Nut socket", "XZ_Plane", offset=-rim_y[1])
    fcprim.polygon(nut, (0.0, 0.0), nut_across_flats, angle=30.0, name="nut")
    fcprim.pocket(bdy, "Nut socket", nut, rim_y[1] - nut_floor, reversed_=True)

    return bdy


fcprim.make(__file__, "TOP_HANDWHEEL_Z_AXIS", top_handwheel_z_axis,
            mesh_volume)
