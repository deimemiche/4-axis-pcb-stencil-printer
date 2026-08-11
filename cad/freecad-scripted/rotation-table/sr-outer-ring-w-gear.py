"""SR_OUTER_RING_W_GEAR - the slewing ring's outer race, with the drive teeth.

Reconstructed from the original author's SR_OUTER_RING_W_GEAR.stl, in that
mesh's own coordinates: Y = -2 .. 10, turned about Y.

A plain ring, stepped inside so it retains the balls, with five bosses round it
for the screws that hold it down.  Only one 72 degree sector of it carries
teeth - the worm never reaches further than that - and the sector's two ends are
buried inside the bosses at either end of it, so nothing shows a cut edge.

The teeth are not involute: each is a plain trapezium with straight flanks, a
land at the tip and another at the root, repeated every 2.25 degrees.  One
tooth is drawn and the rest are a polar pattern of it.

    Section  sketch -> Revolution    the ring and its stepped bore
    Rim      sketch -> Pad           the sector the teeth stand on
    Tooth    sketch -> Pad           one tooth
                    -> PolarPattern  the other twenty eight
    Bosses   sketch -> Pad           five, on the screw circle
    Shanks   sketch -> Pocket        their M3 clearance holes
    Heads    sketch -> Pocket        and the counterbores above them
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

ring_r = 75.45           # the plain outside, and the screw circle
ring_y = (-2.0, 10.0)

bore_d = 140.4           # the ball track's own diameter
bore_step_d = 132.0      # the lip above it that retains them
bore_step_y = 8.0

sector = (234.0, 306.0)  # the toothed sector, ending inside a boss at each end
teeth = 29
tooth_pitch = 2.25       # degrees
tip_r = 79.9506
root_r = 78.5083
tip_land = 0.4341        # degrees of land at the tip
root_land = 0.5819       # and at the root

boss_d = 10.5            # round each screw
boss_at = (90.0, 162.0, 234.0, 306.0, 18.0)

shank_d = 3.5            # M3 clearance
head_d = 6.0
head_y = 6.0             # where the counterbore's floor sits

mesh_volume = 38023.814


def polar(radius, degrees):
    """A point on the ring, in the sketch's own (X, Z) sense."""
    turn = math.radians(degrees)
    return (radius * math.cos(turn), radius * math.sin(turn))


def sr_outer_ring_w_gear(doc):
    bdy = fcprim.body(doc, "SR_OUTER_RING_W_GEAR")
    height = ring_y[1] - ring_y[0]

    # Half a section through the ring; H is the radius, V is height.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (bore_step_d / 2, ring_y[1]),
        (ring_r, ring_y[1]),
        (ring_r, ring_y[0]),
        (bore_d / 2, ring_y[0]),
        (bore_d / 2, bore_step_y),
        (bore_step_d / 2, bore_step_y),
    ], name="section")
    fcprim.revolution(bdy, "Ring", section, axis="V_Axis")

    # The rim the teeth stand on.  Its inner edge is carried well inside the
    # ring, where it is buried, so only the outer arc has to be right.
    buried = bore_d / 2 + 1.0
    rim = fcprim.sketch(bdy, "Rim", "XZ_Plane", offset=-ring_y[1])
    fcprim.polyline(rim, [
        polar(buried, sector[0]),
        polar(root_r, sector[0]),
        polar(root_r, sector[1]),
        polar(buried, sector[1]),
    ], name="rim",
        arcs={1: root_r, 3: -buried})
    fcprim.pad(bdy, "Rim", rim, height)

    # One tooth, drawn about the sector's own centre line and sunk a millimetre
    # into the rim so the two share a face rather than meeting on one.  A polar
    # pattern about +Y turns +Z towards +X, so it runs the sector backwards and
    # the seed tooth is the one at the high angle end.
    first = 0.5 * (sector[0] + sector[1]) + 0.5 * (teeth - 1) * tooth_pitch
    flank = 0.5 * (tooth_pitch - tip_land - root_land)
    tooth = fcprim.sketch(bdy, "Tooth", "XZ_Plane", offset=-ring_y[1])
    fcprim.polyline(tooth, [
        polar(root_r - 1.0, first - tip_land / 2 - flank),
        polar(root_r, first - tip_land / 2 - flank),
        polar(tip_r, first - tip_land / 2),
        polar(tip_r, first + tip_land / 2),
        polar(root_r, first + tip_land / 2 + flank),
        polar(root_r - 1.0, first + tip_land / 2 + flank),
    ], name="tooth")
    cut = fcprim.pad(bdy, "Tooth", tooth, height)
    fcprim.polar_pattern(bdy, "Teeth", [cut], teeth, axis="Y_Axis",
                         angle=(teeth - 1) * tooth_pitch)

    bosses = fcprim.sketch(bdy, "Bosses", "XZ_Plane", offset=-ring_y[1])
    for i, where in enumerate(boss_at):
        fcprim.circle(bosses, polar(ring_r, where), boss_d, name=f"boss{i}")
    fcprim.pad(bdy, "Bosses", bosses, height)

    shanks = fcprim.sketch(bdy, "Shanks", "XZ_Plane", offset=-head_y)
    for i, where in enumerate(boss_at):
        fcprim.circle(shanks, polar(ring_r, where), shank_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Shanks", shanks, head_y - ring_y[0], reversed_=True)

    heads = fcprim.sketch(bdy, "Heads", "XZ_Plane", offset=-ring_y[1])
    for i, where in enumerate(boss_at):
        fcprim.circle(heads, polar(ring_r, where), head_d, name=f"head{i}")
    fcprim.pocket(bdy, "Heads", heads, ring_y[1] - head_y, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  The five `BOLT`n are
    # the five screws through the ring, each on the floor of its own
    # counterbore -- which is where the head seats -- and numbered along the
    # ring rather than round it, which is what sorting the centres does.
    # `TOP_PLATE` is the first of those screws at the ring's underside, where
    # the plate it holds lies; `RING` is the step in the bore, which is what
    # rests on the inner ring's rim.
    seats = sorted(polar(ring_r, where) for where in boss_at)
    for i, (x, z) in enumerate(seats):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, head_y, z), axis=(0, -1, 0))
    first_x, first_z = polar(ring_r, boss_at[0])
    fcprim.lcs(bdy, "TOP_PLATE", at=(first_x, ring_y[0], first_z),
               axis=(0, -1, 0))
    fcprim.lcs(bdy, "RING", at=(0.0, bore_step_y, 0.0), axis=(0, 1, 0))

    return bdy


fcprim.make(__file__, "SR_OUTER_RING_W_GEAR", sr_outer_ring_w_gear,
            mesh_volume)
