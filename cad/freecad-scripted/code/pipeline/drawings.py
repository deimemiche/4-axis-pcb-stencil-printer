"""Draw the eight parts that are cut and drilled rather than printed.

    freecadcmd drawings.py                 # all eight
    freecadcmd drawings.py XY_PLATE        # just this one

A printed part needs no drawing: the STL is the drawing.  These eight are made
from stock -- three aluminium plates, four lengths of 20x20x2 angle and one
2020 extrusion that has to be drilled -- and somebody standing at a machine
needs numbers on paper for them.

The author published drawings for some of this, and they are kept in
[`../../technical-drawings/archive/`](../../technical-drawings/archive/).
They are not good enough: incomplete, and flat files with no model behind
them, so a change means redrawing rather than editing.  `STATUS.md` records
what that cost -- a stencil holder reconstructed faithfully from the sheets,
checked to a hundredth of a millimetre, and still the wrong part, because the
sheets did not describe the machine.  These are generated from the solids the
rest of this tree builds, so they cannot drift from the parts.

## Each drawing is its own document

`technical-drawings/XY_PLATE.FCStd` holds a page and an `App::Link` to the
part, rather than the page living inside `x-axis-carriage/XY_PLATE.FCStd`.
Both would be editable, but a page inside the part document means re-saving
every part whenever a drawing changes, and a link remembers when the thing it
points at was last written -- so that would leave all ten assemblies claiming
their links are out of date on every open.  Keeping the drawing downstream of
the part costs nothing and keeps that from happening.

## It runs headless

TechDraw projects, dimensions and writes DXF under `freecadcmd`, with no
display -- unlike [`view.py`](view.py), which needs one.  Only PDF export goes
through `TechDrawGui`, which a console FreeCAD will not load, so that is a
separate pass; see `rebuild.py`'s `drawings` stage.

## Every dimension is checked

A dimension put on a page by script is attached to an edge found by matching
coordinates, and a wrong match is a plausible-looking drawing with the wrong
number on it -- the exact failure the author's sheets already demonstrate.  So
each one is declared with the value it must show, read back with
`getRawValue()` after the recompute, and a mismatch fails the build.

## Four rules the first set of sheets broke

Michael read the first PDFs and found four things wrong with them.  They are
worth writing down, because each one is a rule the code now keeps rather than
a sheet that was patched.

*Nothing may overlap.*  A dimension is placed by an offset from the middle of
its view, and offsets worked out at the call site put `55,65` through `100`
and buried `213,72` inside a stack of hole positions.  So no builder below
computes an offset: it asks a `Ladder` for the next rung, and the ladders are
spaced for the size TechDraw actually prints.  The note block is placed under
whatever the ladders used, not at a fixed height.

*Symmetry is dimensioned as symmetry.*  A hole pattern that is symmetric about
a centreline is dimensioned across the pair -- `195,3` between two holes --
rather than from an edge to each of them, which is what turned four holes into
`4,15`, `30,85`, `226,15` and `252,85`.  The centrelines are drawn.  Where a
pattern is a bolt circle it is dimensioned as a bolt circle, and the code
checks the holes really are equally spaced on it before saying so.

*A hole table only where the holes will not fit.*  Eighty-three grid holes
earn a table; sixteen do not.  `ALPHA_TOP_PLATE` is the only sheet that gets
one.  The CSV of positions is still written beside every drawing, because it
costs nothing and a machine can read it.

*A hole is called out the way it is ordered.*  `24x M3`, not `DIA 2,5`: the
thread and the count belong in the callout, and the tapping drill belongs in
the notes.  A clearance hole gets `16x DIA 3,2` -- still the count, because
the count is what tells a reader whether the callout covers the pattern.
"""

import math
import os
import sys
import traceback

import FreeCAD as App
import TechDraw
from FreeCAD import Vector

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "technical-drawings"))
TEMPLATES = "/app/share/Mod/TechDraw/Templates/ISO"
TEMPLATE = "A3_Landscape_ISO5457_advanced.svg"

TOLERANCE = 1e-4          # a dimension must read its declared value to this
NEAR = 0.05               # how close a hole must be to the position claimed

# An A3 sheet is 420 x 297 mm and TechDraw measures a page from its bottom
# left corner, in millimetres.  Everything placed beyond that is simply not on
# the paper -- which is not an error anyone reports, it just silently is not
# there, as a first attempt at these sheets demonstrated by putting the hole
# summary at x=455 and the dimensions at y=300.  Hence named positions rather
# than numbers sprinkled through the builders.
#
# The template's frame leaves x from 28 to 392 and y from 22 to 278 usable,
# less the title block, which owns everything right of x=229 below y=76.
SHEET_W, SHEET_H = 420.0, 297.0
MAIN = (150.0, 205.0)     # the view the drawing is mostly about
SIDE = (335.0, 205.0)     # the thin edge view beside it, for a plate
FLAT = (150.0, 235.0)     # a length of angle seen on its flat leg ...
UPRIGHT = (150.0, 140.0)  # ... and again on its upright, under it
END = (335.0, 200.0)      # the section of a length of anything
NOTES_LEFT = 30.0         # the note block's left edge ...
NOTES_TOP = 62.0          # ... and the height of its first line, at most
NOTES_FLOOR = 24.0        # and the line below which it is off the paper
TABLE_LEFT, TABLE_TOP = 252.0, 278.0

# TechDraw prints a dimension at about 6 mm tall and a leader needs room, so
# parallel dimensions want 11 mm between them; 8 was what printed 55,65
# through 100.  FIRST keeps the innermost one off the outline it measures.
PITCH = 11.0
FIRST = 16.0
CALLOUT = 26.0            # from the side of a view to its diameter callouts

