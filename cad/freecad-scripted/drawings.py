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
"""

import math
import os
import sys
import traceback

import FreeCAD as App
import TechDraw
from FreeCAD import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "technical-drawings"))
TEMPLATES = "/app/share/Mod/TechDraw/Templates/ISO"

TOLERANCE = 1e-4          # a dimension must read its declared value to this

# An A3 sheet is 420 x 297 mm and TechDraw measures a page from its bottom
# left corner, in millimetres.  Everything placed beyond that is simply not on
# the paper -- which is not an error anyone reports, it just silently is not
# there, as a first attempt at these sheets demonstrated by putting the hole
# summary at x=455 and the dimensions at y=300.  Hence named positions rather
# than numbers sprinkled through the builders.
SHEET_W, SHEET_H = 420.0, 297.0
MAIN = (150.0, 180.0)     # the view the drawing is mostly about
SIDE = (340.0, 180.0)     # the thin edge or end view beside it
UNDER = (330.0, 110.0)    # a third view under that one
NOTES = (82.0, 58.0)      # bottom left; an annotation is CENTRED here
SUMMARY = (330.0, 262.0)  # top right; also centred on its point


def say(*a):
    os.write(1, (" ".join(str(x) for x in a) + "\n").encode())


# --------------------------------------------------------------- geometry

def circles(view):
    """Every circular edge of a projected view, as (index, x, y, diameter)."""
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
    return best


def hole_at(view, x, y, tol=0.05):
    """The circular edge whose centre is at (x, y)."""
    for i, cx, cy, d in circles(view):
        if abs(cx - x) < tol and abs(cy - y) < tol:
            return i
    raise RuntimeError(f"no hole at ({x}, {y}) in {view.Name}")


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


# ------------------------------------------------------------------ sheet

class Sheet:
    """One drawing: a page, its views, its dimensions and its notes."""

    def __init__(self, doc, page, name):
        self.doc, self.page, self.name = doc, page, name
        self.checks = []                      # (dimension, expected)

    def view(self, source, label, direction, xdirection, at, scale=1.0):
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

    def dim(self, view, kind, refs, at, expect, label=None):
        """One dimension, declared with the value it must come out at.

        `at` is an offset from the middle of `view`, not a place on the page.
        A dimension is a child of the view it measures and TechDraw positions
        it in the view's own frame; passing page coordinates put every one of
        them off the top of the sheet, which the numbers could not catch
        because the numbers were right -- they were just not on the paper.
        """
        d = self.doc.addObject("TechDraw::DrawViewDimension",
                               f"d{len(self.checks):03}")
        d.Type = kind
        d.References2D = [(view, r) for r in refs]
        self.page.addView(d)
        d.X, d.Y = at
        if label:
            d.Label = label
        self.checks.append((d, expect, label or f"{kind} {refs}"))
        return d

    def note(self, text, at, size=3.0):
        a = self.doc.addObject("TechDraw::DrawViewAnnotation",
                               f"note{len(self.page.Views):03}")
        a.Text = text if isinstance(text, list) else [text]
        self.page.addView(a)
        a.X, a.Y = at
        a.TextSize = size
        a.MaxWidth = -1
        return a

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


def titleblock(doc, page, template, name, material, sheet_size, note):
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tmpl.Template = os.path.join(TEMPLATES, template)
    page.Template = tmpl
    texts = dict(tmpl.EditableTexts)
    for key, value in (("title", name), ("drawing_number", name),
                       ("part_material", material), ("scale", sheet_size),
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


def new_sheet(name, template, material, note):
    """A drawing document holding a link to the part and an empty page."""
    doc = App.newDocument(name)
    doc.saveAs(os.path.join(OUT, name + ".FCStd"))   # a link needs a saved owner
    return doc


def link_to(doc, folder, name):
    src = App.openDocument(os.path.join(HERE, folder, name + ".FCStd"))
    body = next(o for o in src.Objects if o.TypeId == "PartDesign::Body")
    link = doc.addObject("App::Link", "PART")
    link.LinkedObject = body
    link.Label = name
    doc.recompute()
    return link, src


def outline(view):
    """The view's four outline edges and where they sit, in view coordinates.

    A view is centred on its own projection, so model coordinates are not view
    coordinates.  Everything below is therefore placed as an offset from an
    outline edge, which is true in either frame.
    """
    box = {}
    for axis, side, key in (("x", -1, "left"), ("x", 1, "right"),
                            ("y", -1, "bottom"), ("y", 1, "top")):
        i = extreme_line(view, axis, side)
        a, b = next((p, q) for j, p, q in lines(view) if j == i)
        box[key] = i
        box[key + "_at"] = a[0] if axis == "x" else a[1]
    return box


# ------------------------------------------------------------- the plates

def draw_plate(sheet, link, spec):
    """A flat plate: face on, an edge view for the thickness, holes called out.

    The plates lie in XZ with their thickness up Y, so the face view looks
    along -Y and the edge view along +X.
    """
    face = sheet.view(link, "Face", (0, -1, 0), (1, 0, 0), MAIN, spec["scale"])
    edge = sheet.view(link, "Edge", (1, 0, 0), (0, 1, 0), SIDE, spec["scale"])

    box = outline(face)
    ebox = outline(edge)
    w, h, t = spec["size"]
    s = spec["scale"]
    half_w, half_h = w * s / 2.0, h * s / 2.0

    sheet.dim(face, "DistanceX", [f"Edge{box['left']}", f"Edge{box['right']}"],
              (0, -half_h - 14), w, f"overall {w}")
    sheet.dim(face, "DistanceY", [f"Edge{box['bottom']}", f"Edge{box['top']}"],
              (-half_w - 14, 0), h, f"overall {h}")
    sheet.dim(edge, "DistanceX", [f"Edge{ebox['left']}", f"Edge{ebox['right']}"],
              (0, -half_h - 12), t, f"thickness {t}")

    # Holes, by family.  `called` are dimensioned on the face where a reader
    # has to see how they differ from the pattern; the pattern itself is left
    # to the table, because eighty-three leader lines is not a drawing.
    found = circles(face)
    by_d = {}
    for i, x, y, d in found:
        by_d.setdefault(round(d, 3), []).append((i, x, y))

    for n, (d, group) in enumerate(sorted(by_d.items())):
        # The callout leader runs from the hole to the label, so calling out
        # whichever hole happens to be first drags a line right across the
        # part.  Take the one nearest the top right corner instead.
        i = max(group, key=lambda h: h[1] + h[2])[0]
        sheet.dim(face, "Diameter", [f"Edge{i}"],
                  (half_w + 24, half_h - n * 9), d, f"hole d{d}")

    # A view is centred on its own projection, so a circle's view coordinates
    # are not the model's -- but its offset from an outline edge is the same in
    # both, which is what turns one back into the other.
    x0, y0 = box["left_at"], box["bottom_at"]
    ox, oy = spec["origin"]
    called = spec.get("called")
    if called:
        picked = [(cx, cy, ox + cx - x0, oy + cy - y0, d)
                  for i, cx, cy, d in found if called(ox + cx - x0,
                                                      oy + cy - y0, d)]
        # One dimension per *distinct* position, not one per hole.  Sixteen
        # holes on a four by four pattern are four x values and four y values,
        # and drawing thirty-two parallel dimensions to say that is how the
        # first attempt at this sheet became unreadable.
        seen_x, seen_y, nx, ny = {}, {}, 0, 0
        # The dedup key is rounded; the value checked against is not.  A bolt
        # circle puts holes at r*cos(72 deg) and the like, so rounding the
        # expectation to three places and then checking it to four is a test
        # that fails on arithmetic rather than on anything being wrong.
        for cx, cy, mx, my, d in sorted(picked, key=lambda h: h[2]):
            value = mx - ox
            key = round(value, 3)
            if key in seen_x:
                continue
            seen_x[key] = True
            v = centre_vertex(face, cx, cy)
            sheet.dim(face, "DistanceX", [f"Edge{box['left']}", f"Vertex{v}"],
                      (0, -half_h - 26 - nx * 8), value,
                      f"x{nx} = {key}")
            nx += 1
        for cx, cy, mx, my, d in sorted(picked, key=lambda h: h[3]):
            value = my - oy
            key = round(value, 3)
            if key in seen_y:
                continue
            seen_y[key] = True
            v = centre_vertex(face, cx, cy)
            sheet.dim(face, "DistanceY", [f"Edge{box['bottom']}", f"Vertex{v}"],
                      (-half_w - 26 - ny * 8, 0), value,
                      f"y{ny} = {key}")
            ny += 1
        say(f"      {len(picked)} hole(s) called out as {nx} x and {ny} y")
    return face


# -------------------------------------------------------------- the angles

def draw_angle(sheet, link, spec):
    """A length of 20x20x2 angle: the flat leg, the upright, and the section.

    These lie along X with the section in YZ.  The row holes go down through
    the horizontal leg (axis Z) and are seen from above; the mount and middle
    holes go through the upright (axis Y) and are seen from the front.
    """
    top = sheet.view(link, "Top", (0, 0, 1), (1, 0, 0), MAIN,
                     spec["scale"])
    front = sheet.view(link, "Front", (0, -1, 0), (1, 0, 0), (MAIN[0], MAIN[1] - 70),
                       spec["scale"])
    end = sheet.view(link, "End", (-1, 0, 0), (0, 1, 0), SIDE, 2.0)

    tbox, fbox, ebox = outline(top), outline(front), outline(end)
    length, leg, wall = spec["size"]

    sheet.dim(top, "DistanceX", [f"Edge{tbox['left']}", f"Edge{tbox['right']}"],
              (0, 26), length, f"length {length}")
    sheet.dim(end, "DistanceX", [f"Edge{ebox['left']}", f"Edge{ebox['right']}"],
              (0, -30), leg, f"leg {leg}")
    sheet.dim(end, "DistanceY", [f"Edge{ebox['bottom']}", f"Edge{ebox['top']}"],
              (-32, 0), leg, f"leg {leg}")

    for view, box in ((top, tbox), (front, fbox)):
        seen = set()
        for i, x, y, d in circles(view):
            if round(d, 3) in seen:
                continue
            seen.add(round(d, 3))
            sheet.dim(view, "Diameter", [f"Edge{i}"],
                      (60, 20 + 9 * len(seen)), d,
                      f"{view.Label} hole d{d}")

    # The row of four through the flat leg, dimensioned from the left end.
    x0 = tbox["left_at"]
    for n, mx in enumerate(spec.get("row_x", [])):
        vx = x0 + (mx - spec["origin"][0])
        cy = next(cc for j, c, cc, d in circles(top) if abs(c - vx) < 0.05)
        v = centre_vertex(top, vx, cy)
        sheet.dim(top, "DistanceX", [f"Edge{tbox['left']}", f"Vertex{v}"],
                  (0, 34 + n * 8), mx - spec["origin"][0], f"row{n}")
    return top


# ----------------------------------------------------------- the extrusion

def draw_extrusion(sheet, link, spec):
    """The one drilled 2020: outside and the cross hole, and nothing else.

    Michael's brief exactly -- the extrusion is bought, and all the drawing has
    to say is where to put the hole in it.  The T-slot profile is drawn because
    it projects, but it is not dimensioned: nobody is machining it.
    """
    front = sheet.view(link, "Front", (0, -1, 0), (1, 0, 0), MAIN,
                       spec["scale"])
    end = sheet.view(link, "End", (0, 0, -1), (1, 0, 0), SIDE, 2.0)

    fbox, ebox = outline(front), outline(end)
    length, side = spec["size"]

    sheet.dim(front, "DistanceY", [f"Edge{fbox['bottom']}", f"Edge{fbox['top']}"],
              (-34, 0), length, f"length {length}")
    sheet.dim(end, "DistanceX", [f"Edge{ebox['left']}", f"Edge{ebox['right']}"],
              (0, -28), side, f"section {side}")
    sheet.dim(end, "DistanceY", [f"Edge{ebox['bottom']}", f"Edge{ebox['top']}"],
              (-30, 0), side, f"section {side}")

    # The stretcher hole: its diameter, and how far up the stick it is.
    hx, hy, hd = spec["cross"]
    vy = fbox["bottom_at"] + (hy - spec["origin"][1])
    i = next(j for j, cx, cy, d in circles(front)
             if abs(cy - vy) < 0.05 and abs(round(d, 3) - hd) < 0.05)
    sheet.dim(front, "Diameter", [f"Edge{i}"], (46, 30), hd, "cross hole")
    cx = next(c for j, c, cc, d in circles(front)
              if abs(cc - vy) < 0.05 and abs(round(d, 3) - hd) < 0.05)
    v = centre_vertex(front, cx, vy)
    sheet.dim(front, "DistanceY", [f"Edge{fbox['bottom']}", f"Vertex{v}"],
              (28, -20), hy - spec["origin"][1], "cross hole height")
    return front


# ------------------------------------------------------------- what to draw

def on_bolt_circle(radius, tol=0.05):
    return lambda x, y, d: abs(math.hypot(x, y) - radius) < tol


SPECS = {
    "XY_PLATE": dict(
        folder="x-axis-carriage", kind="plate", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium, 2 mm sheet", scale=0.5, size=(257.0, 162.0, 2.0),
        origin=(-128.5, -81.0),
        # All sixteen: four X positions by four Z, and the reader needs every
        # one of them, so all sixteen are called out rather than tabled.
        called=lambda x, y, d: True,
        notes=["16 x DIA 3.2 THROUGH",
               "x = +/-97.65 and +/-124.35, z = +/-59 and +/-76",
               "material 2 mm aluminium sheet"]),

    "ALPHA_BOT_PLATE": dict(
        folder="rotation-table", kind="plate", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium, 6 mm plate", scale=0.5, size=(200.0, 200.0, 6.0),
        origin=(-100.0, -100.0),
        # The two circles that matter: the four that hold the ring down, and
        # the five the worm reaches through.  The 24 tapped mounting holes sit
        # in clusters and go in the table.
        called=lambda x, y, d: (abs(math.hypot(x, y) - 61.0) < 0.05
                                or abs(math.hypot(x, y) - 75.45) < 0.05),
        notes=["4 x M3 on a DIA 122 bolt circle, at 0/90/180/270 deg",
               "5 x DIA 10 worm clearance on a DIA 150.9 bolt circle",
               "24 x M3 mounting, in clusters -- see table",
               "M3 holes are tapping size DIA 2.5"]),

    "ALPHA_TOP_PLATE": dict(
        folder="rotation-table", kind="plate", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium, 6 mm plate", scale=0.5, size=(240.0, 200.0, 6.0),
        origin=(-120.0, -100.0),
        # The five on the bolt circle are dimensioned so a reader can see how
        # they differ from the workholding grid; the grid's 83 are tabled.
        called=on_bolt_circle(75.45),
        notes=["5 x DIA 3.5 on a DIA 150.9 bolt circle, at 0 and +/-72 and +/-144 deg",
               "83 x DIA 3.5 workholding grid -- see table",
               "grid pitch 15 in x, 30 in z, alternate columns offset 15"]),

    "STENCIL_HOLDER_BACK": dict(
        folder="stencil-clamp", kind="angle", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium angle 20 x 20 x 2", scale=0.7,
        size=(213.72, 20.0, 2.0), origin=(-106.86, 0.0),
        row_x=(-75.0, -25.0, 25.0, 75.0),
        notes=["angle 20 x 20 x 2, length 213.72",
               "4 x DIA 3.4 in the flat leg, at x = +/-25 and +/-75",
               "mount holes at x = +/-103.11 through both legs",
               "no middle hole -- this is the BACK hand"]),

    "STENCIL_HOLDER_FRONT": dict(
        folder="stencil-clamp", kind="angle", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium angle 20 x 20 x 2", scale=0.7,
        size=(213.72, 20.0, 2.0), origin=(-106.86, 0.0),
        row_x=(-75.0, -25.0, 25.0, 75.0),
        notes=["angle 20 x 20 x 2, length 213.72",
               "4 x DIA 3.4 in the flat leg, at x = +/-25 and +/-75",
               "mount holes at x = +/-103.11 through both legs",
               "1 x DIA 5.4 through the upright at mid length -- the FRONT hand"]),

    "STENCIL_HOLDER_BACK_2": dict(
        folder="stencil-clamp", kind="angle", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium angle 20 x 20 x 2", scale=0.7,
        size=(198.0, 20.0, 2.0), origin=(-99.0, 0.0),
        row_x=(-75.0, -25.0, 25.0, 75.0),
        notes=["angle 20 x 20 x 2, length 198",
               "4 x DIA 3.4 in the flat leg, at x = +/-25 and +/-75",
               "the short angle that closes on STENCIL_HOLDER_BACK",
               "no middle hole -- this is the BACK hand"]),

    "STENCIL_HOLDER_FRONT_2": dict(
        folder="stencil-clamp", kind="angle", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium angle 20 x 20 x 2", scale=0.7,
        size=(198.0, 20.0, 2.0), origin=(-99.0, 0.0),
        row_x=(-75.0, -25.0, 25.0, 75.0),
        notes=["angle 20 x 20 x 2, length 198",
               "4 x DIA 3.4 in the flat leg, at x = +/-25 and +/-75",
               "the short angle that closes on STENCIL_HOLDER_FRONT",
               "1 x DIA 5.4 through the upright at mid length -- the FRONT hand"]),

    "2020_300_TOP_FRONT": dict(
        folder="stock", kind="extrusion", template="A3_Landscape_ISO5457_advanced.svg",
        material="Aluminium extrusion 2020, 300 long", scale=0.5,
        size=(300.0, 20.0), origin=(-10.0, 0.0), cross=(0.0, 150.0, 5.4),
        notes=["bought 2020 extrusion, 300 long -- only the cross hole is machined",
               "1 x DIA 5.4 through, on the stick's axis, at 150 of 300",
               "the T-slot profile is shown but not dimensioned",
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
    """A summary for the sheet, and the full table as a CSV beside it.

    Eighty-three grid holes will not fit on an A3 next to the view, and
    TechDraw's answer to an oversized annotation is to shrink it until it is
    unreadable.  So the sheet carries the counts and the file carries the
    positions -- which is the more useful shape anyway, since a CSV can be
    read straight into whatever drives the machine.
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
    summary += ["", f"{total} holes in all.",
                f"Every position is in {name}-holes.csv,",
                "beside this drawing."]

    path = os.path.join(OUT, name + "-holes.csv")
    with open(path, "w") as fh:
        fh.write("\n".join(csv) + "\n")
    return summary, total


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
    titleblock(doc, page, spec["template"], name, spec["material"],
               f"1 : {1 / spec['scale']:.0f}" if spec["scale"] != 1.0 else "1 : 1",
               "generated -- edit drawings.py")
    doc.recompute()

    sheet = Sheet(doc, page, name)
    BUILDERS[spec["kind"]](sheet, link, spec)
    sheet.note(spec["notes"], NOTES, 3.2)
    summary, total = hole_table(name, link)
    sheet.note(summary, SUMMARY, 2.6)

    checked = sheet.verify()
    doc.recompute()
    doc.save()

    dxf = os.path.join(OUT, name + ".dxf")
    TechDraw.writeDXFPage(page, dxf)
    say(f"  {name}: {checked} dimensions checked, {total} holes tabled, "
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
