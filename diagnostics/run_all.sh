#!/bin/bash
# Run diagnostics on all sweep result folders

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/../results"

echo "=========================================="
echo "Running Sweep Diagnostics on All Results"
echo "=========================================="
echo ""

# Find all sweep folders
for folder in "${RESULTS_DIR}"/sweeps*; do
    if [ -d "$folder" ]; then
        # Check if folder has aggregated results
        if ls "$folder"/results_agg_*.csv 1> /dev/null 2>&1; then
            echo "Processing: $(basename "$folder")"
            python "${SCRIPT_DIR}/run_diagnostics.py" "$folder"
            echo ""
        else
            echo "Skipping: $(basename "$folder") (no aggregated results)"
        fi
    fi
done

echo "=========================================="
echo "All diagnostics complete!"
echo "=========================================="
