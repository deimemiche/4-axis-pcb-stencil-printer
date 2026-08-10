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
| `STENCIL_HOLDER_BACK` | Michael's machine | L 20x20x2, 213.72 | 4 x 3.4 at +-25 / +-75, and a mount's three at each end |
| `STENCIL_HOLDER_FRONT` | Michael's machine | L 20x20x2, 213.72 | the same bar, plus one 5.4 through the upright at the middle |
| `STENCIL_HOLDER_BACK_2` | `stencil-holder-bottom.pdf` | L 20x20x2, 198 | 4 x 3.4 at +-25 / +-75, the short angle that closes on `_BACK` |
| `STENCIL_HOLDER_FRONT_2` | `stencil-holder-bottom.pdf` | L 20x20x2, 198 | the same, plus the 5.4 its long bar has |

Two things fell out of doing these that were not obvious from the build page.
The alpha axis has **two** plates, a fixed 200 x 200 and a rotating 240 x 200,
which is why the page's "200 x 200 x 6" and the drawings' 240 x 200 looked like
a contradiction. And `ALPHA_TOP_PLATE`'s grid comes to exactly the 83 holes its
drawing annotates, which is a real check on having read the stagger right --
the script refuses to build if it does not.

The two stencil holder angles are the exception to the rule above, and the
warning that goes with it. They are named for where they sit -- flat in the top
frame, one behind the other -- rather than for the BOT and TOP their sheets
say, and **their figures are Michael's, off the built machine, not off a
drawing**. `stencil-holder-top.pdf` does describe a 213.72 angle, but it draws
a row of six where the bar has four and gives 5 and 5.4 where every hole is 3.4
M3 clearance, and `stencil-holder-bottom.pdf` describes a 198 bar that is not
in the machine at all. A reconstruction from those sheets was built, checked
against `TOP_CLAMP_BEARING_MOUNT_1` to a hundredth of a millimetre, and was
still the wrong part; both angles had to be reworked by hand. The scripts now
reproduce what he built, exactly. Do not reconcile them with the sheets.

The clamp is **four angles, not two**: each long bar closes on a shorter one
with the foil pinched between, and the short pair is what
`stencil-holder-bottom.pdf` draws -- its 198 is shorter than the long bars'
213.72, not a different front bar as the file name suggests. The four go in two
hands, and the hand is the 5.4 through the upright at the middle: `_FRONT` and
`_FRONT_2` have it, `_BACK` and `_BACK_2` do not. The short pair is the part of
this still taken from a sheet rather than from the machine.

## The parts of Michael's own

The linear Z axis mod in the repository's [README](../../README.md) has printed
parts of its own, and they already exist as CadQuery in
[`../z-axis.py`](../z-axis.py) driven by [`../settings.py`](../settings.py).
They are **transcribed** from that source rather than reverse engineered, which
is the same bargain the transcribed plates make with the author's drawings, and
their cosmetic chamfers and fillets are deliberately left off -- they change no
fit. Most live in `shelved/`, consumed by no assembly; the Z bracket bolts to
the bottom frame, so it is a `bottom-frame/` part and takes that prefix.

| Part | From | Size mm | What it does |
|---|---|---|---|
| `BOT_Z_AXIS_BRACKET` | `z-axis.py` `bracket()` | 62 x 24 x 79.65 | stands an 8 mm Z rod up on a corner of the bottom frame |
| `BOT_Z_AXIS_BRACKET_MIRRORED` | the same, every X negated | 62 x 24 x 79.65 | the other hand, for the other corner |
| `TOP_Z_AXIS_BEARING_MOUNT` | `z-axis.py` `bearingMount()` | 42.2 x 24 x 25.1 | holds the LM8UU the hinge bar rides it on |
| `TOP_HINGE_LOCK_BACK` | `hinge-lock.py` `hingeLockBack()` | 39 x 19.9 x 28.1 | hooks over a member; holds the M3's nut |
| `TOP_HINGE_LOCK_FRONT` | `hinge-lock.py` `hingeLockFront()` | 15 x 48 x 20 | bolts flat to a member's face; carries the M3 |

