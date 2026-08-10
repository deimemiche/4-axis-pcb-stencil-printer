"""SCOPE_HOLDER - the collar the microscope tube hangs in.

Michael's own part, transcribed from `holder()` in
[`../microscope-mount/microscope-mount.py`](../microscope-mount/microscope-mount.py).
It bolts up under `SCOPE_SLIDER`'s ear with two M2.5 at 35 centres and holds
the 50 mm scope tube 49 mm below them, so the whole microscope moves with the
carriage.

A prism 12.7 thick, three shapes in one outline:

* a **plate** 41.5 x 4, drilled 2.7 for the two M2.5 that pull it against the
  slider's ear.  The ear's nuts take them, so these are clearance and the
  thread is 4 mm away in the other part.
* a **neck** 8 wide running 20 down from it, gusseted into both with a fillet
  at each end -- 4 mm where it leaves the plate, 8 mm where it lands on the
  collar.  Those two fillets are the part's whole strength: an 8 mm neck
  carrying a microscope on a 49 mm arm is a lever, and a sharp corner there is
  where it would break.
* the **collar** itself, 58 outside and 50 bored, which is the tube plus one
  wall either side.

    Outline      sketch -> Pad     plate, neck and collar, and the 50 bore
    Mount bolts  sketch -> Pocket  two 2.7 through the plate
    Slit         sketch -> Pocket  3.5 wide, across the neck and the collar

**The slit is the reading to check first.**  The source cuts a 43.5 x 3.5
obround 29 deep, starting 12.5 below the plate, and 3.5 is M3 plus a loose
fit -- so it is drawn at a bolt's size.  What it does is split the neck's
lower half and the top of the collar into two leaves at mid thickness, which
reads as a clamp; but nothing in the source pinches them together, and the
part has no M3 hole anywhere.  It is transcribed exactly as drawn.

**This part carries no volume figure**, and it is the only one in `scope/`
that does not.  Everything else here decomposes into rectangles, circles and
obrounds that arithmetic settles exactly; here the two fillets and the slit
interpenetrate, so an expected volume would have to be a second model of the
part rather than a check on this one.  What checks it instead is
[`microscope.py`](microscope.py): the plate's two holes have to land on the
slider's own nuts, and the collar's bore has to be on the tube's axis.  That
is the same bargain `mod/TOP_Z_AXIS_BEARING_MOUNT` makes.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From ../microscope-mount/settings.py.
wall = 4.0               # Settings.wall_t
fit = 0.2                # Settings.fit
loose_fit = 0.5          # Settings.loose_fit
scope_d = 50.0           # Settings.scope_d, the microscope's own tube

mount_bolt = 2.5         # M2.5, into the slider's ear
clamp_bolt = 3.0         # M3; the slit is drawn at its clearance

depth = 4.7 + 2 * wall   # 12.7, the same thickness the slider is

plate_l = 35.0 + mount_bolt + wall       # 41.5, and the slider's ear's own
plate_t = wall
bolt_at = (-17.5, 17.5)
bolt_hole_d = mount_bolt + fit           # 2.7

neck_w = 2 * wall                        # 8
neck_l = 20.0
neck_top = plate_t / 2.0                 # -2 is where it leaves the plate

ring_od = scope_d + 2 * wall             # 58
ring_id = scope_d                        # 50
ring_y = -(neck_l + scope_d / 2.0 + wall)      # -49, the tube's own axis

gusset_r = neck_w                        # 8, neck on to collar
shoulder_r = neck_w / 2.0                # 4, plate on to neck

# The slit, from the source's own `slot2D(d * 3 / 4, ...)` and `cutBlind`.
slit_l = 3.0 * ring_od / 4.0             # 43.5 overall
slit_w = clamp_bolt + loose_fit          # 3.5
slit_from = plate_t / 2.0 - ring_od / 4.0      # -12.5; the source measures it
slit_deep = ring_od / 2.0                      # 29, down from the plate's face


def gusset():
    """Where the 8 mm gusset touches the flank and the collar, and its centre.

    A circle tangent to the flank and tangent *outside* the collar: its centre
    stands one radius off the flank, and `collar + gusset` from the collar's
    own axis.  Everything about the blend falls out of those two facts.

    Returned as (flank y, collar x, collar y), in the right hand half; the
    other side is the mirror of it.
    """
    outer = ring_od / 2.0
    across = neck_w / 2.0 + gusset_r                       # 12, off the axis
    along = math.sqrt((outer + gusset_r) ** 2 - across ** 2)
    centre_y = ring_y + along                              # -14
    reach = outer + gusset_r
    return (centre_y,
            outer * across / reach,                        # 9.405
            ring_y + outer * along / reach)                # -21.568


def collar_sweep():
    """The long way round the collar, between the two gussets' tangent points.

    Everything the two blends do not already cover, which is all but the top
    of it.
    """
    _, touch_x, touch_y = gusset()
    corner = math.degrees(math.atan2(touch_x, touch_y - ring_y))
    return (ring_od / 2.0, 360.0 - 2.0 * corner)


def outline():
    """Plate, neck and collar as one closed profile.

    **The gussets are drawn rather than filleted.**  They are what a
    `PartDesign::Fillet` would leave on the solid and what the Sketcher's own
    fillet tool would leave in the profile -- except that the Sketcher will not
    make this one: `fillet()` refuses a corner where a line meets an arc from
    the outside, at any radius, with "Not able to fillet point".  So the blend
    is two tangent arcs in the profile, placed by `gusset()`, and the collar's
    own arc picks up where they leave off.  The shoulders where the neck
    leaves the plate are line to line, which the fillet tool does manage, so
    those two are left to it and keep their radius as a named constraint.
    """
    flank_y, touch_x, touch_y = gusset()
    return [
        (-plate_l / 2.0, plate_t / 2.0),
        (-plate_l / 2.0, -plate_t / 2.0),
        (-neck_w / 2.0, -plate_t / 2.0),         # shoulder, filleted 4
        (-neck_w / 2.0, flank_y),                # the gusset leaves the flank
        (-touch_x, touch_y),                     # and lands on the collar
        (touch_x, touch_y),
        (neck_w / 2.0, flank_y),
        (neck_w / 2.0, -plate_t / 2.0),          # shoulder, filleted 4
        (plate_l / 2.0, -plate_t / 2.0),
        (plate_l / 2.0, plate_t / 2.0),
    ]


def check_fillets():
    """The two blends have to fit on the flank they share.

    The gusset takes the flank from its own tangent point down, the shoulder
    takes `shoulder_r` off the top of it, and what is left has to be positive
    or the profile is being asked for something that is not there.
    """
    flank_y, _, _ = gusset()
    room = (-plate_t / 2.0 - shoulder_r) - flank_y
    print(f"  the gusset takes the flank at y {flank_y:.3f}, "
          f"leaving {room:.3f} mm of it straight")
    if room < 0.0:
        raise SystemExit("the two blends overlap on the neck's flank")
    return flank_y


def holder(doc):
    check_fillets()
    bdy = fcprim.body(doc, "SCOPE_HOLDER")

    profile = fcprim.sketch(bdy, "Outline", "XY_Plane")
    fcprim.polyline(profile, outline(), name="outline",
                    arcs={3: -gusset_r, 4: collar_sweep(), 5: -gusset_r},
                    fillets={2: shoulder_r, 7: shoulder_r})
    fcprim.circle(profile, (0.0, ring_y), ring_id, name="bore")
    fcprim.pad(bdy, "Body", profile, depth)

    # The plate's top face is at +2, and XZ offsets towards -Y.
    bolts = fcprim.sketch(bdy, "Mount bolts", "XZ_Plane", offset=-plate_t / 2.0)
    for i, x in enumerate(bolt_at):
        fcprim.circle(bolts, (x, depth / 2.0), bolt_hole_d, name=f"bolt{i + 1}")
    fcprim.pocket(bdy, "Mount bolts", bolts, plate_t, reversed_=True)

    slit = fcprim.sketch(bdy, "Slit", "XZ_Plane", offset=-slit_from)
    reach = (slit_l - slit_w) / 2.0
    fcprim.slot(slit, (-reach, depth / 2.0), (reach, depth / 2.0), slit_w,
                name="slit")
    fcprim.pocket(bdy, "Slit", slit, slit_deep, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   MOUNT  the plate's top face, looking up at the slider's ear
    #   SCOPE  the tube's axis, down the collar
    fcprim.lcs(bdy, "MOUNT", at=(0.0, plate_t / 2.0, depth / 2.0),
               axis=(0, 1, 0))
    for i, x in enumerate(bolt_at):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, plate_t / 2.0, depth / 2.0),
                   axis=(0, 1, 0))
    fcprim.lcs(bdy, "SCOPE", at=(0.0, ring_y, depth / 2.0), axis=(0, 0, 1))

    return bdy


fcprim.make(__file__, "SCOPE_HOLDER", holder)
