"""The bought parts: extrusion, rod, threaded rod, linear and ball bearings.

The printed parts do not locate on each other, they locate on stock -- a rod
through a clamp, a bracket against an extrusion face -- so without these there
is nothing for the assembly to hang off.

These are made as plain `Part::Feature` solids in the assembly document rather
than as documents of their own, because unlike the printed parts there is
nothing to reconstruct and nothing to check against: a rod is a cylinder and
its dimensions are its catalogue number.  What matters is that the axis is
where it should be, which the assembly's own checks confirm.

**Everything here is built along its local +Z** and is turned into place by the
assembly.  Keeping one convention means a joint axis is always the part's Z,
which is what `Cylindrical` and `Revolute` expect anyway.

Two deliberate simplifications, both of which affect looks rather than fit:

* **Threaded rod is drawn as a plain cylinder at its nominal diameter.**  The
  machine has M5 and M8 studding in it; modelling real threads would add
  thousands of faces to every check for no gain, since what the assembly cares
  about is the axis and the pitch, and pitch lives on the `Screw` joint.
* **The extrusion profile is representative rather than a particular brand's.**
  20 x 20 T-slot is drawn with a 6 mm slot mouth opening into an 11 mm channel
  and a 4.2 mm centre bore, which is the common profile; a supplier's own
  section differs in the corner fillets and the web shape.  The outside
  dimensions and the slot positions -- the two things anything bolts to -- are
  right.

  It comes out at **196.1 mm2** of section, and a real 20 x 20 slot 6 profile
  is catalogued at 0.53 kg/m, which at 2.70 g/cm3 is 196 mm2.  That is a check
  worth having, because it is sensitive to exactly the thing the section used
  to get wrong: too much cut away and the number falls, and the boss the centre
  bore runs through stops being attached to anything.  See `_slot`.
"""

import math

import Part
from FreeCAD import Placement, Rotation, Vector

# Slot geometry for a 20 mm T-slot section.
SLOT_MOUTH = 6.0         # the gap a nut drops through
SLOT_MOUTH_DEPTH = 2.0   # and the outer wall it goes through
SLOT_CHANNEL = 11.0      # the widest the T gets, behind that wall
CENTRE_BORE = 4.2        # tapped M5 in most profiles
CORE = 8.0               # across the boss the centre bore is drilled through
RIB = 2.0                # the four diagonal webs that hold the boss on


def _feature(doc, label, shape):
    obj = doc.addObject("Part::Feature", "Stock")
    obj.Label = label
    obj.Shape = shape
    return obj


def _prism(points, length):
    """A closed profile in the XY plane, run up +Z."""
    wire = Part.makePolygon([Vector(x, y, 0.0) for x, y in points]
                            + [Vector(points[0][0], points[0][1], 0.0)])
    return Part.Face(wire).extrude(Vector(0, 0, length))


def _slot(length):
    """One T-slot, as two cutting solids: the mouth and the cavity behind it.

    Drawn for the +Y face of a cell centred on the origin, and then turned to
    each of the four faces.

    **The cavity's flanks run at 45 degrees**, and that is the whole of what
    makes this a section rather than a puzzle.  Cut the cavity as a plain 11 mm
    rectangle 6 deep -- which is what this file did until Michael looked at a
    render and said the extrusions were impossible -- and the four cavities
    meet each other across the diagonals: the boss the centre bore runs through
    is left floating in mid air, joined to nothing, and the profile comes out
    in five pieces rather than one -- the boss, and each of the four corners.
    Sloping the flanks leaves the four diagonal **ribs** that carry the boss out
    to the corners, which is what every real T-slot profile has and why it can
    be extruded at all.  The old section measured 171.1 mm2 against a real
    profile's 196; this one measures 196.1.
    """
    half, wide = 10.0, SLOT_CHANNEL / 2.0
    front = half - SLOT_MOUTH_DEPTH          # the wall's inner face
    back = CORE / 2.0                        # and the boss's own
    rib = RIB / math.sqrt(2.0)               # the ribs, off the diagonal
    cavity = _prism([
        (-wide, front), (wide, front), (wide, wide + rib),
        (back - rib, back), (-(back - rib), back), (-wide, wide + rib),
    ], length)
    mouth = Part.makeBox(SLOT_MOUTH, SLOT_MOUTH_DEPTH + 1.0, length,
                         Vector(-SLOT_MOUTH / 2.0, front, 0))
    return [cavity, mouth]


