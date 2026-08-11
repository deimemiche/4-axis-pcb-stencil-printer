"""Rebuild everything, from the hand-built assembly to the scripted one.

    python3 rebuild.py                 # every stage, in order
    python3 rebuild.py wiring assemble # just these
    python3 rebuild.py --from parts    # this one and everything after
    python3 rebuild.py --list          # what the stages are

Plain Python, run with the system interpreter: it drives FreeCAD as
subprocesses rather than living inside it.  That is what lets one stage open a
document per process -- which is not fastidiousness but a requirement, since
opening several of the nine in one session and closing each before the next
makes FreeCAD fail to restore the links between them.

Everything lands in `data/`, which is committed.  The point of committing
derived files is that the pipeline needs FreeCAD and half an hour, and a
reader who wants to know what the assembly is made of should not need either.
They are all regenerable from `../freecad/` by running this script.

## The stages

    extract    the nine hand-built documents -> data/model.json
    datums     every joint and fastener reference measured -> data/datums.json
    names      named for what mates there -> datum-plan.json
    parts      the 60 part scripts, datums and all
    wiring     old edge name -> new datum -> data/wiring.json
    poses      the hand-built solved placements, to compare against
    assemble   the nine scripted documents in assembly/
    dress      the view data a GUI needs, or they open blank
    drawings   the eight stock parts as TechDraw sheets, in ../../technical-drawings/
    bom        what the machine is made of, counted -> data/bom.json, ../../BOM.md
    verify     scripted against hand-built, parts and bolts

`assemble` needs `fastener-offsets.json`, which is calibrated from an assembled
build -- a bootstrap.  `--calibrate` runs assemble, measures, and assembles
again; without it the committed offsets are used, which is what you want unless
a datum has moved.
"""

import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doclist  # noqa: E402  (needs the path above)

DATA = os.path.join(HERE, "data")
FROZEN = os.path.normpath(os.path.join(HERE, "..", "freecad", "assembly"))
ASM = os.path.join(HERE, "assembly")
DRAWN = os.path.normpath(os.path.join(HERE, "..", "..", "technical-drawings"))

# The parts that are made rather than printed, and so need a drawing.  Kept
# here as well as in drawings.py so the stage can check that each one actually
# produced a sheet, rather than trusting what the script said.
DRAWINGS = ("XY_PLATE", "ALPHA_BOT_PLATE", "ALPHA_TOP_PLATE",
            "STENCIL_HOLDER_BACK", "STENCIL_HOLDER_FRONT",
            "STENCIL_HOLDER_BACK_2", "STENCIL_HOLDER_FRONT_2",
            "2020_300_TOP_FRONT")

FREECAD = ["flatpak", "run", "--command=freecadcmd", "--filesystem=home",
           "org.freecad.FreeCAD"]

# `view.py` needs the real FreeCAD, not freecadcmd: only a GUI can write a
# GuiDocument.xml, and without one every document opens with everything hidden
# and the camera a millimetre wide at the origin.
#
# It needs a real display too, which is the expensive lesson here.  Run under
# `QT_QPA_PLATFORM=offscreen` and there is no GL context -- FreeCAD says so,
# repeatedly, and then six of the ten assemblies deadlock on a futex partway
# through `openDocument`: every thread asleep, no CPU, for ever.  It is not
# about which documents or what is in them; `Top_Frame` hangs offscreen with no
# threaded stock in it at all, while the bigger `Stencil_Clamp` goes through.
# On a real X11 display with direct rendering all ten dress in a couple of
# minutes, `4-Axis_Stencil_Printer` and its 421 links included.
#
# So this pops actual windows on the user's screen for the length of the dress
# stage.  That is a real cost, and it is still the cheap option: the
# alternative is writing `GuiDocument.xml` by hand.
FREECAD_GUI = ["flatpak", "run", "--filesystem=home", "org.freecad.FreeCAD"]

NINE = ["4-Axis_Stencil_Printer", "Bottom_Assembly", "Bottom_Frame", "Eccenter",
        "Rotation_Table", "Stencil_Clamp", "Top_Assembly", "Top_Frame",
        "X-Axis_Carriage"]


def say(*a):
    print(*a, flush=True)


