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
view.py          gives the built .FCStd the view data a GUI needs to show it
verify.py        point-samples a built solid against the mesh it came from
stlrender.py     draws a mesh, so a shape can be looked at rather than guessed
export.py        tessellates a built body back to STL, to render against the
                 original

bot/             bottom frame, X and Y axes, rail and rod holders, the mod's
                 Z bracket, and the bought rod and LM8UU
eccf/            the front eccenter (README calls the mechanism the "eccenter")
sr/              the slewing ring - the rotary alpha axis
top/             top frame, stencil clamp, Z axis
misc/            parts belonging to no one assembly - feet, adapters - and the
                 stock several of them share: 2020 extrusion, M5 studding, the
                 alpha axis's ball bearing
plate/           the plates and angles, drawn from the author's own 2D drawings
mod/             Michael's own parts, transcribed from his CadQuery source
asm/             the machine itself: the parts put together with real joints
asm/render/      four views of each assembly, drawn by asm/render.py
```

`plate/` is the odd group out. Everything else here is reconstructed from an
STL, because that is all the author published of the printed parts -- but the
aluminium was drawn properly, and `../../technical-drawings/` has those
drawings. So those parts are *transcribed* rather than reverse engineered, and
their check is arithmetic on the drawing's own dimensions rather than a
comparison against a mesh. A mistyped hole position fails the build.

`mod/` is the other odd one out, and for the same reason as `plate/`: its parts
belong to the linear Z axis mod in the [repository's
README](../../README.md), they already exist as parametric CadQuery in
[`../z-axis.py`](../z-axis.py), and they are transcribed from it rather than
measured off anything. The mod's **Z bracket** is transcribed the same way but
is not in `mod/`: it bolts to a corner of the bottom frame, so it is a `bot/`
part, and because it is chiral it is two documents --
[`bot/bot-z-axis-bracket.py`](bot/bot-z-axis-bracket.py) builds
`BOT_Z_AXIS_BRACKET` and `BOT_Z_AXIS_BRACKET_MIRRORED`, one for each corner.

The **hinge locks** of [`../hinge-lock.py`](../hinge-lock.py) are there too,
and they, like the bracket, are checked harder: CadQuery can be installed and
run, so their volumes are held against that source's own solids with its
cosmetic chamfers suppressed, and they agree exactly. The bracket goes further
and is booleaned against that solid, which leaves nothing on either side.

`asm/` is the assembly, built with the Assembly workbench so the machine is held
together by joints and can be driven to any pose rather than frozen in one. It
covers all eighteen of the build manual's steps, as **Michael's** machine rather
than the author's original -- the linear Z axis and the workholding top plate
are in it. [`ASSEMBLY.md`](ASSEMBLY.md) is the plan and the progress against it.

The top frame is a **lid**: a hinge bar carried on the two Z rods, and the
stencil frame hinged off it so it swings up to put a board in. Any of the pose's
numbers can be given on the command line, so

```
... asm/machine.py lid=60
```

builds it open, as `MachineOpen.FCStd`, and checks it in that pose too.

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

The exceptions are the **bought stock**, which was never printed and so was
never an STL. The rod and the bearing live in `bot/` with the rest of the
frame; the extrusion and the studding belong to no one assembly - they are cut
for several at once - and so are in `misc/`:

| script | documents | what |
|---|---|---|
| [`misc/2020-extrusion.py`](misc/2020-extrusion.py) | `2020_300` `2020_280` `2020_300_TOP_FRONT` | 20 x 20 T-slot extrusion |
| [`bot/rod-d8.py`](bot/rod-d8.py) | `ROD_D8_300` `ROD_D8_280` `ROD_D8_244` `ROD_D8_140` | 8 mm ground linear rod |
| [`bot/lm8uu.py`](bot/lm8uu.py) | `LM8UU` | 8 mm linear ball bearing |
| [`misc/m5-threaded-rod.py`](misc/m5-threaded-rod.py) | `M5_270` | M5 threaded rod, the three drive screws and the stretcher |
| [`misc/m8-threaded-rod.py`](misc/m8-threaded-rod.py) | `M8_55` | M8 threaded rod, the four eccenter rods |
| [`misc/tube-d8.py`](misc/tube-d8.py) | `TUBE_D8_170` | drawn aluminium tube, 8 x 1 mm |
| [`top/hinge-40.py`](top/hinge-40.py) | `HINGE_40_LEAF` | 40 mm butt hinge - one leaf, and two make the hinge |
| [`misc/bearing-14x5x5.py`](misc/bearing-14x5x5.py) | `BEARING_14X5X5` | 605 ball bearing, 14 x 5 x 5, four on the alpha axis |
| [`misc/spring.py`](misc/spring.py) | `SPRING_ID6_L30_AT12` `SPRING_ID10_L35_AT20` | compression springs, 6 and 10 mm bore - each drawn at the length it is squashed to |

One script, a document per size: a stick of extrusion or of rod is nothing but
its section and how far it runs, so the length is the only parameter that
varies and adding one is adding a number. The LM8UU and the ball bearing come
in one size each and so have a document each.

`2020_300_TOP_FRONT` is the exception, and a document rather than a length: it
is a 300 with a 5.4 mm hole across it at mid length, for the M5 rod of the
stencil stretcher to pass through the lid's front rail. Six of the seven 300s
are plain, so the drilled one cannot share their document.

The M5 studding is the other way round - the manual buys three of one size - so
`M5_270` is a single document holding a body per stick, each named after the job
it does: `M5_270_WORM_SHAFT` turns the alpha axis, `M5_270_X_SCREW` and
`M5_270_Y_SCREW` drive the carriage. Michael has added a fourth,
`M5_100_Stencil_Stretcher`, so the document now holds a length its own name does
not cover - one of the renames its script's **Left to do** lists. They stand
20 mm apart along X, which is document layout rather than geometry. The M8 is
back to a document per length: its four sticks are interchangeable, and all four
are the eccenter rods.

The **M8 is also the one that carries its thread** - a real ISO 60 degree
profile swept along a helix, cut square at both ends the way a hacksaw leaves
it. Everything else here is drawn plain at its nominal major diameter, and the
reason is length: M5 x 270 is 337 turns of swept profile per stick, to show a
surface that never leaves a printed nut or a clearance hole, while the same
thread over 55 mm is 44 turns and this is the rod you take hold of and turn to
level the machine.

The plain ones are the same solids `asm/stock.py` builds for the assembly --
each agrees with it to **zero volume** -- drawn as sketches and pads instead of
booleans so they can be opened and edited like everything else here. Their
checks are arithmetic rather than a mesh comparison: a rod is `pi/4 d^2 L`, and
the extrusion's section is held against the 196 mm2 a real 20 x 20 slot 6
profile is catalogued at, which is what catches a lost rib or a slot the polar
pattern dropped. The threaded rod is checked the same way, off a section area
it works out from the thread profile: a screw sweep has the same cross section
at every height, so a stick cut square at both ends is exactly that area times
its length, with no end effects to allow for.

Every document is **saved already looking right**: the solids visible, the
sketches, datum planes and origins that drew them hidden, and the camera aimed
at the part so it is on screen the moment the file opens. That takes two
things. `fcprim.dress` sets `Visibility`, which is an App level property and so
works with no GUI at all - but a document saved headless carries no
`GuiDocument.xml`, and a GUI opening one builds its view providers from scratch
and hides every single one of them, whatever `Visibility` says. `view.py`
writes that file. Without it a part opens as an empty 3D view over a greyed out
tree, which is exactly what it looked like until it did.

Getting `Visibility` right is subtler than it sounds, and it was wrong
underneath the missing `GuiDocument.xml` for as long as that hid it. A
PartDesign body defaults to `DisplayModeBody = 'Through'`, and in that mode the
body draws *nothing of its own*: what is on screen is whichever of its children
are visible, which has to be the tip. Hiding every feature inside the body -
the tip with them - leaves a body that is visible and empty, so `view.py`
frames a scene with nothing in it and the part still opens blank. `dress` keeps
the tip visible and hides only the features behind it. `view.py` then asserts
it, per document, before saving: it parks the camera somewhere no fit could
return, calls `fitAll`, and fails the document if the camera did not move,
because an empty scene is exactly what leaves it standing still.

### Materials

Every part says what it is made of, so that a machine on screen reads as one:

| what | what it gets | how it looks |
|---|---|---|
| **3D printed** | FreeCAD's `Default` card, its diffuse colour set to **`#FF7800`** | orange, shininess 0.9 |
| **Bought steel** - studding, ground rod, LM8UU, ball bearings, the hinge | the `Steel` card, `4b849c55-6b3a-4f75-a055-40c0d0324596` | near black, shininess 0.06 - the card carries no diffuse colour at all |
| **Aluminium** - the plates, the 2020 extrusion, the 8 mm tube | the `Aluminum-6061-T6` card, `68b152b2-fd5e-4f10-8db0-1a2df3fe0fda` | `#4D4D4D`, shininess 0.09 |

