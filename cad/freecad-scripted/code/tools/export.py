"""Tessellate a built body back to STL, so it can be looked at or diffed.

    freecadcmd cad/freecad-scripted/code/tools/export.py \
        cad/freecad-scripted/rotation-table/SR_WORM_GEAR.FCStd out.stl

Written for `stlrender.py`: rendering the reconstruction over the original in
two colours shows up a wrong handedness, a mirrored profile or a phase error at
a glance, where a volume figure only says "about right".
"""
import struct
import sys

import FreeCAD as App


def main():
    args = [a for a in sys.argv[1:] if not a.endswith("export.py")]
    fcstd = next(a for a in args if a.endswith(".FCStd"))
    out = next((a for a in args if a.endswith(".stl")),
               fcstd[:-len(".FCStd")] + "-built.stl")
    tolerance = float(next((a.split("=", 1)[1] for a in args
                            if a.startswith("tolerance=")), 0.05))

    doc = App.openDocument(fcstd)
    shape = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"][0].Shape
    points, facets = shape.tessellate(tolerance)

    with open(out, "wb") as handle:
        handle.write(b"\0" * 80 + struct.pack("<I", len(facets)))
        for facet in facets:
            tri = [points[i] for i in facet]
            handle.write(struct.pack("<3f", 0.0, 0.0, 0.0))
            for p in tri:
                handle.write(struct.pack("<3f", p.x, p.y, p.z))
            handle.write(b"\0\0")
    print(f"{out}: {len(facets)} facets")
    sys.stdout.flush()


main()
