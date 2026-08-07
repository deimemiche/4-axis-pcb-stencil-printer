# Plan: assembling the machine

The 39 printed parts are rebuilt and each one is checked against the mesh it
came from ([`STATUS.md`](STATUS.md)). This is the plan for putting them
together into a real FreeCAD assembly - one that is *correct*, that can be
rendered and exploded, and that can be extended later.
[`ASSEMBLY_SCRIPT.md`](ASSEMBLY_SCRIPT.md) is the separate plan for rebuilding
that assembly from Python.

**Every stage is built.** All eighteen of the manual's steps are in the model
except the two things it lists that the repository has no part for - the eight
`TOP_BRACKET` and the two hinges - and the machine builds, solves and passes
its own interference, alignment and fit checks in one pass. What each stage
found is at the bottom under [Progress](#progress).

**It is Michael's machine, not the author's original.** The README's four mods
are the ones actually built, and two of them change the assembly: the **linear
Z axis**, which swaps the 2040 for a 2020, the M8 threaded columns for 8 mm
linear rod, and the author's rear `ECCB_*` eccentric for a second pair of his
`ECCF_*`; and the **workholding top plate**, which was already what `plate/`
draws. That decision is Michael's, made when the assembly reached the point of
having to choose, and it is why `ECCB_BODY`, `ECCB_LEVER` and `ECCB_SHIM` are
no longer missing parts - this machine does not have them.

## What was decided

* **A full FreeCAD assembly**, not a picture. It has to hold up as the thing the
  machine is designed in from now on, so it must be correct, extensible, and
  usable for renders and an exploded view.
* **Stock parts are modelled too** - extrusions, rods, plates, bearings. The
  printed parts locate on them, so without them nothing is anchored.
* **Try the Assembly workbench's joints first.** Scripted placements are the
  fallback, not the starting point.

## The machine, from the build page

<https://dengler-mechatronik.de/?p=790>. The page is a full assembly manual:
eighteen steps, each with its own bill of materials. **Quantities re-read off
it and corrected** - the summary this table was first built from had two of
them loose:

| Group | Stock |
|---|---|
| Bottom frame | **1 x 2040 x 300** and **3 x 2020 x 300** extrusion, M4x10 DIN 912 + slot nuts, 4 printed stands |
| X / Y axes | 2 x 8 mm rod x 300 (X) and 2 x 8 mm rod x 244 (Y); 8 x LM8UU; aluminium plate 257 x 162 x 2; **2 x** M5 x 270 threaded rod, 2 handwheels, preload springs |
| Z axis | 2 x M8 x 140 threaded rod, printed clamps top and bottom |
| Alpha (rotary) | aluminium plate **200 x 200 x 6 (fixed) and 240 x 200 x 6 (rotating)**, **4 x** bearing 14 x 7 x 5, printed worm and ring gear, M5 threaded rod to a handwheel |
| Top frame | **3 x 2020 x 300** and **2 x 2020 x 280**, 2 hinges for 2020, linear rod, LM8UU, L profile, printed nut holders, stretcher |
| Eccentrics | 2 assemblies: M8 threaded rod, springs, printed levers, pressing the stencil onto the boards |

The three quantities the plan flagged as "worth double checking" all come out
right: **32 x M4x10**, **8 x LM8UU** and **4 stands** are exactly what step 1
and step 2 of the manual list. (An earlier pass through this file claimed the
32 was invented. That was wrong - it came from reading a summary of the page
rather than the page, and the manual gives it plainly.) The alpha plate is
*two* plates, which is why the 200 x 200 in the old table and the 240 x 200 in
the drawings looked like a contradiction and were not.

**The manual is a per-step bill of materials**, eighteen steps each listing
counts and part names, and it is the source for everything below. Reading it
properly settled both of the questions that were open, so it is worth saying
plainly: the answers were all in the manual, and the earlier passes had been
working from a summary of it.

The author's own CAD renders of each build step sit alongside those lists and
are the best reference there is for how it goes together. `asm/reference.py`
fetches them into `asm/reference/`, which is git-ignored - they are his images,
not ours.

### Four parts the manual needs and the repository does not have

Reading the step lists turned up parts that have no STL in [`../`](../), so
they were never reconstructed:

| Part | Where | Count | What became of it |
|---|---|---|---|
| `TOP_BRACKET` | step 12, top frame | 8 | **left out, flagged** |
| `ECCB_BODY` | step 18, rear eccentric | 2 | not on this machine |
| `ECCB_LEVER` | step 18 | 2 | not on this machine |
| `ECCB_SHIM` | step 18 | 2 | not on this machine |

Three of the four stopped being a problem when the machine became Michael's:
the linear Z axis mod puts a **second pair of `ECCF_*`** at the back in place of
the author's `ECCB_*`, so the rear eccentric is built out of parts that do
exist. `TOP_BRACKET` is left out on Michael's instruction - nothing else
depends on its geometry, and the top frame's size and its rails' spacing are
both fixed by other things.

Two parts of Michael's own join the machine instead: `BOT_Z_AXIS_BRACKET`,
which bolts to the bottom frame and so lives in [`bot/`](bot/) with the rest of
it, and `TOP_Z_AXIS_BEARING_MOUNT`, which rides the lid, in the new
[`mod/`](mod/) group.  The bracket is chiral and the machine needs both hands,
so it is two documents: `BOT_Z_AXIS_BRACKET` and `..._MIRRORED`.
Those are transcribed from his CadQuery in [`../z-axis.py`](../z-axis.py)
rather than reverse engineered, which is the same bargain `plate/` makes with
the author's 2D drawings.

Which printed part belongs where:

* **`bot/`** - frame brackets (`BOT_BRACKETS`, `BOT_BRACKET_X_AXIS`,
  `BOT_RIGHT_ANGLE_CON`), rod ends (`BOT_RAIL_HOLDER`,
  `BOT_ROD_HOLDER_ALPHA_AXIS`, `..._SHORT`), carriage
  (`BOT_RAIL_CLAMP_Y_AXIS`, `..._1`, `BOT_RAIL_CLAMP_X_DRIVE`), screw ends
  (`BOT_BEARING_MOUNT_X_AXIS`, `..._Y_AXIS`, `..._Y_AXIS_DRIVEN`), Z columns
  (`BOT_CLAMP_Z_AXIS`), drive (`BOT_HANDWHEEL`, `BOT_Z_AXIS_COUNTER_HOLDER`,
  `BOT_Z_AXIS_COUNTER_KNOB`).
* **`sr/`** - the alpha axis: `SR_BEARING_PLATE`, `SR_INNER_RING`,
  `SR_OUTER_RING_W_GEAR`, `SR_WORM_GEAR`.
* **`top/`** - Z columns (`TOP_CLAMP_Z_AXIS`, `TOP_HANDWHEEL_Z_AXIS`),
  `TOP_RAIL_HOLDER`, and the stencil clamp (bearing mounts 1 and 2, nut holder,
  spanner case 1 and 2, spanner counter, spanner handwheel, stop, spring plate).
* **`eccf/`** - `ECCF_BOT`, `ECCF_HEIGHT`, `ECCF_MOUNT`, `ECCF_TOP`,
  `ECCF_LEVER` (**two cheeks per eccentric**, and two eccentrics).
* **`misc/`** - `STAND` x 4, `ADAPTER_D5_TO_M3`.

## Datum

One machine origin, **Y up**, matching every part script. **Settled in stage 1**
and implemented in [`asm/frame.py`](asm/frame.py):

* **Y = 0 is the bottom frame's top face**, so a height reads directly as "how
  far above the frame".
* **X = 0, Z = 0 is the centre of the frame**, which runs -170 .. +170 across
  and -150 .. +150 along.  With the mod's four equal 2020s the outline is
  symmetric too; on the author's own frame it is not, because his 2040 side
  member is 20 mm wider than its opposite number.  Either way **the origin
  follows the rails**, which is what everything else is measured from.

`stock.extrusion` puts a section's *top* at its own local Y = 0 rather than
centring it, so members of different heights hang from one common surface
instead of each needing an offset.

### What the pre-positioned groups actually say

The `ECCF_*` and `SR_*` meshes were exported in assembly position, and stage 1
reports rather than assumes where they land:

| | with an identity placement |
|---|---|
| `SR_OUTER_RING_W_GEAR` | Y -2 .. 10, centred on X = Z = 0 |
| `SR_INNER_RING` | Y -2 .. 8, centred |
| `SR_BEARING_PLATE` | Y 8 .. 11, centred |
| `ECCF_BOT` | Y -18 .. -10, centred on X |
| `ECCF_HEIGHT` | Y -10 .. 0 |
| `ECCF_MOUNT` | Y 0 .. 14 |
| `ECCF_TOP` | Y 0 .. 27 |

Both stacks are contiguous to the millimetre, so each group carries its own
**sub-assembly** datum and a good one: the three SR parts and the four ECCF
parts can be dropped in with an identity placement and will be right relative to
each other.

What neither carries is a *machine* datum. The alpha axis and the front
eccentric are each drawn about their own centre and nothing in the meshes
relates one to the other, so each group still has to be located as a unit. Worth
being explicit about, because "the parts are already in assembly position" is
true within a group and false between groups.

## How parts get joined

The risk with the Assembly workbench is that joints reference **named
topological subelements** - `Face12`, `Edge7`. Those names move the moment an
earlier sketch changes, which is exactly the fragility every part script here
avoids. Rebuild a part and the assembly quietly breaks.

So: **each part gains named mounting datums.** A `PartDesign::CoordinateSystem`
placed by the part's own script - on a bore axis, on a mounting face, on a bolt
circle - is parametric, survives a rebuild, and reads as what it is. Joints
reference those, never raw faces.

That is a change to `fcprim` and to the part scripts, and it is why stage 2
exists. It should add perhaps five lines to a typical part.

The joint types available in 1.1.3 cover the machine:

| Mechanism | Joint |
|---|---|
| Anything bolted solid | `Fixed` |
| Rod through a linear bearing or clamp bore | `Cylindrical`, or `Slider` once rotation is pinned |
| Lead screw driving a carriage | `Screw` (has a pitch) |
| Worm to ring gear | `Gears` (has a ratio) |
| Handwheels, the alpha axis | `Revolute` |

Pose then comes from the joints' own driving values, so the machine can be put
at any X / Y / Z / alpha position and re-checked, and an exploded view is an
offset applied along each joint rather than a second model.

## Fasteners: what FreeCAD actually has

Checked, rather than assumed: **FreeCAD 1.1.3 core ships no fastener library.**
The installed workbenches are AddonManager, Assembly, BIM, CAM, Draft, Fem,
Help, Idf, Import, Inspection, Material, Measure, Mesh, MeshPart, OpenSCAD,
Part, PartDesign, Plot, Points, ReverseEngineering, Robot, Show, Sketcher,
Spreadsheet, Start, Surface, TechDraw, Test, Web. No `Fasteners`, no
`PartsLibrary`.

Two ways to get them, and this is a decision for you:

1. **Fasteners Workbench** - an addon, one click in Tools > Addon Manager. It
   generates ISO/DIN screws, nuts and washers as real solids, is scriptable, and
   is what most people use. It would need installing (you install software
   yourself, so this one is yours to make).
2. **Draw them here** - a cap screw is a revolve plus a hexagon pocket, and
   `fcprim` already does both. Perhaps 60 lines for the M3 / M4 / M5 / M8 cap
   screws, nuts and washers this machine uses, fully parametric and with no
   dependency on an addon.

Recommendation: **(2)**, and treat the addon as optional. The machine uses a
handful of sizes in quantity, the parts would match the repository's style and
checks, and the assembly would not depend on an addon being installed to open.
Say the word if you would rather have the addon and I will use it instead.

Michael added: Fasteners workbench is now installed. Use it to follow the common norm.

**Settled: the addon.** It is installed and found, at

```
~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/fasteners
```

so `asm/fasteners.py` will wrap it rather than drawing screws by hand, and the
sizes will be real DIN 912 / ISO geometry. The one thing to confirm when that
file is written is that it generates headless under `freecadcmd`, since parts of
the addon are written against the GUI; if it turns out to need one, drawing them
here is still the fallback and the wrapper's interface would not change.

## The files, and what each one covers

Every one of these is written and passing.

```
cad/freecad/
  fcprim.py            `lcs()` - a named mounting datum on a body
  build.py             knows about the `plate/` and `mod/` groups
  plate/               the parts the author drew in 2D, not printed
    xy-plate.py                XY_PLATE                257 x 162 x 2
    alpha-bot-plate.py         ALPHA_BOT_PLATE         200 x 200 x 6
    alpha-top-plate.py         ALPHA_TOP_PLATE         240 x 200 x 6, drilled
    alpha-top-plate-plain.py   ALPHA_TOP_PLATE_PLAIN   240 x 200 x 6, undrilled
    stencil-holder-back.py     STENCIL_HOLDER_BACK     L 20x20x2, 213.72 long
    stencil-holder-front.py    STENCIL_HOLDER_FRONT    the same, one hole more
    stencil-holder-back-2.py   STENCIL_HOLDER_BACK_2   L 20x20x2, 198 long
    stencil-holder-front-2.py  STENCIL_HOLDER_FRONT_2  the same, one hole more
  mod/                 Michael's own parts, transcribed from his CadQuery
    top-z-axis-bearing-mount.py  TOP_Z_AXIS_BEARING_MOUNT  what rides the rod
                       (the bracket that stands the rod up is a bottom frame
                        part: bot/bot-z-axis-bracket.py, in both hands)
  asm/
    stage0.py          the spike, kept as a regression test
    asmprim.py         helpers: link a part, ground it, make a joint, solve
    stock.py           extrusion, round rod, threaded rod, LM8UU, bearing,
                       spring
    fasteners.py       cap screws, nuts, washers, via the addon
    frame.py           the datum, the bottom frame, step 1's brackets, the feet
    carriage.py        step 2: rails, holders, LM8UU, bearing mounts, the print
                       plate and the Y rails
    alpha.py           steps 4 and 6: the slewing ring stack and both plates,
                       and which of five ways round the ring goes on
    drive.py           steps 3, 5, 7, 8 and 9: the X and Y screws, the worm and
                       its shaft, the sprung nut pairs, three handwheels
    column.py          steps 10, 12 and 13: the top frame, its rails, and the
                       linear Z axis mod in place of the author's columns
    stencil.py         steps 13, 14 and 15: the stencil clamp that rides them
    eccentric.py       steps 11 and 18: four eccentrics, and the working height
    machine.py         the whole machine, at a given pose
    check.py           interference, alignment and fit checks
    reference.py       fetches the author's build-step renders
    render.py          draws ours, and names his to compare against
    render/            the drawings themselves -- committed, they are the
                       deliverable; the .stl beside each is regenerable
  ASSEMBLY.md          this file, kept up to date as it is built
```

The plates are a **new part group rather than stock**, because unlike a rod
they have real drilled geometry that the assembly has to line up with. They are
built by `build.py` like every other part, and their volume check is arithmetic
on the drawing's own dimensions rather than a measurement of somebody's mesh -
so a mistyped hole position fails the build.

## Stages

Each stage ends with something that builds and checks, so progress is never a
half-finished document. **All of them are done**; what each one turned out to
need is under [Progress](#progress), and this is the plan they were built to.

**Stage 0 - DONE.** Prove the Assembly API works headless:
create an assembly, link two parts, ground one, add one `Fixed` and one
`Cylindrical` joint, solve, save, reopen. Joints are Python features and may
want the GUI. *If this fails, we stop and reconsider* - the fallback is scripted
placements, which is known to work but gives up the kinematics. **Do this
first**, because everything else depends on the answer.

**Stage 1 - DONE.** `stock.py` and `asmprim.py`. Place the
extrusions and the four stands. Confirm the frame's overall size against the
published 300 mm profiles, and check where an identity-placed `SR_*` and
`ECCF_*` part lands.

**Stage 2 - mounting datums.** `fcprim.lcs()`, then add datums to the parts as
each is needed. Not all 39 up front - only what the current stage joins.

**Stage 3 - bottom frame - DONE.** Brackets, rod holders, the X and Y rods,
LM8UU, bearing mounts, lead screws, carriage clamps, the print plate. First
real test: are the four X-axis bores collinear? The drives turned out to belong
with the alpha axis rather than here, because the manual builds them last and
two of the three are shared - so they live in `drive.py`.

**Stage 4 - alpha axis - DONE.** Bearing plate, inner and outer ring, worm on
its shaft, handwheel. The tooth pitch is already known (2.25 degrees on the
ring, 3.06986 mm axial on the worm), so the ratio is a check, not a guess.

**Stage 5 - Z columns and top frame - DONE.** The top extrusions,
`TOP_RAIL_HOLDER`, and - this being Michael's machine - the **linear Z axis
mod** rather than the author's M8 rods and clamps.

**Stage 6 - stencil clamp and eccentrics - DONE.** The clamp train and four
eccentrics. The stretcher of step 17 is the one thing left out; see the note at
the end.

**Stage 7 - the whole machine - DONE.** `machine.py` at a parametrised pose,
the full check pass, and renders. `stlrender.py` already draws assembled STLs,
so a render is nearly free.

## How it gets checked

The assembly is worth more as a test than as a picture: it is the first thing
that can catch an error in a part that its own volume and point checks cannot.

1. **Interference** - pairwise `common()` on every placed pair of solids. Any
   overlap above a small tolerance is a bug in a part or a placement. Clearance
   holes must be genuinely clear.
2. **Collinearity** - every bore that shares a rod must have a common axis. The
   four LM8UU on the X rod, the two rod holders, the clamps.
3. **Fit** - an 8 mm rod must pass every bore assigned to it; report the tightest
   clearance found, which also tells us the intended fits.
4. **Fastener alignment** - each screw hole must line up with the tapped hole or
   nut slot it drives, within tolerance. This exercises hole positions across
   part boundaries, which nothing has tested yet.
5. **Travel** - drive each axis to both ends and re-run interference, so the
   checks cover the machine's whole envelope rather than one pose.
6. **Overall size** against the published dimensions.
7. **Section area.** `stock.py`'s T-slot profile comes out at 196.1 mm2, and a
   real 20 x 20 slot 6 extrusion is catalogued at 0.53 kg/m, which at
   2.70 g/cm3 is 196. That is a sharp check on a section, and it caught a bad
   one: the cavities used to be plain rectangles, they met across the
   diagonals, and the profile came out as **five separate lumps** with the
   centre boss floating. See `stock._slot`.
8. **Connectedness** - and the other half of interference, which was missing
   for a long time: no solid may touch *nothing*. `check.connected` joins two
   solids when they come within a bolted joint's worth of each other and
   insists the whole machine is one piece. Interference can only say that two
   parts share space they should not; it is blind to a part hanging in mid air,
   which is exactly what a machine that falls apart looks like. It found the Z
   bearing mounts 8 mm off the bar they bolt to, and four hand levers with
   nothing to hold.

Michael added: Check also render pictures and compare them with existing pictures from the website manual.

## Risks, and what happens if they bite

* **Headless joints may not work.** Stage 0 exists to find out on day one.
  Fallback: scripted `App::Link` placements, adding joints in the GUI later.
* **Solver convergence.** Over-constrained assemblies fail unhelpfully. Build
  one joint at a time and solve after each, so the failing one is obvious.
* **The datum may not be what the parts imply.** Stage 1 tests it cheaply,
  before anything is built on top.
* **Missing information.** The build page gives stock sizes but not every
  position. Where it is silent, positions come from the parts' own mating
  features - which is the better source anyway, and is what the checks confirm.

## Open questions

1. **Fasteners** - the addon, or drawn here? (recommendation above: drawn here).
Michael: See comment above
**Resolved: the addon**, and it is installed. See the fasteners section.

2. **Are the published quantities right?** 32 x M4x10, 8 x LM8UU, 4 stands. They
   will be checked against the parts as each stage is built; a mismatch is worth
   knowing about either way.
Michael: Should be correct, but better double check.
**Checked twice, and all three are right.** 8 x LM8UU and 4 stands are what
steps 1 and 2 list. The 32 x M4x10 is there too - an earlier pass through this
file said it was not, and that was wrong, from reading a summary of the page
rather than the page. The parts settle it anyway: five gussets at five bolts,
the X bracket at three and two right angle connectors at two make **exactly
32**, with none left over. That is also the evidence that the **four feet are
not separately bolted** - each one hangs on the corner bolt of the gusset above
it, which is what its 7 mm counterbore is for. `frame.check_bolts` counts it.

3. **The aluminium plates and L profiles** - the 257 x 162 print plate, the
   200 x 200 x 6 alpha plate, the stencil L profiles. Plain rectangles unless
   you have the real drilling patterns, in which case they are worth having.
Michael: In the "technical drawings" folder are 2D drawings of the plates and the L-profile. You may create also parts in Freecad of them first.
**Done - all five, with their real drilling.** See `plate/`. They are not plain
rectangles: the XY plate has sixteen 3.2 mm holes, the fixed alpha plate has a
122 mm bolt circle and 28 tapped holes, and the rotating one has an 83 hole
workholding grid.

### Settled, by reading the manual instead of guessing

Both of the questions that were open here are now closed, and neither needed
the hardware. They needed the manual's own step lists and a hard look at its
renders.

1. **How do the corners meet, and which way round is the 2040?**
   **Butt joints, and the 2040 lies flat.** Zoom the manual's STEP_1 render on a
   corner and an extrusion **end face** is there, T-slots and all, where a mitre
   would show a diagonal. Butt joints do not care how wide a member is, so the
   2040 lies flat at 40 x 20, every member's top and bottom are flush, and the
   four feet stand level. `check_level` had already argued for exactly this by
   failing.

2. **How long are the rails between their holders?**
   **The rail length *is* the span.** The top frame settles it without
   ambiguity: 2 x 2020 x **280** between two 300 mm members, and rails of
   8 x **280**. So a rail runs the full distance between the inner faces of the
   two members it bolts to. The bottom frame's X rails are 300, so its side
   members are 300 apart, and with a 20 mm member one side and the 40 mm 2040
   the other the frame is **360 x 300** - not the 300 x 300 square stage 1
   first assumed, though every member is still 300 as the manual lists.

### Settled since, by the assembly itself

3. **`ALPHA_BOT_PLATE` is not symmetric** - and it is right. The corner
   clusters of M3 at x = -93.7 and -73.4 are the **worm shaft's two saddles**,
   and the worm exists on one side of the plate, so its saddles do too. What
   proves it is a number neither part states: those clusters put the shaft
   **83.55 mm** from the alpha axis, and the ring's pitch radius plus the
   worm's own is **83.48**. A 2D drawing and a reverse engineered mesh agreeing
   to 0.07 mm is not a coincidence. See `drive.py`.

4. **`STENCIL_HOLDER_BACK`'s end holes are at +-103.11, and that is the top
   frame's rail spacing.** The across-the-leg figures are still the least
   certain thing in that part, but the *lengthways* ones turned out to settle
   something else entirely: those end holes bolt the angle to a bearing mount
   on each rail, so the rails are **206.22 apart** - replacing the +-60 stage 5
   had read off a render. The angle's own odd length falls out of it:
   103.11 + 3.75 is half of 213.72, and the assembly measures the 3.75 back.

5. **Which way the stencil angles' uprights face - and where the bar sits.**
   Settled by `TOP_CLAMP_BEARING_MOUNT_1`'s own dimensions, not by a guess.
   The mount's plate reaches **sideways** off the rail, so the clamp bar sits
   beside the rail rather than under it: the upright stands **up**, and the
   bar stops **9 mm short** of the rail, so no part of the clamp is ever under
   one. Five numbers agree and none was used to get the others - the mount's
   two cross bolts are 9.2 apart and so are the angle's two end holes; the
   mount's end flat is 2 mm long and the upright is 2 mm thick; that flat is
   9.0 from the rail's axis and the angle's end is 106.86 from its middle, so
   the rails run at **115.86**, which is also 103.11 + 12.75 from the other
   end of the same joint. The `OPEN_PAIRS` tuple is now **empty**.

6. **The mod's own two Z parts differ by 2 mm, not 8.** `BOT_Z_AXIS_BRACKET`
   stands the rod 11.55 mm off the face it bolts to and
   `TOP_Z_AXIS_BEARING_MOUNT` reaches 13.55 in from the bore. The 8 mm was an
   artefact of there being no hinge bar: with it, the flange lies on the bar
   and the bore is on the rod, and the 2 mm comes out as the top assembly
   sitting 2 mm inboard of the bottom frame. `column.check_reach` says so.

### Still open, and worth a glance from you

7. **There is no eccenter body in the repository.** `eccf/` has `ECCF_BOT`,
   `_HEIGHT`, `_MOUNT`, `_TOP` and `_LEVER` but nothing for the eccenter that
   turns in the mount's collar - the part the lever's two cheeks grip between
   them. `check.connected` is what noticed: the outer cheek of all four levers
   has nothing to reach. They are listed in `machine.py`'s `ADRIFT` and
   reported every build.

8. **Which of `TOP_CLAMP_BEARING_MOUNT_1` and `..._2` goes on which rail.** A
   bar's two ends are opposite hands, which is why the author drew a mirrored
   pair rather than using one part twice; which end takes which is a coin toss
   here and nothing depends on it.

## Progress

**Stage 0 - done.** [`asm/stage0.py`](asm/stage0.py), kept as a regression test
because a FreeCAD upgrade could take any of this back. What it establishes:

* the Assembly workbench drives fine from `freecadcmd`, no GUI;
* **a joint can reference a `PartDesign::CoordinateSystem`**, and the datum's
  own placement carries through into the assembly - so the plan's central bet
  holds and joints never have to name a face;
* `Fixed` moves a part to exactly the placement the joint implies, and
  `Cylindrical` puts a bore on its rod while leaving the slide and spin free -
  both checked numerically, not by eye;
* it survives save, close and reopen.

Three things about the API cost real time, all of them silent rather than loud,
and all three are now written down in `asmprim.py`'s docstring: a cross-document
link needs the owner document saved **first**; anything not grounded is fair
game for the solver to move instead of the part you meant; and `solve()` returns
**-1** on failure rather than raising, leaving every placement untouched, so an
unchecked call cannot be told apart from success. `asmprim.solve` raises.

**Stage 1 - done.** [`asm/frame.py`](asm/frame.py). The datum above, the four
mitred extrusions and the four stands, all grounded and solved. It checks its
own work: the frame comes out 300 x 300, centred, with its top face on Y = 0,
and the machine stands on Y = -47. A render of it against the author's STEP_1
agrees.

**Fasteners - done.** [`asm/fasteners.py`](asm/fasteners.py), wrapping the
addon: ISO 4762 cap screws (the current number for DIN 912), ISO 4032 nuts,
ISO 7089 washers, all real geometry and all generated headless. Two things had
to be found out the hard way and are written up in that file:

* importing the addon before `Part` is a **segmentation fault**, not an
  exception, so the import order there is deliberate;
* each fastener is **baked into a plain `Part::Feature`** and the addon's own
  `FeaturePython` thrown away, so the finished assembly can be opened by
  somebody who does not have the addon. That was the plan's original reason for
  preferring hand-drawn screws, and baking gets both halves of it.

The addon has no T-slot nut among its 307 types, so `slot_nut()` is drawn here.

**Stage 2 - done for the infrastructure.** `fcprim.lcs()` is written and proven,
and `BOT_RAIL_HOLDER` now carries the first real datums - `RAIL`, `MOUNT`,
`BOLT1`, `BOLT2` - which resolve correctly through `asmprim.at()`. Adding them
left the part's volume check untouched, which is the point: datums are inert.
The rest of the parts get theirs as the stage that joins them needs them.
## Stage 3 - the X axis

[`asm/carriage.py`](asm/carriage.py). Manual step 2. The four rail holders, the
two 300 mm rails and the four LM8UU that ride them, on the 340 x 300 frame.

Measuring `BOT_RAIL_HOLDER` before placing anything is what made this tractable,
because its own geometry pins it down completely:

* **the rail bore and both bolt holes are parallel**, and the bolt heads
  counterbore from the far end - so the screws pull the collar flat against a
  face, and the rail leaves that face at right angles;
* **the two bolts are 18.583 mm apart**, not a multiple of 20, so they cannot
  be in two slots of a 20 mm profile. Both sit in **one** slot, which fixes the
  holder's orientation: its long axis along the slot, the rail out of the face;
* the bore sits **1 mm off the slot centre line**, which is the entire reason
  this part is not symmetric, and puts the rail at Y = -11.

Everything else follows from numbers already established, so nothing here is
placed by eye:

| | where it comes from |
|---|---|
| rails run X -150 .. +150 | the side members' inner faces, 300 apart |
| rails 222 apart, at Z = +-111 | the print plate's four hole clusters |
| bearings at X = +-67.5 | the same clusters; step 2's 16 M3x6 is 4 per mount |
| rail axis at Y = -11 | the 2020's slot centre line, less the holder's 1 mm |

The print plate is **162 across the rails and 257 along them**, not the other
way round: the Y rails are 244 and have to fit on it.

**The collinearity test passes** - the plan's first real test, and the first
thing the assembly can catch that no single part could. Each holder passes its
own volume and point checks and they could still fail to line up; both rails'
bore pairs come out parallel to 0.0 degrees and offset by 7e-14 mm.

Then the print plate, the four `BOT_BEARING_MOUNT_X_AXIS` that stand on it, and
the two Y rails clamped in their troughs.

**Which way round the plate goes was decided by its own bolt pattern**, not by
eye. The mount bolts down with four screws at 17 by 26.7 mm; the plate's holes
come in fours at 76 - 59 = **17** one way and 124.35 - 97.65 = **26.7** the
other. Only one orientation makes those meet, and it puts the plate's 257
across the rails and its 162 along them. Two things then fall out and both
check: each mount's outer face lands **flush with the plate's edge** at
Z = 128.5, and the 244 mm Y rails cross the 257 with 6.5 mm to spare each end.

**The fastener alignment check passes with zero error.** All sixteen mounting
bolts find a hole, the worst off by 0.000 mm. That is worth more than it
sounds: the plate comes from the author's **DXF drawing** and the mount from a
**reconstruction of his STL**, by different routes months apart in the original
work, and their hole patterns agree exactly. It is the first evidence either
one is right about anything beyond its own outline.

The mount is the corner of the XY stage and carries all three axes at right
angles, which fixes the whole stack once the bearing is on the rail:

| | Y |
|---|---|
| print plate, top face | -22.6 |
| X rail | -11 |
| Y rail, in the troughs | +3.6 |

So the plate hangs inside the frame's opening a little below its underside -
which is right for what it is, a carrier for the XY stage rather than a work
surface - and the Y rails run above the frame's top face, which is where the
alpha axis has to be since it rides them.

**Stage 3 is complete as far as the manual's step 2 goes.** The lead screws,
their preload springs and the handwheels are steps 7 to 9, and the manual does
them *after* the alpha axis - steps 3 to 6 build and fit that first, and the
drives are what finally tie the two together. Following its order rather than
the plan's guess, they come after stage 4.

## Stage 4 - the alpha axis

[`asm/alpha.py`](asm/alpha.py). Manual step 4.

### The SR group goes in upside down

This was the one thing stage 4 had to settle, and the parts settle it
themselves. In the meshes' own coordinates `SR_BEARING_PLATE` sits *above* the
rings - Y 8 .. 11 against the rings' -2 .. 10 - which would drive it straight
through the rotating plate. Turned over, everything lands at once:

| flipped | Y | |
|---|---|---|
| `SR_BEARING_PLATE` | -11 .. -8 | bolted flat to the fixed plate |
| `SR_INNER_RING` | -8 .. 2 | **seats on it exactly**, 0.0 mm |
| `SR_OUTER_RING_W_GEAR` | -10 .. 2 | **clears the fixed plate by 1 mm** |
| `ALPHA_TOP_PLATE` | 2 .. 8 | bolted to the outer ring |

Two things make that more than a coincidence of bounding boxes.

* **The ring that turns clears the fixed plate by exactly 1 mm, while the ring
  that does not seats on the bearing plate with exactly none.** A part that
  turns must not rub; a part that does not turn should be supported. The two
  rings differ by precisely the millimetre that needs - and only this way up.
* **Both of the manual's screw lengths come out right.** Step 3's **M3x8**
  passes the 3 mm bearing plate and bites 5 mm into the 6 mm fixed plate;
  step 4's **M3x14** passes the 6 mm top plate and bites 8 mm into the 12 mm
  outer ring. Neither works the other way up.

So the fixed side is bottom plate, bearing plate, inner ring; the turning side
is outer ring and top plate; and the worm drives the outer ring's teeth. The
whole axis stands 25 mm tall, which is the gap the manual's STEP_4 render shows
between its two plates.

### Both interfaces were exact before the stack was known

The two bolted interfaces cross the boundary between work done by completely
different routes - plates transcribed from the author's 2D drawings, rings
reconstructed from his STLs, months apart in the original effort:

| interface | drawing side | reconstruction side | agrees |
|---|---|---|---|
| fixed plate to bearing plate | `ALPHA_BOT_PLATE`, 4 holes | `SR_BEARING_PLATE`, 4 pads | r = **61.000**, 90 deg apart |
| turning plate to toothed ring | `ALPHA_TOP_PLATE`, 5 holes | `SR_OUTER_RING_W_GEAR`, 5 bosses | r = **75.450**, 72 deg apart |

With the sixteen carriage bolts in `carriage.py`, every mounting interface
tested so far agrees to the micron.

### The alpha axis does not go all the way round

`SR_OUTER_RING_W_GEAR` carries **29 teeth at 2.25 degrees**, and only over a
**72 degree sector** of the rim; the rest is plain. It is not a gear that turns
continuously, it is a sector that rocks, and the travel is about **+-32.6
degrees** - which is what a stencil wants: enough to square a board up, not
enough to spin it. 360 / 2.25 = **160** teeth for a complete rim, so a single
start worm gives 160:1 at the handwheel - the ratio the plan expected, arrived
at as a check rather than a guess.

**Still to place:** the worm and its M5 shaft, which belong with the lead
screws and handwheels of steps 7 to 9. `ALPHA_BOT_PLATE` has the 10 mm hole for
it at r = 75.45, so the mesh radius is already known.

## Stage 5 - the Z columns, the hinge bar and the lid

[`asm/column.py`](asm/column.py). Manual steps 10, 12 and 13.

**The top frame is where the frame rule came from**, so applying it back is not
circular: the rule was read off the top frame's own unambiguous arithmetic and
then *applied* to the bottom. Its rails are 280 and so are two of its
extrusions, so the two 300s are the sides, their inner faces are 280 apart, and
the lid is **320 x 300**.

**And it is a lid, not a frame.** The third 300 is the **hinge bar**: it lies
outboard of one side member, the two hinges bridge their top faces, and it is
the bar - not the lid - that the Z rods carry. 320 + 20 = **340**, the bottom
frame's own width, and the whole top assembly hangs off two rods with nothing
else holding it, so the rods put it where it is. See "Steps 10, 12 and 13"
below for the arithmetic that lands its outer face at 168.0.

Its two 280 mm rails come out collinear to 6e-14 mm, the same check the X rails
passed, and they go up with the lid when it opens.

### How far the Z axis adjusts, and why (the author's arrangement)

Step 18 says to "adjust the height of the top frame" without saying by how
much. The rod does: it is **M8 x 140**, `BOT_CLAMP_Z_AXIS` grips **40** of it
and `TOP_CLAMP_Z_AXIS` **34**, and the two cannot overlap, so

    140 - 40 - 34 = 66 mm of travel

`check_travel` reports it from the parts rather than asserting it, so a rebuild
that changed a clamp would change the answer -- and swapping in the mod's collar
and bearing did exactly that, to 92 mm. There is also a reach check:
the rod stands 19.1 mm outboard of the top frame's face and the top clamp is
30.2 mm wide, so it gets there.

### What is left out, and what is inferred

* **`TOP_BRACKET`, 8 off.** Among the four parts with no STL in the repository,
  so there is nothing to place. Two per corner, above and below - the STEP_12
  renders show the pair. Nothing depends on its geometry.
* **The hinge itself is bought**, not printed or drawn, so `stock.hinge_leaf`
  is an ordinary 40 mm butt hinge of about the right size rather than a
  measurement of the author's. Its two leaves are separate solids, because a
  hinge is the one place in the machine where two parts have to move relative
  to each other and one solid could only ever belong to one of them.
* **The two hinges' stations along the bar**, read off the renders. Nothing
  else depends on them.

*(An earlier pass left the third 300 mm extrusion out, on the reading that the
STEP_12 render was "plainly a four member rectangle" and the odd one was
probably the bar the stencil clamp hangs from. It is not: it is the hinge bar,
and leaving it out is what left the Z bearing mounts with nothing to bolt to.)*

## Stage 7 - the whole machine

[`asm/machine.py`](asm/machine.py) and [`asm/check.py`](asm/check.py). Every
sub-assembly in one document at a given pose - X and Y along the rails, Z on
the columns, alpha on the ring, and **lid** for how far the stencil frame is
swung up - so the machine can be driven and re-checked rather than frozen in
one position. Any of them can be given on the command line:

    ... asm/machine.py lid=60          the stencil lifted, to put a board in
    ... asm/machine.py alpha=15 x=20   somewhere else on its axes

Every check runs in whatever pose it is built at, so opening the lid tests the
hinge rather than just drawing it.

**It stands up in one piece with nothing fouling.** 139 solids, 9591 pairs, 203
whose bounding boxes touch at all, and no overlap above 1 mm3 once the pairs
that are *meant* to touch - a rod in its bearing, a nut on its screw, a worm in
its wheel
- are excused.

    envelope 392.8 x 199.4 x 340.7 mm      X -196.0 .. 196.8
                                           Y  -59.4 .. 140.0  (up)
                                           Z -154.7 .. 186.0

The handwheels are what make it wider than the frame in every direction, and
the Z rods what make it 140 tall with the lid down at 66. With the lid at 60
degrees it grows to **403 mm** tall and is still clash free and still one
piece.

**And it is one piece.** `check.connected` joins two solids when they come
within a bolted joint's worth of each other and insists the machine is a single
component. That is the check that catches what interference cannot: a part
bolted to nothing. It found the Z bearing mounts 8 mm off the bar, and four
hand levers holding a part the repository does not have.

### The interference check earned its keep immediately

It found the 2040 in the wrong place. Stage 1 had it lying flat across the
front, from Z = -150 to -110; the X rails sit at Z = +-111 and the print plate
reaches +-128.5, so **the carriage ran straight through it**. Nothing in stage
1, 3 or 5 could see that, because each of them only ever looked at its own
parts.

As a **side** member instead it is clear of both, since the rails run between
the side members rather than across them. That is now the model, and it makes
the frame not symmetric about the origin on the author's machine - the origin
follows the rails, and the 2040's extra 20 mm hangs off the side where
`BOT_BRACKET_X_AXIS` and the X drive go.  The mod's four equal members make it
340 x 300 and symmetric, but the drive is still on that side.

This is exactly what the plan expected the assembly to be worth: "the first
thing that can catch an error in a part that its own volume and point checks
cannot".

### The renders

[`asm/render.py`](asm/render.py) draws four orthographic views of each assembly
into [`render/`](render/) and prints which of the author's build-step images it
should be held against:

| ours | his |
|---|---|
| `render/BottomFrame.png` | STEP_1_1, STEP_1_2 |
| `render/Carriage.png` | STEP_2_2 |
| `render/Alpha.png` | STEP_4_2 |
| `render/Drive.png` | STEP_6_1, STEP_9_1, STEP_9_2 |
| `render/Column.png` | STEP_10_1, STEP_12_1 |
| `render/Stencil.png` | STEP_13_1, STEP_15_2, STEP_16_1 |
| `render/Eccentric.png` | STEP_18_4 (step 11 has no render of its own) |
| `render/Machine.png` | STEP_18_4 |
| `render/MachineOpen.png` | nothing in the manual - hold it against `docs/img/open-top.jpg` |

That is the half of the comparison a script can do - it makes ours and names
his. Deciding whether they agree still wants eyes. `reference.py` fetches his
into `reference/`, which stays git-ignored because they are his images; ours
are committed because they are the deliverable. The `.stl` beside each `.png`
is a by-product and is ignored.

**Holding them up against each other is what found several of the things
below**, and it is worth doing rather than skipping: the drives' layout, the
right angle connectors standing on the frame's corners, the order of the parts
along a stencil rail, and the worm's own saddles all came off the author's
images once the numbers had narrowed the possibilities down.

### What the comparison says, looked at rather than scripted

Against his STEP_18_4, which is the only render he made of the finished
machine, ours agrees on everything structural: two frames one above the other,
the print plate slung under the lower one with its screw along the front, the
alpha plate filling the middle, the two stencil angles running across the top
frame with the nut holders along the lower one, three handwheels on three
different sides, and the Z rods standing at two corners of one long side.

Four differences, all of them known and all of them deliberate:

* **his Z columns are threaded rod with a knurled knob on top; ours are the
  mod's smooth rod and bearing.** That is the mod, and it is also why his knobs
  are missing from ours.
* **his top frame has eight `TOP_BRACKET` corner plates.** Ours has none;
  there is no part for them.
* **his stretcher is on the top frame and ours is not** - see below.
* **his eccentrics stand at the corners of one side and ours are two per side,
  further in.** Ours are placed where the X screw is not, which his machine
  does not have to worry about because his X screw is on the other side of the
  frame from his eccentrics.

`stlrender.py` was already in the repository and does the drawing with nothing
but Pillow, which the flatpak's own Python turns out to have - so this
tessellates and draws in one pass instead of shelling out.

## Steps 3, 5, 7, 8 and 9 - the three screws

[`asm/drive.py`](asm/drive.py). The manual builds the drives *after* the alpha
axis, and two of the three are shared between the carriage and it, so they all
land in one file rather than in stage 3.

| screw | along | held by | its nuts are in | agrees to |
|---|---|---|---|---|
| X | machine X | `BOT_BRACKET_X_AXIS` on the frame | `BOT_RAIL_CLAMP_X_DRIVE` | **0.378 mm** |
| Y | machine Z | `BOT_RAIL_CLAMP_Y_AXIS_1`'s tube | `..._Y_AXIS_DRIVEN`'s arm | **0.000 mm** |
| worm | machine Z | two saddles on the fixed plate | it drives the ring | **0.07 mm** |

Each of those numbers is two parts that were reconstructed separately agreeing
about where a screw is. The X screw's height comes out at Y = 13.000 from the
bracket and Y = 13.000 from the clamp, and its station from Z = -140.000 and
-139.622. The Y screw's two ends agree exactly.

### What the webbed arms are for

`STATUS.md` noticed long ago that `BOT_BEARING_MOUNT_Y_AXIS_DRIVEN` and
`BOT_RAIL_CLAMP_X_DRIVE` are hollowed from both faces over *identical* spans,
and could not say why. The manual's STEP_8 render says why: **the two M5 nuts
of steps 5 and 8 live in those hollows**, one either side of the deep one, with
the spring between them. Sprung apart, the two nuts bite opposite flanks of the
same thread, which is a backlash free nut made out of two nuts and a spring.

That also settles which end of each screw is which, because a nut carrier has
to travel and a bearing has to stay put - so both handwheels are on the fixed
side and neither of them moves with its axis.

### Two parts that are not what their names say

Both were named from the mesh alone, and the assembly reads them differently:

* **`BOT_BEARING_MOUNT_Y_AXIS` is an LM8UU holder**, not a screw bearing. Its
  seat is 15.2 with 13.2 lips, which is an LM8UU dropped in from below; four of
  them clip the alpha plate onto the Y rails, which is what step 6's "clip the
  Alpha Axis Assembly to the LM8UU bearings" means.
* **`BOT_ROD_HOLDER_ALPHA_AXIS` carries the worm's shaft.** Its bore is 5.3 -
  an M5 clearance, not an 8 mm rail.

Reading them that way is what closed the last soft number in the machine: the
alpha plate does not rest on the bearings at Y = 11.1, it **hangs from the
holders' flanges at 15.2**.

## Steps 10, 12 and 13 - the hinge bar, the lid, and the linear Z axis

[`asm/column.py`](asm/column.py).

**The top frame is a lid**, and that is the whole of step 12. It is two bodies,
not one:

    hinge bar      one 2020 x 300, carried on the two Z rods
    -- 2 hinges, screwed to both top faces --
    the lid        2 x 2020 x 300 + 2 x 2020 x 280 + 8 x TOP_BRACKET,
                   and everything the stencil clamp is made of

That is what step 12's **third** 300 mm extrusion is for. An earlier pass here
called it "most likely the bar the stencil clamp mounts to" and left it out; the
manual's STEP_12 renders show it plainly, lying outboard of one side member with
the two hinges bridging their top faces and a `TOP_CLAMP_Z_AXIS` at each end,
and so do Michael's own photographs in [`../../docs/img/`](../../docs/img/).

It matters because it is how the machine is *used*. A stencil printer needs the
stencil lifted clear to put a board in and lowered onto it to print; the lid is
what does that. `POSE["lid"]` opens it, and

    ... asm/machine.py lid=60

builds the machine with the stencil up and saves it as `MachineOpen`, which is
the render to hold against `docs/img/open-top.jpg`. The interference and
connectedness checks both run in that pose too, so the hinge is tested and not
just drawn.

**Where the top assembly sits in X follows from the rods**, because nothing else
holds it: the bracket's collar stands the rod 11.55 out from the bottom frame's
face at 170, and the bearing mount's flange reaches 13.55 in from the bore, so
the hinge bar's outer face lands at **168.0**. Bar plus lid is 20 + 320 = **340**
= the bottom frame's own width, which is the design; the 2 mm it lands off flush
is the difference between Michael's two mod parts, each of which measures the
rod from a different feature of itself.

### The hinge locks

The third of Michael's mods, and the one that exists *because* the lid does:
"the hinges I used still allowed for some play between the back of the frame
and the moving part". `TOP_HINGE_LOCK_BACK` hooks over a member on a 20.1 mm
square channel; `TOP_HINGE_LOCK_FRONT` bolts flat to a member's face with two
M4 and stands a boss off it; one M3 runs along the member from the boss into a
nut the back half holds.

Both are in [`../mod/`](../mod/), and unlike the two Z axis parts they could be
checked against the source rather than only against the assembly: CadQuery
installs, so `hinge-lock.py` runs, and each transcription's volume matches that
solid **exactly** once its cosmetic chamfers and fillets are suppressed. Every
hole position was read off the real solid.

**How it grips is in one number: the channel is 24 mm deep for a 20 mm
member.** Those extra 4 mm are not slop, they are the mechanism. The hook goes
over the lid's own side member *and laps 4 mm onto the hinge bar beyond it*, so
it spans the joint; the M3 then pulls the hook back against the front half,
which is bolted flat to the lid's member. Tighten it and the two bars are
clamped together across the hinge - "repeatability across multiple applies".

That was not obvious, and what turned it up was **building the machine with the
lid open**: the hook fouled the hinge bar by 111 mm3, which at first looked like
a bad placement and is in fact the lock doing its job. `check_lap` now measures
the 4 mm every build, and the lock is left off the open pose, because a fitted
one has to come off before the lid can rise.

Two more of the source's numbers agree and neither was used to get that:

* the back half's M3 sits **7.5 mm** beyond the channel's closed end and the
  front half's **7.5 mm** out from the face its plate bolts to, so the two are
  one bolt only when the closed end lands on that same face - which it does, on
  the lid member's inboard face. `check_lock` proves they are one axis;
* its two M4 are **24 long**, a 4 mm wall and a 20 mm extrusion exactly, so
  they bolt the hook on straight through the member. The stock section here has
  no such holes, so what the interference check sees is the block closing on
  the bar, and that pair is listed as meant to touch.

The columns themselves are Michael's mod, and swapping them in changes three
things:

* the M8 x 140 threaded rods become **8 mm linear rods** of the same length,
  stood up on a `BOT_Z_AXIS_BRACKET` at two corners of the bottom frame, one
  of each hand;
* the hinge bar **rides them on an LM8UU** in a `TOP_Z_AXIS_BEARING_MOUNT`
  instead of being clamped to them, so it slides instead of needing a hex key -
  which is also why this machine has four eccentrics where the author's has two:
  with a sliding Z the hinge end needs a stop of its own;
* the travel goes from **66 mm to 92**, because a collar and a bearing take 24
  mm of rod each where the author's two clamps take 40 and 34.

The Z axis also had to move to the **+X side**, opposite the drives. The
author's columns and his 2040 are both on -X, and so is `BOT_BRACKET_X_AXIS`;
with the 2040 gone and the bracket still there, a column at that corner runs
straight into it - which is what the interference check said when it was tried.
The README's own photograph has the rods on the side away from the handwheels.

## Steps 13, 14 and 15 - the stencil clamp

[`asm/stencil.py`](asm/stencil.py). The lid's two rails are not an axis of the
machine at all: they are what the **stencil clamp** slides on. A clamp bar is a
**pair** of angles with the foil pinched between them - step 14 buys two of the
213.72 and step 15 two of the 198, and their 6 and 4 holes are exactly the 12
and 8 screws those steps list. Two bars, four angles; a spring on each rail
pushes them apart and the foil comes taut.

**The bar sits beside its rails, not under them.** The bearing mount's plate
reaches sideways off the rail along the bar, and the angle bolts to it three
ways at once: two M3 up through the leg and one along the rail through the
upright. Five of that part's own dimensions and the angle's drawing agree, and
none of them was used to get the others:

* the mount's two cross bolts are at -3.6 and +5.6, **9.2 apart**; the angle's
  two end holes are 6.4 and 15.6 from its corner, **9.2 apart**, and laying the
  corner on the mount's end at -10 puts them at -3.6 and +5.6 exactly;
* the mount's end is flatted for its **first 2 mm** "so that end sits against
  whatever it bolts to" - and the upright is **2 mm** thick;
* that flat is **9.0** from the rail's axis and the angle's end is 106.86 from
  its middle, so the rails run at **115.86**; independently, the end holes are
  103.11 from the middle and the mount's bolt line 12.75 in from the rail,
  which is 115.86 as well;
* the plate ends 7.5 above the rail's axis, and standing the upright flush with
  that puts the M3 through it **6.14** below the axis. The mount's own bolt is
  at **6.1385**.

So the upright stands up, the bar stops 9 mm short of each rail, and nothing of
the clamp is ever under one. This replaced +-103.11 as the rail spacing and
emptied `OPEN_PAIRS`.

## Steps 11 and 18 - the eccentrics

[`asm/eccentric.py`](asm/eccentric.py). Four of them, and on this machine all
four are `ECCF_*`: the mod puts the front eccentric at the back too, in place of
the author's unpublished `ECCB_*`.

The `ECCF` group is pre-positioned, so one number places each one - its plate
on the frame's top face - and the four bodies then stack contiguously to 45 mm.
They sit on the two **side** members: `ECCF_BOT`'s bolt line wants a slot
running its way, and the front end member is where the X screw runs at Y = 13,
which the interference check found them standing in.

They reach: with the clamp seated where its mount puts it, `ECCF_HEIGHT`
has **0.8 mm** to wind out, which is well inside a thumb nut's range.

## What is left out, and why

* **`TOP_BRACKET`, 8 off, step 12.** No STL in the repository; left out on
  Michael's instruction. Two per corner, one above and one below - the manual's
  STEP_12 renders show the pair. Nothing depends on its geometry: the lid's
  size comes from its own members and its rails' spacing from the stencil
  angle's joint with its mounts.
* **The eccenter body.** `eccf/` has five parts and none of them is the
  eccenter that turns in `ECCF_MOUNT`'s collar. See open question 7.
* **Nothing of Michael's own.** The hinge locks were the last of it and they
  are in, in `mod/` and on the machine - see below.
* **The stretcher, step 17.** Its parts exist -
  `TOP_CLAMP_SPANNER_CASE_1` and `_2`, `..._COUNTER`, `..._HANDWHEEL` - but
  unlike everything else in the machine they do not interlock at a bore or a
  bolt circle with anything already placed, so where the train goes would be
  read off a render rather than derived. It is the one thing in the manual that
  is modelled as parts but not as an assembly.
* **The author's own Z axis and rear eccentric.** `BOT_CLAMP_Z_AXIS`,
  `TOP_CLAMP_Z_AXIS`, `TOP_HANDWHEEL_Z_AXIS`, `BOT_Z_AXIS_COUNTER_HOLDER` and
  `..._KNOB` are all still reconstructed and still build; this machine simply
  does not use them.
