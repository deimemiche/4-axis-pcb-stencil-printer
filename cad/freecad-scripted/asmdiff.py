"""Step 5: the scripted assembly against the hand-built one.

    ASM_OUT=<report.json> freecadcmd asmdiff.py <Name.FCStd>

Compares the solved global placement of every part instance, matched by link
name.  A tolerance is needed because the solve is not idempotent: consecutive
solves land about 1e-5 mm apart, so anything under that is noise.
"""
import json, math, os, sys, traceback

def say(*a): os.write(1, (" ".join(str(x) for x in a) + "\n").encode())
HERE = os.path.dirname(os.path.abspath(__file__))

def poses(App, path):
    doc = App.openDocument(path)
    out = {}
    for o in doc.Objects:
        if o.TypeId not in ("App::Link", "Assembly::AssemblyLink"):
            continue
        try:
            p = o.getGlobalPlacement()
        except Exception:
            p = o.Placement
        out[o.Name] = (p.Base.x, p.Base.y, p.Base.z,
                       p.Rotation.Q[0], p.Rotation.Q[1],
                       p.Rotation.Q[2], p.Rotation.Q[3])
    return doc, out

def main():
    import FreeCAD as App
    name = [a for a in sys.argv[1:] if a.endswith(".FCStd")][0]
    hand = os.path.join(HERE, "..", "freecad", "assembly", name)
    made = os.path.join(HERE, "asm", name)
    d1, a = poses(App, os.path.abspath(hand))
    d2, b = poses(App, os.path.abspath(made))
    shared = sorted(set(a) & set(b))
    worst, rows = 0.0, []
    for k in shared:
        d = max(abs(x - y) for x, y in zip(a[k][:3], b[k][:3]))
        rows.append((d, k))
        worst = max(worst, d)
    rows.sort(reverse=True)
    within = sum(1 for d, _ in rows if d < 1e-4)
    say(f"{name}")
    say(f"  links hand-built {len(a)} | scripted {len(b)} | matched {len(shared)}")
    say(f"  positions within 1e-4 mm : {within}/{len(shared)}")
    say(f"  worst position difference: {worst:.6f} mm")
    for d, k in rows[:6]:
        if d >= 1e-4:
            say(f"     {k:34} {d:.4f} mm")
try: main()
except Exception: say("DIFF RAISED:"); say(traceback.format_exc())
