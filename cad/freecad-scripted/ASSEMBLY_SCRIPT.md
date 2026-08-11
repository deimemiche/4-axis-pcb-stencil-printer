# Plan: rebuilding the assembly from a script

[`ASSEMBLY.md`](ASSEMBLY.md) is the plan for *assembling the machine*. This is
the plan for **rebuilding, from Python, the assembly Michael built by hand** in
[`../freecad/assembly/`](../freecad/assembly/) — so that the nine documents there stop being the only
copy of that work.

**All six steps are built.** What follows is the design, kept because the
reasoning still explains the code; `## Where it got to` records what actually
happened, including the places the plan was wrong. The work is on the
`assembly-datums` branch, and the nine hand-built documents were never written
to -- verified by checksum after every run.

## Why

Two reasons, and they are Michael's:

* **To see whether it can be built this way at all.** The earlier scripted
  attempt in [`asm/`](asm/) was judged not good enough and retired. If a script
  can reproduce the hand-built assembly, `asm/` could be promoted back to being
  the source.
* **Because the joints are spelled in edge names.** Every joint in
  `../freecad/assembly/` attaches to a `Face`, an `Edge` or a `Vertex` named by OCC's
  topological numbering. Rebuild the part a joint attaches to and the numbering
  can shift, and the joint does not complain — it silently attaches to whatever
  now carries that number. This is already written down as a hazard; it is the
  reason part documents under `stock/`, `rotation-table/`, `stencil-clamp/` and
  the rest must not be casually rebuilt.

He will **not** hand-build the assembly a second time. The script therefore has
to derive everything from the nine documents that exist.

## What is actually in there

Measured off the nine `../freecad/assembly/*.FCStd`, 2026-08-06:

| | count |
|---|---|
| Documents | 9 |
| Authored part instances (`App::Link` + `Assembly::AssemblyLink`) | **145** |
| Fasteners (Fasteners WB, `Part::FeaturePython`) | **245** |
| Joint objects (149 joints + 8 grounded) | **157** |
| Child links FreeCAD materialises on its own | 816 |
| Distinct part documents consumed | 59 |

The fasteners are `ISO4762` x 181, `DIN934` x 33, `ISO4035` x 26, `ISO4027` x 3
and `IUTHeatInsert` x 2. **All 245 have `BaseObject` set** — every one is
attached to a hole edge, none is placed by coordinates.

`Eccenter` is the one sub-assembly with **no** grounded joint.

### Where it goes, and what it is called

The rebuild lives in [`asm/`](asm/), and **keeps Michael's structure and his
names** — nine documents, spelled exactly as the hand-built ones are, so that
the differ compares like with like and so the two can be read side by side:

```
4-Axis_Stencil_Printer          (+1 part)
├── Bottom_Assembly             (+3 parts)
│   ├── Bottom_Frame            (6 parts)
│   ├── Eccenter                (8 parts)
│   ├── Rotation_Table          (14 parts)
│   └── X-Axis_Carriage         (10 parts)
└── Top_Assembly                (+5 parts)
    ├── Stencil_Clamp           (13 parts)
    └── Top_Frame               (6 parts)
```

Three levels, six leaf sub-assemblies. The nesting above is read off the
`LinkedObject` XLinks; because the 816 mirrored child links carry XLinks too,
the extractor in step 1 confirms which links are authored and which FreeCAD
made, and this tree is corrected there if it is wrong.

**The existing contents of `asm/` are to be deleted** — Michael's decision. Its
names (`Alpha`, `Column`, `Drive`, `Eccentric`, `Machine`, `MachineOpen`,
`Stencil`, `Carriage`, `BottomFrame`) are from the retired attempt and do not
map onto the nine. The deletion happens at step 4, when there is something to
replace them with; [`asm/asmprim.py`](asm/asmprim.py) is read before then, not
after.

### The 816 are free

The container documents look enormous — `4-Axis_Stencil_Printer` alone holds 542
objects — but almost all of that is the sub-assemblies' contents mirrored
upward, and FreeCAD creates it. Tested directly: a scratch document with one
`Assembly::AssemblyLink` pointed at `Bottom_Frame`'s assembly went from 9
objects to 76 without another line of script, and the link's `Group` came back
holding the 58 child links by name.

