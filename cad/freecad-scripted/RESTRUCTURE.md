# Plan: splitting the tree, and renaming the folders

**For review. Nothing has been moved.** This is the proposal for separating the
hand-built assembly from the work described in
[`ASSEMBLY_SCRIPT.md`](ASSEMBLY_SCRIPT.md), and for giving the part folders
names that say what is in them.

Michael has decided four things, and they are folded in below: the frozen tree
**keeps no scripts**, the copy is called **`freecad-scripted`**, `scope/` moves
out to **`cad/shelved/`** with its assembly deleted, and eventually everything
in `cad/` that is not `freecad/` or `freecad-scripted/` follows it there.

## What the split has to guarantee

The nine documents in [`../freecad/assembly/`](../freecad/assembly/) join their parts by naming
`Face12`, `Edge52`, `Vertex7`. Step 3 of the datum plan **rebuilds 28 part
documents and edits 31 more**, and a rebuild renumbers topology. Every joint
that names a number is then pointing at whatever now carries that number, and it
will not complain.

So the guarantee is absolute rather than careful: **the part documents the
hand-built assembly links to are never rebuilt.** Dropping the scripts from the
frozen tree is what makes that a fact about the filesystem instead of a rule
someone has to remember — there is nothing there to rebuild with.

## The good news: the links are relative

Every external reference in the nine documents is a relative path:

| form | count | example |
|---|---|---|
| `../<group>/<NAME>.FCStd` | 66 | `../eccf/ECCF_MOUNT.FCStd` |
| bare sibling name | 14 | `Bottom_Frame.FCStd` |
| absolute | **0** | — |

`GuiDocument.xml` carries no external file references at all. So a copy resolves
against itself with nothing to rewrite, and renaming the group folders means
rewriting exactly 66 strings, in nine files, all of the shape `../old/` →
`../new/`.

## The constraint that sets the shape: `fcprim` is found two levels up

Every one of the 67 part scripts opens with

```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fcprim
```

— the **parent of the script's own folder** must be the folder holding
`fcprim.py`. That rules out the obvious tidy-up of collecting the parts under a
`parts/` wrapper: it would add a level and break all 67 imports at once.

So the new folders stay **direct children of the tree root**, exactly as
`bot/` and `top/` are today. Zero script edits, and the XLink rewrite stays the
simple shape `../eccf/` → `../eccentric-clamp/` rather than gaining a segment.

## The two trees

```
cad/
├── freecad/                 ← Michael's.  Frozen.  No scripts, nothing to rebuild with.
│   ├── assembly/                the nine documents, untouched
│   ├── stock/  rotation-table/  stencil-clamp/  eccentric-clamp/
│   ├── x-axis-carriage/  bottom-frame/  top-assembly/  top-frame/  shared/
│   └── (59 .FCStd in total)
│
├── freecad-scripted/        ← the copy.  Where the datum work happens.
│   ├── fcprim.py  build.py  view.py  export.py  verify.py  …
│   ├── the same nine folders, with the scripts and their rebuilt parts
│   ├── shelved/                 9 parts no assembly consumes
│   └── asm/                     the generated assembly, under Michael's nine names
│
└── shelved/                 ← scope/ now; the rest of cad/ later.
    └── scope/                   8 SCOPE_* parts and their scripts
```

`cad/freecad/` keeps its path, so nothing you have open or bookmarked moves.

## The new folder names

Grouped by the sub-assembly each part belongs to, because that mirrors the nine
documents and makes "what does `Bottom_Frame` need" answerable with `ls`.

| new folder | n | from | what is in it |
|---|---|---|---|
| `stock/` | 15 | `misc`, `bot`, `top` | bought and cut-to-length: 2020 extrusion, D8 rods, threaded rod, springs, LM8UU, bearing, hinge leaf, tube |
| `rotation-table/` | 11 | `sr`, `plate`, `bot`, `misc` | slewing ring, worm gear, alpha plates, Y-axis bearing mounts, alpha rod holders |
| `stencil-clamp/` | 10 | `plate`, `top` | the four stencil holders, clamp bearing mounts, nut holder, stop, rail holder, spring plate |
| `eccentric-clamp/` | 6 | `eccf` | all six `ECCF_*` |
| `x-axis-carriage/` | 6 | `plate`, `bot` | XY plate, X bearing mount, rail clamps, rail holder |
| `bottom-frame/` | 4 | `misc`, `bot` | stand, X-axis bracket, Z-axis brackets |
| `top-assembly/` | 4 | `top` | the spanner: cases, counter, handwheel |
| `shared/` | 2 | `bot` | `BOT_BRACKETS`, `BOT_HANDWHEEL` — the only printed parts with more than one consumer |
| `top-frame/` | 1 | `top` | `TOP_CLAMP_Z_AXIS` |
| `shelved/` | 9 | `mod`, `bot`, `top`, `plate` | built, consumed by nothing: the hinge locks, the Z-axis counter parts, `ALPHA_TOP_PLATE_PLAIN`, `BOT_RIGHT_ANGLE_CON`, and four more |

