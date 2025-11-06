#!/bin/bash

# Check if the venv directory exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment and install requirements
source venv/bin/activate
pip install -r requirements.txt

echo "Setup complete. Virtual environment is ready and dependencies are installed."
