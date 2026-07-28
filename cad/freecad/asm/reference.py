"""Fetch the author's own build-step renders, to check ours against his.

The build page walks through the machine one step at a time, and each step has
a CAD render of exactly what has been added.  That makes them the reference the
assembly should agree with: if our stage 3 does not look like his STEP_5, one of
us is wrong and it is worth knowing which.

They are his images, so they are downloaded rather than committed and
`reference/` is git-ignored.

    python3 cad/freecad/asm/reference.py

Runs under plain python3 -- no FreeCAD needed.
"""

import os
import re
import sys
import urllib.request

PAGE = "https://dengler-mechatronik.de/?p=790"
HERE = os.path.dirname(os.path.abspath(__file__))
INTO = os.path.join(HERE, "reference")

# The full-size renders, not the 300w / 768w responsive copies.
STEP = re.compile(
    r"https://dengler-mechatronik\.de/wp-content/uploads/"
    r"\d{4}/\d{2}/STEP_[0-9_]+(?:-\d)?\.png")


def step_number(url):
    """Sort STEP_9_1 before STEP_10_1, which a plain string sort will not."""
    parts = re.findall(r"\d+", os.path.basename(url))
    return [int(p) for p in parts]


def main():
    os.makedirs(INTO, exist_ok=True)
    page = urllib.request.urlopen(PAGE).read().decode("utf-8", "replace")
    urls = sorted(set(STEP.findall(page)), key=step_number)
    if not urls:
        raise SystemExit("no STEP renders found -- has the page changed?")

    for url in urls:
        name = os.path.basename(url)
        path = os.path.join(INTO, name)
        if os.path.exists(path):
            continue
        with urllib.request.urlopen(url) as response:
            with open(path, "wb") as out:
                out.write(response.read())
        print(f"  {name}")
    print(f"{len(urls)} renders in {INTO}")


if __name__ == "__main__":
    sys.exit(main())
