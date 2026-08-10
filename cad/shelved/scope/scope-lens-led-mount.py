"""SCOPE_LENS_LED_MOUNT - the ring of LEDs round the microscope's objective.

Michael's own part, and the only one in `scope/` transcribed from
**build123d** rather than CadQuery:
[`../../microscope-mount/lens-led-mount.py`](../../microscope-mount/lens-led-mount.py).
It is a collar that slips over the objective end of the tube -- 46 mm there,
not the 50 the barrel is, which is why this part has a bore of its own -- and
carries three strips of LEDs facing down at the board.

    Ring       sketch -> Pad           55 over 47, 4 tall
    LED pad    sketch -> Pad           one strip's shelf, 8.5 x 50
               ->  PolarPattern        and the other two, 120 apart
    Boss       sketch -> Pad           the lug at the ring's edge, 11.2 tall
    Heat sert  sketch -> Pocket        4 x 4 into its end, for the insert
    Bolt       sketch -> Pocket        3.2 on through, for the screw's tip

**Where the two holes go is the one reading here that the source does not
settle in as many words.**  They are put on `faces(Select.LAST).sort_by(Axis.X)`
-- the boss's own outer face, first at index 3 and then at index -1 -- so both
land on that face's centre and are coaxial, which is the ordinary way a heat
set insert is drawn: a 4 mm seat and the screw's clearance beyond it.  The
height of that centre is the subtle part.  The LED shelf covers the boss's
first 2.667 mm, so the face starts there rather than at the ring's underside,
and its middle comes out at **6.93 and not 5.6**.  If the insert ever sits too
high in the lug, that is the number to look at.

The edge breaks -- 1 mm round the shelves, 0.67 round the top -- are left off,
as everywhere in `scope/`; see `../STATUS.md`.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# From ../../microscope-mount/settings.py, and the script's own numbers.
wall = 4.0               # Settings.wall_t
fit = 0.2                # Settings.fit
loose_fit = 0.5          # Settings.loose_fit

lens_d = 46.0 + 2 * loose_fit            # 47, the objective plus its fit
ring_od = lens_d + 2 * wall              # 55
ring_h = wall                            # 4

strip_w = 8.5            # led_strip_w, one strip of LEDs
strip_l = 50.0           # led_strip_l
shelf_h = wall * 2.0 / 3.0               # 2.667, how proud the shelf stands
shelf_at = ring_od / 2.0 + (strip_w - wall) / 4.0    # 28.625, its own middle

insert_d = 4.0           # heatsert_d, an M3 heat set insert
insert_l = 4.0
insert_wall = 1.6
boss_t = insert_d + 2 * insert_wall      # 7.2, across the lug
boss_l = 2 * wall                        # 8, out from the ring's edge
boss_h = wall + boss_t                   # 11.2
boss_at = ring_od / 2.0                  # 27.5, the lug's own middle

bolt_hole_d = 3.0 + fit                  # 3.2, the screw past the insert

# The lug's outer face starts where the LED shelf leaves off; see the
# docstring.  Both holes are on its middle.
insert_z = (shelf_h + boss_h) / 2.0      # 6.933


def _lens(radius, half):
    """Area of a circle's slab, |y| <= half, on one side of the axis."""
    return (half * math.sqrt(radius ** 2 - half ** 2)
            + radius ** 2 * math.asin(half / radius))


def _slab(radius, near, far):
    """Area of a circle between two chords across it, near <= x <= far."""
    def part(x):
        return x * math.sqrt(radius ** 2 - x ** 2) + radius ** 2 * math.asin(x / radius)

    return part(far) - part(near)