The orange is Michael's own colour and not a FreeCAD default: this install's
`DefaultShapeColor` is `#727980`, which is the grey a body comes up in when
nobody has said otherwise.

`fcprim.make` takes `made_of=`, and it defaults to `fcprim.PRINTED` because all
but a dozen of these parts are. The dozen that are not say so:

```python
fcprim.make(__file__, "LM8UU", lm8uu, ..., made_of=fcprim.STEEL)
```

**It takes two passes, and the printed parts are why.** The two bought metals
are cards from FreeCAD's own library and carry an appearance of their own, so
`fcprim.material` naming the card as the part is built is the whole job. The
printed parts wear the `Default` card with a colour laid over it, and the GUI
paints anything wearing that card in its own `DefaultShapeColor` whatever the
material says - so their colour has to go on the view provider, and there is no
view provider until a GUI opens the document. `view.py` does it, in `paint`,
which is also the only place that can: the appearance is stored in
`GuiDocument.xml`, and `view.py` is the only thing here that writes one.

So a part is only the right colour once **both** have run, which is the order
they already run in:

```sh
fc cad/freecad/build.py misc/tube-d8.py     # material card, and PartMaterial
fcgui cad/freecad/view.py misc/TUBE_D8_170.FCStd   # the colour, and the camera
```

