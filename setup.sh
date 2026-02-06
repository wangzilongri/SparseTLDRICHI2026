#!/bin/bash

# Setup script for Sparse_TL_DR_ICHI2026 project
# Handles both Python and R dependencies
#
# Usage:
#   ./setup.sh           # Normal setup (skips already-installed components)
#   ./setup.sh --force   # Force reinstall everything
#   ./setup.sh --help    # Show help

set -e  # Exit on error

# =============================================================================
# Parse Arguments
# =============================================================================

FORCE=false
HELP=false

for arg in "$@"; do
    case $arg in
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
    esac
done

if [ "$HELP" = true ]; then
    echo "Usage: ./setup.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --force, -f    Force reinstall all components"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "The script automatically skips already-installed components."
    echo "Use --force to reinstall everything."
    exit 0
fi

# =============================================================================
# Configuration
# =============================================================================

R_VERSION="4.4.2"
R_MIN_VERSION="4.4"
LOCAL_R_DIR="$HOME/local/R-${R_VERSION}"
LOCAL_R_LIBS="$HOME/local/R_libs"
MARKER_FILE=".setup_complete"

echo "=================================="
echo "Setting up Sparse_TL_DR_ICHI2026"
if [ "$FORCE" = true ]; then
    echo "(Force mode: reinstalling all components)"
fi
echo "=================================="

# =============================================================================
# Python Setup
# =============================================================================

echo ""
echo "--- Python Setup ---"

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

# Check if Python packages need installation
NEED_PIP_INSTALL=false

if [ "$FORCE" = true ]; then
    NEED_PIP_INSTALL=true
elif [ ! -f "$MARKER_FILE" ]; then
    NEED_PIP_INSTALL=true
elif ! python -c "import numpy; import pandas; import sklearn" 2>/dev/null; then
    NEED_PIP_INSTALL=true
fi

if [ "$NEED_PIP_INSTALL" = true ]; then
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install requirements
    echo "Installing Python dependencies..."
    if command -v pip &> /dev/null; then
        pip install -r requirements.txt --quiet 2>/dev/null || \
        pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt --quiet
        
        if [ $? -eq 0 ]; then
            echo "✓ Python dependencies installed"
        else
            echo "Warning: Some Python dependencies may have failed"
        fi
    else
        echo "Error: pip not found"
        exit 1
    fi
else
    echo "✓ Python dependencies already installed (use --force to reinstall)"
fi

# =============================================================================
# R Setup (Optional but recommended for glmtrans)
# =============================================================================

echo ""
echo "--- R Setup (for glmtrans) ---"

