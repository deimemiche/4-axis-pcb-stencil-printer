"""ECCF_LEVER - the eccenter's hand lever.

Reconstructed from the original author's ECCF_LEVER.stl. **That mesh holds two
separate shells**: it is a printing pair of two identical cheeks, one either
side of the eccenter, not one part. This builds the cheek at X = -30.4 .. -16.2;
the other is its mirror image about X = -13.2. So the volume checked against is
half the mesh's, and `verify.py` still works because it only samples inside this
cheek's own bounding box, which the other one is 6 mm clear of.

A 4 mm plate with an 8 mm eye at one end and a 4.5 mm pin hole at the other, and
a hub behind the eye so the pair grips the eccenter shaft over 10.2 mm rather
than 4. Every corner of the outline is tangent to its neighbours, so almost the
whole thing is fixed once five centres are named:

* the eye and the pin, each with its boss;
* the pivot the arm sweeps about - the arm is a curved band between two arcs
  concentric on it, 5 mm inside and 11 mm out, running from straight down to
  45 degrees, where its two edges leave on parallel tangents;
* two 3 mm fillets rolling on the *outside* of the hub, one at each side of it,
  placed symmetrically about the hub's 225 degree line;
* one more 3 mm fillet rounding the toe, where the two 45 degree tangents off
  the pin boss meet at a right angle.

    Plate    sketch -> Pad      the side view, 4 mm thick
    Hub      sketch -> Pad      behind the eye
    Rim              Chamfer    1 mm off the hub's far end
    Eye      sketch -> Pocket   8 mm through both
    Pin      sketch -> Pocket   4.5 mm through the plate
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

cheek_x = (-30.4, -26.4)   # the plate; the other cheek mirrors about X = -13.2
hub_x = -16.2              # the hub reaches from the plate to here
hub_d = 13.0
hub_break = 1.0            # 45 degrees off its far end

eye = (22.793, 30.286)     # in the sketch's (Y, Z)
eye_bore_d = 8.0

pin = (5.25, 0.0)
pin_bore_d = 4.5
pin_boss_r = 5.25

pivot = (21.75, 17.929)    # what the arm's two edges are concentric on
arm_r = (5.0, 11.0)        # inside and outside of the band
arm_leaves = 135.0         # where it stops being concentric and goes tangent

blend_r = 3.0
hub_blend_at = 5.84        # each blend, off the hub's 180 and 270 degree lines
toe_h = 8.0435             # where the two tangents off the pin boss cross

mesh_volume = 4929.446 / 2   # one cheek of the printing pair


def at(centre, radius, degrees):
    turn = math.radians(degrees)
    return (centre[0] + radius * math.cos(turn),
            centre[1] + radius * math.sin(turn))


def eccf_lever(doc):
    bdy = fcprim.body(doc, "ECCF_LEVER")
    reach = hub_d / 2 + blend_r          # centre distance for a rolling fillet

    # The two fillets on the hub, mirrored about its 225 degree line.
    inner = at(eye, reach, 270.0 - hub_blend_at)
    outer = at(eye, reach, 180.0 + hub_blend_at)

    # Where the arm's band starts and stops being concentric on the pivot.
    band_out = (pivot[0] - arm_r[1], pivot[1])
    band_in = (pivot[0] - arm_r[0], pivot[1])

    # The pin boss's two 45 degree tangents, and the right angle they cross at.
    off_pin = (at(pin, pin_boss_r, 135.0), at(pin, pin_boss_r, 225.0))
    toe = (toe_h, off_pin[1][1] - (toe_h - off_pin[1][0]))
    toe_blend = (toe_h, toe[1] + blend_r * math.sqrt(2.0))

    # The outer fillet does not touch the arm's band: they curve opposite ways,
    # so a short straight runs between them, tangent to both.
    span = math.hypot(outer[0] - pivot[0], outer[1] - pivot[1])
    lean = (math.degrees(math.atan2(outer[1] - pivot[1], outer[0] - pivot[0]))
            + math.degrees(math.acos((arm_r[1] + blend_r) / span)))

    # Drawn looking along the shaft; H is Y, V is Z, and the pad runs along X.
    plate = fcprim.sketch(bdy, "Plate", "YZ_Plane", offset=cheek_x[0])
    fcprim.polyline(plate, [
        band_out,
        (band_out[0], off_pin[0][1] + (band_out[0] - off_pin[0][0])),
        off_pin[0],
        off_pin[1],
        at(toe_blend, blend_r, 225.0),
        at(toe_blend, blend_r, 315.0),
        (band_in[0], toe[1] + (band_in[0] - toe_h)),
        band_in,
        at(pivot, arm_r[0], arm_leaves),
        at(inner, blend_r, arm_leaves),
        at(inner, blend_r, 90.0 - hub_blend_at),
        at(outer, blend_r, hub_blend_at),
        at(outer, blend_r, lean + 180.0),
        at(pivot, arm_r[1], lean),
    ], name="lever", arcs={
        2: pin_boss_r,
        4: blend_r,
        7: -arm_r[0],
        9: -blend_r,
        10: (hub_d / 2, 270.0 + 2 * hub_blend_at),
        11: -blend_r,
        13: arm_r[1],
    })
    fcprim.pad(bdy, "Plate", plate, cheek_x[1] - cheek_x[0])

    hub = fcprim.sketch(bdy, "Hub", "YZ_Plane", offset=cheek_x[1])
    fcprim.circle(hub, eye, hub_d, name="hub")
    fcprim.pad(bdy, "Hub", hub, hub_x - cheek_x[1])

    # The hub's far end is broken 1 mm; nothing else has reached that plane.
    def rim(edge):
        return abs(fcprim.midpoint(edge).x - hub_x) < 1e-6

    fcprim.chamfer(bdy, "Rim", hub_break, rim)

    bore = fcprim.sketch(bdy, "Eye", "YZ_Plane", offset=cheek_x[0])
    fcprim.circle(bore, eye, eye_bore_d, name="eye")
    fcprim.pocket(bdy, "Eye", bore, hub_x - cheek_x[0], reversed_=True)

    hole = fcprim.sketch(bdy, "Pin", "YZ_Plane", offset=cheek_x[0])
    fcprim.circle(hole, pin, pin_bore_d, name="pin")
    fcprim.pocket(bdy, "Pin", hole, cheek_x[1] - cheek_x[0], reversed_=True)

    return bdy


fcprim.make(__file__, "ECCF_LEVER", eccf_lever, mesh_volume)