The hinge locks and the Z bracket are checked against CadQuery itself, which
can be installed and run: their **volumes match the CadQuery solids exactly**
once that source's cosmetic chamfers and fillets are suppressed, and every hole
position was read off the real solid rather than off the script. `undressed`
(the locks) and `plain_volume` (the bracket) are that number. What is
deliberately left off is only the chamfers and fillets.

The bracket is held to that solid harder still: booleaned against it, in both
hands, it leaves nothing on either side. That check is worth having. Before it
there was no bore in the collar at all, no saw cut and no pinch bolt -- three
pockets that were cutting away from the material rather than into it, and a
volume nobody was holding against anything.

`TOP_Z_AXIS_BEARING_MOUNT` has no such check yet, so what checks it is the
assembly: one rod has to pass both bores on one axis, which is what
`asm/column.py` says.

They also disagree with each other by exactly **2 mm**, and it is worth knowing
why. The bracket measures the rod from the frame face its plate lies on and
stands it 11.55 out; the mount measures it from the flange it bolts through and
reaches 13.55 in. Both are right about themselves, so the difference cannot be
split - the flange has to lie on the bar and the bore has to be on the rod. It
comes out instead as the whole top assembly sitting 2 mm inboard of the bottom
frame's own face, which `asm/column.py`'s `check_reach` prints every build.

## The microscope column, which is not part of this machine

[`../shelved/scope/`](../shelved/scope/) transcribes all eight parts of
[`../microscope-mount/`](../microscope-mount/) -- a column that **stands
beside the stencil printer** and looks down at the board, so that solder joints
and part outlines can be seen. It is a second machine, and it has been shelved:
the parts are kept as a record, and the assembly that linked them has been
deleted rather than carried along.

| Part | From | Size mm | Volume mm3 | What it does |
|---|---|---|---|---|
| `SCOPE_SLIDER` | `microscope-mount.py` `slider()` | 41.5 x 40.5 x 12.7 | 7639.842 | the carriage: a 28.5 square tube over the 2020, on eight running tabs |
| `SCOPE_HOLDER` | `microscope-mount.py` `holder()` | 58 x 80 x 12.7 | *see below* | the split collar that grips the 50 mm barrel, hung off the slider's ear |
| `SCOPE_JOINER` | `microscope-mount.py` `joiner()` | 116 x 13 x 4 | 3536.896 | a strap across the butt between the two sticks; two of them, one per face |
| `SCOPE_TOP` | `microscope-mount.py` `top()` | 28.5 x 43.5 x 9 | 6062.768 | caps the column and seats the 605 the leadscrew turns in |
| `SCOPE_ROLLER_MOUNT` | `roller.py` `roller_mount()` | 53.5 x 20 x 29 | 9322.162 | hangs a wheel under a horizontal member on an M8 |
| `SCOPE_ROLLER_WHEEL` | `roller.py` `wheel()` | 28 dia x 7 | 1583.391 | the tyre a 608 wears to run on an extrusion |
| `SCOPE_LENS_LED_MOUNT` | `lens-led-mount.py` | 55 ring, 3 arms to r 41.3, 11.2 tall | 5905.503 | three strips of LEDs round the 46 mm objective |
| `SCOPE_LED_WEDGE` | `led-wedge.py` | 164.6 x 20 x 10.9 | 11561.221 | a strip of LEDs held at 45 degrees, raking across the board |

Seven of the eight are checked the way the plates are: arithmetic on the numbers
the source states, agreeing to **0.0000 %**. That is a weaker bargain than the
transcribed Z-axis parts', and the reason is only that neither CadQuery nor build123d is
installed here, so there is no solid to boolean against -- the arithmetic is
still a second, independent description of each part rather than a measurement
of the one that was built.

`SCOPE_LED_WEDGE` keeps that shape and borrows one term. Its two 15 mm head
clearances are bored down through a sloping wedge, so what they remove is a
cylinder meeting a prism at an angle and has no closed form; `clearance_loss`
asks `Part` for that one number and everything else is still rectangles and
obrounds. Primitives and a boolean against sketches and pads is still two
descriptions.