59 consumed + 9 shelved = **68**, which is the 77 on disk less the nine that
leave with `scope/`. `misc/`, `plate/`, `eccf/`, `sr/`, `bot/`, `top/`, `mod/`
and `scope/` all disappear.

Naming that last folder `shelved/` is most of the value of the exercise: it says
out loud which parts are load-bearing and which are not. It stays inside
`freecad-scripted/` rather than going to `cad/shelved/` because its scripts still
need `fcprim.py` two levels up — the same constraint as above.

## `scope/` leaves, and its assembly goes

`Microscope.FCStd` is the only document in `scope/` with any external
dependency:

```
Microscope.FCStd   ../misc/2020_280, ../misc/2020_300, ../misc/BEARING_14X5X5, + 8 siblings
SCOPE_HOLDER … SCOPE_TOP   (all eight self-contained)
```

Delete `Microscope.FCStd` and the `microscope.py` that builds it, and the folder
is self-contained — it moves to `cad/shelved/scope/` with **nothing to rewrite**
and no dependency on `stock/`. That also removes the one cross-group edge in the
whole tree, and lets `build.py` drop its `NOT_PARTS` special case for
`microscope.py`.

The eight part scripts move with their documents as a record. They will not
*run* from `cad/shelved/` — no `fcprim.py` two levels up — which is the intended
state for shelved work; reviving one means dropping it back beside a tree that
has it.

## What has to be rewritten

| | where | how |
|---|---|---|
| 66 XLink paths | the nine `../freecad/assembly/*.FCStd` | unzip, `file="../old/X"` → `file="../new/X"`, rezip |
| 14 bare sibling names | the nine | unchanged — the assemblies stay siblings |
| `GROUPS`, `NOT_PARTS` | `build.py:20,27` | new folder list; `microscope.py` case drops out |
| `ASSEMBLIES`, `KEEP_OUT`, `ELSEWHERE`, doc examples | `view.py:35,38,46` | new paths |
| folder paths in prose | `README.md` (48), `STATUS.md` (56), `ASSEMBLY.md` (40), `ASSEMBLY_SCRIPT.md` (22) | mechanical replace, then read |
| part scripts | — | **nothing**, by the design above |

`fcprim.build` saves each document next to its own script, so moving a script
moves its output with it.

## Two hazards

**Family scripts must move with every document they emit.** Five scripts write
more than one part and the name does not match: `misc/2020-extrusion.py` writes
the three `2020_*`, `bot/rod-d8.py` writes the four `ROD_D8_*`, `misc/spring.py`
writes both springs, `eccf/eccf-lever.py` writes `ECCF_LEVER_MIRRORED` as well as
`ECCF_LEVER`, `bot/bot-z-axis-bracket.py` writes the mirrored bracket. A mapping
built from filenames would strand them, so the mover works off the generated
inventory instead.

`spring.py` is the awkward one: it composes `SPRING_ID10_L35_AT20` out of
`springs["ID10"]` and `instances`, so the name appears nowhere in the source and
even a full-text search does not find it. It is the one association the mapping
records by hand, with the reason written next to it.

**Two trees will hold documents with the same internal name.** `ECCF_MOUNT`
exists in both after the copy. FreeCAD resolves XLinks by path but identifies
open documents by name, so opening both trees in one session gets you
`ECCF_MOUNT001`. The rule is: **never open both trees in the same FreeCAD
session.** That belongs in `README.md`.

## How it is verified

Before touching anything, record for each of the nine: object count, joint
count, the full list of resolved references, and the solved placement of every
part instance. After the move, record it again and diff. Only paths changed, so
everything else must match — placements within the 1e-5 the solver wanders by.

If the diff is not empty the move is reverted, not debugged in place. It is one
`git checkout` either way.

## Order of operations

1. Record the verification baseline for the nine. Read-only.
2. Generate the move mapping from the inventory — 77 documents, their scripts,
   their consumers — and print it for review. Read-only.
3. `git rm` `Microscope.FCStd` and `microscope.py`; `git mv scope/` to
   `cad/shelved/scope/`.
4. `git mv` the remaining 68 parts into the nine new folders.
5. Rewrite the 66 XLink paths in the nine assembly documents.
6. Re-record and diff. Stop here if anything moved.
7. Update `build.py`, `view.py`, and the four `.md` files.
8. Copy the tree to `cad/freecad-scripted/`; delete `../freecad/assembly/` from the copy,
   and the scripts and `shelved/` from `cad/freecad/`.
9. Commit 3, 4-5, 7 and 8 separately, so any one can be undone alone.

Steps 1 and 2 change nothing and can run now.

## Later, not now

`cad/` root still holds 40-odd `.stl` exports, eight legacy CadQuery scripts
(`base-plate.py`, `z-axis.py`, `hinge-lock.py` and the rest), four stray
`.FCStd` — `ECCF_LEVER_COMPLIANT`, `ECCF_TOP`, `TOP_CLAMP_NUT_HOLDER_4mm`,
`TOP_CLAMP_SPANNER_COUNTER_4mm` — and the `board-mount/`, `microscope-mount/`
and `output/` folders. All of it goes to `cad/shelved/` once the split above has
settled. `output/` holds only a `.gitkeep` and a stale `__pycache__`, and
nothing writes to it.
