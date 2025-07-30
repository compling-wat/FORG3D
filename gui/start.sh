#!/bin/bash

# Function to activate virtual environment cross-platform
activate_venv() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
}

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

activate_venv
pip install -r requirements.txt
python app.py