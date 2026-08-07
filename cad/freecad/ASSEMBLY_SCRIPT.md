# Plan: rebuilding the assembly from a script

[`ASSEMBLY.md`](ASSEMBLY.md) is the plan for *assembling the machine*. This is
the plan for **rebuilding, from Python, the assembly Michael built by hand** in
[`assembly/`](assembly/) — so that the nine documents there stop being the only
copy of that work.

**Nothing here is built yet.** This is the design and the measurements it rests
on, written down before any code, so the go/no-go is decided on numbers rather
than on enthusiasm.

## Why

Two reasons, and they are Michael's:

* **To see whether it can be built this way at all.** The earlier scripted
  attempt in [`asm/`](asm/) was judged not good enough and retired. If a script
  can reproduce the hand-built assembly, `asm/` could be promoted back to being
  the source.
* **Because the joints are spelled in edge names.** Every joint in
  `assembly/` attaches to a `Face`, an `Edge` or a `Vertex` named by OCC's
  topological numbering. Rebuild the part a joint attaches to and the numbering
  can shift, and the joint does not complain — it silently attaches to whatever
  now carries that number. This is already written down as a hazard; it is the
  reason part documents under `bot/`, `misc/`, `plate/` and the rest must not be
  casually rebuilt.

He will **not** hand-build the assembly a second time. The script therefore has
to derive everything from the nine documents that exist.

## What is actually in there

Measured off the nine `assembly/*.FCStd`, 2026-08-06:

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
attached to a hole face, none is placed by coordinates.

`Eccenter` is the one sub-assembly with **no** grounded joint.

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
j.Reference1 = (obj1, ['Face3']);  j.Reference2 = (obj2, ['Edge5'])
```

Two things bite. The owning document must be **saved before** any `XLink` is
set, or FreeCAD refuses with `Owner document not saved`. And
`ViewProviderJoint` is GUI-only, so a `freecadcmd` build produces joints with no
view provider.

## The problem worth solving

**829 references are spelled topologically:** 584 in joints (339 `Edge`, 173
`Face`, 72 `Vertex`) and all 245 fastener attachments. Twelve joint references —
all in `Eccenter` — name a datum instead.

Transcribing those 829 names into a script reproduces the assembly exactly and
inherits the fragility whole. It would be a script that breaks silently.

### Why not datums

The obvious answer is to put the joints on the `PartDesign::CoordinateSystem`
datums that [`fcprim.py`](fcprim.py)`.lcs` already writes — 34 of the 68 part
documents carry them, and [`bot/rod-d8.py`](bot/rod-d8.py) says outright they are
"Mounting datums for the assembly".

**Michael rejected this, and the reasons are good ones.** The datums that exist
are not all at useful locations — they sit where the part script found it
convenient, not where a joint needs to attach. And mounting *through* a datum
means composing offsets and rotations by hand, which gets awkward as soon as
more than one of either is involved. A joint straight onto a face is ergonomic
precisely because the solver infers the frame from the geometry; a datum hands
that job back to the person writing the script.

So the robustness has to come from somewhere that costs no hand-authoring.

## The approach: resolve references geometrically at build time

Store neither an edge name nor a datum. Store a **description**, and re-find the
element when the script runs:

> the cylindrical face of radius 2.05 whose axis is parallel to local +Z and
> passes through (21, 0, 10)

The script queries the part's shape, finds the one element that matches, and
hands it to the joint. The joint still lands on a real face or edge, so the
Assembly workbench behaves exactly as it does today — only the naming changes.

This answers the objection directly: no datum objects to add, no transforms to
compose, no dependence on `fcprim.lcs` having put a datum somewhere useful. And
it converts the failure mode. A part rebuild that moves a hole makes the
description stop matching, and the build **fails loudly naming the reference**
instead of quietly grabbing a different edge.

The descriptions need no authoring either. They can be derived from the nine
documents: resolve each reference against the current shape, measure it in the
part's local frame, emit the selector.

## Two things to settle before writing a builder

### 1. Is the element map merely switched off?

Every document in this project saves an empty hasher:

```xml
<StringHasher saveall="0" threshold="0" count="0"></StringHasher>
```

Yet the joints carry element-map shadow strings like
`;#564:1;:H11a4,F;:H11a6,F.Face9`. Those mapped names are FreeCAD's own
mitigation for topological naming and are *meant* to survive a rebuild. The
`#564` cannot resolve because the hasher was never persisted — which is also
what the `failed to find hash id` messages in the report view are saying.

So the machinery may already be in the file and simply not being saved. **Test
it first**: enable hasher persistence, rebuild one part, see whether its joints
still resolve. If they do, the selector layer shrinks to a fallback and this
becomes a much smaller job.

### 2. Can every reference be described uniquely?

A plate with sixteen identical M3 holes is the obvious hazard. Position in the
part's local frame is the discriminator, but there will be cases where it is not
enough.

The first thing to build is therefore **not** the generator. It is a read-only
pass that resolves all 829 references, characterises each, and reports how many
are uniquely re-findable and which are not. It touches nothing, and it decides
whether the rest is worth starting. 100% and the remainder is engineering; 80%
and we need a fallback and should know that on day one.

## What a transcriber can and cannot prove

A generator that transcribes the hand-built assembly will reproduce it by
construction. That proves the extraction is complete. It does not show that the
assembly could be *derived*, because nothing in it was.

The version that answers the first of the two motivations is a script that
expresses **intent** — this bracket bolts to that slot, 21 mm in from the end —
with the hand-built documents as the answer key, so that a wrong answer shows up
as a diff rather than as an opinion.

Both need the same prerequisite. Intent-level source is not writable while every
reference is spelled `Edge52`; the selector layer is exactly what makes "the M3
hole nearest the left end of the top face" expressible. Build it once and both
motivations are served.

## Sequence

1. **Extractor**, read-only: nine documents to a neutral model — 145 part
   instances, 245 fastener attachments, 157 joint objects, 59 source documents.
2. **Selector coverage report** — the go/no-go above. Read-only.
3. **Builder**: model to documents, with the DOF check wired in, so a
   transcription cannot quietly reintroduce an over-constraint.
4. **Differ**: rebuilt against hand-built, on object set, joint table and solved
   placements — with a tolerance, because the solve is not idempotent and lands
   about 1e-5 apart between runs.
5. **Intent-level source**, with 1-4 as the safety net.

Steps 1 and 2 are read-only and cannot disturb work in progress.

[`asm/asmprim.py`](asm/asmprim.py) is worth reading before step 3 — not as
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
