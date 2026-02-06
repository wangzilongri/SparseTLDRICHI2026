#!/bin/bash

# Activation script for Sparse_TL_DR_ICHI2026
# Usage: source activate.sh
#
# This script:
# 1. Activates the Python virtual environment
# 2. Sets up R paths for glmtrans (if R 4.4+ is installed)
# 3. Sets environment variables for the project

# =============================================================================
# Python Virtual Environment
# =============================================================================

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Python venv activated"
else
    echo "Error: Virtual environment not found. Run ./setup.sh first."
    return 1 2>/dev/null || exit 1
fi

# =============================================================================
# R Setup for glmtrans
# =============================================================================

# Configuration
R_VERSION="4.4.2"
LOCAL_R_DIR="$HOME/local/R-${R_VERSION}"
LOCAL_R_LIBS="$HOME/local/R_libs"

# Function to check R version >= 4.4
check_r_version() {
    if command -v Rscript &> /dev/null; then
        R_VER=$(Rscript --version 2>&1 | sed -n 's/.*version \([0-9]*\.[0-9]*\).*/\1/p' | head -1)
        if [ -z "$R_VER" ]; then
            R_VER=$(Rscript --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        fi
        if [ -n "$R_VER" ]; then
            R_MAJOR=$(echo $R_VER | cut -d. -f1)
            R_MINOR=$(echo $R_VER | cut -d. -f2)
            if [ "$R_MAJOR" -gt 4 ] || ([ "$R_MAJOR" -eq 4 ] && [ "$R_MINOR" -ge 4 ]); then
                return 0
            fi
        fi
    fi
    return 1
}

# Check for local R installation first
if [ -f "$LOCAL_R_DIR/bin/Rscript" ]; then
    export PATH="$LOCAL_R_DIR/bin:$PATH"
    echo "✓ Using local R ${R_VERSION}"
fi

# Set up R library path
if [ -d "$LOCAL_R_LIBS" ]; then
    export R_LIBS_USER="$LOCAL_R_LIBS"
    export GLMTRANS_R_LIBS="$LOCAL_R_LIBS"
fi

# Check glmtrans availability
get_r_version() {
    Rscript --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

if check_r_version; then
    R_VER=$(get_r_version)
    if Rscript -e 'library(glmtrans)' 2>/dev/null; then
        echo "✓ R $R_VER with glmtrans"
    else
        echo "⚠ R $R_VER found but glmtrans not installed"
        echo "  Run: Rscript -e \"install.packages('glmtrans', repos='https://cloud.r-project.org')\""
    fi
else
    if command -v Rscript &> /dev/null; then
        R_VER=$(get_r_version)
        echo "⚠ R $R_VER found but need 4.4+ for glmtrans"
        echo "  Run ./setup.sh to install R 4.4 locally"
    else
        echo "⚠ R not found (glmtrans methods will use Python fallbacks)"
    fi
fi

# =============================================================================
# Project Environment Variables
# =============================================================================

# Add src to Python path for imports
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)/src"

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "Environment ready. Quick commands:"
echo "  python -m experiments.core_sweeps --help     # See sweep options"
echo "  python -m glmtrans_wrapper --status          # Check glmtrans"
echo "  deactivate                                   # Exit environment"