So the authored surface is about **550 objects**, not 1,400.

### The API is not the problem

All of it is plain Python, from `Mod/Assembly/CommandInsertLink.py` and
`JointObject.py`:

```python
asm  = doc.addObject("Assembly::AssemblyObject", "Assembly")
link = asm.newObject("App::Link", label);  link.LinkedObject = part_obj
jg   = UtilsAssembly.getJointGroup(asm)
j    = jg.newObject("App::FeaturePython", "Joint");  JointObject.Joint(j, type_index)
j.Reference1 = (obj1, ['LCS002.']);  j.Reference2 = (obj2, ['LCS.'])
```

Two things bite. The owning document must be **saved before** any `XLink` is
set, or FreeCAD refuses with `Owner document not saved`. And
`ViewProviderJoint` is GUI-only, so a `freecadcmd` build produces joints with no
view provider — which the differ has to tolerate, or step 4 needs the GUI.

## The problem worth solving

**841 references are spelled topologically:** 584 in joints (339 `Edge`, 173
`Face`, 72 `Vertex`) and all 245 fastener attachments (241 `Edge`, plus 4 whose
sub is stored with a `?` prefix). Only **12** joint references name a datum
instead — 8 in `Stencil_Clamp`, 2 in `Eccenter`, 2 in `X-Axis_Carriage`, all of
them onto a spring.

Transcribing those names into a script reproduces the assembly exactly and
inherits the fragility whole. It would be a script that breaks silently.

## The decision: the joints go on datums, and the datums get fixed

An earlier draft of this plan proposed keeping the joints on faces and edges but
storing a *geometric description* instead of a name — "the cylindrical face of
radius 2.05 whose axis is parallel to local +Z and passes through (21, 0, 10)" —
re-resolved against the shape at build time.

**Michael rejected that.** It leaves the assembly brittle and makes it fail
unpredictably: every joint still depends on a search succeeding, and a search
that quietly matches the wrong candidate is the same failure the plan set out to
remove, wearing a different name.

The decision instead is to **adjust the datums that exist and add the ones that
do not, until every joint has a datum worth naming.** A datum is authored, not
found. It cannot match the wrong thing, it cannot be renumbered by a sketch
change, and it means what the part script says it means.

This was considered and set aside once, for two reasons that were good ones.
Both are answered by *changing the parts* rather than by working around them:

* *The datums that exist are not all at useful locations — they sit where the
  part script found it convenient.* True, and that is exactly what this plan
  changes. The datums move to where the joints need them.
* *Mounting through a datum means composing offsets and rotations by hand.*
  Only if the datum is in the wrong place. [`fcprim.py`](fcprim.py)`.lcs`
  already takes `at`, `axis` and `roll` **in the body's own coordinates**, so
  the composition is done once, in the part script, next to the dimensions it is
  made of. The assembly then names a datum and nothing else — no offset, no
  rotation, no transform arithmetic at the joint.

`fcprim.lcs` was written for this and says so:

> A named mounting datum on a body, for the assembly to join against. The
> assembly joins parts by referring to these rather than to faces. […] `axis` is
> the direction the datum's **Z** points, because that is the axis every joint
> turns or slides about: down a bore, along a rod, up a bolt.

The machinery is already there and already used 86 times in this tree. What is missing is
coverage and placement.

## What this costs, measured

Of the **59** part documents the nine assemblies consume:

| | count |
|---|---|
| Already carry at least one datum | 31 |
| **Carry none at all** | **28** |

The 28 with none, by group:

* `stencil-clamp/` (9) — the four `STENCIL_HOLDER_*`,
  `TOP_CLAMP_BEARING_MOUNT_{1,2}`, `TOP_CLAMP_NUT_HOLDER`, `TOP_CLAMP_STOP`,
  `TOP_SPRING_PLATE`
* `eccentric-clamp/` (6) — all six `ECCF_*`
* `rotation-table/` (6) — `ADAPTER_D5_TO_M3`, `ALPHA_BOT_PLATE`,
  `ALPHA_TOP_PLATE`, `SR_BEARING_PLATE`, `SR_INNER_RING`, `SR_OUTER_RING_W_GEAR`
