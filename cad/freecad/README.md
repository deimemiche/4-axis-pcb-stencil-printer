# Michael's hand-built assembly, and the parts it links

This tree is **frozen**. It holds the nine assembly documents Michael built by
hand in the Assembly workbench, and the 59 part documents they link to, and
nothing else.

```
assembly/            the nine documents
stock/               bought or cut to length, never printed
bottom-frame/  rotation-table/  x-axis-carriage/  eccentric-clamp/
top-frame/  top-assembly/  stencil-clamp/        one folder per sub-assembly
shared/              the two printed parts more than one sub-assembly uses
```

## Why there are no scripts here

The joints in `assembly/` attach to faces, edges and vertices named by OCC's
topological numbering — `Face12`, `Edge52`. Rebuild a part and that numbering
can shift, and the joint does not complain: it silently attaches to whatever now
carries the number.

So the parts these documents depend on must never be rebuilt. There is no
`fcprim.py` here, no `build.py`, no part scripts — **nothing in this tree can
rebuild anything**, which is the guarantee stated as a fact about the filesystem
rather than as a rule someone has to remember.

The scripts, and the work of rebuilding the assembly from Python, are next door
in [`../freecad-scripted/`](../freecad-scripted/). See its `ASSEMBLY_SCRIPT.md`.

## Never open both trees in one FreeCAD session

`../freecad-scripted/` holds part documents with the **same internal names** as
these — both trees have an `ECCF_MOUNT`. FreeCAD resolves links by path but
identifies open documents by name, so opening both at once gets you
`ECCF_MOUNT001` and links that point somewhere you did not intend.

Open one tree or the other.

## Viewing these

`view.py` lives in the other tree and will not walk into `assembly/`, but it
takes a named path, so from `../freecad-scripted/`:

```
flatpak run --filesystem=home --env=QT_QPA_PLATFORM=offscreen \
    org.freecad.FreeCAD view.py ../freecad/assembly/Top_Frame.FCStd
```