def _cell(cx, cy, length):
    """One 20 mm cell of an extrusion: the slots and bore, as cutting solids."""
    cuts = [Part.makeCylinder(CENTRE_BORE / 2.0, length,
                              Vector(cx, cy, 0), Vector(0, 0, 1))]
    for angle in (0, 90, 180, 270):
        rot = Rotation(Vector(0, 0, 1), angle)
        for solid in _slot(length):
            solid.Placement = Placement(Vector(cx, cy, 0), rot) \
                .multiply(solid.Placement)
            cuts.append(solid)
    return cuts


def _mitre_wedge(width, height, at, towards):
    """The wedge a 45 degree mitre removes from one end.

    The cut runs at 45 degrees in plan and takes material off the +X side, so
    the -X face keeps the full length.  In a frame that face is the outside,
    which is what makes the corners come out square.
    """
    z0 = at
    z1 = at + towards * width
    pts = [Vector(-width / 2.0, 0, z0), Vector(width / 2.0, 0, z0),
           Vector(width / 2.0, 0, z1), Vector(-width / 2.0, 0, z0)]
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(Vector(0, -(height + 2.0), 0))


def extrusion(doc, label, length, cells_x=1, cells_y=1, mitre=False):
    """T-slot aluminium extrusion, `cells_x` by `cells_y` cells of 20 mm.

    2020 is 1 x 1; 2040 is 2 x 1 lying flat or 1 x 2 standing up.  The section
    is centred across its width on the local X, its **top face is at local
    Y = 0** so that members of different heights can be hung from a common top
    surface, and the length runs along +Z.

    With `mitre`, both ends are cut at 45 degrees off the +X side, which is how
    the bottom frame's four members make a closed square while each stays the
    full 300 mm along its outer face.
    """
    width, height = cells_x * 20.0, cells_y * 20.0
    shape = Part.makeBox(width, height, length,
                         Vector(-width / 2.0, -height, 0))
    for ix in range(cells_x):
        for iy in range(cells_y):
            cx = -width / 2.0 + 10.0 + ix * 20.0
            cy = -height + 10.0 + iy * 20.0
            for cut in _cell(cx, cy, length):
                shape = shape.cut(cut)
    if mitre:
        shape = shape.cut(_mitre_wedge(width, height, 0.0, 1.0))
        shape = shape.cut(_mitre_wedge(width, height, length, -1.0))
    obj = _feature(doc, label, shape)
    obj.addProperty("App::PropertyLength", "Length", "Stock",
                    "Cut length of the extrusion", locked=True)
    obj.Length = length
    return obj


def rod(doc, label, diameter, length):
    """Ground linear rod -- what the LM8UU run on."""
    return _feature(doc, label,
                    Part.makeCylinder(diameter / 2.0, length,
                                      Vector(0, 0, 0), Vector(0, 0, 1)))


def threaded_rod(doc, label, diameter, length):
    """Studding, drawn plain at nominal diameter; see the module docstring."""
    return _feature(doc, label,
                    Part.makeCylinder(diameter / 2.0, length,
                                      Vector(0, 0, 0), Vector(0, 0, 1)))