# Function to check R version (need 4.4+)
check_r_version() {
    if command -v Rscript &> /dev/null; then
        R_VER=$(Rscript --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [ -n "$R_VER" ]; then
            R_MAJOR=$(echo $R_VER | cut -d. -f1)
            R_MINOR=$(echo $R_VER | cut -d. -f2)
            if [ "$R_MAJOR" -gt 4 ] || ([ "$R_MAJOR" -eq 4 ] && [ "$R_MINOR" -ge 4 ]); then
                return 0  # Good version
            fi
        fi
    fi
    return 1  # Bad or missing version
}

# Function to get R version string
get_r_version() {
    Rscript --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

# Check if local R exists
if [ -f "$LOCAL_R_DIR/bin/Rscript" ]; then
    echo "✓ Local R ${R_VERSION} already installed at $LOCAL_R_DIR"
    export PATH="$LOCAL_R_DIR/bin:$PATH"
elif check_r_version; then
    echo "✓ System R is version 4.4+ (compatible)"
else
    echo ""
    echo "R 4.4+ is required for glmtrans but not found."
    echo ""
    read -p "Would you like to install R ${R_VERSION} locally? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing R ${R_VERSION} locally (this takes ~15-20 minutes)..."
        
        # Create directories
        mkdir -p "$HOME/local"
        cd "$HOME/local"
        
        # Download R
        echo "Downloading R ${R_VERSION}..."
        wget -q "https://cran.r-project.org/src/base/R-4/R-${R_VERSION}.tar.gz"
        tar -xzf "R-${R_VERSION}.tar.gz"
        cd "R-${R_VERSION}"
        
        # Configure and build
        # --with-x=no: Don't require X11 (not available on most servers)
        # --with-readline=no: Don't require readline (optional)
        # --with-cairo=no: Don't require cairo graphics (optional)
        # --enable-R-shlib: Build shared library (needed for some packages)
        echo "Configuring R (this may take a few minutes)..."
        ./configure --prefix="$LOCAL_R_DIR" \
            --enable-R-shlib \
            --with-x=no \
            --with-readline=no \
            --with-cairo=no \
            --disable-java \
            2>&1 | tail -5
        
        echo "Compiling R (this may take 10-15 minutes)..."
        # Use nproc if available, otherwise default to 4
        NCPU=$(nproc 2>/dev/null || echo 4)
        make -j $NCPU
        
        echo "Installing R..."
        make install
        
        # Cleanup
        cd "$HOME/local"
        rm -f "R-${R_VERSION}.tar.gz"
        rm -rf "R-${R_VERSION}"
        
        export PATH="$LOCAL_R_DIR/bin:$PATH"
        echo "✓ R ${R_VERSION} installed to $LOCAL_R_DIR"
        
        # Return to project directory
        cd - > /dev/null
    else
        echo "Skipping R installation. glmtrans methods will not be available."
        echo "You can install R later and re-run this script."
    fi
fi

# =============================================================================
# glmtrans R Package Setup
# =============================================================================

if command -v Rscript &> /dev/null && check_r_version; then
    echo ""
    echo "--- glmtrans Package Setup ---"
    
    # Create R library directory
    mkdir -p "$LOCAL_R_LIBS"
    export R_LIBS_USER="$LOCAL_R_LIBS"
    
    # Check if glmtrans is installed
    if [ "$FORCE" = true ]; then
        echo "Force reinstalling glmtrans..."
        Rscript -e "remove.packages('glmtrans', lib='$LOCAL_R_LIBS')" 2>/dev/null || true
        NEED_GLMTRANS=true
    elif Rscript -e 'library(glmtrans)' 2>/dev/null; then
        echo "✓ glmtrans is already installed"
        NEED_GLMTRANS=false
    else
        NEED_GLMTRANS=true
    fi
    
    if [ "$NEED_GLMTRANS" = true ]; then
        echo "Installing glmtrans R package..."
        Rscript -e "install.packages('glmtrans', lib='$LOCAL_R_LIBS', repos='https://cloud.r-project.org', quiet=TRUE)" 2>/dev/null
        
        if Rscript -e 'library(glmtrans)' 2>/dev/null; then
            echo "✓ glmtrans installed successfully"
        else
            echo "Warning: glmtrans installation failed. Methods will use Python fallbacks."
        fi
    fi
fi

# =============================================================================
# Final Verification
# =============================================================================

echo ""
echo "--- Verification ---"

# Python check
python -c "import numpy; import pandas; import sklearn; print('✓ Python packages OK')" 2>/dev/null || echo "⚠ Some Python packages missing"

# R check
if command -v Rscript &> /dev/null; then
    R_VER=$(get_r_version)
    R_VER=${R_VER:-"unknown"}
    echo "✓ R version: $R_VER"
    
    if Rscript -e 'library(glmtrans); cat("✓ glmtrans OK\n")' 2>/dev/null; then
        :  # Success message already printed
    else
        echo "⚠ glmtrans not available (Python fallbacks will be used)"
    fi
else
    echo "⚠ R not found (glmtrans methods will use Python fallbacks)"
fi

# Mark setup as complete
touch "$MARKER_FILE"

# =============================================================================
# Done
# =============================================================================

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "To activate the environment, run:"
echo "  source activate.sh"
echo ""
echo "To run a sweep:"
echo "  python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 5"
echo ""
echo "To check glmtrans status:"
echo "  cd src && python -m glmtrans_wrapper --status"
echo ""
echo "To force reinstall everything:"
echo "  ./setup.sh --force"
echo ""