# An annotation is positioned by its middle, so placing one by its top left
# corner means knowing how big TechDraw will draw it.  Measured off an
# exported sheet: a line is 3.15 x TextSize apart at LineSpace 100, and a
# character is a bit over half of TextSize wide.  LineSpace sets the height
# of the box a line is drawn in as well as the gap between lines, so tighten
# it too far and the glyphs are cut off at the top -- 50 sliced the tops off
# every note on the first attempt at this.
LINE_PITCH = 3.15
CHAR_W = 0.58
LINE_SPACE = 90           # per cent; 100 is a very airy note


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


def scale_text(s):
    return f"{s:.0f} : 1" if s >= 1.0 else f"1 : {1.0 / s:.0f}"


# --------------------------------------------------------------- geometry

def circles(view):
    """Every circular edge of a projected view, as (index, x, y, diameter).

    The coordinates are the part's own, not the paper's: TechDraw scales a
    view when it draws it but reports its geometry full size.  A dimension's
    X and Y, on the other hand, are millimetres on the paper.  Everything
    below keeps those two frames apart -- geometry is found in part
    millimetres, dimensions are placed in paper millimetres.
    """
    out = []
    for i in range(2000):
        try:
            edge = view.getEdgeByIndex(i)
        except Exception:
            break
        curve = getattr(edge, "Curve", None)
        if curve is not None and "Circle" in type(curve).__name__:
            out.append((i, curve.Center.x, curve.Center.y, curve.Radius * 2.0))
    return out


def lines(view):
    """Every straight edge, as (index, (x1, y1), (x2, y2))."""
    out = []
    for i in range(2000):
        try:
            edge = view.getEdgeByIndex(i)
        except Exception:
            break
        curve = getattr(edge, "Curve", None)
        if curve is not None and "Line" in type(curve).__name__:
            a, b = edge.Vertexes[0].Point, edge.Vertexes[-1].Point
            out.append((i, (a.x, a.y), (b.x, b.y)))
    return out


def extreme_line(view, axis, side):
    """The outermost straight edge of the view: its left, right, top or bottom.

    `axis` is 'x' for the two vertical edges and 'y' for the two horizontal
    ones; `side` is -1 for the lower value and +1 for the higher.  Matching an
    outline edge by where it is rather than by its index is what keeps this
    working when a part is rebuilt and the edges come back renumbered.
    """
    best, best_at = None, None
    for i, a, b in lines(view):
        if axis == "x":
            if abs(a[0] - b[0]) > 1e-6:      # not vertical
                continue
            at = a[0]
        else:
            if abs(a[1] - b[1]) > 1e-6:      # not horizontal
                continue
            at = a[1]
        if best_at is None or (at > best_at if side > 0 else at < best_at):
            best, best_at = i, at
    if best is None:
        raise RuntimeError(f"no {axis}/{side} outline edge in {view.Name}")
    return best, best_at


def outline(view):
    """The view's four outline edges, where they sit, and how big it prints.

    `left`..`top` are edge indices and `left_at`..`top_at` are part
    millimetres; `pw` and `ph` are what the view measures on the paper, which
    is what the ladders need to clear it.
    """
    box = {}
    for axis, side, key in (("x", -1, "left"), ("x", 1, "right"),
                            ("y", -1, "bottom"), ("y", 1, "top")):
        box[key], box[key + "_at"] = extreme_line(view, axis, side)
    box["cx"] = (box["left_at"] + box["right_at"]) / 2.0
    box["cy"] = (box["bottom_at"] + box["top_at"]) / 2.0
    box["pw"] = (box["right_at"] - box["left_at"]) * view.Scale
    box["ph"] = (box["top_at"] - box["bottom_at"]) * view.Scale
    return box


def vertices(view):
    """Every vertex of a projected view, as (index, x, y)."""
    out = []
    for i in range(4000):
        try:
            v = view.getVertexByIndex(i)
        except Exception:
            break
        p = v.Point
        out.append((i, p.x, p.y))
    return out


def centre_vertex(view, x, y, tol=0.01):
    """The vertex TechDraw puts at a circle's centre.

    A dimension from an outline edge to a circle *edge* measures to where the
    circle comes nearest, not to the middle of it -- every hole position came
    out exactly one radius short until this was used instead.  TechDraw emits a
    centre vertex for each circle, and that is the thing to dimension to.
    """
    for i, vx, vy in vertices(view):
        if abs(vx - x) < tol and abs(vy - y) < tol:
            return i
    raise RuntimeError(f"no centre vertex at ({x:.3f}, {y:.3f}) "
                       f"in {view.Name}")


def hole_from(holes, box, axis, offset, view):
    """The hole sitting `offset` in from the view's left or bottom edge.

    Where several holes share that offset -- a column of them usually does --
    the one nearest the edge is taken, so the extension line the dimension
    draws is the short one.
    """
    key, other = (1, 2) if axis == "h" else (2, 1)
    base = box["left_at"] if axis == "h" else box["bottom_at"]
    near = [h for h in holes if abs(h[key] - (base + offset)) < NEAR]
    if not near:
        raise RuntimeError(f"{view.Name}: no hole {offset} from the "
                           f"{'left' if axis == 'h' else 'bottom'} edge")
    return min(near, key=lambda h: h[other])


