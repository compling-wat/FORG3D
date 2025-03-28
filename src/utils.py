"""Utility functions for rendering scenes in Blender."""
import os
import sys
import bpy
from typing import List

def extract_args(input_argv: str = None) -> List[str]:
    """Pull out command-line arguments after '--'.

    Args:
        input_argv: list of command-line arguments
    """
    if input_argv is None:
        input_argv = sys.argv
    output_argv = []
    if '--' in input_argv:
        idx = input_argv.index('--')
        output_argv = input_argv[(idx + 1):]
    return output_argv

def add_object(object_dir: str, name: str, scale: float, loc: tuple[float, float], theta: float = 0) -> None:
    """Load an object from a file. We assume that in the directory object_dir, there
    is a file named "$name.blend" which contains a single object named "$name"
    that has unit size and is centered at the origin.

    Args:
        object_dir: string giving the directory where the object .blend file is located
        name: string giving the name of the object to load
        scale: scalar giving the size that the object should be in the scene
        loc: tuple (x, y) giving the coordinates on the ground plane where the object should be placed.
        theta: optional rotation of the object about the z-axis
    """
    # First figure out how many of this object are already in the scene so we can
    # give the new object a unique name
    count = 0
    for obj in bpy.data.objects:
        if obj.name.startswith(name):
            count += 1

    filename = os.path.join(object_dir, '%s.blend' % name, 'Object', name)
    bpy.ops.wm.append(filename=filename)

    # Give it a new name to avoid conflicts
    new_name = '%s_%d' % (name, count)
    bpy.data.objects[name].name = new_name

    # Set the new object as active, then rotate, scale, and translate it
    x, y = loc
    bpy.context.view_layer.objects.active = bpy.data.objects[new_name]
    bpy.context.object.rotation_euler[2] = theta
    bpy.ops.transform.resize(value=(scale, scale, scale))
    bpy.ops.transform.translate(value=(x, y, scale))
