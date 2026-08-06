"""ALPHA_TOP_PLATE - the plate that turns with the alpha axis.

Drawn from `technical-drawings/top-plate-workholding.dxf`: 240 x 200 x 6, with
two hole patterns.

* **5 x M3 on a 150.9 mm bolt circle**, at 0 and +-72 and +-144 degrees.  That
  radius, 75.45, is larger than `SR_INNER_RING` (70 mm) and fits inside
  `SR_OUTER_RING_W_GEAR` (77 mm), so this plate bolts to the **outer** ring --
  which is the one the worm drives, and is what makes this the rotating plate.
  Drawn as a bolt circle proper, on a construction pentagon: see
  `fcprim.bolt_circle`.  `ALPHA_BOT_PLATE`'s five 10 mm holes are the same
  circle, and the two agree because both are that one radius.
* **83 x M3 workholding grid**, 15 mm apart in X and 30 mm apart in Z, every
  other column offset by 15 mm.  It is a staggered grid rather than a square
  one, so a board can be clamped closer to wherever its edge happens to fall.

The author drew the plate twice.  `top-plate-plain.dxf` is the same 240 x 200
outline with only the five mounting holes; this is the drilled version, and
`alpha-top-plate-plain.py` is the other.

    Outline   sketch -> Pad     the plate
    Mounting  sketch -> Pocket  5 x M3 to the outer ring
    Grid      sketch -> Pocket  83 x M3 workholding

The build page calls the alpha plate 200 x 200 x 6.  The drawings say the
*bottom* plate is 200 x 200 and this one is 240 x 200, so the page is
describing the pair loosely; the drawings win.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 240.0           # along X
width = 200.0            # along Z
thickness = 6.0

mount_d = 3.5            # the drawing's own diameter, M3 clearance
mount_r = 75.45          # bolt circle to SR_OUTER_RING_W_GEAR
mount_count = 5

grid_d = 3.5
grid_pitch_x = 15.0      # every column
grid_pitch_z = 30.0      # within a column
grid_x_max = 105.0
grid_z_max = 75.0


def grid():
    """The staggered workholding grid.

    Columns land every 15 mm; a column is offset half a row pitch whenever it
    is an odd number of steps from the centre, which is what makes the grid
    triangular rather than square.
    """
    out = []
    steps = int(round(grid_x_max / grid_pitch_x))
    for i in range(-steps, steps + 1):
        x = i * grid_pitch_x
        offset = grid_pitch_z / 2.0 if i % 2 else 0.0
        z = offset
        while z <= grid_z_max + 1e-9:
            out.append((x, z))
            if z > 1e-9:
                out.append((x, -z))
            z += grid_pitch_z
    return out


def expected_volume():
    plain = length * width * thickness
    holes = mount_count + len(grid())
    return plain - holes * math.pi * (grid_d / 2.0) ** 2 * thickness


def plate(doc):
    bdy = fcprim.body(doc, "ALPHA_TOP_PLATE")

    outline = fcprim.sketch(bdy, "Outline", "XZ_Plane")
    fcprim.polyline(outline, [
        (-length / 2, -width / 2),
        (length / 2, -width / 2),
        (length / 2, width / 2),
        (-length / 2, width / 2),
    ], name="plate")
    fcprim.pad(bdy, "Plate", outline, thickness, reversed_=True)

    mount = fcprim.sketch(bdy, "Mounting", "XZ_Plane")
    fcprim.bolt_circle(mount, (0.0, 0.0), mount_r, mount_d, mount_count,
                       name="mount")
    fcprim.pocket(bdy, "Ring mounting", mount, midplane=True)

    work = fcprim.sketch(bdy, "Grid", "XZ_Plane")
    for i, (x, z) in enumerate(grid()):
        fcprim.circle(work, (x, z), grid_d, name=f"grid{i}")
    fcprim.pocket(bdy, "Workholding grid", work, midplane=True)

    return bdy


if len(grid()) != 83:
    raise SystemExit(f"the grid should come to 83 holes, got {len(grid())}")

fcprim.make(__file__, "ALPHA_TOP_PLATE", plate, expected_volume(),
            made_of=fcprim.ALUMINIUM)
