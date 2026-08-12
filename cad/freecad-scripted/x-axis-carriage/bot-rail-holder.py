"""BOT_RAIL_HOLDER - collar that holds a rail against the bottom frame.

Reconstructed from the original author's BOT_RAIL_HOLDER.stl, in that mesh's own
coordinates: X = -1.4 .. 10 along the rail, the collar itself spanning 0 .. 10.

It is TOP_RAIL_HOLDER's twin and works the same way - a boss around the rail
bore, a lobe around each M4 bolt, a foot under each bolt standing proud of the
front face - but its bolts are further apart and its bore is offset 1 mm off
their line, so the shape is no longer symmetric.  That offset is the whole point
of the part: the rail sits 1 mm to one side of the bolts.

Where the boss is far enough from the bolt line, the outline runs straight along
the lobes' common tangent and a 5 mm fillet turns each end of that line into the
boss.  On the offset side the boss has come close enough that the line has
vanished and the fillet rolls straight off the lobe.

    Profile      sketch -> Pad     the outline, extruded along the rail
    Feet         sketch -> Pad     the two pads, standing off the front face
    Rail bore    sketch -> Pocket  8 mm, through the collar but not the feet
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

boss_d = 16.0            # around the rail bore
bore_d = 8.0             # the rail
boss_y = -1.0            # how far the rail sits off the bolt line
lobe_d = 10.0            # around each bolt
blend_r = 5.0            # lobe into boss
bolt_z = (5.0, 23.583)   # the two bolts, along the frame

foot_width = 5.0

bolt_hole_d = 4.3        # M4 clearance
head_d = 7.4
head_depth = 4.0

mesh_volume = 2287.705


def bot_rail_holder(doc):
    bdy = fcprim.body(doc, "BOT_RAIL_HOLDER")
    boss_r, lobe_r, half_w = boss_d / 2, lobe_d / 2, foot_width / 2
    boss_z = sum(bolt_z) / 2
    reach = boss_r / (boss_r + blend_r)

    def blend(side, end):
        """One of the four fillets, as (centre, where it lands on the boss).

        Every fillet rolls along the lobes' common tangent, so its centre sits
        one radius outside that line; the boss then fixes how far along it is.
        """
        y = side * (lobe_r + blend_r)
        z = boss_z + end * math.sqrt((boss_r + blend_r) ** 2 - (y - boss_y) ** 2)
        return (y, z), (boss_y + (y - boss_y) * reach, boss_z + (z - boss_z) * reach)

    far_lo, far_lo_boss = blend(1, -1)      # the side the bore leans away from
    far_hi, far_hi_boss = blend(1, 1)
    near_lo, near_lo_boss = blend(-1, -1)   # the side it leans towards
    near_hi, near_hi_boss = blend(-1, 1)

    # On the near side the boss has crowded the fillet right up against the
    # lobe: they touch, and no straight run of the tangent line is left between
    # them.  The meeting point is where the lobe faces the fillet's centre.
    def touch(centre, lobe_z):
        span = math.hypot(centre[0], centre[1] - lobe_z)
        return (centre[0] * lobe_r / span,
                lobe_z + (centre[1] - lobe_z) * lobe_r / span)

    # Drawn looking along the rail; H is Y, V is Z.
    profile = fcprim.sketch(bdy, "Profile", "YZ_Plane")
    fcprim.polyline(profile, [
        (lobe_r, bolt_z[0]),
        (lobe_r, far_lo[1]),
        far_lo_boss,
        far_hi_boss,
        (lobe_r, far_hi[1]),
        (lobe_r, bolt_z[1]),
        touch(near_hi, bolt_z[1]),
        near_hi_boss,
        near_lo_boss,
        touch(near_lo, bolt_z[0]),
    ], name="collar", arcs={1: -blend_r, 2: boss_r, 3: -blend_r,
                            5: lobe_r, 6: -blend_r, 7: boss_r,
                            8: -blend_r, 9: lobe_r})
    fcprim.pad(bdy, "Collar", profile, length)

    # Each foot is the strip of the lobe left between the bolt and the bore.
    def bore_z(y, end):
        return boss_z + end * math.sqrt((bore_d / 2) ** 2 - (y - boss_y) ** 2)

    cap = math.sqrt(lobe_r ** 2 - half_w ** 2)
    feet = fcprim.sketch(bdy, "Feet", "YZ_Plane")
    fcprim.polyline(feet, [
        (-half_w, bolt_z[0] - cap), (half_w, bolt_z[0] - cap),
        (half_w, bore_z(half_w, -1)), (-half_w, bore_z(-half_w, -1)),
    ], name="foot_n", arcs={0: lobe_r, 2: -bore_d / 2})
    fcprim.polyline(feet, [
        (half_w, bolt_z[1] + cap), (-half_w, bolt_z[1] + cap),
        (-half_w, bore_z(-half_w, 1)), (half_w, bore_z(half_w, 1)),
    ], name="foot_p", arcs={0: lobe_r, 2: -bore_d / 2})
    fcprim.pad(bdy, "Feet", feet, foot_length, reversed_=True)

    bore = fcprim.sketch(bdy, "Rail bore", "YZ_Plane")
    fcprim.circle(bore, (boss_y, boss_z), bore_d, name="rail")
    fcprim.pocket(bdy, "Rail clearance", bore, length, reversed_=True)

    bolts = fcprim.sketch(bdy, "Bolt holes", "YZ_Plane", offset=-foot_length)
    for i, z in enumerate(bolt_z):
        fcprim.circle(bolts, (0.0, z), bolt_hole_d, name=f"bolt{i}")
    fcprim.pocket(bdy, "Bolt clearance", bolts, reversed_=True)

    heads = fcprim.sketch(bdy, "Counterbores", "YZ_Plane",
                          offset=length - head_depth)
    for i, z in enumerate(bolt_z):
        fcprim.circle(heads, (0.0, z), head_d, name=f"head{i}")
    fcprim.pocket(bdy, "Head clearance", heads, head_depth, reversed_=True)

    # Mounting datums for the assembly to join against; see fcprim.lcs.
    # Both axes run along X, because in this part the rail and the bolts are
    # parallel -- the collar is bolted flat to a face and the rail leaves that
    # face at right angles.
    fcprim.lcs(bdy, "RAIL", at=(0.0, boss_y, boss_z), axis=(1, 0, 0))
    fcprim.lcs(bdy, "MOUNT", at=(-foot_length, 0.0, boss_z), axis=(-1, 0, 0))
    for i, z in enumerate(bolt_z):
        fcprim.lcs(bdy, f"BOLT{i + 1}", at=(-foot_length, 0.0, z),
                   axis=(-1, 0, 0))

    # Each bolt is counterbored from the far end, so it has a second datum on
    # the floor of that bore -- which is where its head actually seats.
    for i, z in enumerate(bolt_z):
        fcprim.lcs(bdy, f"BOLT{i + 3}", at=(length - head_depth, 0.0, z),
                   axis=(-1, 0, 0))

    # Two the assembly measured on a *face* rather than on anything drawn, and
    # a face's own frame sits at its centre of area -- so these two heights are
    # not dimensions of anything: the collar's outline is lobes and blends, and
    # that is where its middle falls.  Kept as measured; see ASSEMBLY.md Part II,
    # step 6.  Both are on the collar's own front face, `FACE` looking out
    # along the rail and `FRAME` back down it.
    fcprim.lcs(bdy, "FACE", at=(0.0, 4.1272, boss_z), axis=(1, 0, 0),
               roll=180.0)
    fcprim.lcs(bdy, "FRAME", at=(0.0, 2.5, 16.228), axis=(-1, 0, 0),
               roll=180.0)

    return bdy


fcprim.make(__file__, "BOT_RAIL_HOLDER", bot_rail_holder, mesh_volume)