**`SCOPE_HOLDER` has no volume figure at all**, and that is deliberate. Its two
4 mm shoulder fillets, its two 8 mm gussets and the 43.5 x 3.5 slit that splits
the collar all interpenetrate, so arithmetic would have to be a second model of
the part rather than a check on it. It is checked by the assembly instead --
`check_mount` in `microscope.py` says the two M2.5 the holder hangs on land on
the two nuts the slider holds, to a micron, which fails if either transcription
is wrong. `TOP_Z_AXIS_BEARING_MOUNT` is checked the same way and for the same
reason.

### What the transcription had to decide

Four readings in the source are not obvious, and each is written into its own
script's docstring where it will be found:

* **The slider's leadscrew nut slot is only half the nut deep.** The source
  tags its workplane at `z = 0` and only then moves to `t / 2`, so the 4.7 slot
  runs 0 .. 2.35 and opens on the *bottom* face rather than being buried at mid
  height. It is transcribed as drawn.
* **The roller mount's nut pocket is 6.8 and the nut is 9.5.** `nutcatchParallel`
  defaults to a plain hexagon whatever `nutData(kind="hexagon_lock")` returned;
  the nyloc's 9.5 is used only to work out how long the block is. So the collar
  stands 2.7 proud of the pocket, in the 4 mm the block was made longer for.
* **The lens mount's heat sert enters at z = 6.93, not 5.6.** Both holes go on
  `faces(Select.LAST)`, which is the boss's outer face -- and the LED shelf
  covers that face's first 2.667 mm, so its middle is not the lug's own middle.
  If an insert ever sits too high in the lug, that is the number to look at.
* **The roller wheel is a plain cylinder, not a V.** A wheel that runs in a
  V-slot usually carries a 90 degree groove; this one has 0.875 breaks on a
  flat 28 mm face, so it rides the face of the extrusion rather than the slot's
  vee. That is what the source draws.

Cosmetic edge breaks are left off, as in the transcribed Z-axis parts. Three are *not* cosmetic and
are drawn into the sketches instead: the wheel's 0.875 rim, which is the
surface that meets the extrusion; the roller block's 5 mm feet, a quarter of
the plate's width; and the 4 mm between the plate's underside and the block,
which **adds** material and so cannot be a `PartDesign::Chamfer` at all -- it is
a triangle drawn in section and padded across the plate. See the chamfer
section below.

### What putting them together found

Two things the eight scripts could not have caught on their own, because
nothing in `../microscope-mount/` assembles them:

* **The roller mount's gusset fouls its own wheel**, by about 1.6 mm3. The
  wheel's rim comes 2.25 mm below the plate and the 4 mm gusset comes 4 mm
  down into that same space. It lands on the rim's 0.875 chamfer rather than
  the full 28, which is why it is 1.6 and not the 5 the plain diameter would
  give, and a printed rim's fuzz is that size anyway -- so the real wheel would
  very likely turn. It is listed in `OPEN`, which reports it every build
  without failing one.
* **The roller pair reaches nothing.** Its plate wants the underside of a
  horizontal member and this column has none, so the two stand beside it and
  are listed in `ADRIFT`, reported every build rather than quietly placed
  somewhere they would look right. `ECCF_LEVER`'s outer cheek is adrift for the
  same kind of reason: it grips an eccenter body that was never published.

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

## The extrusion section was five pieces, not one

`asm/stock.py` draws the T-slot profile every frame member is cut from, and it
drew each slot's cavity as a plain 11 x 4 rectangle behind the mouth. Four of
those meet each other across the diagonals, so what came out was **five
separate lumps** -- the boss the centre bore runs through, and each of the four
corners -- with nothing joining them. It could not be extruded and it could not
be a profile; Michael looked at a render and said so.

The fix is to slope the cavity's flanks at 45 degrees, which leaves the four
diagonal **ribs** that carry the boss out to the corners. What checks it is a
number nothing else in the repository could have supplied: a real 20 x 20
slot 6 profile is catalogued at 0.53 kg/m, which at 2.70 g/cm3 is **196 mm2**
of section. The old one measured 171.1. This one measures **196.1**.

## A part that is two parts

