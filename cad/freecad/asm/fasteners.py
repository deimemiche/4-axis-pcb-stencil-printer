"""Screws, nuts and washers, from the Fasteners workbench.

The build page specifies DIN 912 cap screws, so the assembly uses real ISO
geometry from the addon rather than screws drawn by hand.  The modern number
for DIN 912 is **ISO 4762**, and that is what is asked for below.

    screw(doc, "M4", 10)     ISO 4762 socket head cap screw, M4 x 10
    nut(doc, "M4")           ISO 4032 hex nut
    washer(doc, "M4")        ISO 7089 plain washer
    slot_nut(doc, "M4")      the extrusion's own sliding nut -- drawn here,
                             because the addon has no such type

Two things had to be worked out to use the addon from a script, and neither is
in its documentation.

**Import order matters, and getting it wrong is a segmentation fault rather
than an error.**  Importing `FastenerBase` -- or `FastenersCmd`, which pulls it
in -- as the first thing a script does takes the whole process down.  Importing
`Part` first makes it work.  So the imports below are ordered deliberately and
the `noqa` on `Part` is load-bearing: removing it as an unused import brings the
crash back.

**What goes in the document is a plain solid, not the addon's own object.**  The
addon builds each fastener as a `Part::FeaturePython` whose shape is recomputed
by a Python proxy living in the addon, which would mean the finished assembly
could only be opened by someone who has the addon installed.  Since the geometry
never needs to change once generated, each fastener is baked: generated with the
addon, its shape copied into an ordinary `Part::Feature`, and the generator
thrown away.  The assembly gets genuine ISO screws and depends on nothing.

Fasteners are built **along +Z with the head at the origin, the shank running
+Z**, matching the rest of `stock.py`, so a bolt's joint axis is its own Z.
"""

import Part  # noqa: F401  -- must precede the addon; see the docstring
import FastenersCmd

from FreeCAD import Placement, Rotation, Vector

CAP = "ISO4762"          # socket head cap screw, was DIN 912
HEX_NUT = "ISO4032"      # hex nut
WASHER = "ISO7089"       # plain washer

# The sliding nut a 20 mm T-slot takes.  Not an ISO part -- every extrusion
# supplier has their own -- so this is the common shape: wide enough to catch
# the channel, narrow enough to drop through the slot mouth when turned.
SLOT_NUT = {"width": 10.0, "along": 6.0, "thick": 3.0}


def _bake(doc, label, generator):
    """Copy a generated fastener into a plain solid and drop the generator.

    See the module docstring: this is what keeps the addon out of the saved
    document.
    """
    doc.recompute()
    shape = generator.Shape.copy()
    doc.removeObject(generator.Name)
    obj = doc.addObject("Part::Feature", "Fastener")
    obj.Label = label
    obj.Shape = shape
    return obj


def _make(doc, kind, size, length=None, label=None):
    gen = doc.addObject("Part::FeaturePython", "FastenerGen")
    FastenersCmd.FSScrewObject(gen, kind, None)
    gen.Diameter = size
    if length is not None:
        # Length is an enumeration of the standard lengths, so it wants "10"
        # and rejects "10.0" -- which is what a float turns into by default.
        gen.Length = f"{length:g}"
    return _bake(doc, label, gen)


# Labels deliberately end in a word rather than a digit.  FreeCAD makes a
# duplicate label unique by incrementing its trailing number, so an "M4 x 10"
# would come back as "M4 x 001" the second time it was used -- and this machine
# uses most of these by the dozen.
def screw(doc, size, length, kind=CAP):
    """A cap screw, `length` being the shank under the head as DIN 912 counts.

    `screw(doc, "M4", 10)` is the M4x10 the bottom frame is bolted with.
    """
    return _make(doc, kind, size, length, f"{size}x{length:g} cap screw")


def nut(doc, size, kind=HEX_NUT):
    return _make(doc, kind, size, label=f"{size} hex nut")


def washer(doc, size, kind=WASHER):
    return _make(doc, kind, size, label=f"{size} washer")


def slot_nut(doc, size="M4", label=None):
    """The extrusion's sliding nut.

    Drawn here rather than taken from the addon, which has no T-slot nut among
    its 307 types.  Sits with its thickness along +Z like everything else, so
    the screw that pulls into it shares its axis.
    """
    w, a, t = SLOT_NUT["width"], SLOT_NUT["along"], SLOT_NUT["thick"]
    bore = float(size[1:])
    shape = Part.makeBox(w, a, t, Vector(-w / 2.0, -a / 2.0, 0))
    shape = shape.cut(Part.makeCylinder(bore / 2.0, t + 2.0,
                                        Vector(0, 0, -1), Vector(0, 0, 1)))
    obj = doc.addObject("Part::Feature", "SlotNut")
    obj.Label = label or f"{size} slot nut"
    obj.Shape = shape
    return obj


def bolt_through(doc, size, length, at, axis=(0.0, 0.0, 1.0),
                 with_nut=None, grip=None):
    """A screw placed on an axis, and optionally the nut it pulls into.

    `at` is where the underside of the head sits and `axis` is the direction
    the shank runs, which is how a bolted joint is actually described: the face
    it clamps and the way it points.  `with_nut` is `"hex"` or `"slot"`, and
    `grip` is how far down the shank the nut sits -- the thickness of whatever
    is being clamped -- defaulting to the far end of the screw.
    """
    turn = Rotation(Vector(0, 0, 1), Vector(*axis))
    made = [screw(doc, size, length)]
    made[0].Placement = Placement(Vector(*at), turn)

    if with_nut is not None:
        fixing = slot_nut(doc, size) if with_nut == "slot" else nut(doc, size)
        down = length if grip is None else grip
        fixing.Placement = Placement(
            Vector(*at) + turn.multVec(Vector(0, 0, down)), turn)
        made.append(fixing)
    return made