* `top-assembly/` (4) — the spanner: both cases, the counter, the handwheel
* `bottom-frame/` (1) `STAND`, `top-frame/` (1) `TOP_CLAMP_Z_AXIS`,
  `x-axis-carriage/` (1) `XY_PLATE`

`eccentric-clamp/`, `top-frame/` and `top-assembly/` have **zero** `lcs()`
calls between them today, and `stencil-clamp/` has three. `stock/` has 29 and
`x-axis-carriage/` 18; those are the model to copy — `ROD`, `MOUNT`,
`BOLT1..n`, one datum per bolt in a circle.

## The fasteners do not fit, and need their own answer

This is the one place the datum route does not reach. All 245 fastener
attachments resolve to a **circular edge**: Fasteners WB reads the hole's
diameter and plane off that edge to pick and position the screw.
A `PartDesign::CoordinateSystem` has no circular edge, so `BaseObject` cannot
name a datum. Three ways out:

1. **Leave the fasteners topological.** They are leaves — a screw that grabs the
   wrong edge lands in the wrong hole, but it does not move a bracket, because
   the joints do not run through it. Cheapest, and the damage is bounded and
   visible.
2. **Drop `BaseObject` and place each fastener from its datum** with a `Fixed`
   joint onto the `BOLT`*n* datum that hole already needs. Uniform with
   everything else, and the fastener becomes an ordinary part instance. Costs
   the automatic diameter inference — the script states the size, which it knows
   anyway. **Recommended.**
3. Keep a hole-finding helper for fasteners only, which is the rejected search,
   scoped to the case where a wrong answer is cheap.

Option 2 is the one that makes the assembly say what it means. Worth deciding
before step 4, not before step 2 — steps 1 to 3 are the same either way.

## Also found: the element map is only half switched off

An earlier note here said every document in this project saves an empty hasher.
That is true of the nine assemblies and **false of the parts**:

| | `Document.xml` | hash table | `*.Shape.Map.txt` |
|---|---|---|---|
| part docs (`eccentric-clamp/`, `bottom-frame/`, … all checked) | `count="0" new="1"` **+ `<StringHasher2 file="StringHasher.Table.txt"/>`** | present, e.g. 351 entries for `ECCF_MOUNT` | `Body`, `Sketch`, `Pad.AddSubShape` |
| `../freecad/assembly/*.FCStd` | `count="0"`, no `StringHasher2` | absent | only the Fasteners WB shapes |

So the parts persist their element maps and their hash ids; the assemblies do
not persist the ids they borrow. That is what `failed to find hash id` in the
report view is saying, and why shadows like `;#124:1;:G3#172;CUT;…` cannot
resolve.

This does not change the decision — datums are wanted regardless, and a mapped
name is still a found name rather than an authored one. It is worth knowing
because it means the existing joints degrade less badly than assumed, and the
hand-built documents can survive a part rebuild better than feared while the
datums are being added.

## Two things to settle before writing a builder

### 1. Where does each datum go?

Not by hand, and not by guessing. The hand-built assembly already knows: every
one of the 572 topological joint references points at a real face, edge or
vertex with a real position and axis. A read-only pass can resolve each one,
measure the frame it implies **in the part's local coordinates**, deduplicate,
and print a proposed `fcprim.lcs(bdy, "…", at=…, axis=…)` call per part script.

Michael reviews and names them. That is the one place the geometry work from the
old plan survives — as a one-shot generator of datum call sites, run once and
reviewed, not as a resolver that runs on every build.

### 2. Naming and deduplication

572 references collapse to far fewer distinct datums — a bolt circle is one
datum per hole, and two joints onto the same bore share one. The proposal pass
has to report the collapsed count, because that is the real size of the edit to
the part scripts, and it is the number that decides whether this is a week or a
month.

## What a rebuild can and cannot prove

A generator that transcribes the hand-built assembly reproduces it by
construction. That proves the extraction is complete. It does not show that the
assembly could be *derived*, because nothing in it was.

