#!/bin/bash

# Setup script for Sparse_TL_DR_ICHI2026 project

echo "=================================="
echo "Setting up Sparse_TL_DR_ICHI2026"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "Installing dependencies..."
if command -v pip &> /dev/null; then
    # Try normal installation first
    pip install -r requirements.txt --quiet
    if [ $? -ne 0 ]; then
        echo "Normal installation failed, trying with --trusted-host flags..."
        pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ Dependencies installed successfully"
    else
        echo "Error: Failed to install dependencies"
        exit 1
    fi
else
    echo "Error: pip not found"
    exit 1
fi

# Verify installation
echo "Verifying installation..."
python -c "import numpy; import pandas; import sklearn; import matplotlib; import seaborn; print('✓ All packages imported successfully')" 2>&1 | grep "✓"

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "Setup complete!"
    echo "=================================="
    echo ""
    echo "To activate the environment, run:"
    echo "  source venv/bin/activate"
    echo ""
    echo "To run the main script:"
    echo "  python src/scratch_estimator.py"
    echo ""
    echo "To deactivate when done:"
    echo "  deactivate"
else
    echo "Warning: Package verification had warnings, but installation may still be successful"
fi
