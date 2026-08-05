# Reconstruction status

## The parts that were drawn, not reverse engineered

The author published the aluminium as proper 2D drawings rather than as meshes,
so these six are transcribed from [`../../technical-drawings/`](../../technical-drawings/)
instead of measured off an STL. There is no mesh to compare against and none is
wanted: the check is that the finished solid's volume matches arithmetic on the
drawing's own dimensions, so a mistyped hole position fails the build.

| Part | Drawing | Size mm | Notes |
|---|---|---|---|
| `XY_PLATE` | `base-plate.dxf` | 257 x 162 x 2 | 16 x 3.2, at x +-97.65 / +-124.35, z +-59 / +-76 |
| `ALPHA_BOT_PLATE` | `bottom-plate.pdf` | 200 x 200 x 6 | 4 x M3 on a 122 bolt circle, 10 for the worm at x 75.45, 24 x M3 in clusters |
| `ALPHA_TOP_PLATE` | `top-plate-workholding.dxf` | 240 x 200 x 6 | 5 x M3 at r 75.45, plus an 83 hole staggered grid |
| `ALPHA_TOP_PLATE_PLAIN` | `top-plate-plain.dxf` | 240 x 200 x 6 | the same plate before the grid is drilled |
| `STENCIL_HOLDER_BOT` | `stencil-holder-bottom.pdf` | L 20x20x2, 198 | 4 x 5 at +-25 / +-75, one 5.4 through the upright |
| `STENCIL_HOLDER_TOP` | `stencil-holder-top.pdf` | L 20x20x2, 213.72 | 6 + 2 x 5, two 5.4; across-leg positions are the least certain thing here |

Two things fell out of doing these that were not obvious from the build page.
The alpha axis has **two** plates, a fixed 200 x 200 and a rotating 240 x 200,
which is why the page's "200 x 200 x 6" and the drawings' 240 x 200 looked like
a contradiction. And `ALPHA_TOP_PLATE`'s grid comes to exactly the 83 holes its
drawing annotates, which is a real check on having read the stagger right --
the script refuses to build if it does not.

## Two parts whose names are misleading

Both were read off the mesh alone, before there was an assembly to put them in,
and the assembly reads them differently. The reconstructions are right; it is
the prose in their docstrings that is not:

* **`BOT_BEARING_MOUNT_Y_AXIS` is an LM8UU holder**, not a bearing for the Y
  screw. Its 15.2 mm seat with 13.2 mm lips is an LM8UU dropped in from below,
  and four of them clip the alpha plate onto the Y rails.
* **`BOT_ROD_HOLDER_ALPHA_AXIS` carries the worm's shaft.** Its bore is 5.3, an
  M5 clearance, and the "alpha axis rod" of its name is that shaft rather than
  a rail.

## The reconstructed meshes

One row per mesh in [`../`](../). "Prismatic" is the fraction of the mesh's
surface area that a prism along the listed axis explains: 1.00 is a pure
extrusion, and the shortfall is chamfers, blends, cross drilled holes and
anything turned or helical. It is a fair proxy for how much work a part is.

Rebuilding a part means: measure it with `stlmeasure.py`, write the script,
then get both checks in [`README.md`](README.md) to pass - volume within the
mesh's own faceting error, and zero point classification mismatches.

**All 39 done.** Every script builds and every one passes `verify.py` with zero
mismatches. The worst volume deviation is 0.26 %, on `SR_WORM_GEAR`, and that is
the original mesh's own faceting error on a helical surface; the next worst is
0.054 %.