def run(script, args=(), env=None, quiet=True):
    """One FreeCAD subprocess.  Returns its combined output."""
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run(FREECAD + [os.path.join(HERE, script)] + list(args),
                       capture_output=True, text=True, env=e)
    out = (p.stdout + p.stderr).replace("\r", "\n")
    # freecadcmd swallows tracebacks, so the scripts print their own; and it
    # exits 0 even when a script raised.  Both are why this looks at the text.
    for marker in ("RAISED", "Traceback (most recent call last)"):
        if marker in out:
            say(f"\n!! {script} failed:")
            say("\n".join(l for l in out.splitlines()
                          if l.strip() and "%)" not in l)[-2000:])
            raise SystemExit(1)
    if not quiet:
        say("\n".join(l for l in out.splitlines()
                      if l.strip() and "%)" not in l and "Importing" not in l))
    return out


def run_gui(script, args=(), timeout=1800):
    """One full-FreeCAD subprocess, on the user's display.

    The timeout is not belt and braces.  FreeCAD deadlocks outright on some
    document combinations -- see `stage_dress` -- and a deadlocked process
    sleeps rather than spins, so nothing short of a clock notices.  Without
    this the whole pipeline waits for ever at no CPU.
    """
    cmd = FREECAD_GUI + [os.path.join(HERE, script)] + list(args)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        say(f"\n!! {script} hung for {timeout}s and was killed"
            + (f" on {os.path.basename(args[0])}" if len(args) == 1 else ""))
        raise SystemExit(1)
    out = (p.stdout + p.stderr).replace("\r", "\n")
    if "RAISED" in out or "Traceback (most recent call last)" in out:
        say(f"\n!! {script} failed:")
        say("\n".join(l for l in out.splitlines() if l.strip())[-2000:])
        raise SystemExit(1)
    return out


