# Handover: where the assembly stands, and what is wrong with it

Written at the end of a session that got the machine assembling and driving,
and then hit a contradiction it could not settle. This is the state to pick up
from. [`ASSEMBLY.md`](ASSEMBLY.md) is the plan and the reasoning;
[`STATUS.md`](STATUS.md) is the per-part record; this file is only "what is
broken and what was being done about it".

## Read this first: the live bug

**Two independent derivations of the alpha assembly's height disagree by about
5 mm, and the assembly cannot be right until that is settled.**

The alpha axis (the slewing ring and its two plates) rides the Y rails above
the print plate. How high it sits is the one number in `machine.py` that was
never derived, and two parts now claim different answers:

| from | says the plate's underside is at | how |
|---|---|---|
| `BOT_BEARING_MOUNT_Y_AXIS` | **Y = 15.2** | its flange top is 11.6 above its bearing bore, and the bore sits on the Y rail at Y = 3.6 |
| `BOT_RAIL_CLAMP_X_DRIVE` | **Y >= 20.15** | its arm tops out 16.55 above the rail it caps, and reaches *inboard*, under where the plate goes |

15.2 is below 20.15, so the plate would be driven through the cap's arm. One of
these readings is wrong.

### What is solid, and what is not

The **caps are almost certainly right**. `BOT_RAIL_CLAMP_Y_AXIS` is not a
standalone clamp at all -- it is the cap for `BOT_BEARING_MOUNT_X_AXIS`'s
trough, and everything agrees:

    mount cap bolts   x = +-9.0     cap bolts   z = +-9.0     same 18 mm
    mount trough      r = 4.05      cap groove  r = 4.05      same 8 mm rod
    mount house_z     +-10.5 (21)   cap length      21        cap sits on it
    mount width       27            cap width       27
    mount cap_nut_across = 5.7      manual buys 8 Square Nut M3

Four mounts, four caps (2 plain, plus `BOT_RAIL_CLAMP_X_DRIVE` and
`BOT_RAIL_CLAMP_Y_AXIS_1`), 8 x M3x10 = two each. That is manual step 7 exactly,
and `carriage.py`'s `check_caps` confirms each cap's groove lands on its
mount's trough.

So the doubt is on the **other** side. Things worth testing, roughly in order
of how likely they look:

1. **`BOT_BEARING_MOUNT_Y_AXIS` may not mount flange-up.** Its docstring says
   "bolted flat under the frame, with a 15.2 mm bearing seat hanging below it",
   which was written in an earlier session and may be a guess. If it hangs the
   other way the 11.6 becomes something else.
2. **The Y rails may not be at Y = 3.6.** That comes from
   `BOT_BEARING_MOUNT_X_AXIS`'s trough being 14.6 above its own bore, and the X
   rail being at Y = -11. Both are derived, but the X rail's -11 rests on the
   rail holder bolting into the *centre* slot of a 2020's inner face, which is
   assumption not measurement.
3. **The caps' arms may point outboard**, not inboard. That was tried in
   passing: it moves the arm to Z ~ +-144, which then fouls the frame's end
   members at Z = +-130..150. So probably not, but it was not tested properly.
4. **The X drive cap may belong on a different mount** from the one it was
   arbitrarily assigned to (`CAPS` in `carriage.py` assigns them in order).

## What is in the working tree but **not committed**

Last commit is `d21d723`. Everything below is uncommitted and only partly
verified -- decide whether to keep it before building on it.

| file | change | verified? |
|---|---|---|
| `bot/bot-rail-clamp-y-axis.py` | `ROD` + `BOLT1..2` datums | yes, builds, 0.018 % |
| `bot/bot-rail-clamp-y-axis-1.py` | same | yes, builds, 0.019 % |
| `bot/bot-rail-clamp-x-drive.py` | same | yes, builds, 0.018 % |
| `asm/carriage.py` | `rail_caps()`, `check_caps()`, `CAPS` | **yes** -- stage 3 passes |
| `asm/machine.py` | caps placed; `alpha_seat()` now derived from the carriage's own height instead of assumed | **no** |
| `asm/check.py` | new `placed()` helper | **no -- written, never run** |

