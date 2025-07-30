#!/bin/bash

BLENDER_EXECUTABLE="YOUR_BLENDER_EXECUTABLE"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/src/render_scene.py"

"$BLENDER_EXECUTABLE" --background --python "$PYTHON_SCRIPT" -- "$@"