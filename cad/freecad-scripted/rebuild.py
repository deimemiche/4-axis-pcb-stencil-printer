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
    assemble   the nine scripted documents in asm/
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
DATA = os.path.join(HERE, "data")
FROZEN = os.path.normpath(os.path.join(HERE, "..", "freecad", "assembly"))
ASM = os.path.join(HERE, "asm")

FREECAD = ["flatpak", "run", "--command=freecadcmd", "--filesystem=home",
           "org.freecad.FreeCAD"]

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
          ("assemble", stage_assemble), ("verify", stage_verify)]


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
