"""TOP_CLAMP_BEARING_MOUNT_2 - the other end's bearing mount.

The original author's TOP_CLAMP_BEARING_MOUNT_2.stl is TOP_CLAMP_BEARING_MOUNT_1
mirrored in Z, vertex for vertex - the two sit at opposite ends of the stencil
clamp's screw and face each other.  So this builds the same body with the mirror
turned on rather than repeating a hundred lines of it.

Editing the shape means editing `top-clamp-bearing-mount-1.py`; both parts follow.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import fcprim

# Run the other script for its `bearing_mount`, telling it not to build its own
# part while we do.  Importing it would not do: its filename is not an
# identifier, and the module-level build would fire on the way past.
mount = {"__file__": os.path.join(HERE, "top-clamp-bearing-mount-1.py"),
         "as_library": True}
with open(mount["__file__"]) as handle:
    exec(compile(handle.read(), mount["__file__"], "exec"), mount)

mesh_volume = 7142.368


def top_clamp_bearing_mount_2(doc):
    return mount["bearing_mount"](doc, "TOP_CLAMP_BEARING_MOUNT_2", hand=-1)


fcprim.make(__file__, "TOP_CLAMP_BEARING_MOUNT_2", top_clamp_bearing_mount_2,
            mesh_volume)
