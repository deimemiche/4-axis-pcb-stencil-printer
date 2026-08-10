"""BOT_CLAMP_Z_AXIS - clamps the bottom frame to the Z axis rods.

Reconstructed from the original author's BOT_CLAMP_Z_AXIS.stl, in that mesh's
own coordinates: 40 mm along Y, the rod running along it.

An 8.2 mm bore in a 16.2 mm boss, with a wing either side of it.  A saw cut runs
from the bore out to one end so the boss can be squeezed shut, which is why the
two wings sit at different heights: 4 mm apart, the width of the cut plus the
material each side of it.

Each wing blends into the boss on an 8 mm radius - a long sweep, tangent to the
boss at one end and to the wing's own face at the other, so the whole top of the
part is one continuous curve.

Four M4 pull the wings together.  Each is counterbored 7.5 mm from the top and
sunk 0.2 mm below the face it lands on; underneath, the part stands on two ribs
across its width rather than on the whole of its underside.

    Body     sketch -> Pad     the side view, extruded the whole length
    Feet     sketch -> Pad     the two ribs it stands on, flared 45 degrees
    Bore     sketch -> Pocket  8.2 mm through
    Saw cut  sketch -> Pocket  what lets the boss close
    Shanks   sketch -> Pocket  four M4 clearance holes, one pair per wing
    Heads    sketch -> Pocket  their counterbores, through from each face
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 40.0            # along the rod
half_x = 15.92

bore_d = 8.2             # the rod
boss_d = 16.2
blend_r = 8.0            # boss to wing, tangent at both ends

base_z = -8.1            # the underside of both wings
low_top = -4.1           # the top of the wing the saw cut passes under
high_top = 1.7           # and of the one above it
cut_z = (-4.1, -2.3)     # the saw cut itself
cut_blend = 1.0          # where its roof runs into the bore

foot_z = -9.1            # the ribs it actually stands on
foot_half = 1.5          # at the floor; they flare out 45 degrees to the part

bolt_x = 11.92
bolt_y = (10.0, 30.0)
shank_d = 4.6            # M4 clearance
head_d = 7.5
spotface = 0.2           # how far the counterbore's floor sits below the face

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 10794.273


def bot_clamp_z_axis(doc):
    bdy = fcprim.body(doc, "BOT_CLAMP_Z_AXIS")
    bore_r, boss_r = bore_d / 2, boss_d / 2
    reach = boss_r + blend_r

    def blend(hand, top):
        """Centre of the wing blend, and where it leaves the boss.

        It is tangent to the boss and to the wing's flat top, which fixes it:
        the centre sits one radius above that top and `reach` from the axis.
        """
        centre = (hand * math.sqrt(reach ** 2 - (top + blend_r) ** 2),
                  top + blend_r)
        return centre, (centre[0] * boss_r / reach, centre[1] * boss_r / reach)

    high, high_touch = blend(1, high_top)
    low, low_touch = blend(-1, low_top)

    # Drawn looking along the rod; H is X, V is Z, and the pad runs along Y.
    # The bore and the saw cut come off afterwards.
    body = fcprim.sketch(bdy, "Body", "XZ_Plane")
    fcprim.polyline(body, [
        (-half_x, base_z),
        (half_x, base_z),
        (half_x, high_top),
        (high[0], high_top),
        high_touch,
        low_touch,
        (low[0], low_top),
        (-half_x, low_top),
    ], name="side", arcs={3: -blend_r, 4: boss_r, 5: -blend_r})
    fcprim.pad(bdy, "Body", body, length, reversed_=True)

    # Drawn end on, where each rib is a trapezium: it meets the underside on a
    # 45 degree flare, and runs the full width without one.
    flare = base_z - foot_z
    feet = fcprim.sketch(bdy, "Feet", "YZ_Plane", offset=-half_x)
    for i, centre in enumerate(bolt_y):
        fcprim.polyline(feet, [
            (centre - foot_half, foot_z),
            (centre + foot_half, foot_z),
            (centre + foot_half + flare, base_z),
            (centre - foot_half - flare, base_z),
        ], name=f"foot{i}")
    fcprim.pad(bdy, "Feet", feet, 2 * half_x)

    bore = fcprim.sketch(bdy, "Bore", "XZ_Plane")
    fcprim.circle(bore, (0.0, 0.0), bore_d, name="rod")
    fcprim.pocket(bdy, "Bore", bore, length)

    # The saw cut.  Its roof runs into the bore on a small radius; the rest of
    # the profile is closed off inside the bore, where it cuts nothing.
    nose = (math.sqrt((bore_r + cut_blend) ** 2 - (cut_z[1] + cut_blend) ** 2),
            cut_z[1] + cut_blend)
    lands = (nose[0] * bore_r / (bore_r + cut_blend),
             nose[1] * bore_r / (bore_r + cut_blend))
    cut = fcprim.sketch(bdy, "Saw cut", "XZ_Plane")
    fcprim.polyline(cut, [
        lands,
        (nose[0], cut_z[1]),
        (half_x + over, cut_z[1]),
        (half_x + over, cut_z[0]),
        (0.0, cut_z[0]),
        (0.0, lands[1]),
    ], name="cut", arcs={0: cut_blend})
    fcprim.pocket(bdy, "Saw cut", cut, length)

    # Each wing's bolts go in from its own face, so the two pairs are drilled
    # to different depths and counterbored from different heights.
    for hand, label, top in ((-1, "low", low_top), (1, "high", high_top)):
        floor = top - spotface
        shanks = fcprim.sketch(bdy, f"Shanks {label}", "XY_Plane",
                               offset=foot_z)
        for i, y in enumerate(bolt_y):
            fcprim.circle(shanks, (hand * bolt_x, y), shank_d, name=f"bolt{i}")
        fcprim.pocket(bdy, f"Shanks {label}", shanks, floor - foot_z,
                      reversed_=True)

        heads = fcprim.sketch(bdy, f"Heads {label}", "XY_Plane", offset=floor)
        for i, y in enumerate(bolt_y):
            fcprim.circle(heads, (hand * bolt_x, y), head_d, name=f"head{i}")
        fcprim.pocket(bdy, f"Heads {label}", heads, reversed_=True)

    return bdy


fcprim.make(__file__, "BOT_CLAMP_Z_AXIS", bot_clamp_z_axis, mesh_volume)
