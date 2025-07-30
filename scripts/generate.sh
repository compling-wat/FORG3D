#!/bin/bash

# Hugging Face token
HF_TOKEN="YOUR_HF_TOKEN"

# Function to activate virtual environment cross-platform
activate_venv() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/src/generate_background.py"

cd "$PROJECT_ROOT/src"

ARGS=("$@")

if [ ! -d "venv" ]; then
    echo "First time setup detected. This will take 5-10 minutes to download models and install dependencies..."
    python3 -m venv venv
    activate_venv
    pip install torch --extra-index-url https://download.pytorch.org/whl/cu121
    pip install -r requirements.txt
else
    activate_venv
fi

huggingface-cli login --token "$HF_TOKEN"
python "${PYTHON_SCRIPT}" "${ARGS[@]}"

deactivate