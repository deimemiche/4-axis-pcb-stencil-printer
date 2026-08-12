"""Run the part scripts under FreeCAD and report which ones built.

freecadcmd swallows tracebacks -- a script that raises simply prints nothing --
so every build goes through here instead:

    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \
        cad/freecad-scripted/code/pipeline/build.py   # everything
    flatpak run --command=freecadcmd --filesystem=home org.freecad.FreeCAD \
        cad/freecad-scripted/code/pipeline/build.py eccentric-clamp/eccf-bot.py

Paths are relative to this directory.  With no arguments every part script in
every group is rebuilt, in group order.
"""

import os
import sys
import traceback

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the tree root

# Every part script says a bare `import fcprim`, and nothing else puts the
# library within reach: Python seeds sys.path with *this* script's folder,
# which is `pipeline/`, not `lib/`.  Until these two lived apart the import
# resolved by accident, because build.py sat next to fcprim.py.
sys.path.insert(0, os.path.join(HERE, "code", "lib"))
# The part folders, named for the sub-assembly each part belongs to.  `stock/`
# is what is bought or cut to length, `shared/` the two printed parts more than
# one sub-assembly uses, `archive/` what no assembly consumes any more.
GROUPS = ("stock", "bottom-frame", "rotation-table", "x-axis-carriage",
          "eccentric-clamp", "top-frame", "top-assembly", "stencil-clamp",
          "shared", "archive")

# Every script in a group folder builds a part.  An assembly has to be built
# after all of them, which is why `assembly/` is a folder of its own and is run
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