def hole_pair(holes, box, axis, span, view):
    """The two holes a symmetric dimension runs between.

    A symmetric pattern is dimensioned across itself rather than from an edge,
    so this looks for the two holes sitting `span`/2 either side of the view's
    middle.  Of the pairs that fit it takes the one whose holes are level with
    each other, which is the pair a reader will see as a pair.
    """
    key, other = (1, 2) if axis == "h" else (2, 1)
    mid = box["cx"] if axis == "h" else box["cy"]
    lo = [h for h in holes if abs(h[key] - (mid - span / 2.0)) < NEAR]
    hi = [h for h in holes if abs(h[key] - (mid + span / 2.0)) < NEAR]
    if not lo or not hi:
        raise RuntimeError(f"{view.Name}: no hole pair {span} apart "
                           f"across the {'vertical' if axis == 'h' else 'horizontal'}"
                           f" centreline")
    return min(((a, b) for a in lo for b in hi),
               key=lambda p: (round(abs(p[0][other] - p[1][other]), 3),
                              p[0][other]))


def wall_edges(view, axis, thickness):
    """The two outline edges `thickness` apart: the section of one leg.

    An angle's wall is the gap between the outside of a leg and the inside of
    it, and both are ordinary outline edges -- so rather than name them, look
    for the outermost pair that measures what the stock is sold as.
    """
    seen = {}
    for i, a, b in lines(view):
        if axis == "h" and abs(a[0] - b[0]) < 1e-6:
            seen.setdefault(round(a[0], 3), i)
        if axis == "v" and abs(a[1] - b[1]) < 1e-6:
            seen.setdefault(round(a[1], 3), i)
    at = sorted(seen)
    for i, first in enumerate(at):
        for second in at[i + 1:]:
            if abs(second - first - thickness) < 1e-3:
                return seen[first], seen[second]
    raise RuntimeError(f"{view.Name}: no pair of edges {thickness} apart")


# ------------------------------------------------------------------ sheet

class Ladder:
    """Somewhere to hang a nest of parallel dimensions, each clear of the last.

    A dimension's X and Y are an offset from the middle of its view, in paper
    millimetres.  Working that offset out at the call site is how the first
    sheets came out with 55,65 printed through 100, so nothing below computes
    one: it asks a ladder for the next rung.  Rungs go outwards from the view,
    which is why callers add the smallest dimension first -- nested, the way a
    reader expects.
    """

    def __init__(self, sheet, view, side, clear, step=PITCH):
        self.sheet, self.view, self.side = sheet, view, side
        self.at, self.step, self.n = clear, step, 0

    def rung(self):
        d = self.at + self.n * self.step
        self.n += 1
        return {"below": (0.0, -d), "above": (0.0, d),
                "left": (-d, 0.0), "right": (d, 0.0)}[self.side]

    def add(self, kind, refs, value, label):
        return self.sheet.dim(self.view, kind, refs, self.rung(), value, label)