`ECCF_LEVER.stl` holds **two shells**: it is a printing pair of cheeks that go
one either side of the eccenter and grip its shaft between their hubs, 6 mm
apart. They are a *chiral* pair and not two of the same part - reflect one
about X = -13.2 and all 1087 of its vertices land on the other, slide it across
by the 20.2 mm between them instead and only 336 do - so `eccentric-clamp/eccf-lever.py`
builds both hands, `ECCF_LEVER` at X = -30.4 .. -16.2 and `ECCF_LEVER_MIRRORED`
at X = -10.2 .. 4.0. For a long time it built only the first, and the assembly
placed only that one - and it is the *outer* cheek, so it touched nothing at
all.

`asm/check.py`'s connectedness check is what found it: four hand levers hanging
in mid air, which no interference check can ever see. The inner cheek is now
mirrored in and lands against `ECCF_TOP`. The outer one still reaches nothing,
because what it grips is the **eccenter body, and there is no part for it** -
`eccentric-clamp/` has `_BOT`, `_HEIGHT`, `_MOUNT`, `_TOP` and `_LEVER` and nothing else.
It is listed in `asm/machine.py`'s `ADRIFT` and reported every build.

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

The one exception is **`ECCF_MOUNT`, and it is deliberate**: its cross bolt hole
is opened out from the author's 3.5 mm to 5.7 mm for a heat set threaded insert,
so the part is no longer the mesh. Its volume is checked against the mesh less
the 132 mm3 that widening takes out, and `verify.py` reports 184 mismatches in
20000 samples, all inside the enlarged hole. See `eccentric-clamp/eccf-mount.py`.