def per_document(script, sources, out_path, label):
    """Run `script` once per document and merge the JSON it writes.

    One process each: FreeCAD cannot restore links between documents that were
    opened and closed earlier in the same session -- `Top_Assembly` loses every
    link into `Stencil_Clamp.FCStd` if this is done in one go.  A document that
    produces no file did not report nothing, it died, so that is fatal.
    """
    tmp = os.path.join(DATA, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    parts = []
    for src in sources:
        name = os.path.basename(src)[:-6]
        path = os.path.join(tmp, name + ".json")
        if os.path.exists(path):
            os.remove(path)
        run(script, [src], env={"ASM_OUT": path})
        if not os.path.exists(path):
            raise SystemExit(f"!! {script} produced nothing for {name}")
        parts.append(json.load(open(path)))
        say(f"    {name}")

    merged = {}
    for got in parts:
        for key, value in got.items():
            if isinstance(value, list):
                merged.setdefault(key, []).extend(value)
            else:
                merged.setdefault(key, {}) if isinstance(value, dict) else None
                if isinstance(value, dict):
                    merged[key].update(value)
                else:
                    merged[key] = value
    # extract.py writes one entry per document keyed by name; datums.py writes
    # {"rows": [...], "failed": [...]}.  Both fall out of the above.
    for got in parts:
        if "rows" not in got:
            merged.update(got)

    json.dump(merged, open(out_path, "w"), indent=1, sort_keys=True)
    n = len(merged["rows"]) if "rows" in merged else len(merged)
    say(f"  {label}: {n} -> {os.path.relpath(out_path, HERE)}")


# ---------------------------------------------------------------- stages

def stage_extract():
    per_document("extract.py", sorted(glob.glob(os.path.join(FROZEN, "*.FCStd"))),
                 os.path.join(DATA, "model.json"), "documents")


def stage_datums():
    per_document("datums.py", sorted(glob.glob(os.path.join(FROZEN, "*.FCStd"))),
                 os.path.join(DATA, "datums.json"), "references")


def stage_names():
    subprocess.run([sys.executable, os.path.join(HERE, "datum-names.py"),
                    os.path.join(DATA, "datums.json"),
                    f"--write={os.path.join(HERE, 'datum-plan.json')}",
                    f"--text={os.path.join(HERE, 'datum-proposal.txt')}"],
                   check=True)


def stage_parts():
    """Rebuild the 60 part documents, `fcprim.apply_datums` and all."""
    out = run("build.py")
    tail = [l.strip() for l in out.splitlines() if "/" in l and "built" in l]
    if not tail:
        raise SystemExit("!! build.py reported no result")
    say(f"  {tail[-1]}")
    made, want = tail[-1].split()[0].split("/")
    if made != want:
        raise SystemExit(f"!! only {made} of {want} parts built")


def stage_wiring():
    subprocess.run([sys.executable, os.path.join(HERE, "wiring.py"),
                    os.path.join(DATA, "datums.json"),
                    os.path.join(HERE, "datum-plan.json"),
                    os.path.join(DATA, "wiring.json")], check=True)


def stage_poses():
    """The hand-built solved placements: what `verify` compares against."""
    d = os.path.join(DATA, "hand")
    os.makedirs(d, exist_ok=True)
    for name in NINE:
        src = os.path.join(FROZEN, name + ".FCStd")
        run("asmpose.py", [src], env={"ASM_OUT": os.path.join(d, name + ".json")})
        say(f"    {name}")


def stage_assemble(calibrate=False):
    if not os.path.exists(os.path.join(ASM, "FASTENER_SEED.FCStd")):
        say("  minting the fastener seed (FastenersCmd cannot be imported "
            "directly; it segfaults)")
        run("fastener-seed.py")
    env = {"ASM_MODEL": os.path.join(DATA, "model.json"),
           "ASM_WIRING": os.path.join(DATA, "wiring.json"),
           "ASM_OFFSETS": os.path.join(HERE, "fastener-offsets.json"),
           "ASM_FASTENERS": "1"}
    if calibrate:
        env["ASM_FRAMES"] = os.path.join(DATA, "frames.json")
    out = run("asmbuild.py", env=env, quiet=False)

    if not calibrate:
        return
    say("\n  calibrating the fastener offsets against the frames this build used")
    subprocess.run([sys.executable, os.path.join(HERE, "calibrate-from-build.py"),
                    os.path.join(DATA, "frames.json"),
                    os.path.join(DATA, "model.json"),
                    os.path.join(HERE, "fastener-offsets.json")]
                   + sorted(glob.glob(os.path.join(DATA, "hand", "*.json"))),
                   check=True)
    say("  assembling again with the calibrated offsets")
    del env["ASM_FRAMES"]
    run("asmbuild.py", env=env, quiet=False)


def stage_dress():
    """Give every built document the view data a GUI needs to show it.

    A document built headless has no `GuiDocument.xml`, and FreeCAD then makes
    one from scratch on opening: every object comes up **hidden**, overriding
    the App-level `Visibility`, and with no saved camera the 3D view starts a
    few millimetres wide at the origin.  So an assembly that is perfectly
    correct opens blank, which is how this looked when Michael opened it.

    `view.py` writes both, and checks its own work: it parks the camera
    somewhere no fit could ever return and asks FreeCAD to fit, so a scene with
    nothing visible in it cannot move the camera and the failure is caught
    rather than saved.

    The parts go in one process; each assembly gets its own.  An assembly opens
    every part it links, and a document reopened after being closed earlier in
    the same session makes FreeCAD log `Reload partial document` and deadlock --
    all eight threads asleep on a futex, no CPU, for ever.  This is the same
    hazard `per_document` is built around, and dressing had it too: a run died
    on the third assembly and left all ten of them blank.

    Which is why this counts what it produced rather than trusting that it ran.
    `view.py` cannot report a hang, so the check is made from outside, on the
    files: a `.FCStd` is a zip, and either `GuiDocument.xml` is in it or the
    document opens blank.

    **It is slower than it looks and says nothing while it works.**  The parts
    pass prints one line and then runs for minutes; each assembly prints its
    name only once its own process has finished.  A run takes around five
    minutes and a partly written log is the normal sight most of the way
    through, not a failure -- read it to the end before concluding anything.
    If a document really is left blank, `view.py` takes one at a time:

        flatpak run --filesystem=home org.freecad.FreeCAD \\
            view.py assembly/Top_Assembly.FCStd
    """
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        raise SystemExit(
            "!! dress needs a real display: no DISPLAY or WAYLAND_DISPLAY set.\n"
            "   Offscreen deadlocks FreeCAD -- see the note on FREECAD_GUI.\n"
            "   Run this stage from a desktop session, or under a virtual\n"
            "   display that provides GL (xvfb-run -s '-screen 0 1280x1024x24').")

    every = doclist.documents()
    parts = [p for p in every if not doclist.is_assembly(p)]
    assemblies = [p for p in every if doclist.is_assembly(p)]

    say(f"  {len(parts)} parts, in one process")
    run_gui("view.py", parts)
    for path in assemblies:
        say(f"    {os.path.basename(path)}")
        run_gui("view.py", [path])

    missing = doclist.undressed(every)
    if missing:
        say(f"\n!! {len(missing)} document(s) have no GuiDocument.xml "
            f"and will open blank:")
        for path in missing:
            say(f"     {os.path.relpath(path, HERE)}")
        raise SystemExit(1)
    say(f"  {len(every)} dressed, all carrying a GuiDocument.xml")


def stage_drawings():
    """Draw the eight parts that are cut and drilled rather than printed.

    Two passes, because they need different FreeCADs.  `drawings.py` builds
    the pages, dimensions them, checks every dimension against the model and
    writes DXF -- all headless.  `drawings-pdf.py` only exports PDF, which
    goes through `TechDrawGui`, which a console FreeCAD refuses to load, so
    that pass needs the display for the same reason `dress` does.
    """
    out = run("drawings.py", quiet=False)
    drawn = [l for l in out.splitlines() if "drawn" in l]
    if not drawn or not drawn[-1].strip().startswith(
            str(len(DRAWINGS))):
        raise SystemExit(f"!! drawings.py did not draw all {len(DRAWINGS)}")
    run_gui("drawings-pdf.py")
    missing = [n for n in DRAWINGS
               if not os.path.exists(os.path.join(DRAWN, n + ".pdf"))]
    if missing:
        raise SystemExit("!! no PDF for: " + ", ".join(missing))
    say(f"  {len(DRAWINGS)} sheets, each with its FCStd, PDF, DXF and hole CSV")


def stage_bom():
    """Count what the machine is made of, from the assembly that holds it.

    Runs after `assemble`, because that is what it counts, and it walks down
    through the sub-assemblies so a part inside an `Eccenter` is counted once
    for each of the four the machine has.
    """
    out = run("bom.py", quiet=False)
    if not os.path.exists(os.path.join(DATA, "bom.json")):
        raise SystemExit("!! bom.py wrote no data/bom.json")
    total = json.load(open(os.path.join(DATA, "bom.json")))
    pieces = sum(sum(rows.values()) for rows in total["groups"].values())
    say(f"  {pieces} pieces in {len(total['groups'])} families "
        f"-> data/bom.json, BOM.md")


def stage_verify():
    d = os.path.join(DATA, "made")
    os.makedirs(d, exist_ok=True)
    for name in NINE:
        run("asmpose.py", [os.path.join(ASM, name + ".FCStd")],
            env={"ASM_OUT": os.path.join(d, name + ".json")})
    subprocess.run([sys.executable, os.path.join(HERE, "asmverify.py")],
                   check=True)


STAGES = [("extract", stage_extract), ("datums", stage_datums),
          ("names", stage_names), ("parts", stage_parts),
          ("wiring", stage_wiring), ("poses", stage_poses),
          ("assemble", stage_assemble), ("dress", stage_dress),
          ("drawings", stage_drawings), ("bom", stage_bom),
          ("verify", stage_verify)]


def main():
    argv = sys.argv[1:]
    if "--list" in argv:
        for n, _ in STAGES:
            say(" ", n)
        return
    calibrate = "--calibrate" in argv
    argv = [a for a in argv if not a.startswith("--") or a == "--from"]
    names = [n for n, _ in STAGES]
    if "--from" in argv:
        i = argv.index("--from")
        first = argv[i + 1]
        chosen = names[names.index(first):]
    else:
        chosen = [a for a in argv if a in names] or names

    os.makedirs(DATA, exist_ok=True)
    for name, fn in STAGES:
        if name not in chosen:
            continue
        say(f"\n== {name}")
        t = time.time()
        if name == "assemble":
            fn(calibrate=calibrate)
        else:
            fn()
        say(f"   ({time.time() - t:.0f}s)")
    say("\ndone")


main()
