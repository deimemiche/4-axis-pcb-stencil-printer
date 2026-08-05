# Parametric reconstructions of the original author's parts

The original author published the printed parts as STL meshes only, so there is
nothing to edit: no sketches, no dimensions, no history. This directory rebuilds
them as FreeCAD **PartDesign** bodies driven by fully constrained sketches, so
any dimension can be changed by double clicking a sketch and typing a new
number.

Each part is a Python script that draws the body, and the `.FCStd` it produces.
The script is the source; the `.FCStd` is a build artefact that is committed so
the parts can be opened without running anything.

## Layout

```
fcprim.py        the helper library every part script is written against
stlmeasure.py    measures the original meshes: layers, outlines, bores
build.py         rebuilds part scripts and reports which ones failed
verify.py        point-samples a built solid against the mesh it came from
stlrender.py     draws a mesh, so a shape can be looked at rather than guessed
export.py        tessellates a built body back to STL, to render against the
                 original

bot/             bottom frame, X and Y axes, rail and rod holders
eccf/            the front eccenter (README calls the mechanism the "eccenter")
sr/              the slewing ring - the rotary alpha axis
top/             top frame, stencil clamp, Z axis
misc/            parts belonging to no one assembly - feet, adapters
plate/           the plates and angles, drawn from the author's own 2D drawings
asm/             the machine itself: the parts put together with real joints
asm/render/      four views of each assembly, drawn by asm/render.py
```

`plate/` is the odd group out. Everything else here is reconstructed from an
STL, because that is all the author published of the printed parts -- but the
aluminium was drawn properly, and `../../technical-drawings/` has those
drawings. So those parts are *transcribed* rather than reverse engineered, and
their check is arithmetic on the drawing's own dimensions rather than a
comparison against a mesh. A mistyped hole position fails the build.

`asm/` is the assembly, built with the Assembly workbench so the machine is held
together by joints and can be driven to any pose rather than frozen in one.
[`ASSEMBLY.md`](ASSEMBLY.md) is the plan and the progress against it.

Every group holds `<part-name>.py` next to the `<PART_NAME>.FCStd` it builds,
named after the STL in [`../`](../) it was reconstructed from.

**Next to it is not tidiness.** `fcprim.make` saves beside its own source, so a
script in one group and its document in another means every rebuild lands in
the wrong place and has to be copied over the right one. That copy is a
*different document*: a build regenerates the element map, so the topological
names any assembly stored - `Pad.;#6:1;:G;XTR;:H440:7,F.Face1` - no longer
resolve, and every joint made against a face or an edge of that part breaks.
Moving a built document is the same trap. This is what LCS datums are for, and
why the scripted assemblies in `asm/` use nothing else; see `fcprim.lcs`.

## Building

FreeCAD 1.1 is needed. With the flatpak:

```sh
alias fc='flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD'

fc cad/freecad/build.py                    # rebuild everything
fc cad/freecad/build.py eccf/eccf-bot.py   # rebuild one part
```

Run from the repository root. `build.py` exists because `freecadcmd` swallows
tracebacks - a script that raises simply prints nothing - so every build goes
through a wrapper that catches and prints them.

## Checking a reconstruction against the original

Two independent checks guard every part.

`build.py` compares the finished solid's volume against the mesh's. Agreement
to a few hundredths of a percent is the faceting error of the mesh's own curved
surfaces, and anything worse fails the build.

Matching volumes are good evidence but not proof, since material moved from one
place to another cancels out. That is not hypothetical: `ECCF_TOP`'s shoulders
were first drawn as plain rectangles because that is what a horizontal slice
through the middle of them looks like. They are really chamfered, and the
chamfer happens to have exactly the same volume as the rectangle - the build
check passed and the part was still wrong.

`verify.py` therefore classifies random points against both shapes -
`isInside` on the solid, ray casting on the mesh - and reports every
disagreement:

```sh
fc cad/freecad/verify.py cad/freecad/eccf/ECCF_BOT.FCStd cad/ECCF_BOT.stl
```

Points within 0.05 mm of a surface are excused, because there the mesh and the
true surface legitimately differ.

## Reading a mesh you want to reconstruct

`stlmeasure.py` runs under plain `python3` - no FreeCAD, no dependencies:

```sh
python3 cad/freecad/stlmeasure.py cad/BOT_RAIL_HOLDER.stl
python3 cad/freecad/stlmeasure.py cad/*.stl --summary
```

Measuring answers "what is there"; a picture answers "what is it". Arc fitting
cannot tell a fillet from a sweep from a draft, and a part whose outline is
nothing but tangent arcs is far quicker to read than to measure:

```sh
python3 cad/freecad/stlrender.py cad/ECCF_LEVER.stl          # four views
python3 cad/freecad/stlrender.py cad/A.stl cad/B.stl out.png # two, overlaid
```

Overlaying a reconstruction on its original is the quickest check there is that
a thread runs the right way round or a profile is not mirrored:

