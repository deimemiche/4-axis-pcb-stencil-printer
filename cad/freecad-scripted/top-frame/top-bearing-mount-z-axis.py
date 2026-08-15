"""TOP_BEARING_MOUNT_Z_AXIS - carries the top frame on a Z rod, on an LM8UU.

Michael's own part, and the one that retired `TOP_CLAMP_Z_AXIS`: the lid used
to be *clamped* to the two Z rods by a split collar pinched with two M4, so
raising or lowering it meant slackening four bolts and doing it by hand.  This
runs on a linear bearing instead, and the lid slides.

So it is `TOP_CLAMP_Z_AXIS` from the plate back, and a bearing housing in front
of it.  Transcribed from Michael's own document rather than from a mesh -- he
drew it in the GUI, so there are real sketches to read.  Its check is his solid
rather than an STL, and a harder one than a volume: booleaned against his body
both ways, each cut is empty.  The volume below is his, held to 1e-4; the two
documents' own figures differ by 2e-6 of the part, which is OCC integrating the
same revolved faces twice rather than any difference in shape.

What changed, feature by feature:

* the D8.2 rod bore and its D16.2 boss became a **D15.2 housing** for the
  LM8UU, in a D21 boss.  The housing is grooved rather than pocketed, because
  it is not one diameter: a D13.2 lip at each end holds the bearing in, and a
  1 mm lead-in at 45 degrees gets it past them.  The seat is 24.6 mm for a
  24 mm bearing.
* the **saw cut is gone**, and with it the relief bores the pinch bolts' heads
  needed and the blends the boss made into the faces either side.  The three
  M4 are still three, but none of them pinches anything now: two go in through
  the plate, clear of the housing on either side, and the third down through
  the top plate, and all three simply bolt the mount to the frame.
* the back of the boss is **open over 60 degrees**, in a wedge whose apex is on
  the bore's own axis -- so the wall is cut right through and the housing is a
  C rather than a ring.  The gap is 7.6 mm where it meets the seat and widens
  outwards, which is narrower than the bearing: it opens the bore to the back,
  it does not let the LM8UU out sideways.
* the part is **36 mm across** rather than 32, and 27 mm along the rod rather
  than 34.  The plate's two M4 moved out with it, to Z +-13.
* the 45 degree breaks along the bottom edges are gone; there is no bottom
  edge left to break, the boss now reaching further down than the plate did.

Boss and housing are **concentric**, both 10 mm out from the origin, so the
wall is 2.9 mm all the way round.  They were 0.1 mm apart in the first version
of Michael's document -- 10.1 against 10.2 -- and he has since put them on one
axis, which is why there is a single `bore` here rather than two numbers that
agree by eye.

    Body      sketch -> Pad     the side view, extruded along the rod
    Rib       sketch -> Pad     the pad the bolts land on
    Shelf     sketch -> Pad     what sits under the top plate
    Top       sketch -> Pad     the top plate
    Top bore  sketch -> Pocket  4.6 mm down through the top plate, for the
                                third M4
    Bolts     sketch -> Pocket  two M4 through the plate, into the frame
    Bearing   sketch -> Groove  the LM8UU seat, its two lips and their leads
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

body_y = (-3.0, 24.0)    # along the rod
half_z = 18.0

bore = (-10.0, 0.0)      # the housing's axis, in the sketch's (X, Z)
boss_d = 21.0            # what stands round it; concentric, so a 2.9 mm wall
notch_half = 30.0        # half the wedge the back of the boss is open over

bore_d = 15.2            # the LM8UU, 15 mm over its outer race
lip_d = 13.2             # what holds the bearing in, at each end
lip_t = 0.2
lead = 1.0               # 45 degrees, to get the bearing past the lip
bearing_y = (body_y[0] + lip_t + lead, body_y[1] - lip_t - lead)

plate_x = (-4.0, 0.0)    # the plate hung off the boss

rib_x = (0.0, 1.0)       # a pad on the plate's back, for the bolt heads
rib_y = (7.5, 12.5)
shelf_x = (7.5, 12.5)    # a foot under the far end of the top plate
shelf_y = (19.0, 20.0)
top_x = (-4.0, 14.0)
top_y = (20.0, 24.0)

bolt = (10.0, 13.0)      # (Y, |Z|) - one either side of the boss
bolt_d = 4.6
bolt_x = (-9.0, 1.0)

top_bore = (10.0, 0.0)   # through the top plate, in (X, Z)
top_bore_d = 4.6

hand_volume = 8308.575   # Michael's own document, not a mesh


def top_bearing_mount_z_axis(doc):
    bdy = fcprim.body(doc, "TOP_BEARING_MOUNT_Z_AXIS")
    boss_r, bore_r, lip_r = boss_d / 2, bore_d / 2, lip_d / 2

    # Where the plate's back face cuts the boss, and where the wedge at the
    # back of it leaves the boss.  Both fall out of the boss's own radius.
    meets = math.sqrt(boss_r ** 2 - (plate_x[0] - bore[0]) ** 2)
    notch = (bore[0] - boss_r * math.cos(math.radians(notch_half)),
             boss_r * math.sin(math.radians(notch_half)))

    # Drawn looking along the rod; H is X, V is Z, and the pad runs along Y.
    body = fcprim.sketch(bdy, "Body", "XZ_Plane", offset=-body_y[1])
    fcprim.polyline(body, [
        (plate_x[1], -half_z),
        (plate_x[1], half_z),
        (plate_x[0], half_z),
        (plate_x[0], meets),
        notch,
        bore,
        (notch[0], -notch[1]),
        (plate_x[0], -meets),
        (plate_x[0], -half_z),
    ], name="side", arcs={3: boss_r, 6: boss_r})
    fcprim.pad(bdy, "Body", body, body_y[1] - body_y[0])

    for label, span_x, span_y in (("Rib", rib_x, rib_y),
                                  ("Shelf", shelf_x, shelf_y),
                                  ("Top", top_x, top_y)):
        sk = fcprim.sketch(bdy, label, "XZ_Plane", offset=-span_y[1])
        fcprim.polyline(sk, [
            (span_x[0], -half_z), (span_x[1], -half_z),
            (span_x[1], half_z), (span_x[0], half_z),
        ], name=label.lower())
        fcprim.pad(bdy, label, sk, span_y[1] - span_y[0])

    through = fcprim.sketch(bdy, "Top bore", "XZ_Plane", offset=-top_y[1])
    fcprim.circle(through, top_bore, top_bore_d, name="bore")
    fcprim.pocket(bdy, "Top bore", through, top_y[1] - shelf_y[0],
                  reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolts", "YZ_Plane", offset=bolt_x[0])
    for side in (-1, 1):
        fcprim.circle(bolts, (bolt[0], side * bolt[1]), bolt_d,
                      name=f"bolt{'np'[side > 0]}")
    fcprim.pocket(bdy, "Bolts", bolts, bolt_x[1] - bolt_x[0], reversed_=True)

    # The housing, swept about its own axis.  A groove rather than a pocket
    # because the seat is not one diameter: it is the bearing's bore, a lip at
    # each end and a lead-in between them.  The sketch is shifted onto the
    # housing's axis so the sweep can turn about its own V axis, which means H
    # here reads as a **radius out from that axis**, and so runs negative.
    seat = fcprim.sketch(bdy, "Bearing", "XY_Plane", shift=(bore[0], 0.0))
    fcprim.polyline(seat, [
        (0.0, body_y[0]),
        (0.0, body_y[1]),
        (-lip_r, body_y[1]),
        (-lip_r, body_y[1] - lip_t),
        (-bore_r, bearing_y[1]),
        (-bore_r, bearing_y[0]),
        (-lip_r, body_y[0] + lip_t),
        (-lip_r, body_y[0]),
    ], name="seat")
    fcprim.groove(bdy, "Bearing", seat, axis="V_Axis")

    # Mounting datums for the assembly; see fcprim.lcs.  `BEARING` is the seat
    # at its lower end, on the housing's axis, which is where the LM8UU's own
    # `BORE` lands.  The two `FRAME`n are the shelf's top face at each end --
    # the shelf is a foot *under* the lid's top plate, so what lands on the
    # member is its upper side.  Of the three bolts, `BOLT1` and `BOLT2` go in
    # through the plate's back face, one either side of the housing, and
    # `BOLT3` comes down through the top plate.
    fcprim.lcs(bdy, "BEARING", at=(bore[0], bearing_y[0], bore[1]),
               axis=(0, -1, 0), roll=180.0)
    for sign, label in ((-1, "BOLT1"), (1, "BOLT2")):
        fcprim.lcs(bdy, label, at=(plate_x[0], bolt[0], sign * bolt[1]),
                   axis=(-1, 0, 0))
    fcprim.lcs(bdy, "BOLT3", at=(top_bore[0], top_y[1], top_bore[1]),
               axis=(0, -1, 0))
    for sign, label in ((-1, "FRAME1"), (1, "FRAME2")):
        fcprim.lcs(bdy, label, at=(0.0, shelf_y[1], sign * half_z),
                   axis=(0, -1, 0), roll=270.0)

    return bdy


fcprim.make(__file__, "TOP_BEARING_MOUNT_Z_AXIS", top_bearing_mount_z_axis,
            hand_volume, tolerance=1e-4)