| Part | Size mm | Volume mm3 | Axis | Prismatic | Status |
|---|---|---|---|---|---|
| `ADAPTER_D5_TO_M3` | 6.4 x 3.5 x 6.4 | 52 | Y | 0.94 | **done** `misc/` |
| `BOT_BEARING_MOUNT_X_AXIS` | 27.0 x 26.2 x 35.0 | 10098 | X | 0.85 | **done** `bot/` |
| `BOT_BEARING_MOUNT_Y_AXIS` | 27.0 x 18.0 x 38.0 | 6369 | X | 0.94 | **done** `bot/` |
| `BOT_BEARING_MOUNT_Y_AXIS_DRIVEN` | 27.0 x 18.0 x 49.9 | 9014 | X | 0.96 | **done** `bot/` |
| `BOT_BRACKETS` | 60.0 x 4.0 x 60.0 | 8118 | Y | 1.00 | **done** `bot/` |
| `BOT_BRACKET_X_AXIS` | 36.0 x 19.8 x 60.0 | 9746 | X | 0.91 | **done** `bot/` |
| `BOT_CLAMP_Z_AXIS` | 31.8 x 40.0 x 17.2 | 10794 | Y | 0.86 | **done** `bot/` |
| `BOT_HANDWHEEL` | 30.0 x 26.0 x 29.4 | 10725 | Y | 0.81 | **done** `bot/` |
| `BOT_RAIL_CLAMP_X_DRIVE` | 43.9 x 16.5 x 27.0 | 8418 | Z | 0.83 | **done** `bot/` |
| `BOT_RAIL_CLAMP_Y_AXIS` | 21.0 x 7.0 x 27.0 | 3145 | X | 0.89 | **done** `bot/` |
| `BOT_RAIL_CLAMP_Y_AXIS_1` | 49.1 x 11.3 x 45.1 | 9094 | X | 0.83 | **done** `bot/` |
| `BOT_RAIL_HOLDER` | 11.4 x 16.0 x 28.6 | 2288 | X | 0.94 | **done** `bot/` |
| `BOT_RIGHT_ANGLE_CON` | 21.0 x 20.0 x 20.0 | 3861 | Z | 0.95 | **done** `bot/` |
| `BOT_ROD_HOLDER_ALPHA_AXIS` | 68.6 x 12.2 x 28.3 | 6310 | X | 0.62 | **done** `bot/` |
| `BOT_ROD_HOLDER_ALPHA_AXIS_SHORT` | 20.0 x 12.2 x 28.3 | 3204 | X | 0.93 | **done** `bot/` |
| `BOT_Z_AXIS_COUNTER_HOLDER` | 40.0 x 24.0 x 20.0 | 6349 | Y | 0.88 | **done** `bot/` |
| `BOT_Z_AXIS_COUNTER_KNOB` | 24.0 x 17.0 x 23.7 | 4762 | Y | 0.80 | **done** `bot/` |
| `ECCF_BOT` | 40.0 x 8.0 x 20.0 | 4961 | Y | 1.00 | **done** `eccf/` |
| `ECCF_HEIGHT` | 44.0 x 10.0 x 43.4 | 10162 | Y | 1.00 | **done** `eccf/` |
| `ECCF_LEVER` | 34.4 x 29.3 x 45.8 | 4929 | X | 0.74 | **done** `eccf/` |
| `ECCF_MOUNT` | 26.4 x 14.0 x 26.4 | 3888 | Y | 0.74 | **done** `eccf/` |
| `ECCF_TOP` | 44.0 x 27.0 x 26.4 | 13649 | Y | 0.89 | **done** `eccf/` |
| `SR_BEARING_PLATE` | 130.0 x 3.0 x 130.0 | 4887 | Y | 0.94 | **done** `sr/` |
| `SR_INNER_RING` | 140.0 x 10.0 x 140.0 | 12887 | Y | 0.63 | **done** `sr/` |
| `SR_OUTER_RING_W_GEAR` | 154.0 x 12.0 x 160.6 | 38024 | Y | 1.00 | **done** `sr/` |
| `SR_WORM_GEAR` | 10.0 x 20.0 x 10.0 | 754 | Y | 0.32 | **done** `sr/` |
| `STAND` | 11.5 x 7.0 x 11.5 | 373 | Y | 0.62 | **done** `misc/` |
| `TOP_CLAMP_BEARING_MOUNT_1` | 26.0 x 27.0 x 21.0 | 7142 | X | 0.94 | **done** `top/` |
| `TOP_CLAMP_BEARING_MOUNT_2` | 26.0 x 27.0 x 21.0 | 7142 | X | 0.94 | **done** `top/` |
| `TOP_CLAMP_NUT_HOLDER` | 16.4 x 30.0 x 14.0 | 4127 | Y | 0.90 | **done** `top/` |
| `TOP_CLAMP_SPANNER_CASE_1` | 3.2 x 14.0 x 58.0 | 1782 | X | 0.93 | **done** `top/` |
| `TOP_CLAMP_SPANNER_CASE_2` | 9.0 x 14.0 x 58.0 | 3572 | X | 0.96 | **done** `top/` |
| `TOP_CLAMP_SPANNER_COUNTER` | 16.4 x 30.0 x 58.0 | 19315 | Z | 0.94 | **done** `top/` |
| `TOP_CLAMP_SPANNER_HANDWHEEL` | 5.0 x 33.8 x 34.0 | 3111 | X | 0.99 | **done** `top/` |
| `TOP_CLAMP_STOP` | 10.0 x 20.8 x 15.6 | 1750 | X | 0.88 | **done** `top/` |
| `TOP_CLAMP_Z_AXIS` | 30.2 x 34.0 x 32.0 | 10387 | Y | 0.86 | **done** `top/` |
| `TOP_HANDWHEEL_Z_AXIS` | 38.0 x 17.0 x 37.5 | 11108 | Y | 0.91 | **done** `top/` |
| `TOP_RAIL_HOLDER` | 11.4 x 16.1 x 27.6 | 2166 | X | 0.91 | **done** `top/` |
| `TOP_SPRING_PLATE` | 19.4 x 4.4 x 19.4 | 769 | Y | 0.81 | **done** `top/` |

