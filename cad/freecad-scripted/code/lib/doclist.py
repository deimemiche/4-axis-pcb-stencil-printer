"""Which built documents there are, and in what order they must be handled.

Plain Python on purpose: `view.py` needs this from inside a FreeCAD GUI, and
`rebuild.py` needs the same list from the system interpreter to decide how many
processes to start.  Neither import of this module pulls in FreeCAD.
"""

import os

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root
ASSEMBLIES = os.path.join(HERE, "assembly")

# Assemblies that do not live in `assembly/`.  There are none now that the
# microscope has been shelved, but the ordering rule below still needs the hook.
ELSEWHERE = ()

# Folders not to walk into.  Michael's hand-built assembly lives in the frozen
# `../freecad/assembly/` tree and holds its parts together with **face and edge
# names** rather than with the LCS datums this tree uses; re-saving a document
# whose topological references have gone stale is how they get quietly rebound
# to the wrong edge.  It is not listed here because it cannot be reached: this
# walk starts at `HERE`, and `../freecad/` is not under it.  Naming one of those
# documents on the command line still works.
#
# Nothing may be excluded by the name "assembly" -- that is now *this* tree's
# own generated assembly folder, and skipping it would silently drop all ten
# machine documents from every walk.
KEEP_OUT = ("__pycache__",)


def is_assembly(path):
    """Whether `path` is one of the documents that links others.

    The distinction is not cosmetic: an assembly opens every part it links, so
    it is the only kind of document that can collide with one opened earlier.
    """
    return (os.path.dirname(os.path.abspath(path)) == ASSEMBLIES
            or os.path.basename(path) in ELSEWHERE)


def documents(argv=()):
    """Every built document, parts before the assemblies that link them.

    Order matters even though each document is saved on its own: a link
    remembers when the part it points at was last written, so re-saving a part
    after the assembly leaves the assembly complaining that its links are out
    of date every time it is opened.  They sort first alphabetically, which
    is exactly the wrong way round.

    A named path may point outside this tree, which is how the hand-built
    assembly in `../freecad/assembly/` gets dressed without this ever walking
    into it.
    """
    chosen = [a for a in argv if a.endswith(".FCStd")]
    if chosen:
        return [c if os.path.isabs(c) else os.path.join(HERE, c)
                for c in chosen]
    found = []
    for folder, subs, names in os.walk(HERE):
        subs[:] = [s for s in subs if s not in KEEP_OUT]
        found += [os.path.join(folder, n)
                  for n in names if n.endswith(".FCStd")]
    return sorted(found, key=lambda p: (is_assembly(p), p))


def undressed(paths):
    """Those of `paths` that carry no `GuiDocument.xml`, so open blank.

    The check the dress stage was missing.  A `.FCStd` is a zip, so this reads
    the answer straight off the disk without FreeCAD having to open anything --
    which means it stays true even if the run that was supposed to write the
    file died, hung, or was killed halfway.  That is exactly what happened: a
    deadlock on the third assembly left all ten of them undressed and the
    pipeline reported success.
    """
    import zipfile
    missing = []
    for path in paths:
        try:
            with zipfile.ZipFile(path) as z:
                if "GuiDocument.xml" not in z.namelist():
                    missing.append(path)
        except (OSError, zipfile.BadZipFile):
            missing.append(path)
    return missing
