"""TOP_CLAMP_Z_AXIS - clamps the top frame to a Z axis rod.

Reconstructed from the original author's TOP_CLAMP_Z_AXIS.stl, in that mesh's
own coordinates: 34 mm along Y, the rod running along it.

The same 8.2 mm bore in a 16.2 mm boss as `BOT_CLAMP_Z_AXIS`, split by a 2 mm
saw cut whose far face is tangent to the bore, with a plate hung off it and a
shelf across the top.  Two M4 pull the cut shut; because the boss blends into
the plate on a 6.25 mm radius, each of them needs the blend relieving where its
head lands, which is what the two clearance bores do.

The whole bottom edge is broken 8 mm at 45 degrees, both sides.

    Body      sketch -> Pad     the side view, extruded along the rod
    Foot      sketch -> Pocket  the 45 degree breaks at the bottom
    Rib       sketch -> Pad     the pad the bolts land on
    Shelf     sketch -> Pad     what sits under the top plate
    Top       sketch -> Pad     the top plate
    Rod       sketch -> Pocket  8.2 mm through
    Top bore  sketch -> Pocket  4.6 mm down through the top plate
    Bolts     sketch -> Pocket  two M4 across the saw cut
    Heads     sketch -> Pocket  relief for their heads, into the blends
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

body_y = (-10.0, 24.0)   # along the rod
half_z = 16.0

rod = (-8.1, 0.0)        # the bore's axis, in the sketch's (X, Z)
rod_d = 8.2
boss_d = 16.2
blend_r = 6.25           # boss into each of the two faces beside it

back_x = -9.0            # the face the far blend lands on
plate_x = (-4.0, 0.0)    # the plate hung off the boss
cut_x = (-6.0, -4.0)     # the saw cut, in from Z = +16
cut_blend_r = 2.0        # where its far face runs into the bore

foot_break = 8.0         # 45 degrees off both bottom edges

rib_x = (0.0, 1.0)       # a pad on the plate's back, for the bolt heads
rib_y = (7.5, 12.0)
shelf_x = (7.5, 12.5)    # a foot under the far end of the top plate
shelf_y = (19.0, 20.0)
top_x = (-4.0, 14.0)
top_y = (20.0, 24.0)

bolt = (10.0, 12.0)      # (Y, |Z|) - one either side of the rod
bolt_d = 4.6
bolt_x = (-9.0, 1.0)
head_far_d = 12.0        # relief behind the far face, at Z = +12
head_near_d = 8.0        # and behind the plate, at Z = -12

top_bore = (10.0, 0.0)   # through the top plate, in (X, Z)
top_bore_d = 4.6

over = 2.0               # how far cutting profiles run past the part

mesh_volume = 10386.622


def top_clamp_z_axis(doc):
    bdy = fcprim.body(doc, "TOP_CLAMP_Z_AXIS")
    rod_r, boss_r = rod_d / 2, boss_d / 2
    reach = boss_r + blend_r

    def blend(face_x, side):
        """A fillet of `blend_r` tangent to the boss and to a face at `face_x`.

        Returns its centre and where it leaves the boss.  `side` says which end
        of the boss it rolls on, since the face runs past both.
        """
        centre = (face_x - blend_r,
                  side * math.sqrt(reach ** 2
                                   - (face_x - blend_r - rod[0]) ** 2))
        return centre, (rod[0] + boss_r * (centre[0] - rod[0]) / reach,
                        rod[1] + boss_r * (centre[1] - rod[1]) / reach)

    far, off_far = blend(back_x, 1)
    near, off_near = blend(plate_x[0], -1)

    # The saw cut's far face runs into the bore on a small radius, the same way
    # BOT_CLAMP_Z_AXIS's roof does.
    nose = (cut_x[0] - cut_blend_r,
            math.sqrt((rod_r + cut_blend_r) ** 2
                      - (cut_x[0] - cut_blend_r - rod[0]) ** 2))
    lands = (rod[0] + rod_r * (nose[0] - rod[0]) / (rod_r + cut_blend_r),
             rod[1] + rod_r * (nose[1] - rod[1]) / (rod_r + cut_blend_r))
    opens = math.degrees(math.atan2(lands[1] - rod[1], lands[0] - rod[0]))

    # Drawn looking along the rod; H is X, V is Z, and the pad runs along Y.
    body = fcprim.sketch(bdy, "Body", "XZ_Plane", offset=-body_y[1])
    fcprim.polyline(body, [
        (back_x, half_z),
        (back_x, far[1]),
        off_far,
        off_near,
        (plate_x[0], near[1]),
        (plate_x[0], -half_z),
        (plate_x[1], -half_z),
        (plate_x[1], half_z),
        (plate_x[0], half_z),
        (plate_x[0], rod[1]),
        lands,
        (cut_x[0], nose[1]),
        (cut_x[0], half_z),
    ], name="side", arcs={
        1: -blend_r,
        2: boss_r,
        3: -blend_r,
        9: (rod_r, opens - 360.0),
        10: cut_blend_r,
    })
    fcprim.pad(bdy, "Body", body, body_y[1] - body_y[0])

    # Both bottom corners broken at 45 degrees.  H is Y, V is Z; the pockets
    # run right across the part.
    foot = fcprim.sketch(bdy, "Foot", "YZ_Plane", offset=-(boss_r + over))
    for side in (-1, 1):
        fcprim.polyline(foot, [
            (body_y[0] + foot_break, side * half_z),
            (body_y[0], side * (half_z - foot_break)),
            (body_y[0] - over, side * (half_z - foot_break)),
            (body_y[0] - over, side * (half_z + over)),
            (body_y[0] + foot_break, side * (half_z + over)),
        ], name=f"foot{'np'[side > 0]}")
    fcprim.pocket(bdy, "Foot", foot, boss_d + 2 * over + abs(top_x[1]),
                  reversed_=True)

    for label, span_x, span_y in (("Rib", rib_x, rib_y),
                                  ("Shelf", shelf_x, shelf_y),
                                  ("Top", top_x, top_y)):
        sk = fcprim.sketch(bdy, label, "XZ_Plane", offset=-span_y[1])
        fcprim.polyline(sk, [
            (span_x[0], -half_z), (span_x[1], -half_z),
            (span_x[1], half_z), (span_x[0], half_z),
        ], name=label.lower())
        fcprim.pad(bdy, label, sk, span_y[1] - span_y[0])

    bore = fcprim.sketch(bdy, "Rod", "XZ_Plane", offset=-body_y[1])
    fcprim.circle(bore, rod, rod_d, name="rod")
    fcprim.pocket(bdy, "Rod", bore, body_y[1] - body_y[0], reversed_=True)

    through = fcprim.sketch(bdy, "Top bore", "XZ_Plane", offset=-top_y[1])
    fcprim.circle(through, top_bore, top_bore_d, name="bore")
    fcprim.pocket(bdy, "Top bore", through, top_y[1] - shelf_y[0],
                  reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolts", "YZ_Plane", offset=bolt_x[0])
    for side in (-1, 1):
        fcprim.circle(bolts, (bolt[0], side * bolt[1]), bolt_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolts", bolts, bolt_x[1] - bolt_x[0], reversed_=True)

    # Each head is relieved back through whatever the blend leaves in its way.
    for label, at, diameter, side in (("Head far", back_x, head_far_d, 1),
                                      ("Head near", plate_x[0],
                                       head_near_d, -1)):
        sk = fcprim.sketch(bdy, label, "YZ_Plane", offset=at)
        fcprim.circle(sk, (bolt[0], side * bolt[1]), diameter, name="head")
        fcprim.pocket(bdy, label, sk, boss_d + over)

    # Mounting datums for the assembly; see fcprim.lcs.  `ROD1` is the bore's
    # own axis at the clamp's lower end, where the Z rod enters.  The two
    # `FRAME`n are the shelf's top face at each end -- the shelf is a foot
    # *under* the lid's top plate, so what lands on the member is its upper
    # side.  Of the three bolts, two pinch the collar shut -- one from each
    # side, so one is on the far face and one on the plate -- and the third
    # comes down through the top plate.
    fcprim.lcs(bdy, "ROD1", at=(rod[0], body_y[0], rod[1]), axis=(0, -1, 0))
    for sign, label in ((-1, "FRAME1"), (1, "FRAME2")):
        fcprim.lcs(bdy, label, at=(0.0, shelf_y[1], sign * half_z),
                   axis=(0, -1, 0), roll=270.0)
    fcprim.lcs(bdy, "BOLT1", at=(bolt_x[0], bolt[0], bolt[1]), axis=(1, 0, 0))
    fcprim.lcs(bdy, "BOLT2", at=(plate_x[0], bolt[0], -bolt[1]),
               axis=(-1, 0, 0))
    fcprim.lcs(bdy, "BOLT3", at=(top_bore[0], top_y[1], top_bore[1]),
               axis=(0, -1, 0))

    # One the assembly measured on a *face* rather than on anything drawn, and
    # a face's own frame sits at its centre of area -- the clamp's top face is
    # the body's outline with the boss and the saw cut taken out of it, so its
    # middle is not on any dimension here.  Kept as measured; see
    # ASSEMBLY.md Part II, step 6.
    fcprim.lcs(bdy, "ROD2", at=(1.9601, body_y[1], 0.2527), axis=(0, 1, 0),
               roll=180.0)

    return bdy


fcprim.make(__file__, "TOP_CLAMP_Z_AXIS", top_clamp_z_axis, mesh_volume)
