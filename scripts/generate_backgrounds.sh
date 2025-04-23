#!/bin/bash

cd "../src"

# Path to Python executable
PYTHON_EXECUTABLE="python"

# Prompt for the generation
PROMPT=""
NEGATIVE_PROMPT=""

# Hugging Face Token
HF_TOKEN=""

# Install dependencies
if ! python -c "import torch" &> /dev/null; then
    pip install torch --index-url https://download.pytorch.org/whl/cu121/
fi

if ! pip freeze | grep -q -f requirements.txt; then
    pip install -r requirements.txt
fi

# Hugging Face authentication
huggingface-cli login --token "$HF_TOKEN"

$PYTHON_EXECUTABLE generate_background.py "$PROMPT" "$NEGATIVE_PROMPT"