def expected_volume():
    """Arithmetic on the numbers above; see `../STATUS.md`.

    Three shapes overlap here -- ring, shelf and lug -- so what has to be
    counted is each one's own new material, which is where the two helpers
    above come in.
    """
    outer = ring_od / 2.0
    ring = math.pi / 4.0 * (ring_od ** 2 - lens_d ** 2) * ring_h

    # A shelf reaches from 24.375 to 32.875, and everything it has inside the
    # ring's own circle is already there.
    shelf_near = shelf_at - strip_w / 2.0
    shelf_far = shelf_at + strip_w / 2.0
    shelves = 3 * (strip_w * strip_l - _slab(outer, shelf_near, outer)) * shelf_h

    # The lug, less what the ring and the shelf under it already fill.
    half = boss_t / 2.0
    boss = boss_l * boss_t * boss_h
    in_ring = (_lens(outer, half) - (boss_at - boss_l / 2.0) * boss_t) * ring_h
    in_shelf = (min(boss_at + boss_l / 2.0, shelf_far) - shelf_near) \
        * boss_t * shelf_h
    in_both = (_lens(outer, half) - shelf_near * boss_t) * shelf_h

    insert = math.pi / 4.0 * insert_d ** 2 * insert_l
    bolt = math.pi / 4.0 * bolt_hole_d ** 2 * (boss_at + boss_l / 2.0
                                               - insert_l - lens_d / 2.0)

    return ring + shelves + boss - in_ring - in_shelf + in_both - insert - bolt


def mount(doc):
    bdy = fcprim.body(doc, "SCOPE_LENS_LED_MOUNT")

    ring = fcprim.sketch(bdy, "Ring", "XY_Plane")
    fcprim.circle(ring, (0.0, 0.0), ring_od, name="ring")
    fcprim.circle(ring, (0.0, 0.0), lens_d, name="bore")
    fcprim.pad(bdy, "Ring", ring, ring_h)

    # One shelf, and a polar pattern for the other two -- which is what
    # `PolarLocations(od / 2, 3)` says, said in the way this directory says it.
    shelf = fcprim.sketch(bdy, "LED pad", "XY_Plane")
    fcprim.polyline(shelf, [
        (shelf_at - strip_w / 2.0, -strip_l / 2.0),
        (shelf_at + strip_w / 2.0, -strip_l / 2.0),
        (shelf_at + strip_w / 2.0, strip_l / 2.0),
        (shelf_at - strip_w / 2.0, strip_l / 2.0),
    ], name="shelf")
    pad = fcprim.pad(bdy, "LED pad", shelf, shelf_h)
    fcprim.polar_pattern(bdy, "LED pads", [pad], 3, axis="Z_Axis")

    boss = fcprim.sketch(bdy, "Boss", "XY_Plane")
    fcprim.polyline(boss, [
        (boss_at - boss_l / 2.0, -boss_t / 2.0),
        (boss_at + boss_l / 2.0, -boss_t / 2.0),
        (boss_at + boss_l / 2.0, boss_t / 2.0),
        (boss_at - boss_l / 2.0, boss_t / 2.0),
    ], name="boss")
    fcprim.pad(bdy, "Boss", boss, boss_h)

    # Both holes enter the lug's outer face, so both are drawn on it.  YZ
    # offsets towards +X and its pocket cuts back the way the pad came.
    face = boss_at + boss_l / 2.0
    seat = fcprim.sketch(bdy, "Heat sert", "YZ_Plane", offset=face)
    fcprim.circle(seat, (0.0, insert_z), insert_d, name="insert")
    fcprim.pocket(bdy, "Heat sert", seat, insert_l)

    bolt = fcprim.sketch(bdy, "Bolt", "YZ_Plane", offset=face)
    fcprim.circle(bolt, (0.0, insert_z), bolt_hole_d, name="bolt")
    fcprim.pocket(bdy, "Bolt", bolt)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   SCOPE   the objective's axis, down the bore
    #   INSERT  the lug's own hole, looking out of the face it enters
    fcprim.lcs(bdy, "SCOPE", axis=(0, 0, 1))
    fcprim.lcs(bdy, "FACE", at=(0.0, 0.0, ring_h), axis=(0, 0, 1))
    fcprim.lcs(bdy, "INSERT", at=(face, 0.0, insert_z), axis=(1, 0, 0))

    return bdy


fcprim.make(__file__, "SCOPE_LENS_LED_MOUNT", mount, expected_volume())