## The gusset that looked like a free-form blend

`BOT_RAIL_CLAMP_Y_AXIS_1` held out longest, and only because it was measured
the wrong way. Fitting arcs to its sections gave radii that changed with height,
which reads as a doubly curved surface and is exactly what a **torus** does: a
section of one is not a circle. Its outer surface is a 33.5 mm arc turned about
the tube's own axis, and two of the part's dimensions fall out of that arc
rather than being chosen - it reaches furthest out where the clamp block ends,
and it lands on the tube's own diameter where the part stops.

The flanks looked worse still: ruled, but neither plane, cylinder nor cone. They
are simply the two lines tangent to the tube **from the block's own front
corners**, rounded into those corners on 10 mm. Once that is seen the whole
gusset is one prism and one revolved cut.

The lesson is the same one `stlrender.py` teaches: measure a section and you get
numbers that fit many shapes; ask what construction would put a surface there
and usually only one answer survives.

## Shapes that turned up more than once

Recognising these cut the work on the second and third instance to almost
nothing, so they are worth looking for first.

* **Rail holders** (`BOT_RAIL_HOLDER`, `TOP_RAIL_HOLDER`) are twins, and
  `BOT_ROD_HOLDER_ALPHA_AXIS`'s first 20 mm are
  `BOT_ROD_HOLDER_ALPHA_AXIS_SHORT`.
* **`TOP_CLAMP_BEARING_MOUNT_2`** is exactly `..._1` mirrored in Z, vertex for
  vertex. `top-clamp-bearing-mount-2.py` runs the other script for its builder
  rather than repeating it.
* **The webbed arm.** `BOT_BEARING_MOUNT_Y_AXIS_DRIVEN` and
  `BOT_RAIL_CLAMP_X_DRIVE` are hollowed from both faces over *identical* spans -
  a 2 mm skin at each end and one 2 mm rib, at -13.5/-11.5, -9.5, 5.1/7.1,
  11.5/13.5. Both use the same two hollow shapes: a half round of radius 5.5
  about the eye between the ribs, and beside each skin the same idea drawn to a
  smaller radius and roofed with a 120 degree vee so it prints unsupported.
* **Knurled knobs** (`BOT_HANDWHEEL`, `BOT_Z_AXIS_COUNTER_KNOB`,
  `TOP_HANDWHEEL_Z_AXIS`, `ECCF_HEIGHT`) are all one turned section, one flute
  pocket and a polar pattern.
* **The 8.2 mm rod clamp** - bore 8.2 in a 16.2 boss, saw cut, M3 pulling it
  shut - is `BOT_CLAMP_Z_AXIS`, `TOP_CLAMP_Z_AXIS` and `TOP_CLAMP_STOP`.

## Look at the part

Everything here was measured before it was ever seen, and for prismatic parts
that is the better way round - an arc fitted to a section is worth more than a
picture. For the last few it was the wrong way round. `stlrender.py` draws a
mesh from four orthographic views; `ECCF_LEVER` had been sitting in the "hard,
organically blended" pile and turned out, on sight, to be a flat plate with an
eye at each end and a waisted arm between - an afternoon's guesswork replaced by
one glance.

It also checks work. `export.py` tessellates a built body back to STL, and
rendering the two together in different colours settles at a glance what a
volume figure cannot: whether a thread runs the right way round.

    python3 cad/freecad/stlrender.py cad/ECCF_LEVER.stl
    fc cad/freecad/export.py cad/freecad/sr/SR_WORM_GEAR.FCStd built.stl
    python3 cad/freecad/stlrender.py cad/SR_WORM_GEAR.stl built.stl cmp.png

## The one thing a revolve cannot do

`SR_WORM_GEAR` is a helix, and a helix advances along its axis as it turns.
`fcprim.helix` wraps `PartDesign::AdditiveHelix`, which sweeps a sketched
profile along one and wants exactly the same fully constrained sketch as
everything else - so the worm is a bored tube plus one trapezium, and not the
mesh it was assumed it would have to stay.

