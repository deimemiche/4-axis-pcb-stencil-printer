"""SCOPE_SLIDER - the carriage the microscope column rides an extrusion on.

Michael's own part, transcribed from the CadQuery in
[`../microscope-mount/microscope-mount.py`](../microscope-mount/microscope-mount.py)
driven by [`../microscope-mount/settings.py`](../microscope-mount/settings.py),
the same way `mod/` transcribes the Z axis mod.  Read `../STATUS.md` for what
that bargain leaves off.

A 28.5 mm square tube, 12.7 long, that slips over a 20 mm extrusion.  Three
things hang off it:

* **eight tabs** standing 0.19 mm proud inside the 20.5 bore.  The bore itself
  is a loose fit on the extrusion, and only the tabs touch it: 20.5 less twice
  0.1895 is 20.121, which is the 20 mm profile plus the source's own
  `running_fit` of 0.121.  A running fit on eight small pads instead of on four
  whole faces is what stops the carriage binding.
* an **ear** at the bottom, 41.5 long, which `SCOPE_HOLDER` bolts up against
  with two M2.5.  The nuts sit in hexagonal pockets in the ear's own shelf and
  the bolts come up through it from below.
* a **nut boss** on top, holding the M5 nut that the leadscrew turns in.  The
  leadscrew runs parallel to the extrusion, 18.25 off its axis.

    Outline     sketch -> Pad     the square tube, the ear and the boss, and
                                  the tabbed bore, all in one profile
    Rod         sketch -> Pocket  5 mm, the leadscrew, the length of the boss
    Rod nut     sketch -> Pocket  the M5 nut's own slot, open at the top
    Mount nuts  sketch -> Pocket  two M2.5 hexagons in the ear's shelf
    Mount bolts sketch -> Pocket  and their two 3 mm clearances, through

**The rod nut's slot is only half the nut deep, and that is what the source
says.**  `nutcatchSidecut` cuts `nut thickness` from the plane it is given,
and the plane it is given here is the tag taken at the part's own bottom face
rather than at mid thickness -- the tag is set before the `workplane(t / 2)`
that would have moved it.  So the 4.7 mm slot runs from 0 to 2.35 and opens on
the bottom face, where a slot from 4 to 8.7 would have caught the nut in the
middle of the boss.  It is transcribed as it is drawn, because the alternative
is to redesign the part in the reconstruction; it is the first thing to check
if the nut falls out.

Coordinates are the source's own: the bore's axis is **Z**, which is the way
the extrusion runs, and the profile is drawn in XY.  That is not the machine's
"Y is up" -- this column is a sub-assembly with its own frame, and keeping the
CadQuery's coordinates is what lets the two be compared part for part.
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
v_slot = 20.0            # Settings.v_slot_d

# and from microscope-mount.py itself.
running_fit = 0.121      # what the tabs are meant to leave on the extrusion

# The two bolts, from cq_queryabolt's own tables.
rod_bolt_d = 5.0         # M5, the leadscrew
rod_nut_w = 8.0          # its nut, across the flats
rod_nut_t = 4.7          # and how thick it is
mount_bolt = 2.5         # M2.5, what the holder hangs on
mount_nut_w = 5.0
mount_nut_t = 2.0

slider_id = v_slot + loose_fit           # 20.5, the bore
slider_od = slider_id + 2 * wall         # 28.5, the outside
tab = (loose_fit - running_fit) / 2.0    # 0.1895, how far a tab stands proud
tab_w = v_slot / 4.0                     # 5, and how wide it is
tab_at = slider_id / 4.0                 # 5.125, off the wall's own middle

depth = rod_nut_t + 2 * wall             # 12.7, how far the carriage runs

# The nut boss, and the leadscrew it carries.
rod_clearance = rod_nut_w / 2.0          # 4, the nut's own reach past the slot
nutcatch_l = rod_clearance + rod_nut_w / 2.0 + wall      # 12
boss_w = rod_nut_w + 2 * wall            # 16
rod_y = slider_od / 2.0 + rod_clearance  # 18.25, the leadscrew off the axis
boss_top = slider_od / 2.0 + nutcatch_l  # 26.25

# The ear the holder bolts to.
bolt_span = 35.0                         # slider_bolt_s, "a nice round number"
ear_l = bolt_span + mount_bolt + wall    # 41.5
ear_t = wall
ear_shelf = slider_od / 2.0 - ear_t      # 10.25, and the shelf the nuts sit in
bolt_at = (-bolt_span / 2.0, bolt_span / 2.0)
mount_bolt_d = mount_bolt + loose_fit    # 3.0

rod_hole_d = rod_bolt_d                  # boltHole() with no clearance asked

over = 2.0               # how far a cutting profile runs past the part


def outer_profile():
    """Tube, ear and boss, which meet as one outline."""
    half = slider_od / 2.0
    return [
        (-ear_l / 2.0, -half), (ear_l / 2.0, -half),
        (ear_l / 2.0, -ear_shelf), (half, -ear_shelf),
        (half, half), (boss_w / 2.0, half),
        (boss_w / 2.0, boss_top), (-boss_w / 2.0, boss_top),
        (-boss_w / 2.0, half), (-half, half),
        (-half, -ear_shelf), (-ear_l / 2.0, -ear_shelf),
    ]


def bore_profile():
    """The bore, walked wall by wall, each with its two tabs.

    One wall is written out and the other three are it, turned a quarter turn
    at a time -- which is what the source's two `rarray`s come to, and says
    plainly that the four are the same.
    """
    half = slider_id / 2.0
    inner = half - tab
    wall_run = [(-half, -half)]
    for centre in (-tab_at, tab_at):
        wall_run += [(centre - tab_w / 2.0, -half),
                     (centre - tab_w / 2.0, -inner),
                     (centre + tab_w / 2.0, -inner),
                     (centre + tab_w / 2.0, -half)]

    def turned(point, quarters):
        x, y = point
        for _ in range(quarters):
            x, y = -y, x
        return (x, y)

    return [turned(point, quarter)
            for quarter in range(4) for point in wall_run]


def nut_slot():
    """`nutcatchSidecut`'s own profile: the nut's lower half, opened upwards.

    Two flats, the point between them, and the slot the nut drops in through
    running out of the top of the boss.
    """
    across = rod_nut_w / 2.0
    flank = rod_nut_w * math.sqrt(3.0) / 6.0     # the flats' own corners
    point = rod_nut_w / math.sqrt(3.0)           # and how far the point reaches
    top = boss_top + over
    return [(-across, top),
            (-across, rod_y - flank),
            (0.0, rod_y - point),
            (across, rod_y - flank),
            (across, top)]


def expected_volume():
    """Arithmetic on the numbers above; see `../STATUS.md`.

    There is no mesh and no drawing behind this part, so what guards it is that
    the same solid comes out of two independent descriptions.
    """
    outer = (slider_od ** 2
             + (ear_l - slider_od) * ear_t         # the ears, both together
             + boss_w * nutcatch_l)
    bore = slider_id ** 2 - 8 * tab_w * tab
    body = (outer - bore) * depth

    rod = math.pi / 4.0 * rod_hole_d ** 2 * depth

    # The nut's slot, over what the boss and the wall under it actually have
    # in its way: the point, then a full width run up to the top of the boss.
    flank = rod_nut_w * math.sqrt(3.0) / 6.0
    point = rod_nut_w / math.sqrt(3.0)
    slot_deep = rod_nut_t / 2.0
    slot = (0.5 * rod_nut_w * (point - flank)
            + rod_nut_w * (boss_top - (rod_y - flank))) * slot_deep
    shared = math.pi / 4.0 * rod_hole_d ** 2 * slot_deep   # counted twice

    hexagon = math.sqrt(3.0) / 2.0 * mount_nut_w ** 2
    circle = math.pi / 4.0 * mount_bolt_d ** 2
    mount = 2 * (circle * ear_t + hexagon * mount_nut_t - circle * mount_nut_t)

    return body - rod - slot + shared - mount


def slider(doc):
    bdy = fcprim.body(doc, "SCOPE_SLIDER")

    # Outline and bore in one sketch: a pad takes the inner wire as a hole.
    outline = fcprim.sketch(bdy, "Outline", "XY_Plane")
    fcprim.polyline(outline, outer_profile(), name="outline")
    fcprim.polyline(outline, bore_profile(), name="bore")
    fcprim.pad(bdy, "Body", outline, depth)

    rod = fcprim.sketch(bdy, "Rod", "XY_Plane")
    fcprim.circle(rod, (0.0, rod_y), rod_hole_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance", rod, midplane=True)

    # Reversed because a pocket drawn on XY cuts towards -Z, and the slot runs
    # up from the bottom face; see the docstring for why it stops half way.
    nut = fcprim.sketch(bdy, "Rod nut", "XY_Plane")
    fcprim.polyline(nut, nut_slot(), name="nut")
    fcprim.pocket(bdy, "Rod nut", nut, rod_nut_t / 2.0, reversed_=True)

    # The ear's shelf faces +Y, and XZ offsets towards -Y, so the offset is
    # the shelf's own coordinate negated twice and comes out positive.
    nuts = fcprim.sketch(bdy, "Mount nuts", "XZ_Plane", offset=ear_shelf)
    for i, x in enumerate(bolt_at):
        fcprim.polygon(nuts, (x, depth / 2.0), mount_nut_w, name=f"nut{i + 1}")
    fcprim.pocket(bdy, "Mount nuts", nuts, mount_nut_t, reversed_=True)

    bolts = fcprim.sketch(bdy, "Mount bolts", "XZ_Plane", offset=ear_shelf)
    for i, x in enumerate(bolt_at):
        fcprim.circle(bolts, (x, depth / 2.0), mount_bolt_d, name=f"bolt{i + 1}")
    fcprim.pocket(bdy, "Mount bolts", bolts, midplane=True)

    # Mounting datums for the assembly; see fcprim.lcs.
    #   SLOT   the bore's axis, which is the extrusion's
    #   ROD    the leadscrew's, parallel to it
    #   MOUNT  the ear's underside, looking the way the holder comes up
    fcprim.lcs(bdy, "SLOT", at=(0.0, 0.0, depth / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "ROD", at=(0.0, rod_y, depth / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "MOUNT", at=(0.0, -slider_od / 2.0, depth / 2.0),
               axis=(0, -1, 0))
    for i, x in enumerate(bolt_at):
        fcprim.lcs(bdy, f"BOLT{i + 1}",
                   at=(x, -slider_od / 2.0, depth / 2.0), axis=(0, -1, 0))

    return bdy


fcprim.make(__file__, "SCOPE_SLIDER", slider, expected_volume())