The version that answers the first of the two motivations is a script that
expresses **intent** — this bracket bolts to that slot, 21 mm in from the end —
with the hand-built documents as the answer key, so that a wrong answer shows up
as a diff rather than as an opinion. Datums are what make that expressible:
`MOUNT`, `ROD`, `BOLT3` are intent; `Edge52` is not.

## Where it got to

    parts      145/145 exact, worst 0.000000 mm
    bolts      244/245 exact
    joints     149, none naming an edge
    datums     308 across 59 part documents, all written by the part scripts

Every leaf sub-assembly -- `Bottom_Frame`, `Eccenter`, `Rotation_Table`,
`Top_Frame`, `X-Axis_Carriage`, `Stencil_Clamp` -- reproduces the hand-built
machine exactly, parts and bolts alike. **A joint on a named datum puts a part
exactly where a joint on `Edge52` did**, which is the question the whole plan
existed to answer.

The pipeline, in order:

    extract-all.sh    the nine documents -> model.json          (step 1)
    datums-all.sh     every reference measured -> datums.json   (step 2)
    datum-names.py    named by what mates there -> datum-plan.json
    datum-derive.py   which sketched feature each one sits on   (step 6)
    build.py          the parts, datums and all                 (step 3)
    wiring.py         old edge name -> new datum -> wiring.json
    calibrate.py      each fastener's offset, in the datum frame
    asmbuild.py       the nine assemblies                       (step 4)
    asmpose.py        solved placements, one document per process (step 5)

`rebuild.py` drives the lot; its stage names are `extract datums names parts
wiring poses assemble dress drawings bom verify`.

## Step 6: the datums say where they came from

The plan's last step was *"intent-level source"*, and the concrete thing it
meant was this: **a datum position should be an expression in the part's own
dimensions, not a number measured off an assembly.** A literal is checkable but
it is not readable, and it does not move when the part does -- widen a hole
pattern and the datum stays where the old assembly had it, silently.

All 308 are now written by the part scripts, in those scripts' own terms:

```python
# before -- from datum-plan.json, applied by fcprim.apply_datums
fcprim.lcs(bdy, "BOLT1", at=(-124.35, 0.0, -76.0), axis=(0, -1, 0))

# after -- in xy-plate.py, off the same list the holes are drilled from
for i, (x, z) in enumerate(sorted(holes())):
    fcprim.lcs(bdy, f"BOLT{i + 1}", at=(x, 0.0, z), axis=(0, -1, 0))
```

**`datum-plan.json` did not go away; it changed job.** It is now the **answer
key**: `fcprim.apply_datums` holds every datum a script writes against the
position measured off the hand-built machine, to a micron, and *fails the
build* if they disagree. So an expression is not a guess -- it is a claim that
has to come out on the measured spot. Getting `BEARING_MOUNT_Y3` wrong by
29 mm, or `FRAME1` by 1 mm because it named the wrong face of a shelf, is a
traceback rather than a part that quietly moves.

`datum-derive.py` is what made the edit tractable. It is read-only: it opens
each built part, and for every literal in the plan says which sketched feature
sits exactly there -- the centre of circle `bolt_a0`, a point `4` mm along that
circle's axis, a vertex of the `plate` profile, a sketch's own plane. 263 of
the 308 were explained outright, and the name it gives is the name the *script*
knows the feature by, so the expression is read off the source rather than
worked out.

Two things are worth knowing about what came out of it.

**Position and Z are enforced; `roll` is reported.** Five datums are turned
about their own axis relative to the measurement -- `RAIL` on both rail
holders, `ROD` on the short alpha holder, `SCREW` on the X bracket, `FACE_A` on
the ball bearing. Every one of them is an axis of revolution, where the
measured roll is whatever the underlying curve's parameterisation handed back,
and no joint uses it. `apply_datums` prints these and carries on; a roll that
*does* matter shows up in `asmdiff` against the hand-built placements, which is
where it should.

**Seven datums cannot be expressed, and are kept as measured with a note.**
They are the ones the hand-built assembly picked on a *face* rather than on
anything drawn, and a face's own frame sits at its centre of area: the notched
hinge leaf (`FACE1`, `FACE2`, `FRAME1`), both rail holders' collar face
(`FRAME`), the spanner case's top edge (`FRAME`), the clamp bearing mount's
barrel end (`BEARING`), and the Z clamp's top face (`ROD2`). `M8_55`'s two
eccenter datums are the same case in a different guise -- a thread trimmed
square leaves an end face whose centre is 0.3606 mm off the rod's axis. Each
carries a comment saying so where it is written, because the number means
nothing on its own and moving it onto the axis would move the parts hung off it.

