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
GROUPS = ("misc", "plate", "eccf", "sr", "bot", "top")


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
                  for n in sorted(os.listdir(folder)) if n.endswith(".py")]
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
    return 1 if failed else 0


sys.exit(main(sys.argv[1:]))
