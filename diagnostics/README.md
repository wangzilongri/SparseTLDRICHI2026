# Sweep Diagnostics

Comprehensive diagnostic tools for analyzing CATE estimator benchmark sweep results.

## Quick Start

```bash
# Run diagnostics on a results folder
cd diagnostics
python run_diagnostics.py ../results/sweeps_remote

# Specify custom output folder
python run_diagnostics.py ../results/sweeps_remote --output ../diagnostics_output/remote
```

## What It Checks

### 1. Calibration Analysis
- **Calibration Slope**: Should be ~1.0. Values far from 1 indicate systematic magnitude errors.
- **Calibration Intercept**: Should be ~0.0. Non-zero values indicate baseline prediction bias.
- **Calibration R²**: Should be high (>0.5). Low R² means predictions don't track true effects.
- **τ-ECE**: Should be low (<2). High ECE indicates miscalibration across prediction ranges.

### 2. Multi-Axis Failure Detection
Identifies methods failing on multiple metrics simultaneously:
- PEHE > 6.0 (prediction error too high)
- ATE Error > 3.0 (average effect estimation poor)  
- Spearman ρ < 0.5 (ranking quality poor)
- Calibration R² < 0.3 (predictions uncorrelated with truth)
- τ-ECE > 3.0 (calibration is poor)

Methods failing 3+ metrics should be considered critically broken.

### 3. Method Comparison Heatmaps
Visual comparison of methods across (m₀, m₁) grid to identify:
- Problematic budget configurations
- Performance scaling patterns
- Method-specific strengths/weaknesses

### 4. Performance vs Budget
Analysis of how performance scales with target data:
- Total budget (m₀ + m₁) effects
- Disconnected target (m₁=0) viability
- Diminishing returns patterns

## Output Files

After running diagnostics, the output folder contains:

```
diagnostics/
├── diagnostic_report.md           # Main report with embedded images
├── diagnostic_report_compiled.pdf # All figures compiled
├── calibration_analysis.png/pdf   # Calibration diagnostic plots
├── calibration_summary.csv        # Calibration metrics table
├── multi_axis_failure.png/pdf     # Multi-axis failure plots
├── failure_summary.csv            # Failure detection results
├── heatmap_*.png/pdf              # Method comparison heatmaps
├── performance_vs_budget.png/pdf  # Budget scaling plots
```

## Interpreting Results

### Critical Failure Indicators

**ProposedB_SourceDR example (from actual results):**
- PEHE ~7-8 (vs ~3.5 for working methods) — 2× worse
- ATE Error ~5 (vs ~0.15) — 30× worse  
- Spearman ρ ~0.40 (vs ~0.74) — ranking is wrong
- Calibration R² ~0.16 (vs ~0.55) — 3× worse
- τ-ECE ~5.1 (vs ~1.0) — 5× worse

This pattern indicates the method is **fundamentally broken**, not just slightly worse.

### Healthy Method Indicators

- PEHE improves with budget (variance-dominated, not bias)
- Calibration slope near 1.0 with low variance
- High R² (>0.5) indicating predictions track truth
- Low τ-ECE (<2) indicating good calibration across ranges

## Thresholds Used

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| PEHE | <4 | 4-6 | >6 |
| ATE Error | <1 | 1-3 | >3 |
| Spearman ρ | >0.7 | 0.5-0.7 | <0.5 |
| Calib R² | >0.5 | 0.3-0.5 | <0.3 |
| τ-ECE | <2 | 2-3 | >3 |
| Calib Slope | 0.8-1.2 | 0.5-0.8 or 1.2-1.5 | <0.5 or >1.5 |

## Requirements

```
pandas
numpy
matplotlib
seaborn
```

## Usage Examples

```bash
# Analyze remote sweep results
python run_diagnostics.py ../results/sweeps_remote

# Analyze local test results
python run_diagnostics.py ../results/sweeps_test6

# Compare multiple sweeps
for folder in ../results/sweeps_*; do
    python run_diagnostics.py "$folder"
done
```

## Notes

- Diagnostics require aggregated results CSV (`results_agg_*.csv`)
- Replicate-level data (`results_rep_*.csv`) is optional but enhances analysis
- PDF compilation requires matplotlib's PdfPages backend
