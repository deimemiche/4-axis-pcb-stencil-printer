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
"""

import Part
from FreeCAD import Placement, Rotation, Vector

# Slot geometry for a 20 mm T-slot section.
SLOT_MOUTH = 6.0         # the gap a nut drops through
SLOT_MOUTH_DEPTH = 2.0
SLOT_CHANNEL = 11.0      # the wider space behind it
SLOT_DEPTH = 6.0         # total, from the face inwards
CENTRE_BORE = 4.2        # tapped M5 in most profiles


def _feature(doc, label, shape):
    obj = doc.addObject("Part::Feature", "Stock")
    obj.Label = label
    obj.Shape = shape
    return obj


def _cell(cx, cy, length):
    """One 20 mm cell of an extrusion: the slots and bore, as cutting solids."""
    cuts = [Part.makeCylinder(CENTRE_BORE / 2.0, length,
                              Vector(cx, cy, 0), Vector(0, 0, 1))]
    for angle in (0, 90, 180, 270):
        rot = Rotation(Vector(0, 0, 1), angle)
        # A slot cut in the +Y face, then turned to each of the four faces.
        mouth = Part.makeBox(SLOT_MOUTH, SLOT_MOUTH_DEPTH + 1.0, length,
                             Vector(-SLOT_MOUTH / 2.0, 10.0 - SLOT_MOUTH_DEPTH,
                                    0))
        channel = Part.makeBox(SLOT_CHANNEL, SLOT_DEPTH - SLOT_MOUTH_DEPTH,
                               length,
                               Vector(-SLOT_CHANNEL / 2.0, 10.0 - SLOT_DEPTH,
                                      0))
        for solid in (mouth, channel):
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
