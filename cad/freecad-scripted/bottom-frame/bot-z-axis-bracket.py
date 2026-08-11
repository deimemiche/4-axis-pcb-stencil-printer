"""BOT_Z_AXIS_BRACKET - corner gusset that stands a linear Z rod up, both hands.

Michael's own part, from the linear Z axis mod in the repository's README, and
one of the few here **transcribed from a parametric source rather than reverse
engineered**: it already exists as CadQuery in [`../../archive/z-axis.py`](../../archive/z-axis.py),
driven by [`../../archive/settings.py`](../../archive/settings.py), so every dimension below is
read off that script.

It bolts flat to a **corner of the bottom frame** -- it replaces the author's
`BOT_CLAMP_Z_AXIS` and one of his corner gussets with a single part -- so it
takes the `BOT_` prefix the rest of that frame uses, and lives here rather than
in `mod/` with the parts that belong to the lid.  `z-axis.py` still exports it
as `TOP_Z_AXIS_BRACKET.step`, because there it is named after the axis it
carries rather than the frame it sits on.

**Two hands.**  The bracket is chiral -- an L plate with the rod hung off one
leg -- and the machine has one at each of two corners on the same side, so only
mirrored do both rods come out on the same face:

    BOT_Z_AXIS_BRACKET.FCStd            the corner at -Z
    BOT_Z_AXIS_BRACKET_MIRRORED.FCStd   the corner at +Z

They are the same drawing with every X negated, which is what `hand` does
below; the mirror is about the plate's own outer corner, so both documents
share an origin and a set of datums and either drops into the same placement.
`column.py` used to mirror the shape at build time instead, which gave the
assembly a solid it could show but no part anybody could print.

    Plate       sketch -> Pad     the L, 60 x 60 x 4
    Bolt holes  sketch -> Pocket  five M4 clearance on the 20 mm grid
    Web         sketch -> Pad     the flange the collar hangs off, 24 tall
    Ear         sketch -> Pad     what the pinch bolt pulls on
    Collar      sketch -> Pad     16.2 outside, standing the full 24
    Rod bore    sketch -> Pocket  8.2 for the rod, through
    Saw cut     sketch -> Pocket  the 1 mm slit, out through the ear
    Brace       sketch -> Pad     the fin tying the web to the plate
    Bolts       sketch -> Pocket  the mounting M4 and the pinch M4, through
    Counterbores -> Pocket        4 deep for the one, a spot face for the other

**The two M4 across the mount are the point of this part**, and both were
missing here until Michael said so:

* the **mounting bolt**, through the web at the one place the web's inner face
  is not behind the collar.  Its axis is 14 mm down from the plate's top face,
  which is 10 mm below the member -- the outer face slot's own centre line --
  and the web's outer face is flush with the plate's edge, so it lies against
  that member and the bolt goes into a slot nut in it.  It is counterbored the
  head's own 4 mm, leaving 3.45 mm of web for the thread to pull on.
* the **pinch bolt**, through the ear on the same line, crossing the saw cut so
  it can pull the collar shut on the rod.  A 0.2 mm spot face rather than a
  counterbore, which is what the CadQuery asks for.

Both are at the centre of the face they are drilled into, because that is where
`cboreBoltHole` put them: `centerOption="CenterOfBoundBox"` on a face the collar
has already taken a bite out of, so the expressions below say where that bite
leaves the centre rather than quoting a number.

What checks it is arithmetic, not a mesh: `plain_volume` is the CadQuery
solid's own volume with its cosmetic chamfers and fillets suppressed, the way
the hinge locks are checked, and this agrees with it exactly.  The chamfers are
left off here for the same reason they are there: they change nothing that
anything fits against.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# All of these come from cad/settings.py and cad/z-axis.py.
wall = 4.0               # Settings.wallThickness
fit = 0.2                # Settings.fit
rod_d = 8.0              # Settings.rodD
bearing_d = 15.0         # Settings.bearingD, an LM8UU
bearing_fit = 0.1        # Settings.tightFit
ext = 20.0               # Settings.extD
compliance = 1.0         # Settings.compliance
head_d = 7.5             # Settings.frameBoltHeadD, M4 socket head plus slop

bolt_hole_d = 4.2        # M4 plus Settings.boltFit
cbore_d = 7.3            # the head, plus that fit and cq_queryabolt's own 0.1
cbore_depth = 4.0        # an M4 socket head's length: the head goes right in
spot_depth = 0.2         # what the pinch bolt gets instead

bore_d = rod_d + fit                     # 8.2, as the author's own rod clamps
collar_d = bore_d + 2 * wall             # 16.2, likewise
collar_h = ext + wall                    # 24: the member, and the plate on it

plate_size = 3 * ext                     # 60 square before the L is cut
plate_thickness = wall
leg_width = ext
bolt_inset = 10.0
bolt_pitch = 20.0
bolts_per_leg = 3

# The mount: a web across the plate's outer edge, the collar in the middle of
# it and the ear out to one side.  Its width is what `z-axis.py` calls
# `bearingMountW` -- bolt head, wall, bearing, wall, bolt head, and a loose
# wall so it does not stand proud of the extrusion.
web_width = bearing_d + 3 * wall + 2 * head_d            # 42
web_depth = (bearing_d + bearing_fit - bore_d) / 2 + wall    # 7.45
rod_x = web_width / 2.0                  # 21: the web starts at the corner
rod_out = (bearing_d + bearing_fit + 2 * wall) / 2       # 11.55

# The ear, from the collar out to the web's end, and the slit through it.  Both
# sit a quarter of the bore above the collar's centre line, which is where the
# CadQuery's `push([(w / 4, rD / 4)])` puts them.
ear_up = bore_d / 4.0                    # 2.05
brace_thickness = wall / 2.0             # the fin off the plate's outer edge

bolt_y = plate_thickness + ext / 2.0     # 14, the member's slot centre line


def _reach(across):
    """Half the chord where the collar meets a plane `across` off its axis.

    Both M4 are drilled at the centre of a face the collar has bitten into, so
    what fixes them is where that bite ends.
    """
    return math.sqrt((collar_d / 2.0) ** 2 - across ** 2)


def bracket(doc, hand=1):
    """The bracket, `hand` +1 as `z-axis.py` draws it and -1 mirrored."""
    name = "BOT_Z_AXIS_BRACKET" + ("" if hand > 0 else "_MIRRORED")
    bdy = fcprim.body(doc, name)

    def x(value):
        return hand * value

    # The L, its outer corner on the origin and both legs running inboard.
    plate = fcprim.sketch(bdy, "Plate", "XZ_Plane")
    fcprim.polyline(plate, [
        (0.0, 0.0), (x(plate_size), 0.0), (x(plate_size), leg_width),
        (x(leg_width), leg_width), (x(leg_width), plate_size),
        (0.0, plate_size),
    ], name="plate")
    fcprim.pad(bdy, "Plate", plate, plate_thickness, reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "XZ_Plane")
    for i in range(bolts_per_leg):
        fcprim.circle(bolts, (x(bolt_inset + i * bolt_pitch), bolt_inset),
                      bolt_hole_d, name=f"bolt_a{i}")
        if i:                                  # the corner hole is shared
            fcprim.circle(bolts, (x(bolt_inset), bolt_inset + i * bolt_pitch),
                          bolt_hole_d, name=f"bolt_b{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts)

    # The web hangs off the plate's outer edge and carries the collar out past
    # the frame; its outer face stays flush with that edge, which is what puts
    # it against the member and lets the mounting bolt reach the slot.
    web = fcprim.sketch(bdy, "Web", "XZ_Plane")
    fcprim.polyline(web, [
        (0.0, -web_depth), (x(web_width), -web_depth), (x(web_width), 0.0),
        (0.0, 0.0),
    ], name="web")
    fcprim.pad(bdy, "Web", web, collar_h, reversed_=True)

    # The ear reaches from the collar to the web's far end, and the saw cut
    # splits it so the pinch bolt has something to pull together.
    ear = fcprim.sketch(bdy, "Ear", "XZ_Plane")
    fcprim.polyline(ear, [
        (x(rod_x), -rod_out - ear_up),
        (x(web_width), -rod_out - ear_up),
        (x(web_width), -rod_out - ear_up + bore_d),
        (x(rod_x), -rod_out - ear_up + bore_d),
    ], name="ear")
    fcprim.pad(bdy, "Ear", ear, collar_h, reversed_=True)

    collar = fcprim.sketch(bdy, "Collar", "XZ_Plane")
    fcprim.circle(collar, (x(rod_x), -rod_out), collar_d, name="collar")
    fcprim.pad(bdy, "Collar", collar, collar_h, reversed_=True)

    bore = fcprim.sketch(bdy, "Rod bore", "XZ_Plane")
    fcprim.circle(bore, (x(rod_x), -rod_out), bore_d, name="rod")
    fcprim.pocket(bdy, "Rod clearance", bore, collar_h)

    # The slit runs from the bore straight out through the ear, so the collar
    # is a C that the pinch bolt can close.
    cut = fcprim.sketch(bdy, "Saw cut", "XZ_Plane")
    fcprim.polyline(cut, [
        (x(rod_x), -rod_out + ear_up - compliance / 2.0),
        (x(web_width), -rod_out + ear_up - compliance / 2.0),
        (x(web_width), -rod_out + ear_up + compliance / 2.0),
        (x(rod_x), -rod_out + ear_up + compliance / 2.0),
    ], name="slit")
    fcprim.pocket(bdy, "Saw cut", cut, collar_h)

    # A fin down the plate's outer edge, tying the web back to the plate.
    brace = fcprim.sketch(bdy, "Brace", "XZ_Plane")
    fcprim.polyline(brace, [
        (x(-brace_thickness), -web_depth), (0.0, -web_depth),
        (0.0, web_depth), (x(-brace_thickness), web_depth),
    ], name="brace")
    fcprim.pad(bdy, "Brace", brace, 2 * web_depth, reversed_=True)

    # The two M4 across the mount, both on the member's slot centre line.  They
    # are drilled along the part's own Z -- into the frame -- so they are
    # sketched on XY, where a pocket runs the way they go.
    mount_x = (rod_x - _reach(bore_d / 2.0)) / 2.0
    pinch_x = (rod_x + _reach(ear_up) + web_width) / 2.0
    across = fcprim.sketch(bdy, "Bolts", "XY_Plane")
    fcprim.circle(across, (x(mount_x), bolt_y), bolt_hole_d, name="mount")
    fcprim.circle(across, (x(pinch_x), bolt_y), bolt_hole_d, name="pinch")
    fcprim.pocket(bdy, "Bolt clearance across", across)

    # Each counterbore is cut from the outer face of what it goes through: the
    # web for the one, the ear for the other.
    seat = fcprim.sketch(bdy, "Mount counterbore", "XY_Plane", offset=-web_depth)
    fcprim.circle(seat, (x(mount_x), bolt_y), cbore_d, name="mount_head")
    fcprim.pocket(bdy, "Mount head", seat, cbore_depth, reversed_=True)

    spot = fcprim.sketch(bdy, "Pinch spot face", "XY_Plane",
                         offset=-rod_out - ear_up)
    fcprim.circle(spot, (x(pinch_x), bolt_y), cbore_d, name="pinch_head")
    fcprim.pocket(bdy, "Pinch spot", spot, spot_depth, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `ROD` is the collar's
    # axis, `MOUNT` the plate's underside, and the five bolts are what hold the
    # whole thing on the frame's corner.
    fcprim.lcs(bdy, "ROD", at=(x(rod_x), 0.0, -rod_out), axis=(0, 1, 0))
    fcprim.lcs(bdy, "MOUNT", axis=(0, -1, 0))
    at = [(bolt_inset + i * bolt_pitch, bolt_inset)
          for i in range(bolts_per_leg)]
    at += [(bolt_inset, bolt_inset + i * bolt_pitch)
           for i in range(1, bolts_per_leg)]
    for i, (bx, bz) in enumerate(at):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x(bx), 0.0, bz), axis=(0, -1, 0))

    # And what the assembly joins to on top of those.  `ROD2` is the collar's
    # far end -- the same line as `ROD`, `collar_h` along it, where the rod
    # comes out.  `FRAME` and `ECC_BOT` are the plate's top face at its two
    # ends, the member on one and the eccenter's foot on the other.  The two
    # M4 across the mount take theirs on the floor of what is bored for the
    # head, which is where the head actually seats: `cbore_depth` into the web
    # for the one, `spot_depth` into the ear for the other.
    fcprim.lcs(bdy, "ROD2", at=(x(rod_x), collar_h, -rod_out), axis=(0, -1, 0))
    fcprim.lcs(bdy, "FRAME", at=(0.0, plate_thickness, 0.0), axis=(0, 1, 0),
               roll=270.0)
    fcprim.lcs(bdy, "ECC_BOT", at=(x(plate_size), plate_thickness, 0.0),
               axis=(0, 1, 0), roll=270.0)
    fcprim.lcs(bdy, "MOUNT_BOLT",
               at=(x(mount_x), bolt_y, -web_depth + cbore_depth), axis=(0, 0, 1))
    fcprim.lcs(bdy, "PINCH_BOLT",
               at=(x(pinch_x), bolt_y, -rod_out - ear_up + spot_depth),
               axis=(0, 0, 1))

    return bdy


# `z-axis.py`'s own solid with its chamfers and fillets suppressed, measured
# under CadQuery 2.8.  Mirroring does not change it, so it checks both hands.
plain_volume = 19534.9215

for side in (1, -1):
    fcprim.make(__file__,
                "BOT_Z_AXIS_BRACKET" + ("" if side > 0 else "_MIRRORED"),
                lambda doc, h=side: bracket(doc, h),
                plain_volume, tolerance=1e-4)