class Sheet:
    """One drawing: a page, its views, its dimensions and its notes."""

    def __init__(self, doc, page, name):
        self.doc, self.page, self.name = doc, page, name
        self.checks = []                      # (dimension, expected, label)
        self.floor = SHEET_H                  # lowest thing on the left half

    def view(self, source, label, direction, xdirection, at, scale):
        v = self.doc.addObject("TechDraw::DrawViewPart", label)
        v.Source = [source]
        self.page.addView(v)
        v.Direction = Vector(*direction)
        v.XDirection = Vector(*xdirection)
        v.Scale = scale
        v.ScaleType = "Custom"
        v.X, v.Y = at
        v.Label = label
        self.doc.recompute()
        return v

    def dim(self, view, kind, refs, at, expect, label=None, text=None):
        """One dimension, declared with the value it must come out at.

        `at` is an offset from the middle of `view`, not a place on the page.
        A dimension is a child of the view it measures and TechDraw positions
        it in the view's own frame; passing page coordinates put every one of
        them off the top of the sheet, which the numbers could not catch
        because the numbers were right -- they were just not on the paper.

        `text` replaces what is printed, for a callout that has to read `24x
        M3` rather than a diameter.  It cannot lie: the value is still read
        back off the geometry and checked.
        """
        d = self.doc.addObject("TechDraw::DrawViewDimension",
                               f"d{len(self.checks):03}")
        d.Type = kind
        d.References2D = [(view, r) for r in refs]
        self.page.addView(d)
        d.X, d.Y = at
        if text:
            d.FormatSpec = text
            d.Arbitrary = "%" not in text
        if label:
            d.Label = label
        self.checks.append((d, expect, label or f"{kind} {refs}"))
        # `view.X` is a Quantity, not a number, and adding a float to one is
        # a unit mismatch rather than an answer.
        if float(view.X) + at[0] < 240.0:     # clear of the title block
            self.floor = min(self.floor, float(view.Y) + at[1])
        return d

    def callouts(self, view, threads, at, step=PITCH):
        """One diameter dimension per size of hole, saying how many there are.

        The count comes from the view, not from the notes, so a hole added to
        the part is a hole added to the callout.  A tapped hole is called out
        by its thread, because that is what the person at the machine has to
        pick a tap for; the drill that goes before it belongs in the notes.

        Holes are counted by where they are, not by how many circles they
        project as.  Drilling across a 2020 extrusion cuts two outer walls and
        the core, which is one hole and three circular edges -- and the sheet
        said `3x DIA 5,4` until this counted positions instead.
        """
        by_d = {}
        for i, x, y, d in circles(view):
            by_d.setdefault(round(d, 2), {}).setdefault(
                (round(x, 2), round(y, 2)), (i, x, y))
        x, y = at
        for n, (d, at_) in enumerate(sorted(by_d.items())):
            group = list(at_.values())
            # The leader runs from the hole to the label, so calling out
            # whichever hole happens to be first drags a line right across the
            # part.  Take the one nearest the top right corner instead.
            i = max(group, key=lambda h: h[1] + h[2])[0]
            thread = threads.get(d)
            text = (f"{len(group)}x {thread}" if thread
                    else f"{len(group)}x ⌀%.1w")
            self.dim(view, "Diameter", [f"Edge{i}"], (x, y - n * step), d,
                     f"{len(group)} x {thread or d}", text)

    def centrelines(self, view, box, axes):
        """The centrelines a symmetric part is dimensioned about.

        Cosmetic edges are appended after the projected ones, so these go on
        last: anything that counts circles or looks for an outline edge has to
        run before a centreline turns up in the middle of the list.
        """
        over = 6.0 / view.Scale                    # a little past the outline
        for axis in axes:
            if axis == "h":                        # the vertical centreline
                a = Vector(box["cx"], box["bottom_at"] - over, 0)
                b = Vector(box["cx"], box["top_at"] + over, 0)
            else:
                a = Vector(box["left_at"] - over, box["cy"], 0)
                b = Vector(box["right_at"] + over, box["cy"], 0)
            self.dash(view, view.makeCosmeticLine(a, b))
        self.doc.recompute()

    def bolt_circle(self, view, box, radius, at):
        """The circle a ring of holes sits on, drawn and dimensioned.

        `check_ring` has already satisfied itself that the holes are equally
        spaced on this radius, so what is drawn here is the pattern the note
        claims, not a circle of the right size that happens to pass near some
        holes.
        """
        tag = view.makeCosmeticCircle(Vector(box["cx"], box["cy"], 0), radius)
        self.dash(view, tag)
        self.doc.recompute()
        i = next(j for j, cx, cy, d in circles(view)
                 if abs(d - radius * 2.0) < 1e-6)
        return self.dim(view, "Diameter", [f"Edge{i}"], at, radius * 2.0,
                        f"bolt circle {radius * 2.0}", "⌀%.1w B.C.")

    def dash(self, view, tag):
        """Chain-dash a cosmetic edge, the way a centreline is drawn."""
        edge = view.getCosmeticEdge(tag)
        try:
            edge.Format = {"style": 4, "weight": 0.25,
                           "color": (0.0, 0.0, 0.0, 1.0), "visible": True}
        except Exception:
            pass                              # dashed will do if it will not

    def note(self, text, left, top, size=3.0):
        """A block of text placed by its top left corner.

        TechDraw positions an annotation by its middle, which is why the first
        sheets ran their notes off the left of the frame: the block was
        centred on a point 45 mm from the edge and was 100 mm wide.  So the
        size it will print at is worked out here and the middle derived from
        it.
        """
        lines_ = text if isinstance(text, list) else [text]
        a = self.doc.addObject("TechDraw::DrawViewAnnotation",
                               f"note{len(self.page.Views):03}")
        a.Text = lines_
        self.page.addView(a)
        a.TextSize = size
        a.LineSpace = LINE_SPACE
        a.MaxWidth = -1
        pitch = size * LINE_PITCH * LINE_SPACE / 100.0
        a.X = left + size * CHAR_W * max(len(l) for l in lines_) / 2.0
        a.Y = top - pitch * (len(lines_) - 1) / 2.0
        if top - pitch * (len(lines_) - 1) < NOTES_FLOOR:
            raise RuntimeError(f"{self.name}: {len(lines_)} lines of note "
                               f"starting at y={top:.0f} run off the bottom "
                               f"of the sheet -- say it in fewer")
        return a

    def centred(self, text, x, y, size=3.0):
        """One line of text, middled on a point: what a view is a view of."""
        return self.note([text], x - size * CHAR_W * len(text) / 2.0, y, size)

    def verify(self):
        """Read every dimension back.  A wrong reference is caught here."""
        self.doc.recompute()
        bad = []
        for d, expect, label in self.checks:
            got = d.getRawValue()
            if abs(got - expect) > TOLERANCE:
                bad.append(f"      {label}: reads {got:.4f}, "
                           f"should be {expect:.4f}")
        if bad:
            raise RuntimeError(f"{self.name}: {len(bad)} dimension(s) wrong:\n"
                               + "\n".join(bad))
        return len(self.checks)


def check_ring(view, box, ring):
    """Make sure a ring of holes is the bolt circle the sheet will call it.

    A note saying `5 x DIA 10 equally spaced on a DIA 150.9 bolt circle` is a
    dimension in prose, and prose is not read back off the model by
    `Sheet.verify`.  So it is checked here instead: the right number of holes,
    all of the right size, all on the radius, all a whole step apart.  A
    pattern that has drifted fails the build rather than being described
    wrongly on paper.
    """
    on = []
    for i, x, y, d in circles(view):
        r = math.hypot(x - box["cx"], y - box["cy"])
        if abs(r - ring["radius"]) < NEAR and abs(d - ring["hole"]) < NEAR:
            on.append(math.degrees(math.atan2(y - box["cy"], x - box["cx"])))
    if len(on) != ring["count"]:
        raise RuntimeError(f"{view.Name}: {len(on)} holes of DIA {ring['hole']} "
                           f"on the DIA {ring['radius'] * 2} circle, "
                           f"not {ring['count']}")
    step = 360.0 / ring["count"]
    for a in sorted(on):
        off = (a - ring["at"]) % step
        if min(off, step - off) > 0.01:
            raise RuntimeError(f"{view.Name}: a hole at {a:.3f} deg is not on "
                               f"the {step:.0f} deg pattern from {ring['at']}")
    return len(on)


