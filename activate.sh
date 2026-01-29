#!/bin/bash

# Quick activation script
# Usage: source activate.sh

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo "Python: $(which python)"
    echo "To deactivate, run: deactivate"
else
    echo "Error: Virtual environment not found. Run ./setup.sh first."
fi