`build.py` used to lose all of this: it writes a new document from a script,
the appearance lives in the document rather than in the source, so a part that
had been coloured by hand came back grey and git had no copy to put it back.

What a body carries is a `PartMaterial` string, in its **Stock** property
group, and `paint` only touches bodies that have one. A document built before
this existed says nothing, is left exactly as it was, and so dressing an old
part can never repaint a rod or a plate orange - but it will stay whatever
colour it already is until its script is rebuilt.

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

Then dress what was built, so that opening it shows something:

```sh
alias fcgui='flatpak run --filesystem=home \
    --env=QT_QPA_PLATFORM=offscreen org.freecad.FreeCAD'

fcgui cad/freecad/view.py                    # every document
fcgui cad/freecad/view.py bot/BOT_HANDWHEEL.FCStd
```

This is the one script here that needs a real GUI rather than `freecadcmd`,
because `GuiDocument.xml` is written by the view providers and `freecadcmd` has
none. Qt's offscreen platform means it still needs no display, and no window
appears.

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

**A ring of holes is a bolt circle, not five coordinates.** `fcprim.bolt_circle`
puts the holes on the corners of a construction polygon inscribed in a
construction circle, dimensions only the first one, and holds the rest equal
and coincident with a corner. Computing each centre in Python draws the same
holes but the sketch then says nothing about them: nothing on screen shows they
belong to one circle, and editing the radius leaves them where they were.
`ALPHA_BOT_PLATE`'s five 10 mm holes are drawn this way.

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
  lever cheeks, not one part, and a chiral pair at that: the plate carries its
  hub on one face and the two hubs have to face each other across the shaft.
  `eccf/eccf-lever.py` builds both hands, `ECCF_LEVER` and
  `ECCF_LEVER_MIRRORED`, each keeping the coordinates of the shell it came
  from.
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

All 39 meshes are rebuilt, the 6 drawn parts and Michael's 2 alongside them, so
`build.py` comes back **47/47**. [`STATUS.md`](STATUS.md) carries the per-part table and
what each awkward one turned out to be; [`ASSEMBLY.md`](ASSEMBLY.md) is the plan
for putting them together into the machine, and how far it has got.
