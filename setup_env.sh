#!/bin/bash
# This script sets up a virtual environment and installs dependencies.

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if python3 is available
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found, please install it."
    exit
fi

# Create a virtual environment named 'venv'
echo "Creating virtual environment..."
python3 -m venv venv

# Activate the virtual environment and install dependencies
echo "Installing dependencies from requirements.txt..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo "To activate the virtual environment, run the following command:"
echo "source venv/bin/activate"