### Two bugs step 6 turned up

**Eleven datums were never being created.** `datum-names.py` dropped the kept
labels from its "already taken" set before numbering the generated ones, so a
part whose script already wrote `BOLT1`..`BOLT5` could be handed `BOLT1` again
for a different spot -- and the old `apply_datums` *skipped* a label it found
rather than checking it. `BOT_BRACKETS`, the three rail clamps and both hands
of `BOT_Z_AXIS_BRACKET` lost between them eleven of the plan's datums, which is
seven of the eight fasteners the plan listed as unfinished. They are named for
what is actually there now: `BOLT2_HEAD` is the far end of `BOLT2`, and the Z
bracket's two are `MOUNT_BOLT` and `PINCH_BOLT`. `datum-names.py` reproduces
those names from a `REVIEWED` table, so a re-run does not undo the review.

**`--calibrate` wrote an empty offsets file.** `calibrate-from-build.py` split
the hand-pose filenames on an `fh-` prefix they have not carried for some time,
so nothing matched and it wrote nothing -- reporting "0 offsets" and carrying
on. Eight bolts moved before this was spotted. It now takes the basename and
refuses a file that is not one of the nine.

### Chasing the last ten bolts

Ten of the 245 were missing after step 6, and every one of them turned out to
be a name that had moved rather than a datum in the wrong place. Four separate
things, in the order they came off:

**Four `?Edge` nuts, placed by inspection.** `Stencil_Clamp`'s `Nut003`,
`Nut004`, `Nut009` and `Nut010` attach to `Pocket004.?Edge39` and `?Edge37` --
the `?` meaning FreeCAD could not map the element, so the reference comes back
a **null shape** and there was nothing for step 2 to measure. What is broken is
broken in the hand-built document, and no amount of measuring finds it. They
are all `ISO4035` in `TOP_CLAMP_BEARING_MOUNT_1`'s two nut slots across the
screw, one pair in each of its two instances; the part now carries datums for
both slots on both hands, and **those datums land on the four hand-built nut
positions to 0.000 mm**, which is what makes this a reading rather than a
guess. `wiring.py`'s `BY_INSPECTION` says so out loud.

**A datum addressed by a name the builder does not mint.** `wiring.json`
records a path of hand-built link names ending in an internal object name --
`BOT_BRACKET_X_AXIS001.LCS008.` -- and both halves move. `Bottom_Frame` holds
one X-axis bracket, which the hand document calls `BOT_BRACKET_X_AXIS001` and
the build calls `BOT_BRACKET_X_AXIS`, so `Nut030` resolved to nothing.
`asmbuild.datum_sub` now asks the part which of its datums is **labelled**
`NUT` -- a label is what the part script wrote and nothing downstream renames
it -- and `_only_instance` finds the link by what it is an instance of where
the sub-assembly holds exactly one. Two identical builds now hand back
identical frames for all 244; before, some moved by a whole hole spacing.

**Six bolts that were never missing.** `asmverify` says, and has always said,
that it does not compare fasteners by name, because a container renames one:
`Screw108` is taken by a mirrored child before the builder gets to it, so the
bolt it authored is called `Screw115`. But it still *selected* the scripted
bolts by the hand document's names -- so `Screw115` was left out of the count
and the mirror standing 18 mm away was counted in its place. `asmpose` already
marks what each assembly itself holds; the count uses that now. Measured
properly, the score before any of this work was 239, not 235.

**A metric that flagged the honest ones.** `calibrate-from-build.py` reported
every offset more than a millimetre from its datum, which is nine -- including
a nut sitting 20 mm up a stud, which is exactly what an offset is *for*. It now
splits the offset **along** the datum's own Z from **across** it, and only
across is worth reading. 236 of 244 are dead on their datum's axis.

### What is not done

**One fastener.** `Nut031`'s `BaseObject` lands on `Bottom_Assembly` itself
rather than on any part, so there is no datum for it to name.