### The last run, and why it failed

`machine.py` last completed with the alpha plate at **Y = 74.6**, which is
nonsense, and the slewing ring then clashed with the top frame's rails. That
number came from a **real bug that is fixed in the tree but never tested**:

> `App::Link` shares its shape with every other link to the same part, so
> `link.Shape.BoundBox` is the part where it was *drawn*, not where it was put.
> `alpha_seat()` was asking links for their bounding boxes directly and getting
> the wrong answer.

`check.placed()` was added to do this properly and `machine.py` now calls it.
**The very next thing to do is run `machine.py` and see what seat height it
gives.** It should be about 21.2 (the caps' top at 20.15 plus 1 mm). If it is,
the machine will assemble clash-free -- but it will still be sitting at a height
that contradicts `BOT_BEARING_MOUNT_Y_AXIS`, which is the bug above.

Note the same `.Shape` mistake may be lurking elsewhere; `check.solids()` always
handled links correctly, but anything else asking a link for geometry directly
is suspect.

## Everything else that is open

**Four parts exist nowhere** -- no STL, no drawing. Michael has said to leave
them for now:

    TOP_BRACKET   x8   step 12, top frame corners
    ECCB_BODY     x2   step 18, rear eccentric
    ECCB_LEVER    x2
    ECCB_SHIM     x2

**The worm drive is unplaced.** `ALPHA_BOT_PLATE` has a 10 mm hole at r = 75.45
but the ring's teeth are at r ~ 79, so the hole is not where a worm meshing
those teeth would sit. `BOT_ROD_HOLDER_ALPHA_AXIS` holds the worm shaft and its
geometry was never measured -- that is the evidence to go at next, and it should
settle the mesh radius directly.

**The Y bearing spacing is assumed.** `carriage.Y_BEARING_SPACING = 120.0` is a
guess, and it is what limits Y travel to +-25 mm. Closer together gives more.

**`TOP_CLAMP_Z_AXIS` does not verify clean** -- 2 mismatches in 20000 points,
reproducible, predating this work. See `STATUS.md`.

**Manual steps 8 and 9** (lead screws, springs, handwheels) are not built. The
two caps that carry the drives are now placed, which is the groundwork for them.

## What is done and working

All committed, all passing:

* 45 parts build (39 reconstructed from STLs, 6 drawn from the author's 2D
  drawings), `build.py` reports 45/45
* stages 0, 1, 2, 4, 5 and 7 pass; stage 3 passes including the caps
* the machine drives: X +-55, Y +-25, Z 66 mm, alpha +-32.6 deg, with
  interference re-checked at every step of the travel walk
* 32 fasteners placed from the parts' own `BOLT` datums, counts matching the
  manual
* exploded view and renders in `asm/render/`

## Running things

```sh
alias fc='flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD'

fc cad/freecad/build.py                 # all 45 parts
fc cad/freecad/asm/stage0.py            # the regression test for joints
fc cad/freecad/asm/frame.py             # stage 1
fc cad/freecad/asm/carriage.py          # stage 3
fc cad/freecad/asm/alpha.py             # stage 4
fc cad/freecad/asm/column.py            # stage 5
fc cad/freecad/asm/machine.py           # stage 7, the whole thing
fc cad/freecad/asm/render.py            # redraw everything
python3 cad/freecad/asm/reference.py    # fetch the author's step images
```

`machine.py` takes a few minutes -- the travel walk runs an interference pass
per step. `freecadcmd` prints **nothing at all** for an uncaught exception, so a
silent run means a crash, not success; `build.py` and `render.py` wrap
themselves to print tracebacks, and anything new should too.

Two flags worth knowing: `freecadcmd` swallows script arguments unless they come
after `--pass`, and it sets `__name__` to the module's basename rather than
`"__main__"`, which is why the stage scripts guard on `asmprim.is_entry()`.