```sh
fc cad/freecad/export.py cad/freecad/sr/SR_WORM_GEAR.FCStd built.stl
python3 cad/freecad/stlrender.py cad/SR_WORM_GEAR.stl built.stl cmp.png
```

Printed parts are layered, so `stlmeasure.py` finds the axis a prism would
explain best,
finds the heights at which the cross section changes, and reports each layer's
outline with the arcs fitted back to centres and radii. It also lists every
cylindrical face about each axis, which is how cross drilled holes are found -
those never show up in the layers.

## Conventions

**Parts are modelled in their mesh's own coordinates.** Several of the STLs were
exported in assembly position rather than about a part origin - the ECCF and SR
groups stack around Y = 0 as they do in the machine. Keeping those coordinates
means the reconstruction can be compared to the mesh directly, and that the
assembly can place most parts without a transform.

**Y is up.** The original author's machine has Y vertical, so parts built along
their print axis are usually sketched on the XZ plane. Note that XZ pads towards
**-Y** while XY pads towards +Z and YZ towards +X; `fcprim.sketch` documents the
full mapping. A sketch normally sits on the part's top face with the pad running
down from it.

**Sketches come out fully constrained.** `fcprim.polyline` works out which
segments are horizontal or vertical, groups the coordinates those constraints
tie together, and adds exactly one dimension per remaining degree of freedom -
no redundancy, whatever mix of straight, slanted and arc segments a profile
uses. `build.py` warns about any sketch that ends up underdefined.

**A 45 degree break that adds material is a tapered pad, not a chamfer.**
`fcprim.pad` takes `taper=45.0`, which drafts the sides as the pad runs; draw
the profile at whichever end of the break is smaller. A `PartDesign::Chamfer`
can only take material away, and it also fails outright where the break has to
die out on a curved face. `STATUS.md` says which parts need which.

**A feature that fails is fatal.** `fcprim.finish` refuses to save if anything
came out `Invalid`, because FreeCAD's own behaviour is to report the throw to
the console, keep the last shape that worked, skip every later feature and hand
back a perfectly valid solid that is missing half the part.

**Constraints are named after what they drive**, so `leg_x1`, `bolt_y_u` and
`nut_across_corners` read sensibly in the Elements panel rather than appearing
as anonymous numbers.

## Notes on individual meshes

* `ECCF_LEVER.stl` contains **two separate shells** - it is a printing pair of
  two identical lever cheeks, not one part.
* `SR_WORM_GEAR.stl` is a helical gear. It is the one part a revolve cannot
  make, and `fcprim.helix` - `PartDesign::AdditiveHelix` - makes it from the
  same kind of fully constrained sketch as everything else.
* `TOP_CLAMP_BEARING_MOUNT_2.stl` is exactly `TOP_CLAMP_BEARING_MOUNT_1.stl`
  mirrored in Z, vertex for vertex. One part script covers both; the assembly
  mirrors it rather than a second body existing.

Several parts come in families, and finding the family is most of the work:

* `BOT_RAIL_HOLDER` and `TOP_RAIL_HOLDER` are the same collar drawn twice - a
  boss around the rail bore, a lobe around each bolt, a fillet rolling along the
  lobes' common tangent, a foot under each bolt. Only the bolt spacing differs,
  and that the bottom one's bore sits 1 mm off the bolt line.
* `BOT_ROD_HOLDER_ALPHA_AXIS`'s first 20 mm are
  `BOT_ROD_HOLDER_ALPHA_AXIS_SHORT` exactly; the rest is the barrel carrying on
  as a 1 degree cone.
* `TOP_CLAMP_SPANNER_CASE_1` and `_2` share an outline exactly.
* `TOP_CLAMP_NUT_HOLDER` and `TOP_CLAMP_SPANNER_COUNTER` share an X/Y footprint
  (X -11.4 .. 5, Y -14.8 .. 15.2) and the same side view - a spine, a block hung
  off it, and the gap between them - so the two run on the same rail.
* `BOT_BEARING_MOUNT_Y_AXIS_DRIVEN` and `BOT_RAIL_CLAMP_X_DRIVE` are hollowed
  from both faces over *identical* spans, with the same two hollow shapes. Once
  the first was drawn the second was mostly a matter of changing the eye's
  position.
* The three 8.2 mm rod clamps - `BOT_CLAMP_Z_AXIS`, `TOP_CLAMP_Z_AXIS` and
  `TOP_CLAMP_STOP` - are all a bore in a 16.2 mm boss with a saw cut and an M3
  pulling it shut.

All 39 meshes are rebuilt, and the 6 drawn parts alongside them, so `build.py`
comes back **45/45**. [`STATUS.md`](STATUS.md) carries the per-part table and
what each awkward one turned out to be; [`ASSEMBLY.md`](ASSEMBLY.md) is the plan
for putting them together into the machine, and how far it has got.