def positions(sheet, view, box, plan, axis, ladder):
    """Every declared hole dimension on one axis, innermost first.

    Three ways of saying where a hole is, and the order they come out in is
    the order of the numbers themselves, so the nest reads outwards:

    `spans`   across a symmetric pair -- the whole point of the rewrite
    `froms`   from the left or bottom edge, where a pattern is not symmetric
    `pitches` between two neighbours, for a grid too big to dimension whole
    """
    holes = circles(view)
    edge = f"Edge{box['left'] if axis == 'h' else box['bottom']}"
    want = []
    for span in plan.get("spans", {}).get(axis, []):
        a, b = hole_pair(holes, box, axis, span, view)
        want.append((span, [f"Vertex{centre_vertex(view, a[1], a[2])}",
                            f"Vertex{centre_vertex(view, b[1], b[2])}"],
                     f"span {span}"))
    for off in plan.get("froms", {}).get(axis, []):
        h = hole_from(holes, box, axis, off, view)
        want.append((off, [edge, f"Vertex{centre_vertex(view, h[1], h[2])}"],
                     f"from the edge {off}"))
    for first, second in plan.get("pitches", {}).get(axis, []):
        a = hole_from(holes, box, axis, first, view)
        b = hole_from(holes, box, axis, second, view)
        want.append((second - first,
                     [f"Vertex{centre_vertex(view, a[1], a[2])}",
                      f"Vertex{centre_vertex(view, b[1], b[2])}"],
                     f"pitch {second - first}"))
    kind = "DistanceX" if axis == "h" else "DistanceY"
    for value, refs, label in sorted(want):
        ladder.add(kind, refs, value, label)
    return len(want)


# ------------------------------------------------------------- the plates

def draw_plate(sheet, link, spec):
    """A flat plate: face on, an edge view for the thickness, holes called out.

    The plates lie in XZ with their thickness up Y, so the face view looks
    along -Y and the edge view along +X.  Both keep Z up the page, so a hole
    that is high on one is high on the other.
    """
    s = spec["scale"]
    face = sheet.view(link, "Face", (0, -1, 0), (1, 0, 0), MAIN, s)
    edge = sheet.view(link, "Edge", (1, 0, 0), (0, 1, 0), SIDE, s)
    box, ebox = outline(face), outline(edge)
    w, h, t = spec["size"]

    below = Ladder(sheet, face, "below", box["ph"] / 2.0 + FIRST)
    left = Ladder(sheet, face, "left", box["pw"] / 2.0 + FIRST)
    positions(sheet, face, box, spec, "h", below)
    positions(sheet, face, box, spec, "v", left)
    below.add("DistanceX", [f"Edge{box['left']}", f"Edge{box['right']}"],
              w, f"overall {w}")
    left.add("DistanceY", [f"Edge{box['bottom']}", f"Edge{box['top']}"],
             h, f"overall {h}")

    sheet.dim(edge, "DistanceX", [f"Edge{ebox['left']}", f"Edge{ebox['right']}"],
              (0.0, -ebox["ph"] / 2.0 - FIRST), t, f"thickness {t}")
    sheet.centred("EDGE VIEW", SIDE[0], SIDE[1] + ebox["ph"] / 2.0 + 8.0)

    sheet.callouts(face, spec.get("threads", {}),
                   (box["pw"] / 2.0 + CALLOUT, box["ph"] / 2.0))

    # A ring of holes is dimensioned as a ring: the circle they sit on, drawn
    # and measured, and a note saying how many and how far apart.  Their
    # positions are then nobody's business -- which is what takes ten leader
    # lines off the two rotation table plates.
    # Out to the right, and one ring well below the next.  TechDraw runs a
    # diameter dimension's line from the circle through its centre to the
    # text and turns the text to match, so two rings called out side by side
    # print their labels on top of each other, and a ring called out straight
    # up prints its label vertically off the top of the sheet.  Both
    # happened.  Different heights on the same side give each one its own
    # angle, which is what keeps them apart.
    for n, ring in enumerate(spec.get("rings", [])):
        found = check_ring(face, box, ring)
        sheet.bolt_circle(face, box, ring["radius"],
                          (box["pw"] / 2.0 + CALLOUT, -15.0 - n * 28.0))
        say(f"      {found} holes checked onto the DIA "
            f"{ring['radius'] * 2:.1f} bolt circle")
    sheet.centrelines(face, box, spec.get("mirror", ""))
    return face


# -------------------------------------------------------------- the angles