| Part | Size mm | Volume mm3 | Axis | Prismatic | Status |
|---|---|---|---|---|---|
| `ADAPTER_D5_TO_M3` | 6.4 x 3.5 x 6.4 | 52 | Y | 0.94 | **done** `rotation-table/` |
| `BOT_BEARING_MOUNT_X_AXIS` | 27.0 x 26.2 x 35.0 | 10098 | X | 0.85 | **done** `x-axis-carriage/` |
| `BOT_BEARING_MOUNT_Y_AXIS` | 27.0 x 18.0 x 38.0 | 6369 | X | 0.94 | **done** `rotation-table/` |
| `BOT_BEARING_MOUNT_Y_AXIS_DRIVEN` | 27.0 x 18.0 x 49.9 | 9014 | X | 0.96 | **done** `rotation-table/` |
| `BOT_BRACKETS` | 60.0 x 4.0 x 60.0 | 8118 | Y | 1.00 | **done** `shared/` |
| `BOT_BRACKET_X_AXIS` | 36.0 x 19.8 x 60.0 | 9746 | X | 0.91 | **done** `bottom-frame/` |
| `BOT_CLAMP_Z_AXIS` | 31.8 x 40.0 x 17.2 | 10794 | Y | 0.86 | **done** `shelved/` |
| `BOT_HANDWHEEL` | 30.0 x 26.0 x 29.4 | 10725 | Y | 0.81 | **done** `shared/` |
| `BOT_RAIL_CLAMP_X_DRIVE` | 43.9 x 16.5 x 27.0 | 8418 | Z | 0.83 | **done** `x-axis-carriage/` |
| `BOT_RAIL_CLAMP_Y_AXIS` | 21.0 x 7.0 x 27.0 | 3145 | X | 0.89 | **done** `x-axis-carriage/` |
| `BOT_RAIL_CLAMP_Y_AXIS_1` | 49.1 x 11.3 x 45.1 | 9094 | X | 0.83 | **done** `x-axis-carriage/` |
| `BOT_RAIL_HOLDER` | 11.4 x 16.0 x 28.6 | 2288 | X | 0.94 | **done** `x-axis-carriage/` |
| `BOT_RIGHT_ANGLE_CON` | 21.0 x 20.0 x 20.0 | 3861 | Z | 0.95 | **done** `shelved/` |
| `BOT_ROD_HOLDER_ALPHA_AXIS` | 68.6 x 12.2 x 28.3 | 6310 | X | 0.62 | **done** `rotation-table/` |
| `BOT_ROD_HOLDER_ALPHA_AXIS_SHORT` | 20.0 x 12.2 x 28.3 | 3204 | X | 0.93 | **done** `rotation-table/` |
| `BOT_Z_AXIS_COUNTER_HOLDER` | 40.0 x 24.0 x 20.0 | 6349 | Y | 0.88 | **done** `shelved/` |
| `BOT_Z_AXIS_COUNTER_KNOB` | 24.0 x 17.0 x 23.7 | 4762 | Y | 0.80 | **done** `shelved/` |
| `ECCF_BOT` | 40.0 x 8.0 x 20.0 | 4961 | Y | 1.00 | **done** `eccentric-clamp/` |
| `ECCF_HEIGHT` | 44.0 x 10.0 x 43.4 | 10162 | Y | 1.00 | **done** `eccentric-clamp/` |
| `ECCF_LEVER` | 34.4 x 29.3 x 45.8 | 4929 | X | 0.74 | **done** `eccentric-clamp/` |
| `ECCF_MOUNT` | 26.4 x 14.0 x 26.4 | 3888 | Y | 0.74 | **done** `eccentric-clamp/` |
| `ECCF_TOP` | 44.0 x 27.0 x 26.4 | 13649 | Y | 0.89 | **done** `eccentric-clamp/` |
| `SR_BEARING_PLATE` | 130.0 x 3.0 x 130.0 | 4887 | Y | 0.94 | **done** `rotation-table/` |
| `SR_INNER_RING` | 140.0 x 10.0 x 140.0 | 12887 | Y | 0.63 | **done** `rotation-table/` |
| `SR_OUTER_RING_W_GEAR` | 154.0 x 12.0 x 160.6 | 38024 | Y | 1.00 | **done** `rotation-table/` |
| `SR_WORM_GEAR` | 10.0 x 20.0 x 10.0 | 754 | Y | 0.32 | **done** `rotation-table/` |
| `STAND` | 11.5 x 7.0 x 11.5 | 373 | Y | 0.62 | **done** `bottom-frame/` |
| `TOP_CLAMP_BEARING_MOUNT_1` | 26.0 x 27.0 x 21.0 | 7142 | X | 0.94 | **done** `stencil-clamp/` |
| `TOP_CLAMP_BEARING_MOUNT_2` | 26.0 x 27.0 x 21.0 | 7142 | X | 0.94 | **done** `stencil-clamp/` |
| `TOP_CLAMP_NUT_HOLDER` | 16.4 x 30.0 x 14.0 | 4127 | Y | 0.90 | **done** `stencil-clamp/` |
| `TOP_CLAMP_SPANNER_CASE_1` | 3.2 x 14.0 x 58.0 | 1782 | X | 0.93 | **done** `top-assembly/` |
| `TOP_CLAMP_SPANNER_CASE_2` | 9.0 x 14.0 x 58.0 | 3572 | X | 0.96 | **done** `top-assembly/` |
| `TOP_CLAMP_SPANNER_COUNTER` | 16.4 x 30.0 x 58.0 | 19315 | Z | 0.94 | **done** `top-assembly/` |
| `TOP_CLAMP_SPANNER_HANDWHEEL` | 5.0 x 33.8 x 34.0 | 3111 | X | 0.99 | **done** `top-assembly/` |
| `TOP_CLAMP_STOP` | 10.0 x 20.8 x 15.6 | 1750 | X | 0.88 | **done** `stencil-clamp/` |
| `TOP_CLAMP_Z_AXIS` | 30.2 x 34.0 x 32.0 | 10387 | Y | 0.86 | **done** `top-frame/` |
| `TOP_HANDWHEEL_Z_AXIS` | 38.0 x 17.0 x 37.5 | 11108 | Y | 0.91 | **done** `shelved/` |
| `TOP_RAIL_HOLDER` | 11.4 x 16.1 x 27.6 | 2166 | X | 0.91 | **done** `stencil-clamp/` |
| `TOP_SPRING_PLATE` | 19.4 x 4.4 x 19.4 | 769 | Y | 0.81 | **done** `stencil-clamp/` |

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
    fc cad/freecad/export.py cad/freecad/rotation-table/SR_WORM_GEAR.FCStd built.stl
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
* **`SCOPE_ROLLER_MOUNT`'s 4 mm gusset** is the same case as the first: the
  source writes it as `chamfer(wall_t)` on the plate's underside, but it is the
  web that stops the block folding and it adds every cubic millimetre of
  itself. Drawn here as a triangle in section, padded across the plate.

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
