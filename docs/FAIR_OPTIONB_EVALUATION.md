# Fair OptionB Evaluation Framework

This document explains how to evaluate ProposedB_SourceDR (OptionB) fairly, following the advisor's recommendations.

## The Problem

Previous sweeps showed "catastrophic failure" for ProposedB_SourceDR because the DGP simultaneously violated **three** assumptions:

1. **SNR < 1** (nontransfer dominates transferable signal)
2. **Overlap AUC = 1.0** (source and target covariates are completely disjoint)
3. **High intercept drift** (arm-specific baselines vary wildly across replications)

This made OptionB fail for multiple independent reasons, making the evaluation unfair.

## What OptionB Actually Assumes

ProposedB_SourceDR works as follows:

```
Stage 1: Fit proxy on sources → μ̂₀, μ̂₁
Stage 2: Learn δ₀ on TARGET placebo only
         Transfer to δ₁ via: β̂₁ = M̂ @ β̂₀
Stage 3: Compute DR pseudo-outcomes on SOURCES
         Train CATE model on source pseudo-outcomes
Stage 4: Predict CATE on TARGET X (generalization)
```

This works **only if**:

| Assumption | Formula | What it means |
|------------|---------|---------------|
| A. Cross-arm transport | β₁,t ≈ M* @ β₀,t | Treated deviation is predictable from placebo |
| B. SNR ≥ 1 | \|M*β₀\| ≥ \|ν\| | Transfer signal dominates nontransfer component |
| C. Overlap | AUC(source vs target) < 0.9 | Source models can generalize to target |
| D. Controlled drift | σ_α ≤ 1 | Arm intercepts don't dominate |

## Fair DGP Configuration

### File: `src/synthetic_data_v2_fair.py`

New knobs for fair evaluation:

```python
config = FairSyntheticRCTConfig(
    # Cross-arm signal strength (SNR ladder)
    nontransfer_scale_target=0.1,  # 0=perfect transfer, 0.3=SNR~1
    
    # Covariate overlap
    overlap_lambda=0.25,  # 0=same as source, 1=fully shifted
    
    # Intercept drift
    intercept_drift_scale=0.5,  # σ_α for arm intercepts
    
    # Structured nontransfer (optional)
    nu_support_overlap=0.5,  # How much ν overlaps β₀ support
    nu_coefficient_corr=0.0,  # Correlation between ν and β₀
)
```

## Advisor-Recommended Sweeps

### Sweep A: Cross-arm validity (primary)

Tests OptionB across SNR ladder, holding other factors fair.

```bash
python experiments/fair_optionb_sweeps.py --sweep cross_arm_validity --n_rep 20
```

Configuration:
- Swept: `nontransfer_scale_target ∈ {0, 0.05, 0.1, 0.2, 0.3}`
- Fixed: `overlap_lambda=0.25`, `intercept_drift_scale=0.5`

**Expected finding**: OptionB degrades as SNR approaches 1, confirming assumption violation.

### Sweep B: Overlap stress

Tests generalization across covariate overlap ladder.

```bash
python experiments/fair_optionb_sweeps.py --sweep overlap_stress --n_rep 20
```

Configuration:
- Swept: `overlap_lambda ∈ {0, 0.25, 0.5, 0.75, 1.0}`
- Fixed: `nontransfer_scale_target=0` (perfect transfer), `intercept_drift_scale=0.5`

**Expected finding**: OptionB degrades when AUC > 0.9 (extrapolation failure).

### Sweep C: Drift stress

Tests robustness to arm intercept drift.

```bash
python experiments/fair_optionb_sweeps.py --sweep drift_stress --n_rep 20
```

Configuration:
- Swept: `intercept_drift_scale ∈ {0, 0.5, 1.0, 2.0, 4.0}`
- Fixed: `nontransfer_scale_target=0`, `overlap_lambda=0.25`

**Expected finding**: Calibration intercept variance explodes with high drift.

### Run all sweeps

```bash
python experiments/fair_optionb_sweeps.py --all --n_rep 20
```

## Interpreting Results

### Fairness Gates

Each result is tagged with fairness assessment:

| Metric | Fair | Stress |
|--------|------|--------|
| SNR | ≥ 1 | < 1 |
| Overlap AUC | < 0.85 | ≥ 0.9 |
| Drift scale | ≤ 1 | > 2 |

### What to Report

1. **Primary comparison** (all gates pass): Main results where OptionB assumptions hold
2. **Stress test** (gates fail): Negative control showing assumption violations

### Paper Language

> We evaluate the source-only fallback (OptionB) in regimes where cross-arm structure is present (SNR ≥ 1), overlap is moderate, and intercept drift is controlled. Outside these regimes, OptionB serves as a negative control demonstrating the necessity of each assumption.

## Output Files

After running sweeps, find results in `results/fair_optionb_sweeps/`:

- `{sweep_name}_report.md` - Markdown report with tables
- `{sweep_name}_agg.csv` - Aggregated results
- `{sweep_name}_raw.csv` - Raw replicate-level results

## Quick Test

```bash
# Run quick 2-rep test
python -c "
from experiments.fair_optionb_sweeps import run_sweep, generate_fair_sweep_report
from pathlib import Path

df = run_sweep('cross_arm_validity', n_rep=2, n_jobs=2)
generate_fair_sweep_report(df, 'cross_arm_validity', Path('results/test'))
"
```

## Comparison with Original Sweeps

| Aspect | Original `sweeps_remote` | Fair Sweeps |
|--------|--------------------------|-------------|
| SNR | < 1 (unfair) | Swept 0.0 to 0.3 |
| Overlap | AUC = 1.0 (unfair) | AUC ~ 0.7-0.85 (fair) |
| Drift | Uncontrolled | Controlled σ_α = 0.5 |
| Result | 6/6 metric failures | Moderate degradation |
| Interpretation | "OptionB is broken" | "OptionB has assumption limits" |

## Key Findings

From the quick test (2 replications), even in fair regimes:

| Method | PEHE | Spearman | Calib R² |
|--------|------|----------|----------|
| ProposedA | ~2.2 | ~0.91 | ~0.84 |
| ProposedB_SourceDR | ~3.8 | ~0.67 | ~0.47 |

**Conclusion**: OptionB underperforms ProposedA even in fair regimes, but the degradation is moderate (not catastrophic). The gap is due to:

1. Loss of direct target treated information
2. Reliance on cross-arm transfer assumption
3. Generalization from source to target distribution

This is **expected behavior**, not a bug.