def draw_angle(sheet, link, spec):
    """A length of 20x20x2 angle: the flat leg, the upright, and the section.

    These lie along X with the section in YZ.  The flat leg is drilled through
    its thickness, so those holes are round seen from above; the upright's are
    round seen from the front.  Two views rather than one because a hole shows
    as a hole in exactly one of them, and the end view carries the section.
    """
    s = spec["scale"]
    length, leg, wall = spec["size"]

    flat = sheet.view(link, "Flat", (0, 0, 1), (1, 0, 0), FLAT, s)
    fbox = outline(flat)
    below = Ladder(sheet, flat, "below", fbox["ph"] / 2.0 + FIRST)
    left = Ladder(sheet, flat, "left", fbox["pw"] / 2.0 + FIRST)
    positions(sheet, flat, fbox, spec["flat"], "h", below)
    positions(sheet, flat, fbox, spec["flat"], "v", left)
    below.add("DistanceX", [f"Edge{fbox['left']}", f"Edge{fbox['right']}"],
              length, f"length {length}")
    sheet.callouts(flat, {}, (fbox["pw"] / 2.0 + CALLOUT, fbox["ph"] / 2.0))
    sheet.centred("THE FLAT LEG, FROM ABOVE", FLAT[0],
                  FLAT[1] + fbox["ph"] / 2.0 + 8.0)
    sheet.centrelines(flat, fbox, "h")

    if spec.get("upright"):
        up = sheet.view(link, "Upright", (0, -1, 0), (1, 0, 0), UPRIGHT, s)
        ubox = outline(up)
        ubelow = Ladder(sheet, up, "below", ubox["ph"] / 2.0 + FIRST)
        uleft = Ladder(sheet, up, "left", ubox["pw"] / 2.0 + FIRST)
        positions(sheet, up, ubox, spec["upright"], "h", ubelow)
        positions(sheet, up, ubox, spec["upright"], "v", uleft)
        sheet.callouts(up, {}, (ubox["pw"] / 2.0 + CALLOUT, ubox["ph"] / 2.0))
        sheet.centred("THE UPRIGHT, FROM THE FRONT", UPRIGHT[0],
                      UPRIGHT[1] + ubox["ph"] / 2.0 + 8.0)
        sheet.centrelines(up, ubox, "h")

    end = sheet.view(link, "End", (1, 0, 0), (0, 1, 0), END, 2.0)
    ebox = outline(end)
    a, b = wall_edges(end, "h", wall)
    sheet.dim(end, "DistanceX", [f"Edge{a}", f"Edge{b}"],
              (0.0, ebox["ph"] / 2.0 + FIRST), wall, f"wall {wall}")
    sheet.dim(end, "DistanceX", [f"Edge{ebox['left']}", f"Edge{ebox['right']}"],
              (0.0, -ebox["ph"] / 2.0 - FIRST), leg, f"leg {leg}")
    sheet.dim(end, "DistanceY", [f"Edge{ebox['bottom']}", f"Edge{ebox['top']}"],
              (-ebox["pw"] / 2.0 - FIRST, 0.0), leg, f"leg {leg}")
    sheet.centred(f"END VIEW   {scale_text(2.0)}", END[0],
                  END[1] - ebox["ph"] / 2.0 - FIRST - PITCH)
    return flat


# ----------------------------------------------------------- the extrusion

def draw_extrusion(sheet, link, spec):
    """The one drilled 2020: outside and the cross hole, and nothing else.

    Michael's brief exactly -- the extrusion is bought, and all the drawing has
    to say is where to put the hole in it.  The T-slot profile is drawn because
    it projects, but it is not dimensioned: nobody is machining it.
    """
    s = spec["scale"]
    length, side = spec["size"]

    # The stick runs along Z, and a 300 long part lies down on an A3 rather
    # than standing up it, so the front view takes Z across the page.
    front = sheet.view(link, "Front", (0, -1, 0), (0, 0, 1), UPRIGHT, s)
    box = outline(front)
    below = Ladder(sheet, front, "below", box["ph"] / 2.0 + FIRST)
    positions(sheet, front, box, spec, "h", below)
    below.add("DistanceX", [f"Edge{box['left']}", f"Edge{box['right']}"],
              length, f"length {length}")
    # The one hole is at mid length, so its callout goes up and to the right
    # of it rather than out past the end of a 150 mm long view: a leader that
    # crosses half the part to reach the margin says nothing on the way.
    sheet.callouts(front, {}, (25.0, box["ph"] / 2.0 + 25.0))
    sheet.centrelines(front, box, "h")

    end = sheet.view(link, "End", (0, 0, 1), (1, 0, 0), END, 2.0)
    ebox = outline(end)
    sheet.dim(end, "DistanceX", [f"Edge{ebox['left']}", f"Edge{ebox['right']}"],
              (0.0, -ebox["ph"] / 2.0 - FIRST), side, f"section {side}")
    sheet.dim(end, "DistanceY", [f"Edge{ebox['bottom']}", f"Edge{ebox['top']}"],
              (-ebox["pw"] / 2.0 - FIRST, 0.0), side, f"section {side}")
    sheet.centred(f"END VIEW   {scale_text(2.0)}", END[0],
                  END[1] - ebox["ph"] / 2.0 - FIRST - PITCH)
    return front


# ------------------------------------------------------------- what to draw
#
# A spec says what the part is made of and which dimensions the sheet carries.
# The positions are all offsets within a view -- a `span` is measured across
# the middle of it, a `from` in from its left or bottom edge -- because that
# is what a reader measures, and because it means no spec has to know where
# the part sits in the machine's coordinates.  Every one of them is looked up
# against the solid, so a spec that no longer matches the part fails loudly
# rather than printing a number nothing has.