**Eight offsets sit across their datum's axis**, and neither is a fault in the
datums:

* `Top_Frame`'s six `TOP_CLAMP_Z_AXIS` screws, 3.110 mm each. The build
  reproduces the hand-built machine exactly there -- 46 of 46 -- so this is
  where Michael's screws actually are, beside the holes rather than in them.
* `Bottom_Assembly`'s `Screw140` and `Nut032`, 597 mm. Those two are **adrift
  in the hand-built assembly**: the nearest authored part to where they sit is
  245 mm away. The offset is faithfully reproducing two fasteners floating in
  space, which is worth knowing and not worth "fixing" here.

### What the plan got wrong

*"Two things bite"* about the API was two of about eight. The ones that cost
most:

* `findPlacement` returns the **identity** for a fastener. It is built for
  joint references, which carry two subs; a `BaseObject` carries one and falls
  through. Every fastener datum was measured at the part origin, and no amount
  of fixing the transform afterwards helped.
* A joint reference stores **two** subs, `(element, vertex)`. A one-element
  list makes the workbench's own validation raise `list index out of range`.
* The same edge reached through the links and from inside the body can come
  back with **opposite orientation**, and a circle's `Axis` follows. An offset
  measured in one frame and applied in the other puts a bolt out by exactly
  twice its own offset.
* `import FastenersCmd` **segfaults** under `freecadcmd`. The module loads only
  when FreeCAD restores it from a document that already holds a fastener, which
  is what `fastener-seed.py` exists for.
* `isPartConnected` reports almost every part in a working assembly as
  unreached. It is not a DOF check.

The solve turned out to be **idempotent** after all: the plan budgeted a 1e-5
tolerance and the difference is 0.000000 mm.

## Sequence

1. **Extractor**, read-only: nine documents to a neutral model — 145 part
   instances, 245 fastener attachments, 157 joint objects, 59 source documents.
2. **Datum proposal report**, read-only: every reference resolved and measured
   in its part's local frame, deduplicated, emitted as proposed `lcs()` calls
   grouped by part script, with the collapsed count. Replaces the old
   selector-coverage go/no-go.
3. **Add the datums to the part scripts** and rebuild those parts — 28 documents
   that have none, plus additions to the 31 that have some. This is the step
   that renumbers topology and so breaks the hand-built joints; it happens on
   this branch, and `../freecad/assembly/` is not re-saved.
4. **Builder**: model to the nine documents under `asm/`, under Michael's names
   and nesting, joints named against datums, with the DOF check wired in, so a
   rebuild cannot quietly reintroduce an over-constraint. The retired `asm/`
   documents and their scripts are deleted here, and the fastener question above
   is decided here.
5. **Differ**: `asm/` against `../freecad/assembly/`, document for document under the same
   names, on object set, joint table and solved placements — with a tolerance,
   because the solve is not idempotent and lands about 1e-5 apart between runs.
6. **Intent-level source**, with 1-5 as the safety net. Every datum position
   becomes an expression in its part's own dimensions, and `datum-plan.json`
   becomes the answer key those expressions are checked against. See
   `## Step 6` above for what that turned into.

Steps 1 and 2 are read-only and cannot disturb work in progress. Step 3 is the
first one that writes.

`asm/asmprim.py` was worth reading before step 4 — not as authority, but it had
already solved the document-creation plumbing. It has since been deleted with
the rest of the retired attempt.

## Carried over from diagnosing the assembly

Three things found while working out why the assembly would not recompute, which
the builder has to respect:

* **The DOF check belongs in the build.** Both `Top_Assembly` and
  `4-Axis_Stencil_Printer` were over-constrained by exactly one constraint, in
  both cases a `Parallel` where an `Angle` would do. That is what produced
  `still touched after recompute` — not a cyclic reference; there are none.
* **The solve is not idempotent.** Consecutive solves land about 1e-5 mm apart,
  so any comparison of placements needs a tolerance.
* **Placements are outputs, not data.** Every authored part is joint-constrained,
  so the script does not store 145 placements. It does still need a plausible
  start pose, or the solver can converge into the wrong branch — the lid folded
  through the frame rather than above it.
