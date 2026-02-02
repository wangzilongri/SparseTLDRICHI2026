#!/bin/bash
# =============================================================================
# Run Ablation Benchmark and Compile Report
# =============================================================================
# This script runs the ablation benchmark with configurable Monte Carlo
# replicates and compiles the results to PDF using pandoc.
#
# Usage:
#   ./scripts/run_ablation_report.sh [n_mc]
#
# Arguments:
#   n_mc  - Number of Monte Carlo replicates (default: 20)
#
# Output:
#   results/ablation_full_report/
#     - ablation_methodology_report.md   (Markdown report)
#     - ablation_methodology_report.pdf  (PDF with LaTeX rendering)
#     - ablation_methodology.csv         (Raw results)
#     - *.png, *.pdf                     (Plots)
# =============================================================================

set -e  # Exit on error

# Configuration
N_MC=${1:-20}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/results/ablation_full_report"

echo "============================================================"
echo "Ablation Benchmark Report Generator"
echo "============================================================"
echo "Project root: $PROJECT_ROOT"
echo "Monte Carlo replicates: $N_MC"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check for virtual environment
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "Using active virtual environment: $VIRTUAL_ENV"
else
    echo "Warning: No virtual environment found. Using system Python."
fi

# Check dependencies
echo ""
echo "Checking dependencies..."

# Check Python
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi
echo "  ✓ Python: $(python --version 2>&1)"

# Check pandoc (optional but recommended)
if command -v pandoc &> /dev/null; then
    echo "  ✓ Pandoc: $(pandoc --version | head -1)"
    HAVE_PANDOC=1
else
    echo "  ⚠ Pandoc not found (PDF will use fpdf2 fallback)"
    HAVE_PANDOC=0
fi

# Check xelatex (for proper LaTeX in PDF)
if command -v xelatex &> /dev/null; then
    echo "  ✓ XeLaTeX: available"
else
    echo "  ⚠ XeLaTeX not found (LaTeX equations may not render)"
fi

# Run the benchmark
echo ""
echo "============================================================"
echo "Running ablation benchmark ($N_MC MC replicates)..."
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"
python experiments/run_ablation_report.py --n_mc "$N_MC"

# Verify output
echo ""
echo "============================================================"
echo "Results"
echo "============================================================"

if [ -f "$OUTPUT_DIR/ablation_methodology_report.pdf" ]; then
    echo "✓ PDF report: $OUTPUT_DIR/ablation_methodology_report.pdf"
    echo "  Size: $(du -h "$OUTPUT_DIR/ablation_methodology_report.pdf" | cut -f1)"
else
    echo "⚠ PDF not generated"
fi

if [ -f "$OUTPUT_DIR/ablation_methodology_report.md" ]; then
    echo "✓ Markdown: $OUTPUT_DIR/ablation_methodology_report.md"
fi

if [ -f "$OUTPUT_DIR/ablation_methodology.csv" ]; then
    echo "✓ CSV data: $OUTPUT_DIR/ablation_methodology.csv"
fi

# Count plots
N_PLOTS=$(ls -1 "$OUTPUT_DIR"/*.png 2>/dev/null | wc -l | tr -d ' ')
echo "✓ Plots: $N_PLOTS PNG files"

echo ""
echo "Done!"
