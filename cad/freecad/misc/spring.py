"""SPRING_ID<b>_L<free>_AT<at> - the machine's two springs, drawn compressed.

Bought stock, like the extrusion, the studding and the linear rod, and like
them they had no document of their own: a spring existed only as a stand-in
swept inside the retired `asm/`, at whatever diameter and wire the assembly
that wanted one happened to name.  These are the two Michael needs, and they
are specified by what they have to do rather than by a shop's order code:

                      the small one    the big one
    bore              6 mm             10 mm
    free length       30 mm            35 mm
    working length    12 mm            20 mm
    max compression   60 %             40 %, the `L40` in the order code

The **bore is the fit** -- each goes over something that size, and the outside
is free to be whatever the wire makes it.  The **working length** is how far
down it is squashed where it is fitted, and is what these are drawn at.

**Where the working length sits in the range is the whole of the difference
between them.**  60 % of 30 is 18 mm of travel, leaving 30 - 18 = **12**: the
small one works at exactly the bottom of its range, with no margin, and none is
meant.  40 % of 35 is 14, leaving **21** -- and the big one is fitted at
**20**, which is 42.9 % and so a millimetre *past* the limit rather than on it.
That is Michael's own call and deliberate, so the build prints a `NOTE` for it
and carries on rather than refusing: what it costs is that the big spring will
take a small set on first fitting and come back a touch shorter than 35.
`rated_floor` is what works this out, and it is worth re-reading whenever a
free length moves, because the limit moves with it.

Adding a spring is adding a line to `springs`; drawing one at another length is
adding a line to `instances`.

    End A    sketch -> Helix   the bottom dead coil, one turn nearly shut
    Body     sketch -> Helix   the active coils, at the pitch the length wants
    End B    sketch -> Helix   the top dead coil, the same turn again

**Drawn at their working length, not their free length.**  A spring in an
assembly is as long as the gap it is fitted into, so the document that gets
linked has to be the squashed one: `SPRING_ID6_L30_AT12` is the `..._L30`
spring at 12, and the name says both because a document called `SPRING_ID6_L12`
would read off a parts list as a 12 mm spring to order, which is not a thing
that exists.
Compressing is a change of pitch and nothing else -- same wire, same coils,
same bore -- and the volume check below is what proves it: the free and the
squashed spring come to the *same number*, because the pitch is the one thing
that number cannot see.

    Grind A  sketch -> Pocket  the bottom coil taken back to a flat
    Grind B  sketch -> Pocket  and the top one

**Closed ends, ground flat**, which is what Michael's springs have and what the
last two features are for: each end presents a **flat ring** to whatever it
bears on, rather than the tangent line a round wire would touch a face along.

Closed is the winding, ground is the face, and they are separate things.  The
end turns are laid at very nearly pitch = the wire, so each comes down onto its
neighbour and the spring finishes on a full coil bearing all the way round
instead of on a cut-off spiral standing on a point -- that is closed, and it
makes the length the textbook

    L = p na + 3 d

for `na` active coils, give or take `touch_gap` and the grinding.  Then each end
coil is wound **sunk `grind` below the plane it will be cut on** and the two
pockets take it back to that plane, which is grinding and is why `pitch` also
carries a `2 grind` term: what is ground away has to be wound on first or the
spring comes out short.

**How much is ground off is the tip thickness, and that is the number to set.**
`tip` is what fraction of the wire survives at the very end of the coil -- a
quarter of it, which is the usual minimum a grinder leaves -- so `grind` is the
other three quarters.  The flat that results is not a uniform ring: it is
widest at the tip, where nearly the whole wire is cut through, and tapers away
to nothing about **260 degrees** round, where the coil has climbed clear of the
plane.  That is what a ground end actually looks like, and it is a consequence
of the winding rather than a shape drawn by hand: how far round the flat runs
is `grind / (wire + touch_gap)` of a turn and nothing else.

A useful side effect: `END_A` and `END_B` now sit **on** the two flats, so a
joint made to either bears on a face instead of on a tangent line.

**`touch_gap` is the one number here that is not the spring's.**  A real closed
coil sits *on* the next one, and drawn that way this part comes out empty: the
two wires then meet along a tangent line, and the fuse that lays the body's
first turn onto the end turn hands back nothing at all for it -- an empty shape
wearing an `Up-to-date` state, which is the silent kind of failure `finish`'s
volume check exists to catch, and did.  So the dead coils are wound 0.05 mm
open instead of shut.  It is a twentieth of a millimetre on a coil that is free
to move anyway, it keeps every segment a clean sweep meeting the next on a
shared face, and it leaves the volume exact rather than double counting an
overlap.

**The coil's own volume does not depend on the pitch.**  A helical sweep is a
screw motion, and a screw motion has the same Jacobian as a plain rotation, so
Pappus carries over unchanged: the wire's own circle, times the circumference
its centre travels, times the number of turns -- how fast the coil climbs while
it goes round does not enter.  So `wire_volume` is exact rather than an
estimate, and it is a real check on the sweep: a helix wound at the wrong
radius, from the wrong wire, or for the wrong number of turns cannot come out
at the right volume.  What it cannot catch is the pitch, since that is the one
thing it is blind to -- and that blindness is what makes it the right check for
a spring drawn squashed, as above.

**Grinding is the part that does depend on it**, because a flat is a plane cut
and a plane cut across a screw sweep breaks the very symmetry Pappus needs.
What survives is Pappus applied a slice at a time.  In each half plane through
the axis, the piece being ground away is the **segment of the wire's circle
below the cut**, and a segment of a circle is symmetric about the radius
through its centre -- so its centroid sits on the wire's own radius whatever
the segment, and the volume it sweeps is still its area times the circle that
radius travels.  The centre climbs at a constant rate through the end coil, so
summing over the turn is a change of variable rather than an integral over
angle, and what is left is elementary:

    A(u) = a^2 acos(u/a) - u sqrt(a^2 - u^2)          a = wire / 2
    F(u) = a^2 (u acos(u/a) - sqrt(a^2 - u^2)) + (a^2 - u^2)^(3/2) / 3
    off  = mean (2 pi / dead pitch) (F(a) - F(a - grind))

for `A` the area under the cut when the wire's centre stands `u` above it and
`F` its antiderivative, and `F(a) = 0` because a coil that has climbed clear
has nothing below the plane.  `ground_off` is those three lines, and
`wire_volume` less twice it is what the build checks.

**That figure is exact for the ideal coil and the built one misses it by a few
per cent, and the few per cent is the sweep rather than the sum.**  The
antiderivative is right -- it agrees with a brute force integration to 1e-13 --
and the swept coil before grinding still matches Pappus to 0.0000 %.  What
does not match is the material the flats take off: 8.55 against a predicted
8.88 on the small spring, 21.28 against 20.63 on the big one, a few per cent
each way.  The proof that this is numerical and not geometric is that the
**two ends of the same spring disagree with each other** -- 25.38 and 25.82 mm2
of flat on the big one, for two faces that are identical by construction.  A
helical sweep is a B-spline approximation of the screw surface, and slicing one
where the material tapers away to nothing turns a deviation far too small to
see into a few per cent of a very small volume.

It is 0.20 % and 0.14 % of the whole part, so the default 1 % stands, and the
check still bites where it matters: leave the grinding out altogether and the
volume moves 5 %, set `tip` to half the wire instead of a quarter and it moves
some 3 %.  Both are well outside the noise.

**And the bounding box the build prints will not catch the length either.**  A
swept coil is a B-spline surface and `Shape.BoundBox` measures those by their
control points rather than by the surface, exactly as
[`m8-threaded-rod.py`](m8-threaded-rod.py) warns: these report Z[-1.200,
13.200] and Z[-1.440, 21.440] for springs that really do run 0 to 12 and 0 to
20 -- and they are ground dead flat on both of those planes, so it is not even
close.  What does check them is the tessellation -- `export.py` and then
`stlmeasure.py`, or three lines of `Shape.tessellate` -- and measured that way
they come out **12.0000 long over 8.0000 on a bore of 6.0000**, and **20.0000
long over 12.4000 on a bore of 10.0000**.

### What is measured and what is not

Michael's, and the whole of the specification: the **bore**, the **free
length**, the **working length** and the **percentage**.  The two numbers a
spring is actually wound from, the **wire** and the **coil count**, are in none
of them and are assumptions -- but not free ones, because the working length
constrains them from below:

    wire      1.0 on the small one and 1.2 on the big one, which put the
              outsides at 6 + 2(1.0) = 8.0 and 10 + 2(1.2) = 12.4.  Nothing in
              the specification fixes either: the bore is the fit, and the
              outside is whatever the wire adds to it.  The big one is wound
              from the heavier wire because it is the bigger spring, which is
              a habit rather than a measurement.
    coils     10 and 12, so they go **solid at 10 x 1.0 = 10.0** and at
              **12 x 1.2 = 14.4** -- 2.0 and 5.6 mm clear of the lengths they
              work at, which is the margin that makes those lengths reachable
              at all.

That margin is the thing to check against the real springs, and the coil count
is the cheap way to check it: count the turns, and if the small one has more
than **12** of 1.0 wire, or the big one more than **16** of 1.2, it is already
solid at its working length -- dead on the seat rather than pushing on it, and
the working length is not what it says here.  `spring` refuses to draw one that
cannot reach, rather than quietly self intersecting.

Coordinates: the axis is the part's own **+Z**, running from zero at the
bearing face, which is what the rods and the studding already use and what a
`Cylindrical` joint expects.  A spring is joined by its ends, so `END_A` and
`END_B` are the ones that matter and they sit on the two faces it pushes
against; `AXIS` is at mid length for whatever it is sleeved on.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fcprim

# What the machine's springs are: bore, free length, wire, total coils, and how
# far down they may be squashed.  The wire and the coils are the assumptions --
# see the module docstring.
#
#               bore  free  wire  coils  max squash
springs = {
    "ID6": (6.0, 30.0, 1.0, 10, 0.60),
    "ID10": (10.0, 35.0, 1.2, 12, 0.40),
}

# What to draw, and at what length: a spring in an assembly is at the length it
# is fitted at, not its free length.  `None` draws it as it comes.  The big one
# is fitted a millimetre past its own limit; see the module docstring.
instances = (
    ("ID6", 12.0),
    ("ID10", 20.0),
)

dead = 1                 # dead coils at each end, one turn apiece
touch_gap = 0.05         # how far short of shut they are wound; see the docstring
tip = 0.25               # of the wire, left at the tip of a ground end coil
over = 2.0               # how far the grinding profiles clear the coil


def grind(wire):
    """How deep the end coils are sunk, and so how much is ground back off."""
    return (1.0 - tip) * wire


def pitch(length, wire, coils):
    """What the active coils have to climb at, from `L = p na + 3 d`.

    Plus the two `touch_gap`s the dead coils stand open by and the two `grind`s
    the ends lose to the flats, so that the length comes out on the nose
    whether the spring is drawn free or squashed.
    """
    return ((length + 2.0 * grind(wire) - 3.0 * wire - 2.0 * touch_gap)
            / (coils - 2.0 * dead))


def solid(wire, coils):
    """Coil on coil, which is as short as the real spring goes."""
    return wire * coils


def drawn_floor(wire, coils):
    """As short as *this drawing* goes, which is `touch_gap` per coil longer.

    Below it the active coils would touch, and a tangent contact is exactly
    what the sweep cannot fuse; see the module docstring.  Less the two grinds,
    which come off the ends and so off the length.
    """
    return (3.0 * wire + 2.0 * touch_gap
            + (coils - 2 * dead) * (wire + touch_gap) - 2.0 * grind(wire))


def rated_floor(free, squash):
    """As short as the spring is *allowed* to go: the 60 % off the free length."""
    return free * (1.0 - squash)


def wire_volume(bore, wire, coils):
    """The wire's circle times the circle its centre goes round, `coils` times.

    Pappus, which holds for a screw sweep as much as for a revolve; see the
    module docstring for why the pitch is not in it -- and therefore why a
    squashed spring weighs exactly what the free one does.  The grinding is not
    in it either; that is `ground_off`.
    """
    return math.pi * (wire / 2.0) ** 2 * math.pi * (bore + wire) * coils


def ground_off(bore, wire):
    """What one ground flat takes off: Pappus a slice at a time.

    `F` is the antiderivative of the segment area under the cut, and the end
    coil climbs from `a - grind` at its tip to `a`, where it is clear of the
    plane and `F` is zero.  The whole of the derivation is in the module
    docstring.
    """
    a = wire / 2.0
    low = a - grind(wire)
    mean = (bore + wire) / 2.0
    f_low = (a ** 2 * (low * math.acos(low / a) - math.sqrt(a ** 2 - low ** 2))
             + (a ** 2 - low ** 2) ** 1.5 / 3.0)
    return mean * (2.0 * math.pi / (wire + touch_gap)) * -f_low


def spring(doc, name, bore, wire, coils, length):
    """One spring at `length`, standing on Z = 0 and wound right handed up +Z."""
    if length < drawn_floor(wire, coils):
        raise SystemExit(
            f"{name}: {length} mm is shorter than this spring can be drawn -- "
            f"solid at {solid(wire, coils):.1f}, and the coils touch at "
            f"{drawn_floor(wire, coils):.2f}")
    bdy = fcprim.body(doc, name)
    mean = (bore + wire) / 2.0           # the radius the wire's centre runs at
    climb = pitch(length, wire, coils)

    # Three sweeps end to end, each starting where the last one stopped.  The
    # profile is the wire's own section, drawn in the plane through the axis at
    # the height that turn begins: on XZ, H is the radius and V is the height,
    # and the helix runs up V from there.  The first turn's centre starts half
    # a wire up and then `grind` *below* that, so that the end coil is sunk
    # through the Z = 0 plane and has something for the flat to be cut out of.
    at = wire / 2.0 - grind(wire)
    for label, climb_by, turns in (("End A", wire + touch_gap, dead),
                                   ("Body", climb, coils - 2 * dead),
                                   ("End B", wire + touch_gap, dead)):
        section = fcprim.sketch(bdy, label, "XZ_Plane")
        fcprim.circle(section, (mean, at), wire, name="wire")
        fcprim.helix(bdy, label, section, climb_by, climb_by * turns)
        at += climb_by * turns

    # The two flats: everything past each end plane, taken off square.  H is X
    # and V is Y on XY_Plane, and each pocket runs away from the spring -- the
    # same trim m8-threaded-rod.py cuts its rod back to length with.
    reach = (bore + 2.0 * wire) / 2.0 + over
    for label, plane, away in (("Grind A", 0.0, False),
                               ("Grind B", length, True)):
        flat = fcprim.sketch(bdy, label, "XY_Plane", offset=plane)
        fcprim.polyline(flat, [
            (-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach),
        ], name="grind")
        fcprim.pocket(bdy, label, flat, grind(wire) + over, reversed_=away)

    # Mounting datums for the assembly; see fcprim.lcs and the module docstring.
    fcprim.lcs(bdy, "AXIS", at=(0.0, 0.0, length / 2.0), axis=(0, 0, 1))
    fcprim.lcs(bdy, "END_A", axis=(0, 0, -1))
    fcprim.lcs(bdy, "END_B", at=(0.0, 0.0, length), axis=(0, 0, 1))
    return bdy


for key, at in instances:
    bore, free, wire, coils, squash = springs[key]
    length = free if at is None else at
    name = (f"SPRING_{key}_L{free:.0f}"
            + ("" if at is None else f"_AT{at:.0f}"))
    rated = rated_floor(free, squash)
    print(f"{name}: {free:.0f} free, drawn at {length:.0f} -- "
          f"{(free - length) / free * 100.0:.0f} % of {squash * 100.0:.0f} % "
          f"allowed, solid at {solid(wire, coils):.1f}")
    if length < rated - 1e-9:
        print(f"  NOTE {length:.1f} is past the {rated:.1f} the "
              f"{squash * 100.0:.0f} % allows -- it would take a set")
    fcprim.make(__file__, name,
                lambda doc, name=name, bore=bore, wire=wire, coils=coils,
                length=length: spring(doc, name, bore, wire, coils, length),
                wire_volume(bore, wire, coils) - 2.0 * ground_off(bore, wire),
                made_of=fcprim.STEEL)
