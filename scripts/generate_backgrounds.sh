#!/bin/bash

cd "../src"

# Path to Python executable
PYTHON_EXECUTABLE="python"

# Prompt for the model (required)
PROMPT=""

# Install dependencies
if ! pip freeze | grep -q -f requirements.txt; then
    pip install -r requirements.txt
fi

if ! python -c "import torch, torchvision, torchaudio" &> /dev/null; then
    pip install torch --index-url https://download.pytorch.org/whl/cu121/torch_stable.html
fi

$PYTHON_EXECUTABLE generate_background.py "$PROMPT"