SPECS = {
    "XY_PLATE": dict(
        folder="x-axis-carriage", kind="plate",
        material="Aluminium, 2 mm sheet", scale=0.5, size=(257.0, 162.0, 2.0),
        # Sixteen holes on a rectangle, symmetric both ways: four dimensions
        # say all of it, where sixteen from two edges said it in numbers like
        # 4,15 that no one would set a machine to.
        mirror="hv",
        spans=dict(h=[195.3, 248.7], v=[118.0, 152.0]),
        table=False,
        notes=["2 mm aluminium sheet, cut 257 x 162",
               "16 x DIA 3.2 through, clearance for M3",
               "symmetrical about both centrelines",
               "the sixteen are the corners of two rectangles on that",
               "centre: 195.3 x 152 and 248.7 x 118"]),

    "ALPHA_BOT_PLATE": dict(
        folder="rotation-table", kind="plate",
        material="Aluminium, 6 mm plate", scale=0.5, size=(200.0, 200.0, 6.0),
        # Symmetric top to bottom and not side to side, so the rows are
        # dimensioned across the centreline and the columns from the left
        # edge.  The two rings are dimensioned as rings.
        mirror="v",
        spans=dict(v=[104.0, 140.0, 168.0, 192.0]),
        froms=dict(h=[6.3, 18.0, 26.6, 47.0, 153.0, 182.0]),
        rings=[dict(radius=61.0, hole=2.5, count=4, at=0.0),
               dict(radius=75.45, hole=10.0, count=5, at=0.0)],
        threads={2.5: "M3"},
        table=False,
        notes=["6 mm aluminium plate, cut 200 x 200",
               "symmetrical about the horizontal centreline only",
               "4 x M3 on the DIA 122 bolt circle, at 0/90/180/270 deg",
               "5 x DIA 10 worm clearance, equally spaced on DIA 150.9",
               "24 x M3 mounting in the six columns; tapping drill DIA 2.5"]),

    "ALPHA_TOP_PLATE": dict(
        folder="rotation-table", kind="plate",
        material="Aluminium, 6 mm plate", scale=0.5, size=(240.0, 200.0, 6.0),
        # Eighty-three grid holes are the one pattern on the machine that
        # earns a table.  The sheet dimensions the grid's extent and its
        # pitch; the table carries the positions.
        mirror="hv",
        spans=dict(h=[210.0, 180.0], v=[150.0, 120.0]),
        pitches=dict(h=[(15.0, 30.0)], v=[(25.0, 55.0)]),
        rings=[dict(radius=75.45, hole=3.5, count=5, at=0.0)],
        table=True,
        notes=["6 mm aluminium plate, cut 240 x 200",
               "symmetrical about both centrelines",
               "83 x DIA 3.5 workholding grid: columns every 15, rows",
               "every 30, alternate columns offset by 15 -- see the table",
               "5 x DIA 3.5 equally spaced on the DIA 150.9 bolt circle"]),

    "STENCIL_HOLDER_BACK": dict(
        folder="stencil-clamp", kind="angle",
        material="Aluminium angle 20 x 20 x 2", scale=0.5,
        size=(213.72, 20.0, 2.0),
        flat=dict(spans=dict(h=[50.0, 150.0, 206.22]),
                  froms=dict(v=[6.4, 8.0, 15.6])),
        upright=dict(spans=dict(h=[206.22]), froms=dict(v=[15.64])),
        table=False,
        notes=["aluminium angle 20 x 20 x 2, cut 213.72 long",
               "symmetrical about mid length",
               "4 x DIA 3.4 through the flat leg, 50 and 150 apart",
               "at each end 2 x DIA 3.4 through the flat leg and one",
               "through the upright -- no hole at mid length, the BACK hand"]),

    "STENCIL_HOLDER_FRONT": dict(
        folder="stencil-clamp", kind="angle",
        material="Aluminium angle 20 x 20 x 2", scale=0.5,
        size=(213.72, 20.0, 2.0),
        flat=dict(spans=dict(h=[50.0, 150.0, 206.22]),
                  froms=dict(v=[6.4, 8.0, 15.6])),
        upright=dict(spans=dict(h=[206.22]),
                     froms=dict(h=[106.86], v=[11.5, 15.64])),
        table=False,
        notes=["aluminium angle 20 x 20 x 2, cut 213.72 long",
               "symmetrical about mid length",
               "4 x DIA 3.4 through the flat leg, 50 and 150 apart",
               "at each end 2 x DIA 3.4 through the flat leg and one",
               "through the upright; 1 x DIA 5.4 at mid length, FRONT hand"]),

    "STENCIL_HOLDER_BACK_2": dict(
        folder="stencil-clamp", kind="angle",
        material="Aluminium angle 20 x 20 x 2", scale=0.5,
        size=(198.0, 20.0, 2.0),
        flat=dict(spans=dict(h=[50.0, 150.0]), froms=dict(v=[10.0])),
        upright=None,                 # nothing goes through it, so no view
        table=False,
        notes=["aluminium angle 20 x 20 x 2, cut 198 long",
               "symmetrical about mid length",
               "4 x DIA 3.4 through the flat leg, 50 and 150 apart",
               "the short angle that closes on STENCIL_HOLDER_BACK",
               "nothing goes through the upright -- the BACK hand"]),

    "STENCIL_HOLDER_FRONT_2": dict(
        folder="stencil-clamp", kind="angle",
        material="Aluminium angle 20 x 20 x 2", scale=0.5,
        size=(198.0, 20.0, 2.0),
        flat=dict(spans=dict(h=[50.0, 150.0]), froms=dict(v=[10.0])),
        upright=dict(froms=dict(h=[99.0], v=[11.5])),
        table=False,
        notes=["aluminium angle 20 x 20 x 2, cut 198 long",
               "symmetrical about mid length",
               "4 x DIA 3.4 through the flat leg, 50 and 150 apart",
               "the short angle that closes on STENCIL_HOLDER_FRONT",
               "1 x DIA 5.4 through the upright at mid length, FRONT hand"]),

    "2020_300_TOP_FRONT": dict(
        folder="stock", kind="extrusion",
        material="Aluminium extrusion 2020, 300 long", scale=0.5,
        size=(300.0, 20.0),
        froms=dict(h=[150.0]),
        table=False,
        notes=["bought 2020 extrusion, 300 long -- one hole is machined",
               "1 x DIA 5.4 across, on the stick's axis, at mid length",
               "the T-slot profile and its DIA 4.2 core are drawn but not",
               "dimensioned: nobody is cutting them",
               "this is the ONE 300 that is drilled: the lid's front rail"]),
}


