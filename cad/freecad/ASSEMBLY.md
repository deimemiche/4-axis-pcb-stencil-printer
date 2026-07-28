# Plan: assembling the machine

The 39 printed parts are rebuilt and each one is checked against the mesh it
came from ([`STATUS.md`](STATUS.md)). This is the plan for putting them
together into a real FreeCAD assembly - one that is *correct*, that can be
rendered and exploded, and that can be extended later.

**Stages 0, 1, 2, 4, 5 and 7 are built, stage 3 as far as the XY carriage**, along
with the fasteners and the six parts the author drew in 2D. The Assembly
workbench works headless and joints can reference named datums, so the plan
below stands as written rather than falling back to scripted placements. What
is done, and what it found, is at the bottom under [Progress](#progress).

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
they were never reconstructed and the machine cannot be completed without them:

| Part | Where | Count |
|---|---|---|
| `TOP_BRACKET` | step 12, top frame | 8 |
| `ECCB_BODY` | step 18, rear eccentric | 2 |
| `ECCB_LEVER` | step 18 | 2 |
| `ECCB_SHIM` | step 18 | 2 |

`STATUS.md` says all 39 meshes are rebuilt and that is still true - but 39 is
not the whole machine. The front eccentric (`ECCF_*`) is published and the rear
one (`ECCB_*`) is not, and the top frame's own brackets are missing too. Stages
5 and 6 will reach them; there is nothing to reconstruct from, so they will
have to be drawn from the renders or left out and flagged.

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
  and -150 .. +150 along.  The frame reaches -190 .. +170 across, because the
  frame is 340 x 300 and centred on it.  Y = 0 is the top of the three 2020s;
  the 2040 at the back stands on edge and rises 20 mm above it, and the one
  plane all four members share is the **underside**, at Y = -20.

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

## Files to be added

A tick is written and passing.

```
cad/freecad/
  fcprim.py            [x] gains `lcs()` - a named mounting datum on a body
  build.py             [x] knows about the new `plate/` group
  plate/               [x] the five parts the author drew in 2D, not printed
    xy-plate.py                XY_PLATE                257 x 162 x 2
    alpha-bot-plate.py         ALPHA_BOT_PLATE         200 x 200 x 6
    alpha-top-plate.py         ALPHA_TOP_PLATE         240 x 200 x 6, drilled
    alpha-top-plate-plain.py   ALPHA_TOP_PLATE_PLAIN   240 x 200 x 6, undrilled
    stencil-holder-bot.py      STENCIL_HOLDER_BOT      L 20x20x2, 198 long
    stencil-holder-top.py      STENCIL_HOLDER_TOP      L 20x20x2, 213.72 long
  asm/
    stage0.py          [x] the spike, kept as a regression test
    asmprim.py         [x] helpers: link a part, ground it, make a joint, solve
    stock.py           [x] extrusion, round rod, threaded rod, LM8UU, bearing,
                           spring
    frame.py           [x] the datum, the bottom frame, the four stands
    reference.py       [x] fetches the author's build-step renders
    render.py          [x] draws ours, and names his to compare against
    render/            [x] the drawings themselves -- committed, they are the
                           deliverable; the .stl beside each is regenerable
    fasteners.py       [x] cap screws, nuts, washers, via the addon
    carriage.py        [~] rails, holders, LM8UU, bearing mounts, the print
                           plate and the Y rails.  Still to come: the lead
                           screws, their preload springs and the handwheels
    alpha.py           [x] the slewing ring stack and both plates; the
                           worm drive goes with steps 7 to 9
    column.py          [x] the two Z columns and the top frame
    stencil.py         [!] stencil clamp, stretcher, eccentrics -- blocked,
                           see stage 6 below
    machine.py         [x] the whole machine, at a given pose
    check.py           [x] interference, alignment and fit checks
  ASSEMBLY.md          this file, kept up to date as it is built
```

`build.py` gains an `asm/` pass so the whole thing rebuilds with one command.

The plates are a **new part group rather than stock**, because unlike a rod
they have real drilled geometry that the assembly has to line up with. They are
built by `build.py` like every other part, and their volume check is arithmetic
on the drawing's own dimensions rather than a measurement of somebody's mesh -
so a mistyped hole position fails the build.

## Stages

Each stage ends with something that builds and checks, so progress is never a
half-finished document.

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

**Stage 3 - bottom frame.** Brackets, rod holders, the X and Y rods, LM8UU,
bearing mounts, lead screws, carriage clamps, the print plate. First real test:
are the four X-axis bores collinear?

**Stage 4 - alpha axis.** Bearing plate, inner and outer ring, worm on its
shaft, `Gears` joint to the ring, handwheel. The tooth pitch is already known
(2.25 degrees on the ring, 3.06986 mm axial on the worm), so the ratio is a
check, not a guess.

**Stage 5 - Z columns and top frame.** M8 rods, the four Z clamps, the top
extrusions, `TOP_RAIL_HOLDER`, the top handwheel.

**Stage 6 - stencil clamp and eccentrics.** The clamp train, the stretcher, two
eccentrics with two lever cheeks each.

**Stage 7 - the whole machine.** `machine.py` at a parametrised pose, the full
check pass, an exploded view, and renders. `stlrender.py` already draws
assembled STLs, so a render is nearly free.

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
**Checked against the page.** 8 x LM8UU and 4 stands are right. The 32 x M4x10
is not on the page at all, so it should not be trusted; the corrected stock
table above has what the page really says, including two things the old table
had wrong.

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
   **Butt joints, and the 2040 stands on edge at the back.** Zoom the manual's STEP_1 render on a
   corner and an extrusion **end face** is there, T-slots and all, where a mitre
   would show a diagonal. Butt joints do not care how wide a member is, so the
   2040 can be 20 x 40 on edge, the four members line up underneath, and the
   four feet stand level. `check_level` had already argued for exactly this by
   failing.

2. **How long are the rails between their holders?**
   **The rail length *is* the span.** The top frame settles it without
   ambiguity: 2 x 2020 x **280** between two 300 mm members, and rails of
   8 x **280**. So a rail runs the full distance between the inner faces of the
   two members it bolts to. The bottom frame's X rails are 300, so its side
   members are 300 apart, so with a 20 mm member each side the frame is
   **340 x 300** - not the 300 x 300 square stage 1 first assumed, though every
   member is still 300 as the manual lists.

### Still open, and worth a glance from you

3. **`ALPHA_BOT_PLATE` is not symmetric.** The corner clusters of M3
   (x = -93.7 and -73.4) exist on the **left of the drawing only**; the inner
   clusters are on both sides. Read twice and it is still what the drawing
   shows, but it is unusual enough to be worth confirming.

4. **`STENCIL_HOLDER_TOP`'s across-the-leg hole positions.** That drawing
   dimensions from the inner face of the opposite leg, the opposite convention
   to the lower profile, and the two views show different legs at the same
   station. Lengthways (+-25, +-75, +-103.11) and the section are certain; the
   4.4 / 13.6 / 4.36 across-leg figures are my best reading.

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
two 300 mm rails and the four LM8UU that ride them, on the corrected 340 x 300
frame.

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

## Stage 5 - the Z columns and the top frame

[`asm/column.py`](asm/column.py). Manual steps 10, 12 and 13.

**The top frame is where the frame rule came from**, so applying it back is not
circular: the rule was read off the top frame's own unambiguous arithmetic and
then *applied* to the bottom. Its rails are 280 and so are two of its
extrusions, so the two 300s are the sides, their inner faces are 280 apart, and
the frame is **320 x 300** - exactly one member narrower each side than the
bottom frame's 340 x 300, which is what lets it sit inboard of the columns.

Its two 280 mm rails come out collinear to 6e-14 mm, the same check the X rails
passed.

### How far the Z axis adjusts, and why

Step 18 says to "adjust the height of the top frame" without saying by how
much. The rod does: it is **M8 x 140**, `BOT_CLAMP_Z_AXIS` grips **40** of it
and `TOP_CLAMP_Z_AXIS` **34**, and the two cannot overlap, so

    140 - 40 - 34 = 66 mm of travel

`check_travel` reports it from the parts rather than asserting it, so a rebuild
that changed a clamp would change the answer. There is also a reach check:
the rod stands 19.1 mm outboard of the top frame's face and the top clamp is
30.2 mm wide, so it gets there.

### The two Z clamps mount completely differently

Worth recording, because assuming they were alike put both in the wrong place
until the interference check said so. `BOT_CLAMP_Z_AXIS` has its two M4 along
its own Z: it bolts flat to a **vertical face** with the rod standing off it,
and on the machine that face is the back 2040's outer face - whose 40 mm height
is exactly the clamp's own. `TOP_CLAMP_Z_AXIS`'s two M4 only pull its saw cut
shut; what holds it to the machine is a single bolt straight **up** through its
shelf into the top frame's underside.

Both now carry `ROD` and `MOUNT` datums and are placed from those rather than
by eye.

### What is left out, deliberately

* **The third 300 mm extrusion.** Step 12 lists three, and the STEP_12 render
  is plainly a four member rectangle. Step 16 then adds eight more screws and
  slot nuts, so the odd one is most likely the bar the stencil clamp hangs
  from - stage 6's business. Left out rather than guessed at.
* **The hinges and `TOP_BRACKET`.** The brackets are among the four parts with
  no STL in the repository, so there is nothing to place.
* **The columns' stations in plan.** Both Z clamps are on one side near its
  ends - the STEP_10 and STEP_12 renders agree, and the two hinges on that same
  side are what make it a lid. The exact stations along that side are read off
  the renders and are the least certain thing in this stage. Nothing else
  depends on them.

## Stage 7 - the whole machine

[`asm/machine.py`](asm/machine.py) and [`asm/check.py`](asm/check.py). Every
sub-assembly in one document at a given pose - X and Y along the rails, Z on
the columns, alpha on the ring - so the machine can be driven and re-checked
rather than frozen in one position.

**It stands up with nothing fouling.** 46 solids, 1035 pairs, 30 whose bounding
boxes touch at all, and no overlap above 1 mm3 once the pairs that are *meant*
to touch - a rod in its bearing, a clamp on what it holds - are excused.

    envelope 365.3 x 167.0 x 300.0 mm      X -195.3 .. 170.0
                                           Y  -27.0 .. 140.0  (up)
                                           Z -150.0 .. 150.0

### The interference check earned its keep immediately

It found the 2040 in the wrong place - twice, in the end, and each wrong answer
was ruled out by something real rather than by taste.

Stage 1 first had it **lying flat across the front**, from Z = -150 to -110.
The X rails sit at Z = +-111 and the print plate reaches +-128.5, so the
carriage ran straight through it. Nothing in stage 1, 3 or 5 could see that,
because each of them only ever looked at its own parts.

Moving it to a **side** cleared the carriage and passed every check - and was
still wrong, because it put the 2040 nowhere near the hinges. Michael caught
that one: the hinges mount to it, and they are on the **back**.

It is the **back member, standing on edge** - 20 mm across in plan like the
rest, 40 mm tall, with the four members flush underneath rather than on top so
it rises 20 mm proud. That upstand is what the hinges bolt to, it clears the
carriage because it is only 20 mm in plan, and the flush undersides are what
let all four feet be the same length. The frame is **340 x 300** and centred.

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
| `render/Column.png` | STEP_10_1, STEP_12_1 |
| `render/Machine.png` | STEP_18_1 |

That is the half of the comparison a script can do - it makes ours and names
his. Deciding whether they agree still wants eyes. `reference.py` fetches his
into `reference/`, which stays git-ignored because they are his images; ours
are committed because they are the deliverable. The `.stl` beside each `.png`
is a by-product and is ignored.

`stlrender.py` was already in the repository and does the drawing with nothing
but Pillow, which the flatpak's own Python turns out to have - so this
tessellates and draws in one pass instead of shelling out.

### The machine actually drives now

X and Y were accepted in the pose and then ignored -- the header printed them
and nothing read them. They drive it now, and the travel is *measured* rather
than declared: each axis is walked outwards a step at a time until either two
parts touch or a bearing runs off the end of its rod.

| axis | travel | what stops it |
|---|---|---|
| X | **+-55 mm** | the bearing mounts reach the rail holders |
| Y | **+-25 mm** | the LM8UU run off the 244 mm Y rails |
| Z | **66 mm** | the M8 rod, less what the two clamps grip |
| alpha | **+-32.6 deg** | the ring's 29 teeth over a 72 degree sector |

So the work area is **110 x 50 mm**, and interference is re-checked at every
step of the walk, which is the plan's "drive each axis to both ends and re-run
interference".

Two things had to be got right for that to mean anything. An interference check
**cannot see a carriage running off the end of its rail** -- there is nothing
left to collide with -- so `check.on_its_rod` bounds the travel instead, and
the four LM8UU that carry the alpha axis along the Y rails had to be modelled
for it to have something to measure. That completes the manual's eight: four on
X, four on Y.

And the walk had to stop re-testing the whole machine at every step. Driving an
axis cannot change whether two *stationary* parts overlap, so `interference`
takes an `only` set and looks at pairs involving something that moved. Without
it the check does not finish.

### The fasteners are in

32 screws, placed from the parts' own `BOLT` datums rather than positioned a
second time -- so they land wherever the part says its holes are and cannot
disagree with it. The counts fall out of the datums and match the manual for
what is built: 8 x M4x10 into slot nuts for the bottom rail holders, 16 x M3x6
for the bearing mounts, 8 x M4x10 for the top ones.

The M3x6 is a small confirmation in itself. Those bolts come up from *under*
the print plate and into the mount's foot -- 2 mm plus 4 mm -- and the manual
buys exactly M3x6 for them.

### An exploded view

`explode()` lifts each layer clear of the one below in build order and saves
`MachineExploded.FCStd`; `render/MachineExploded.png` is the drawing. It is an
offset applied to the assembled machine, not a second model, which is the whole
reason for keeping it in one document at a known pose.

### The one number in it that is still soft

Where the alpha assembly sits on the Y rails. Manual step 6 says only "clip the
Alpha Axis Assembly to the LM8UU bearings", so its fixed plate rests directly
on top of them at Y = 11.1. Step 7's four `BOT_RAIL_CLAMP_*` are what actually
do the clipping and they are not modelled yet; whatever thickness they add,
they add here. The spacing of the two LM8UU along each Y rail is assumed at
120 mm, and that is what sets the +-25 mm of Y travel -- closer together would
give more.

## Stage 6 - not built, and why

The stencil clamp and the eccentrics are the one stage that cannot simply be
worked out, for two reasons that are worth separating.

* **Half the parts do not exist.** `ECCB_BODY`, `ECCB_LEVER` and `ECCB_SHIM` -
  the *rear* eccentric, step 18 - have no STL in the repository, nor does
  `TOP_BRACKET`. There is nothing to reconstruct from. The front eccentric
  (`ECCF_*`) is published and its four parts stack contiguously under an
  identity placement, so that half could be built.
* **Step 11 has no render.** Every other step in the manual has at least one
  CAD image; the front eccentric has none. So the one group whose parts *do*
  exist is also the one with no picture of how they go together.

The honest position is that stage 6 needs either the missing meshes from the
author or a decision to draw the rear eccentric from scratch, and that is a
choice for you rather than a gap to paper over.

**Next**, in the order the manual would do them: the lead screws, springs and
handwheels of steps 7 to 9, which finish stage 3 and also carry the worm that
drives the alpha ring; then whatever is decided about stage 6.
