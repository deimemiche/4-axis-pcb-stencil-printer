"""BOT_HANDWHEEL - the handwheel on the bottom frame's screw.

Reconstructed from the original author's BOT_HANDWHEEL.stl, in that mesh's own
coordinates: Y = 0 .. 26, turned about Y.

A 30 mm rim with ten 6 mm flutes to grip by, a hub above it, and an 8 mm spigot
on top.  The 5 mm bore stops 5 mm short of the bottom, and a lug on one side
carries an M3 grub screw into it.

Every edge is broken 1 mm, and where each break sits decides how it is drawn:

* the rim's **top** break stops at the rim's own diameter and the flutes are cut
  straight through it, so it belongs in the turned section;
* the rim's **bottom** break follows the flutes round, so it has to be a chamfer
  taken after they are cut;
* the lug's two breaks sweep its whole outline, and neither can be a dressup -
  the one at its foot *adds* material - so each is a 45 degree tapered pad.

The bore is cut last.  Left in the turned section it would be half filled in
again by the lug, which reaches across the axis.

    Section   sketch -> Revolution    rim, hub and spigot
    Flute     sketch -> Pocket        one grip flute
                     -> PolarPattern  the other nine
    Underside          Chamfer        1 mm round the rim's bottom face
    Lug       sketch -> Pad           what the grub screw goes through
    Lug foot  sketch -> Pad, tapered  its break where it stands on the rim
    Lug crown sketch -> Pad, tapered  its break at the top
    Lug slot  sketch -> Pocket        the gap that lets the hub squeeze
    Bore      sketch -> Pocket        5 mm up the axis
    Grub      sketch -> Pocket        M3 into the bore
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

rim_d = 30.0
rim_y = (0.0, 18.0)
edge_break = 1.0

hub_d = 12.0
hub_y = (19.0, 24.0)     # a 45 degree chamfer joins it to the rim
collar_d = 10.0          # what the hub chamfers down to
spigot_d = 8.0
spigot_y = (25.0, 26.0)

bore_d = 5.0
bore_floor = 5.0

flutes = 10
flute_d = 6.0            # cut on the rim's own diameter

lug_d = 17.2             # the grub screw's lug, across the wheel
lug_across = 9.4         # how wide it is
lug_round = 1.0          # its two outer corners
lug_slot = (4.0, 6.6)    # a slot through it, either side of the grub screw
lug_slot_across = 5.4
lug_y = (18.0, 25.0)
grub_hole_d = 3.5        # M3
grub_y = 21.5

mesh_volume = 10724.895


def lug_outline(sk, name, grow=0.0):
    """The lug seen from above: a rectangle rounded at its two outer corners.

    `grow` pushes the whole outline out or in, which is what the 45 degree
    breaks at either end of it sweep through.  The end on the axis stays put
    either way, being buried in the hub.
    """
    reach, half, corner = lug_d / 2 + grow, lug_across / 2 + grow, \
        lug_round + grow
    fcprim.polyline(sk, [
        (0.0, -half),
        (-reach, -half),
        (-reach, half),
        (0.0, half),
    ], name=name,
        fillets={1: corner, 2: corner} if corner > 1e-9 else None)


def bot_handwheel(doc):
    bdy = fcprim.body(doc, "BOT_HANDWHEEL")
    rim_r = rim_d / 2

    # Half a section through the wheel; H is the radius, V is height.  The rim
    # is solid here: the bore comes off at the end, once the lug is on.
    section = fcprim.sketch(bdy, "Section", "XY_Plane")
    fcprim.polyline(section, [
        (0.0, rim_y[0]),
        (rim_r, rim_y[0]),
        (rim_r, rim_y[1] - edge_break),
        (rim_r - edge_break, rim_y[1]),
        (hub_d / 2 + edge_break, rim_y[1]),
        (hub_d / 2, hub_y[0]),
        (hub_d / 2, hub_y[1]),
        (collar_d / 2, spigot_y[0]),
        (spigot_d / 2, spigot_y[0]),
        (spigot_d / 2, spigot_y[1]),
        (0.0, spigot_y[1]),
    ], name="section")
    fcprim.revolution(bdy, "Turned body", section, axis="V_Axis")

    flute = fcprim.sketch(bdy, "Flute", "XZ_Plane", offset=-rim_y[1])
    fcprim.circle(flute, (0.0, -rim_r), flute_d, name="flute")
    cut = fcprim.pocket(bdy, "Flute", flute, rim_y[1] - rim_y[0],
                        reversed_=True)
    fcprim.polar_pattern(bdy, "Grip", [cut], flutes, axis="Y_Axis")

    # The break round the underside, taken after the flutes so it follows them.
    # Everything down there is rim: nothing else has reached Y = 0 yet.
    def underside(edge):
        return abs(fcprim.midpoint(edge).y - rim_y[0]) < 1e-6

    fcprim.chamfer(bdy, "Underside", edge_break, underside)

    # The lug, standing off the hub on one side.  Drawn looking down; H is X,
    # V is Z, and every pad runs down.  Its straight part reaches from the rim
    # to just short of the top.
    lug = fcprim.sketch(bdy, "Lug", "XZ_Plane", offset=-hub_y[1])
    lug_outline(lug, "lug")
    fcprim.pad(bdy, "Lug", lug, hub_y[1] - lug_y[0])

    # Both ends of it are broken 1 mm right round the outline.  Neither can be
    # a Chamfer dressup: the break at the foot adds material rather than taking
    # it away, and the one at the top dies out where the outline crosses the
    # collar, which is where OCC gives up.  A 45 degree taper over 1 mm draws
    # each of them in one pad, from whichever end of the break is the smaller.
    foot = fcprim.sketch(bdy, "Lug foot", "XZ_Plane",
                         offset=-(lug_y[0] + edge_break))
    lug_outline(foot, "foot")
    fcprim.pad(bdy, "Lug foot", foot, edge_break, taper=45.0)

    crown = fcprim.sketch(bdy, "Lug crown", "XZ_Plane", offset=-lug_y[1])
    lug_outline(crown, "crown", grow=-edge_break)
    fcprim.pad(bdy, "Lug crown", crown, edge_break, taper=45.0)

    # A slot through the lug, so the grub screw's thread is only held at its
    # outer end and the hub is free to be squeezed onto the shaft.
    slot = fcprim.sketch(bdy, "Lug slot", "XZ_Plane", offset=-lug_y[1])
    fcprim.polyline(slot, [
        (-lug_slot[0], -lug_slot_across / 2),
        (-lug_slot[1], -lug_slot_across / 2),
        (-lug_slot[1], lug_slot_across / 2),
        (-lug_slot[0], lug_slot_across / 2),
    ], name="slot")
    fcprim.pocket(bdy, "Lug slot", slot, lug_y[1] - lug_y[0], reversed_=True)

    bore = fcprim.sketch(bdy, "Bore", "XZ_Plane", offset=-spigot_y[1])
    fcprim.circle(bore, (0.0, 0.0), bore_d, name="bore")
    fcprim.pocket(bdy, "Bore", bore, spigot_y[1] - bore_floor, reversed_=True)

    grub = fcprim.sketch(bdy, "Grub screw", "YZ_Plane", offset=-lug_d / 2)
    fcprim.circle(grub, (grub_y, 0.0), grub_hole_d, name="grub")
    fcprim.pocket(bdy, "Grub screw", grub, lug_d / 2, reversed_=True)

    # Mounting datums for the assembly; see fcprim.lcs.  `SHAFT` is where the
    # rod's end comes to rest -- the bore's floor -- with Z pointing back down
    # the rod, so a screw joint reads as "the wheel goes on this far".
    fcprim.lcs(bdy, "SHAFT", at=(0.0, bore_floor, 0.0), axis=(0, -1, 0))
    fcprim.lcs(bdy, "FACE", at=(0.0, rim_y[0], 0.0), axis=(0, -1, 0))

    # What the assembly joins to on top of those.  `STUD` is `SHAFT`'s point
    # looking *up* the bore, which is the way the studding comes in;
    # `BRACKET_X` is the spigot's far end, which is what stands against the
    # bracket.  The grub screw is on its own axis at the lug's outer face,
    # and its nut on the near wall of the slot the lug is split by.
    fcprim.lcs(bdy, "STUD", at=(0.0, bore_floor, 0.0), axis=(0, 1, 0),
               roll=270.0)
    fcprim.lcs(bdy, "BRACKET_X", at=(0.0, spigot_y[1], 0.0), axis=(0, -1, 0))
    fcprim.lcs(bdy, "GRUB", at=(-lug_d / 2, grub_y, 0.0), axis=(1, 0, 0))
    fcprim.lcs(bdy, "NUT", at=(-lug_slot[0], grub_y, 0.0), axis=(-1, 0, 0))

    return bdy


fcprim.make(__file__, "BOT_HANDWHEEL", bot_handwheel, mesh_volume)
