#!/bin/bash

# Path to Blender executable (required)
BLENDER_EXECUTABLE=""

PYTHON_SCRIPT="../src/render_scene.py"

# Arguments for Python script (see src/render_scene.py for more details)
# Here is an example:
ARGS="
    --objects shoe puma \
    --object1-rotation 180 \
    --object2-rotation 90 \
    --distance-between-objects 3 \
    --direction left \
    --camera-tilt 90 \
    --camera-pan 45 \
    --camera-height 1.5 \
    --camera-focal-length 60 \
"

"$BLENDER_EXECUTABLE" --background --python "$PYTHON_SCRIPT" -- $ARGS