# Plan: rebuilding the assembly from a script

[`ASSEMBLY.md`](ASSEMBLY.md) is the plan for *assembling the machine*. This is
the plan for **rebuilding, from Python, the assembly Michael built by hand** in
[`../freecad/assembly/`](../freecad/assembly/) — so that the nine documents there stop being the only
copy of that work.

**Nothing here is built yet.** This is the design and the measurements it rests
on, written down before any code, so the go/no-go is decided on numbers rather
than on enthusiasm. The work happens on the `assembly-datums` branch; the nine
hand-built documents are not touched until the last step.

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
6. **Intent-level source**, with 1-5 as the safety net.

Steps 1 and 2 are read-only and cannot disturb work in progress. Step 3 is the
first one that writes.

[`asm/asmprim.py`](asm/asmprim.py) is worth reading before step 4 — not as
authority, but it already solved the document-creation plumbing, even though its
joints were scripted placements rather than real ones.

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
