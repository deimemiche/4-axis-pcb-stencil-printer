"""The checks that are worth more than the picture.

The assembly's real value is as a test: it is the first thing that can catch an
error in a part that the part's own volume and point checks cannot see, because
those only ever compare a part with itself.  Two parts can each be perfect and
still not fit.

    interference   no two solids may share space
    collinear      every bore on one rod must have one axis
    fit            a rod must pass every bore assigned to it
    envelope       the machine must come out the size the manual says

Interference is the expensive one, so it is done in two passes: bounding boxes
first, which throws away almost every pair for the cost of six comparisons, then
a real boolean only on the pairs that survive.  Without that a machine of this
many solids takes minutes rather than seconds.

A small overlap is not automatically a bug.  A rod is a sliding fit in its
bearing and a clamp is *meant* to close on what it holds, so the tolerance below
is the volume at which an overlap stops being a fit and starts being a mistake.
"""

import math

from FreeCAD import Vector

# An overlap smaller than this is a fit, not a clash.  A 8 mm rod in a 8.2 mm
# clamp bore that has been drawn shut would show a sliver of this order.
CLASH_MM3 = 1.0


# The assembly container carries a Shape of its own that is the union of
# everything inside it, so counting it as a solid makes it appear to collide
# with every part in the machine.
CONTAINERS = ("Assembly::AssemblyObject", "Assembly::JointGroup",
              "App::DocumentObjectGroup", "App::Part")


def placed(obj):
    """An object's shape in machine coordinates.

    An `App::Link` shares its shape with every other link to the same part, so
    `link.Shape` is the part where it was *drawn*, not where it was put.  Asking
    a link for its bounding box directly is therefore wrong, and quietly so.
    """
    shape = obj.Shape
    if obj.TypeId == "App::Link":
        shape = obj.LinkedObject.Shape.copy()
        shape.Placement = obj.Placement.multiply(shape.Placement)
    return shape


def solids(doc):
    """Every placed solid in a document, as (label, shape in machine space)."""
    out = []
    for obj in doc.Objects:
        if obj.TypeId in CONTAINERS:
            continue
        shape = getattr(obj, "Shape", None)
        if shape is None or not shape.Solids:
            continue
        out.append((obj.Label, placed(obj)))
    return out


def interference(doc, say, tolerance=CLASH_MM3, ignore=(), only=None):
    """Every pair of solids that shares more space than it should.

    `ignore` is pairs of label fragments that are allowed to touch -- a rod in
    its own clamp, say.

    `only` is a set of labels that just moved.  Driving an axis cannot change
    whether two *stationary* parts overlap, so a travel check need only look at
    pairs involving something that moved -- which turns an O(n^2) sweep over
    the whole machine into a narrow one, and is the difference between a check
    that runs in seconds and one that does not finish.
    """
    placed = solids(doc)
    pairs = len(placed) * (len(placed) - 1) // 2
    if only is None:
        say(f"  {len(placed)} solids, {pairs} pairs")

    near = []
    for i, (label_a, a) in enumerate(placed):
        for label_b, b in placed[i + 1:]:
            if only is not None and label_a not in only and label_b not in only:
                continue
            box_a, box_b = a.BoundBox, b.BoundBox
            box_a.enlarge(-1e-6)
            if box_a.intersect(box_b):
                near.append((label_a, a, label_b, b))
    if only is None:
        say(f"  {len(near)} pairs whose bounding boxes touch at all")

    clashes = []
    for label_a, a, label_b, b in near:
        if any(x in label_a and y in label_b or x in label_b and y in label_a
               for x, y in ignore):
            continue
        try:
            shared = a.common(b)
        except Exception:                      # a boolean that will not run
            say(f"  ? could not test {label_a} against {label_b}")
            continue
        if shared.Solids and shared.Volume > tolerance:
            clashes.append((label_a, label_b, shared.Volume))

    if only is None:
        for label_a, label_b, volume in sorted(clashes, key=lambda c: -c[2]):
            say(f"  CLASH {label_a} into {label_b}: {volume:.1f} mm3")
        if not clashes:
            say(f"  ok: nothing overlaps by more than {tolerance} mm3")
    return clashes


def on_its_rod(pairs, margin=0.0):
    """Is every bearing still somewhere along the rod it runs on?

    An interference check cannot see a carriage that has run off the end of its
    rail -- there is nothing left to collide with -- so travel has to be bounded
    by this instead.  Each pair is (bearing, rod), and both are compared along
    whichever axis the rod is longest in, which is the one it was built along.
    """
    for bearing, rod in pairs:
        rb, sb = rod.Shape.BoundBox, bearing.Shape.BoundBox
        spans = ((rb.XLength, (rb.XMin, rb.XMax), (sb.XMin, sb.XMax)),
                 (rb.YLength, (rb.YMin, rb.YMax), (sb.YMin, sb.YMax)),
                 (rb.ZLength, (rb.ZMin, rb.ZMax), (sb.ZMin, sb.ZMax)))
        _, (lo, hi), (blo, bhi) = max(spans)
        if blo < lo - margin or bhi > hi + margin:
            return False
    return True


def collinear(frames, say, tolerance=1e-6):
    """Every frame in `frames` must lie on one axis.

    `frames` is a list of (label, Placement); the axis is each one's Z, which
    is the convention `fcprim.lcs` sets up.
    """
    if len(frames) < 2:
        return True
    (first_label, first), *rest = frames
    axis = first.Rotation.multVec(Vector(0, 0, 1))
    ok = True
    for label, placement in rest:
        other = placement.Rotation.multVec(Vector(0, 0, 1))
        tilt = math.degrees(axis.getAngle(other))
        tilt = min(tilt, 180.0 - tilt)
        off = (placement.Base - first.Base).cross(axis).Length / axis.Length
        if tilt > tolerance or off > tolerance:
            say(f"  FAIL {label} is {off:.4f} mm and {tilt:.4f} deg off "
                f"{first_label}")
            ok = False
    if ok:
        say(f"  ok: {len(frames)} bores on one axis")
    return ok


def envelope(doc, say, want=None, tolerance=0.5):
    """The machine's overall size, and optionally what it should be."""
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for _, shape in solids(doc):
        bb = shape.BoundBox
        for i, (a, b) in enumerate(((bb.XMin, bb.XMax), (bb.YMin, bb.YMax),
                                    (bb.ZMin, bb.ZMax))):
            lo[i], hi[i] = min(lo[i], a), max(hi[i], b)
    size = [hi[i] - lo[i] for i in range(3)]
    say(f"  envelope {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
        f"(X, Y up, Z)")
    say(f"    X {lo[0]:7.1f} .. {hi[0]:7.1f}")
    say(f"    Y {lo[1]:7.1f} .. {hi[1]:7.1f}")
    say(f"    Z {lo[2]:7.1f} .. {hi[2]:7.1f}")
    if want is not None:
        for i, axis in enumerate("XYZ"):
            if want[i] is not None and abs(size[i] - want[i]) > tolerance:
                say(f"  FAIL {axis} is {size[i]:.1f}, expected {want[i]}")
                return None
    return size
