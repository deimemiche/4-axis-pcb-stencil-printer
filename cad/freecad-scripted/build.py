"""Run the part scripts under FreeCAD and report which ones built.

freecadcmd swallows tracebacks -- a script that raises simply prints nothing --
so every build goes through here instead:

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \
        cad/freecad/build.py                     # everything
    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \
        cad/freecad/build.py eccf/eccf-bot.py    # just one

Paths are relative to this directory.  With no arguments every part script in
every group is rebuilt, in group order.
"""

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
# The part folders, named for the sub-assembly each part belongs to.  `stock/`
# is what is bought or cut to length, `shared/` the two printed parts more than
# one sub-assembly uses, `shelved/` what no assembly consumes any more.
GROUPS = ("stock", "bottom-frame", "rotation-table", "x-axis-carriage",
          "eccentric-clamp", "top-frame", "top-assembly", "stencil-clamp",
          "shared", "shelved")

# Every script in a group folder builds a part.  An assembly has to be built
# after all of them, which is why `asm/` is a folder of its own and is run
# separately -- building it here would run it first, off whatever the last run
# left behind.
NOT_PARTS = ()


def part_scripts(argv):
    chosen = [a for a in argv if a.endswith(".py")
              and os.path.basename(a) != "build.py"]
    if chosen:
        return [c if os.path.isabs(c) else os.path.join(HERE, c) for c in chosen]
    found = []
    for group in GROUPS:
        folder = os.path.join(HERE, group)
        if not os.path.isdir(folder):
            continue
        found += [os.path.join(folder, n)
                  for n in sorted(os.listdir(folder))
                  if n.endswith(".py") and n not in NOT_PARTS]
    return found


def build(path):
    namespace = {"__file__": path, "__name__": "__part__"}
    with open(path) as handle:
        code = compile(handle.read(), path, "exec")
    exec(code, namespace)


def say(*args):
    """Print and flush.

    freecadcmd exits the process without draining stdout, so anything still
    sitting in the buffer when the run ends is simply never seen.
    """
    print(*args)
    sys.stdout.flush()


def main(argv):
    scripts = part_scripts(argv)
    if not scripts:
        say("no part scripts found")
        return 1
    failed = []
    for path in scripts:
        name = os.path.relpath(path, HERE)
        say(f"=== {name}")
        try:
            build(path)
        except BaseException:                  # SystemExit counts as a failure
            failed.append(name)
            say(traceback.format_exc())
        sys.stdout.flush()
    say(f"\n{len(scripts) - len(failed)}/{len(scripts)} built")
    for name in failed:
        say(f"  FAILED {name}")
    # Nothing headless can write GuiDocument.xml, so everything just built
    # would open in the GUI as an empty 3D view; see view.py.
    say("\nnow dress them, or they open blank:  view.py under the full FreeCAD")
    return 1 if failed else 0


sys.exit(main(sys.argv[1:]))
