#!/bin/bash

# Path to Blender executable (required)
BLENDER_EXECUTABLE=""

PYTHON_SCRIPT="../src/render_scene.py"

# Arguments for Python script (see src/render_scene.py for more details)
# Here is an example:
ARGS="
    --distance-between-objects 3 \
    --render-random \
    --max-images 5 \
    --max-camera-configs 4 \
"

"$BLENDER_EXECUTABLE" --background --python "$PYTHON_SCRIPT" -- $ARGS