def linear_bearing(doc, label="LM8UU", bore=8.0, outer=15.0, length=24.0):
    """LM8UU and friends: a sleeve, bore along +Z.

    LM8UU is 8 mm bore, 15 mm outside, 24 mm long.
    """
    shape = Part.makeCylinder(outer / 2.0, length, Vector(0, 0, 0),
                              Vector(0, 0, 1))
    shape = shape.cut(Part.makeCylinder(bore / 2.0, length + 2.0,
                                        Vector(0, 0, -1), Vector(0, 0, 1)))
    return _feature(doc, label, shape)


def ball_bearing(doc, label, bore, outer, width):
    """A deep groove ball bearing as two rings.

    The alpha axis uses 14 x 7 x 5.  Drawn as an outer and an inner ring with
    the ball track between them left empty, which is enough to show a press fit
    and to let a shaft joint find the bore.
    """
    ring = (outer - bore) / 6.0
    shape = Part.makeCylinder(outer / 2.0, width, Vector(0, 0, 0),
                              Vector(0, 0, 1))
    shape = shape.cut(Part.makeCylinder(outer / 2.0 - ring, width + 2.0,
                                        Vector(0, 0, -1), Vector(0, 0, 1)))
    inner = Part.makeCylinder(bore / 2.0 + ring, width, Vector(0, 0, 0),
                              Vector(0, 0, 1))
    inner = inner.cut(Part.makeCylinder(bore / 2.0, width + 2.0,
                                        Vector(0, 0, -1), Vector(0, 0, 1)))
    return _feature(doc, label, shape.fuse(inner))


def spring(doc, label, outer, wire, length, turns=None):
    """A compression spring, drawn as a helical sweep.

    The eccentrics and the X screw preload both use one.  Free length is what
    is drawn; the assembly does not compress it.
    """
    turns = turns or max(3, int(length / (wire * 2.5)))
    helix = Part.makeHelix(length / turns, length, (outer - wire) / 2.0)
    profile = Part.Wire(Part.makeCircle(
        wire / 2.0, Vector((outer - wire) / 2.0, 0, 0), Vector(0, 1, 0)))
    return _feature(doc, label,
                    Part.Wire(helix.Edges).makePipeShell([profile], True, True))


# A butt hinge from the shop, of the size the manual's step 12 calls for.  It
# is bought, not printed and not drawn, so these are the proportions of an
# ordinary 40 mm steel hinge rather than a measurement of the author's.
HINGE_LEAF = 20.0        # how far each leaf reaches from the pivot
HINGE_LENGTH = 40.0      # along the pivot
HINGE_THICK = 2.0
HINGE_KNUCKLE = 5.0


def hinge_leaf(doc, label, spans, hand=1, leaf=HINGE_LEAF,
               length=HINGE_LENGTH, thick=HINGE_THICK,
               knuckle=HINGE_KNUCKLE):
    """One leaf of a butt hinge, its pivot on the origin and axis along +Z.

    A hinge is drawn as two of these rather than one solid, because the whole
    point of it is that the two halves move relative to each other: one leaf
    stays with the hinge bar and the other goes up with the lid, and a single
    solid could only ever belong to one of them.

    `spans` are the knuckle segments this leaf carries along the pivot; the two
    leaves interleave, so between them they cover the whole length once.  The
    leaf lies flat on the face it is screwed to, which puts the pivot `thick`
    above that face -- a surface mounted hinge, which is what the photographs
    of the machine show.
    """
    plate = Part.makeBox(leaf, thick, length,
                         Vector(0.0 if hand > 0 else -leaf, 0.0,
                                -length / 2.0))
    shape = plate
    for z0, z1 in spans:
        shape = shape.fuse(Part.makeCylinder(
            knuckle / 2.0, z1 - z0, Vector(0, thick, z0), Vector(0, 0, 1)))
    for z in (-length / 4.0, length / 4.0):
        shape = shape.cut(Part.makeCylinder(
            2.1, thick + 2.0, Vector(hand * leaf / 2.0, -1.0, z),
            Vector(0, 1, 0)))
    return _feature(doc, label, shape.removeSplitter())