Two things about it are worth knowing. The thread starts and stops at the part's
own ends rather than running past them, so its first and last turn are only
partly there; running the sweep long and trimming instead puts 10 mm3 too much
material in. And `Mode` takes `"pitch-height-angle"` in lower case - the string
FreeCAD shows in the GUI is rejected.

## Chamfers that add material, and where dressups give up

A 45 degree break is a `PartDesign::Chamfer` only when it takes material away
from an edge that already exists. Two cases here are neither:

* **A break at the foot of a boss adds material** - `BOT_HANDWHEEL`'s lug is
  1 mm wider where it stands on the rim, and `BOT_CLAMP_Z_AXIS` stands on two
  ribs that flare out where they meet its underside. No dressup can do that.
* **A break that dies out on a curved surface** makes OCC fail outright:
  `BOT_HANDWHEEL`'s lug is broken 1 mm round its top, and that break runs out
  where the outline crosses the collar. `BRep_API: command not done`.

Both are drawn instead as a `Pad` with `taper=45.0`, which drafts the sides as
the pad runs. Draw the profile at whichever end of the break is *smaller* and
let the taper open it out. Where the tapered face must not appear on every side
of the profile - `BOT_CLAMP_Z_AXIS`'s ribs run the full width without a flare on
their ends - draw the trapezium in section and pad it the other way instead.

A dressup is still the right answer where the break follows something no single
sketch contains: both handwheels and the counter knob are broken 1 mm round the
rim, and that break follows the grip flutes as well, so it has to be taken after
the flutes are cut.

## A feature that fails is not an error

`fcprim.finish` now refuses to save if any feature came out `Invalid`. Without
that check a throwing feature is only reported to the console: the body keeps
the last shape that worked, **every later feature is silently skipped**, and the
result is still a valid solid. A failed chamfer on `BOT_HANDWHEEL` swallowed the
bore and two pockets after it and still built.

## Fillets that are surfaces, not extrusions

Where a boss stands on a plate, the fillet round its root runs along a curved
edge that no single sketch contains. `PartDesign::Fillet` is the obvious answer
and it does not work here: on `BOT_Z_AXIS_COUNTER_HOLDER` the boss also blends
into the plate's long edges tangentially, and a fillet that has to terminate on
a tangent surface junction fails outright - at any radius, one edge at a time or
all of them.

What does work is to draw the fillet in section, revolve it all the way round,
and pocket back the part of the ring that has no plate under it. Three sketched
features instead of one dressup, every dimension named, and nothing depends on
an edge number that moves when an earlier sketch changes.

Beware `Shape.BoundBox` after a revolve: it bounds the surfaces' control hulls,
not the solid, and read 0.9 mm too wide on that part. Point sampling said there
was nothing there, and there was not.

## Two ways the layer scan lies

Both cost an afternoon before they were understood, so they are worth stating
plainly. Neither shows up as a bad volume, which is why `verify.py` exists.

**A layer boundary is not always a real step.** `levels()` finds heights where
facets face along the build axis, and a cross drilled hole's cylinder has such
facets where it is tangent to the cutting plane. `BOT_ROD_HOLDER_ALPHA_AXIS_SHORT`
appears to have three layers and really has one: the two inner boundaries are
where its M3 holes turn over. `BOT_BEARING_MOUNT_X_AXIS` scans as a step at
X = +/-6.703 and that is only where its 3.6 mm bolt holes turn over. Worse, a
section taken through such a hole is cut into several loops that look like
separate bodies - `TOP_CLAMP_STOP` sections as three pieces at every height, and
is one.

**A real step does not always show up as a layer.** Anything sloped has no
facet facing along the axis at all. `TOP_CLAMP_STOP` scans as a clean prism
along X and its tongue has a 3 mm chamfer off both far corners;
`BOT_BRACKET_X_AXIS` scans the same way and its plate's inside corner is a
22.5 mm sweep. A prismatic score below about 0.95 means at least one such
surface is there to be found.

## When the volume is out, compare sections rather than guessing

Volume is one number and says nothing about where the material is. Slicing both
the mesh and the built solid at the same run of heights and differencing the
areas localises the error immediately, and the *shape* of the difference names
it: a constant offset is a missing prism, a smooth curve is a missing round.

`BOT_RAIL_CLAMP_X_DRIVE` was 13.8 % over. The section scan showed the error was
zero outside one span, so the outline and every hole were right; inside that
span the difference was a smooth symmetric curve, which turned out to be an
unmodelled tapered channel up the underside, plus a flat 32.9 mm2 that was a
half round drawn with its arcs bulging the wrong way.
