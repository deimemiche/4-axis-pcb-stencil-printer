"""What kind of thing a part in an assembly is.

Pure Python on purpose: `asmbuild.py` uses this to put each object in a
group as it builds, and `bom.py` uses the same call to count them
afterwards.  Two copies of a classifier is two answers to the same
question, and this tree has already paid for that once with the bolts.
Nothing here imports FreeCAD -- it only reads attributes off whatever it
is handed.
"""

import os


# The five families Michael sorts an assembly into, in the order he lists
# them.  His own trees drifted -- `Printed_parts` in six documents but
# `3D_parts` in `Bottom_Frame`, `CNC_parts` in two but `CNC` in
# `Stencil_Clamp` -- so the scripted build settles on one spelling of each.
GROUPS = ("Printed_parts", "CNC_parts", "Norm_parts", "COTS", "Assemblies")


def category(obj):
    """Which of `GROUPS` an object in a built assembly belongs to.

    Derived, not listed.  A name list is what this tree keeps learning not to
    trust, and there is a real distinction underneath to read instead:

    * a fastener is a `Part::FeaturePython` the Fasteners workbench made;
    * a sub-assembly comes in as an `Assembly::AssemblyLink`;
    * everything else is a link to a part, and that part already says what it
      is made of, in the `PartMaterial` `fcprim.material` gave it.

    Printed against machined against bought is the one that needs care, since
    a plate and an extrusion are both aluminium.  What separates them is not
    the material but who shaped it: **everything in `stock/` is bought**, cut
    or drilled to length at most, and everything in a sub-assembly folder is
    made here.  So `ALPHA_TOP_PLATE` in `rotation-table/` is CNC work and
    `2020_300` in `stock/` is a bought extrusion, which is exactly how
    Michael's own trees have them.
    """
    if obj.TypeId == "Part::FeaturePython":
        return "Norm_parts"
    if obj.TypeId == "Assembly::AssemblyLink":
        return "Assemblies"
    target = getattr(obj, "LinkedObject", None)
    if target is None:
        return None
    if getattr(target, "PartMaterial", None) == "printed":
        return "Printed_parts"
    source = getattr(target.Document, "FileName", "") or ""
    if os.path.basename(os.path.dirname(source)) == "stock":
        return "COTS"
    return "CNC_parts"