def holes_of(link):
    """Every hole in the part, read off the solid rather than off the script.

    A cylindrical face is a hole; its axis says which way it was drilled and
    its centre says where.  Taking this from the shape means the table
    describes what the part *is*, not what the script meant to build -- which
    is the whole complaint about the author's sheets.
    """
    seen = {}
    for f in link.LinkedObject.Shape.Faces:
        s = f.Surface
        if type(s).__name__ != "Cylinder":
            continue
        axis = (abs(round(s.Axis.x, 2)), abs(round(s.Axis.y, 2)),
                abs(round(s.Axis.z, 2)))
        c = s.Center
        seen.setdefault((round(s.Radius * 2, 2), axis), set()).add(
            (round(c.x, 3), round(c.y, 3), round(c.z, 3)))
    return seen


def hole_table(name, link):
    """The positions as a CSV, and a summary for the one sheet that wants it.

    Eighty-three grid holes will not fit on an A3 next to the view, and
    TechDraw's answer to an oversized annotation is to shrink it until it is
    unreadable.  So `ALPHA_TOP_PLATE` carries the counts on the sheet and the
    file carries the positions.  The other seven have few enough holes to
    dimension outright, and a table beside a dimensioned pattern is two
    answers to one question -- so they get the file and no table.
    """
    seen = holes_of(link)
    csv = ["diameter_mm,axis_x,axis_y,axis_z,x_mm,y_mm,z_mm"]
    summary = ["HOLE SUMMARY", ""]
    for (d, axis), where in sorted(seen.items()):
        summary.append(f"{len(where):3} x DIA {d:.2f}  drilled along "
                       f"{'xyz'[axis.index(max(axis))].upper()}")
        for x, y, z in sorted(where):
            csv.append(f"{d:.2f},{axis[0]},{axis[1]},{axis[2]},{x},{y},{z}")
    total = sum(len(w) for w in seen.values())
    summary += ["", f"{total} holes in all; every position",
                f"is in {name}-holes.csv,", "beside this drawing."]

    path = os.path.join(OUT, name + "-holes.csv")
    with open(path, "w") as fh:
        fh.write("\n".join(csv) + "\n")
    return summary, total


def titleblock(doc, page, name, spec, note):
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tmpl.Template = os.path.join(TEMPLATES, TEMPLATE)
    page.Template = tmpl
    texts = dict(tmpl.EditableTexts)
    for key, value in (("title", name), ("drawing_number", name),
                       ("part_material", spec["material"]),
                       ("scale", scale_text(spec["scale"])),
                       ("document_type", "Component Drawing"),
                       ("document_status", note),
                       ("general_tolerances", "ISO 2768-m"),
                       ("responsible_department", ""),
                       ("creator", "generated by drawings.py"),
                       ("approval_person", ""),
                       ("supplementary_title_1", ""),
                       ("supplementary_title_2", ""),
                       ("revision_index", ""), ("sheet_number", "1 / 1")):
        if key in texts:
            texts[key] = value
    tmpl.EditableTexts = texts
    return tmpl


def link_to(doc, folder, name):
    src = App.openDocument(os.path.join(HERE, folder, name + ".FCStd"))
    body = next(o for o in src.Objects if o.TypeId == "PartDesign::Body")
    link = doc.addObject("App::Link", "PART")
    link.LinkedObject = body
    link.Label = name
    doc.recompute()
    return link, src


BUILDERS = {"plate": draw_plate, "angle": draw_angle,
            "extrusion": draw_extrusion}


def build(name):
    """One drawing document, checked, saved, and written out as DXF."""
    spec = SPECS[name]
    doc = App.newDocument(name)
    path = os.path.join(OUT, name + ".FCStd")
    doc.saveAs(path)                      # an external link needs a saved owner

    link, src = link_to(doc, spec["folder"], name)
    page = doc.addObject("TechDraw::DrawPage", "Page")
    titleblock(doc, page, name, spec, "generated -- edit drawings.py")
    doc.recompute()

    sheet = Sheet(doc, page, name)
    BUILDERS[spec["kind"]](sheet, link, spec)

    # The notes go under whatever the dimensions used rather than at a fixed
    # height: ALPHA_BOT_PLATE's six columns hang far enough down the sheet
    # that a note block at the usual place printed through them.
    summary, total = hole_table(name, link)
    sheet.note(spec["notes"], NOTES_LEFT,
               min(NOTES_TOP, sheet.floor - PITCH), 3.0)
    if spec["table"]:
        sheet.note(summary, TABLE_LEFT, TABLE_TOP, 2.6)

    checked = sheet.verify()
    doc.recompute()
    doc.save()

    dxf = os.path.join(OUT, name + ".dxf")
    TechDraw.writeDXFPage(page, dxf)
    say(f"  {name}: {checked} dimensions checked, {total} holes "
        f"{'tabled' if spec['table'] else 'in the CSV'}, "
        f"-> {os.path.basename(dxf)}")
    return doc, src


def main(argv):
    names = [a for a in argv if a in SPECS] or list(SPECS)
    os.makedirs(OUT, exist_ok=True)
    failed = []
    for name in names:
        try:
            build(name)
        except BaseException:
            failed.append(name)
            say(f"  {name}: FAILED\n{traceback.format_exc()}")
        for open_name in list(App.listDocuments()):
            App.closeDocument(open_name)
    say(f"\n{len(names) - len(failed)}/{len(names)} drawn")
    for name in failed:
        say(f"  FAILED {name}")
    return 1 if failed else 0


STATUS = main([a for a in sys.argv[1:]])
