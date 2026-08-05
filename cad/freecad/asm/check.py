"""The checks that are worth more than the picture.

The assembly's real value is as a test: it is the first thing that can catch an
error in a part that the part's own volume and point checks cannot see, because
those only ever compare a part with itself.  Two parts can each be perfect and
still not fit.

    interference   no two solids may share space
    connected      and none may share space with nothing at all
    collinear      every bore on one rod must have one axis
    fit            a rod must pass every bore assigned to it
    envelope       the machine must come out the size the manual says

`interference` and `connected` are the two halves of one question and neither
is any use without the other: a model can be free of clashes and still be a
pile of parts in mid air.

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

# And how close two solids have to be before they count as holding each other.
# A bolted joint with a slot nut and a washer in it, because the bolts are not
# modelled; small enough that a part standing in mid air still shows up.
CONTACT_MM = 2.5


# The assembly container carries a Shape of its own that is the union of
# everything inside it, so counting it as a solid makes it appear to collide
# with every part in the machine.
CONTAINERS = ("Assembly::AssemblyObject", "Assembly::JointGroup",
              "App::DocumentObjectGroup", "App::Part")


def solids(doc):
    """Every placed solid in a document, as (label, shape in machine space)."""
    out = []
    for obj in doc.Objects:
        if obj.TypeId in CONTAINERS:
            continue
        shape = getattr(obj, "Shape", None)
        if shape is None or not shape.Solids:
            continue
        if obj.TypeId == "App::Link":
            shape = obj.LinkedObject.Shape.copy()
            shape.Placement = obj.Placement.multiply(shape.Placement)
        out.append((obj.Label, shape))
    return out


def interference(doc, say, tolerance=CLASH_MM3, ignore=(), open_pairs=()):
    """Every pair of solids that shares more space than it should.

    `ignore` is pairs of label fragments that are allowed to touch -- a rod in
    its own clamp, say.  `open_pairs` is different and deliberately noisier:
    pairs that overlap because something about the real machine is not yet
    understood.  They are reported as OPEN every build and do not fail it, so
    they cannot quietly turn into furniture the way an ignored pair can.
    """
    placed = solids(doc)
    say(f"  {len(placed)} solids, {len(placed) * (len(placed) - 1) // 2} pairs")

    near = []
    for i, (label_a, a) in enumerate(placed):
        for label_b, b in placed[i + 1:]:
            box_a, box_b = a.BoundBox, b.BoundBox
            box_a.enlarge(-1e-6)
            if box_a.intersect(box_b):
                near.append((label_a, a, label_b, b))
    say(f"  {len(near)} pairs whose bounding boxes touch at all")

    def matches(label_a, label_b, pairs):
        return any(x in label_a and y in label_b
                   or x in label_b and y in label_a for x, y in pairs)

    clashes, opens = [], []
    for label_a, a, label_b, b in near:
        if matches(label_a, label_b, ignore):
            continue
        try:
            shared = a.common(b)
        except Exception:                      # a boolean that will not run
            say(f"  ? could not test {label_a} against {label_b}")
            continue
        if shared.Solids and shared.Volume > tolerance:
            where = opens if matches(label_a, label_b, open_pairs) else clashes
            where.append((label_a, label_b, shared.Volume))

    for label_a, label_b, volume in sorted(opens, key=lambda c: -c[2]):
        say(f"  OPEN  {label_a} into {label_b}: {volume:.1f} mm3")
    for label_a, label_b, volume in sorted(clashes, key=lambda c: -c[2]):
        say(f"  CLASH {label_a} into {label_b}: {volume:.1f} mm3")
    if not clashes:
        say(f"  ok: nothing overlaps by more than {tolerance} mm3, "
            f"{len(opens)} known-open pairs aside")
    return clashes


def connected(doc, say, reach=CONTACT_MM, adrift=()):
    """Nothing may float: every solid has to reach something else.

    This is the check that was missing, and it is the one that would have
    caught the Z axis.  `interference` can only ever say that two parts share
    space they should not; it is blind to a part that shares space with
    *nothing*, which is exactly what a machine that falls apart looks like.
    A bearing mount hanging 8 mm off the frame it is supposed to be bolted to
    passes every other check in this file.

    So: build a graph over every solid in the document, join two of them when
    they come within `reach`, and insist the whole machine is one piece.
    `reach` is a bolted joint's worth rather than nothing at all -- parts are
    held together by screws that are not modelled, and a washer or a slot nut
    is a couple of millimetres -- but it is small enough that a part with no
    neighbour at all cannot hide.
    """
    placed = solids(doc)
    boxes = []
    for _, shape in placed:
        box = shape.BoundBox
        box.enlarge(reach / 2.0)
        boxes.append(box)

    parent = list(range(len(placed)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    tested = 0
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            root_i, root_j = find(i), find(j)
            if root_i == root_j or not boxes[i].intersect(boxes[j]):
                continue
            tested += 1
            try:
                gap = placed[i][1].distToShape(placed[j][1])[0]
            except Exception:
                continue                       # a distance that will not run
            if gap <= reach:
                parent[root_i] = root_j

    groups = {}
    for i, (label, _) in enumerate(placed):
        groups.setdefault(find(i), []).append(label)

    def name(group):
        return (f"{len(group)} " + ", ".join(sorted(group)[:6])
                + (" ..." if len(group) > 6 else ""))

    excused, loose = [], []
    for group in sorted(groups.values(), key=len)[:-1]:
        (excused if all(any(a in label for a in adrift) for label in group)
         else loose).append(group)

    say(f"  {len(placed)} solids, {tested} pairs close enough to measure")
    for group in excused:
        say(f"  ADRIFT {name(group)} -- held by a part the repository "
            f"does not have")
    for group in loose:
        say(f"  LOOSE {name(group)} with nothing holding "
            f"{'them' if len(group) > 1 else 'it'}")
    if not loose:
        say(f"  ok: the machine is one piece -- every solid reaches another "
            f"within {reach} mm"
            + (f", {len(excused)} adrift aside" if excused else ""))
    return loose


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
