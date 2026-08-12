"""TOP_RAIL_HOLDER - collar that holds a rail against the top frame.

Reconstructed from the original author's TOP_RAIL_HOLDER.stl, in that mesh's own
coordinates: X = -1.4 .. 10 along the rail, the collar itself spanning 0 .. 10.

Looked at end on it is a dog bone: a 16.1 mm boss around the 8.1 mm rail bore,
a 10 mm lobe around each M4 bolt, and a 5 mm fillet blending each lobe into the
boss.  Nothing here is a straight line: the fillets roll along the lobes' common
tangent, but the boss stands so far past it that they touch the lobes directly
and no length of the tangent itself survives.

Under the collar, standing 1.4 mm proud of its front face, a 5 mm wide foot
reaches out from the rail bore to each lobe - that is what the bolts actually
pull down on.  From the back the bolts are counterbored 7.4 mm for their heads.

    Profile      sketch -> Pad     the dog bone, extruded along the rail
    Feet         sketch -> Pad     the two pads, standing off the front face
    Rail bore    sketch -> Pocket  8.1 mm, through the collar but not the feet
    Bolt holes   sketch -> Pocket  two M4 clearance holes, through everything
    Counterbores sketch -> Pocket  their heads, from the back
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

length = 10.0            # the collar, along the rail
foot_length = 1.4        # how far the feet stand off its front face

boss_d = 16.1            # around the rail bore
bore_d = 8.1             # the rail
lobe_d = 10.0            # around each bolt
blend_r = 5.0            # lobe into boss
bolt_z = 8.809           # how far the bolts sit off the rail axis

foot_width = 5.0

bolt_hole_d = 4.3        # M4 clearance
head_d = 7.4
head_depth = 4.0

mesh_volume = 2166.054


def top_rail_holder(doc):
    bdy = fcprim.body(doc, "TOP_RAIL_HOLDER")
    boss_r, lobe_r, half_w = boss_d / 2, lobe_d / 2, foot_width / 2

    # Centre of the blend in the first quadrant.  It rolls along the lobes'
    # common tangent, so it stands one radius outside that line; the boss then
    # fixes how far along it is.
    blend_y = lobe_r + blend_r
    blend_z = math.sqrt((boss_r + blend_r) ** 2 - blend_y ** 2)

    # Where it lands on the boss, and where it meets the lobe.  The boss has
    # crowded it right up against the lobe, so no straight run of the tangent
    # line is left between them and they simply touch.
    reach = boss_r / (boss_r + blend_r)
    on_boss = (blend_y * reach, blend_z * reach)
    span = math.hypot(blend_y, blend_z - bolt_z)
    on_lobe = (blend_y * lobe_r / span,
               bolt_z + (blend_z - bolt_z) * lobe_r / span)

    # The blends bite a little past the lobe's equator, so what is left of the
    # lobe is slightly more than a half circle and has to be asked for by sweep.
    lobe_sweep = 180.0 + 2 * math.degrees(math.atan2(bolt_z - on_lobe[1],
                                                     on_lobe[0]))

    # Drawn looking along the rail; H is Y, V is Z.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (on_boss[0], -on_boss[1]),
        (on_boss[0], on_boss[1]),
        (on_lobe[0], on_lobe[1]),
        (-on_lobe[0], on_lobe[1]),
        (-on_boss[0], on_boss[1]),
        (-on_boss[0], -on_boss[1]),
        (-on_lobe[0], -on_lobe[1]),
        (on_lobe[0], -on_lobe[1]),
    ], name="collar", arcs={0: boss_r, 1: -blend_r,
                            2: (lobe_r, lobe_sweep), 3: -blend_r,
                            4: boss_r, 5: -blend_r,
                            6: (lobe_r, lobe_sweep), 7: -blend_r})
    fcprim.pad(bdy, "Collar", profile, length)

    # Each foot is the strip of the lobe left between the bolt and the bore.
    feet = fcprim.sketch(bdy, "Feet", "YZ_Plane")
    outer = bolt_z + math.sqrt(lobe_r ** 2 - half_w ** 2)
    inner = math.sqrt((bore_d / 2) ** 2 - half_w ** 2)
    fcprim.polyline(feet, [
        (-half_w, -outer), (half_w, -outer),
        (half_w, -inner), (-half_w, -inner),
    ], name="foot_n", arcs={0: lobe_r, 2: -bore_d / 2})
    fcprim.polyline(feet, [
        (half_w, outer), (-half_w, outer),
        (-half_w, inner), (half_w, inner),
    ], name="foot_p", arcs={0: lobe_r, 2: -bore_d / 2})
    fcprim.pad(bdy, "Feet", feet, foot_length, reversed_=True)

    bore = fcprim.sketch(bdy, "Rail bore", "YZ_Plane")
    fcprim.circle(bore, (0.0, 0.0), bore_d, name="rail")
    fcprim.pocket(bdy, "Rail clearance", bore, length, reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "YZ_Plane", offset=-foot_length)
    for z in (-bolt_z, bolt_z):
        fcprim.circle(bolts, (0.0, z), bolt_hole_d, name=f"bolt{'np'[z > 0]}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, reversed_=True)

    heads = fcprim.sketch(bdy, "Counterbores", "YZ_Plane",
                          offset=length - head_depth)
    for z in (-bolt_z, bolt_z):
        fcprim.circle(heads, (0.0, z), head_d, name=f"head{'np'[z > 0]}")
    fcprim.pocket(bdy, "Head clearance", heads, head_depth, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  Unlike its bottom
    # twin this collar's bore sits *on* the bolt line, so RAIL and MOUNT differ
    # only by the feet.
    fcprim.lcs(bdy, "RAIL", axis=(1, 0, 0))
    fcprim.lcs(bdy, "MOUNT", at=(-foot_length, 0.0, 0.0), axis=(-1, 0, 0))
    for i, z in enumerate((-bolt_z, bolt_z)):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(-foot_length, 0.0, z),
                   axis=(-1, 0, 0))

    # Each bolt is counterbored from the far end, so it has a second datum on
    # the floor of that bore, which is where its head seats.
    for i, z in enumerate((-bolt_z, bolt_z)):
        fcprim.lcs(bdy, f"BOLT{i + 3}", at=(length - head_depth, 0.0, z),
                   axis=(-1, 0, 0))

    # `FRAME` is the collar's own front face, and the assembly measured it
    # there -- a face's frame sits at its centre of area, and this outline is
    # lobes and blends, so neither number below is a dimension of anything.
    # Kept as measured; see ASSEMBLY.md Part II, step 6.
    fcprim.lcs(bdy, "FRAME", at=(0.0, -2.5, -3.1863), axis=(-1, 0, 0),
               roll=270.0)

    return bdy


fcprim.make(__file__, "TOP_RAIL_HOLDER", top_rail_holder, mesh_volume)
