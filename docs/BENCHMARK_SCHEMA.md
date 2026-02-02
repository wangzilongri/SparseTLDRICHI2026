# Benchmark Data Model & Schema Specification

This document defines the canonical data model for all benchmark experiments.

---

## 0. Canonical Data Model (Use Everywhere)

### 0.1 Rep-Level Results (`results_rep`)

**One row = one rep × one scenario × one method**

Index-free, long-format (easy to concat).

#### Identifier Columns

| Column | Type | Description |
|--------|------|-------------|
| `benchmark_id` | str | e.g., `"gold_sweep"` |
| `scenario_id` | str | Stable hash/key of scenario params |
| `rep` | int | Monte Carlo replicate id |
| `method` | str | e.g., `"ProposedB_LinearStepB"` |
| `feasibility` | str | `"FeasibleRestricted"` / `"OracleTargetTreated"` / `"InfeasibleByDesign"` |
| `uses_target_placebo` | bool | |
| `uses_target_treated` | bool | |
| `uses_source_data` | bool | Usually True |
| `seed` | int | Optional but nice |

#### Scenario Parameter Columns (fill NA when irrelevant)

| Column | Type | Description |
|--------|------|-------------|
| `m0` | int | Target placebo used for estimation |
| `m1` | int | Target treated used for estimation |
| `n_proxy_total` | int | Total proxy samples across sources |
| `C_sources` | int | Number of source sites |
| `imbalance_ratio` | float | Site imbalance measure |
| `dirichlet_alpha` | float | Dirichlet concentration for site allocation |
| `shift_strength` | float | Covariate shift knob |
| `shift_metric_w1` | float | Measured Wasserstein-1 distance |
| `shift_metric_mmd` | float | Measured MMD |
| `overlap_strength` | float | Overlap/positivity knob |
| `ess_weights` | float | Effective sample size from weights |
| `max_weight_p99` | float | 99th percentile of weights |
| `a5_effective_sparsity` | float | Effective sparsity (k/p or power-law α) |
| `a5_nonlin_type` | str | `"interactions"` / `"piecewise"` / `"tree"` / `"mlp"` |
| `a5_nonlin_strength` | float | Scale of nonlinear term |
| `a6_rank_true` | int | True rank of M* |
| `a6_rank_fit` | int | Assumed rank in Step B |
| `a6_nonlin_rho` | float | Mixing parameter for nonlinear transfer |
| `nontransfer_scale` | float | Scale of non-transferable component |
| `graph_type` | str | `"chain"` / `"star"` / `"two_components"` |
| `K_treatments` | int | Number of treatments |

#### Primary Metrics

| Column | Type | Description |
|--------|------|-------------|
| `pehe` | float | √(E[(τ̂-τ)²]) - NA for real data |
| `tau_corr` | float | Spearman correlation τ̂ vs τ |
| `ate_hat` | float | Estimated ATE |
| `ate_abs_err` | float | |ATE_hat - ATE_true| |
| `mu0_rmse` | float | RMSE of μ̂₀ |
| `mu1_rmse` | float | RMSE of μ̂₁ (NA if not evaluable) |
| `mu0_calib_rmse` | float | Calibration RMSE for μ₀ |
| `mu0_ece` | float | ECE for μ₀ |
| `policy_regret` | float | Policy regret vs oracle |
| `qini_auc` | float | Oracle Qini AUC |

#### Stage-2 / Stability / Runtime Diagnostics

| Column | Type | Description |
|--------|------|-------------|
| `stage2_lambda` | float | Selected LASSO λ |
| `stage2_n_selected` | int | Number of nonzero coefficients |
| `stage2_l2_norm_beta` | float | ‖β̂‖₂ |
| `runtime_sec` | float | Total runtime |

#### Uncertainty (if doing coverage)

| Column | Type | Description |
|--------|------|-------------|
| `ate_se_if` | float | IF-based standard error |
| `ate_se_boot` | float | Bootstrap standard error |
| `ate_ci_low` | float | 95% CI lower bound |
| `ate_ci_high` | float | 95% CI upper bound |
| `ate_covered_95` | int | 0/1 indicator |

---

### 0.2 Aggregated Results (`results_agg`)

**One row = one scenario × one method**

Compute from `results_rep` by grouping on:
```
[benchmark_id, scenario_id, method, feasibility, (all scenario param cols)]
```

#### For each metric X ∈ {pehe, ate_abs_err, mu0_rmse, ...}:

| Column | Type | Description |
|--------|------|-------------|
| `X_mean` | float | Mean across reps |
| `X_sd` | float | Std dev across reps |
| `X_n` | int | Number of valid reps |

#### Paired Deltas vs Reference Method

Reference: `ProxyOnly` (unless noted)

| Column | Type | Description |
|--------|------|-------------|
| `pehe_delta_vs_proxy_mean` | float | Mean(PEHE_method - PEHE_proxy) |
| `pehe_delta_vs_proxy_sd` | float | Std of delta |
| `pehe_p_value` | float | Paired t-test or Wilcoxon |
| `pehe_q_value` | float | Holm-corrected p-value |

Same for: `mu0_rmse_*`, `ate_abs_err_*`, etc.

---

### 0.3 Regime Definitions (`regime_definitions`)

| Column | Type | Description |
|--------|------|-------------|
| `regime_id` | str | R1–R4 |
| `shift_strength` | float | |
| `overlap_strength` | float | |
| `m0` | int | |
| `n_proxy_total` | int | |
| `disconnected` | bool | |
| `notes` | str | |

---

## 1. Benchmark-Specific Required Columns

### 1.1 Gold-Budget Sweep (`benchmark_id="gold_sweep"`)

**Required:** `m0`, `m1`, `n_proxy_total`, `shift_strength`, `nontransfer_scale`, `a6_rank_true`, `a6_rank_fit`

### 1.2 Proxy-Budget Sweep (`benchmark_id="proxy_sweep"`)

**Required:** `n_proxy_total`, `m0`, plus fixed config columns

### 1.3 Site Imbalance Sweep (`benchmark_id="site_imbalance"`)

**Required:** `n_proxy_total`, `m0`, `imbalance_ratio` OR `dirichlet_alpha`

### 1.4 Covariate Shift Sweep (`benchmark_id="covariate_shift"`)

**Required:** `shift_strength`, `shift_metric_w1`, `m0`, `n_proxy_total`, `ess_weights`, `max_weight_p99`

### 1.5 Overlap Stress-Test (`benchmark_id="overlap_stress"`)

**Required:** `overlap_strength`, `m0`, `n_proxy_total`, `ess_weights`, `max_weight_p99`

### 1.6 A5 Dense Correction (`benchmark_id="a5_dense"`)

**Required:** `a5_effective_sparsity`, `m0`, `n_proxy_total`

### 1.7 A5 Nonlinear Correction (`benchmark_id="a5_nonlinear"`)

**Required:** `a5_nonlin_type`, `a5_nonlin_strength`, `m0`, `n_proxy_total`

### 1.8 A6 Rank Mismatch (`benchmark_id="a6_rank"`)

**Required:** `a6_rank_true`, `a6_rank_fit`, `m0`, `n_proxy_total`

### 1.9 A6 Nonlinear Mapping (`benchmark_id="a6_nonlinear"`)

**Required:** `a6_nonlin_rho`, `nontransfer_scale`, `m0`, `n_proxy_total`

### 1.10 Disconnected Graph Family (`benchmark_id="disconnected_graph"`)

**Required:** `K_treatments`, `graph_type`, `m0`

### 1.11 Coverage / Uncertainty (`benchmark_id="coverage"`)

**Required:** Same scenario cols as setting + `ate_ci_low`, `ate_ci_high`, `ate_covered_95`, `ate_se_if`

### 1.12 Lambda Stability (`benchmark_id="lambda_stability"`)

**Required:** `m0`, `stage2_lambda`, `stage2_n_selected`

---

## 2. Python Dataclasses

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class Scenario:
    """Immutable scenario configuration."""
    benchmark_id: str
    scenario_id: str
    
    # Common knobs
    m0: Optional[int] = None
    m1: Optional[int] = None
    n_proxy_total: Optional[int] = None
    C_sources: Optional[int] = None

    # Shift / overlap
    shift_strength: Optional[float] = None
    shift_metric_w1: Optional[float] = None
    overlap_strength: Optional[float] = None
    ess_weights: Optional[float] = None
    max_weight_p99: Optional[float] = None

    # A5 knobs
    a5_effective_sparsity: Optional[float] = None
    a5_nonlin_type: Optional[str] = None
    a5_nonlin_strength: Optional[float] = None

    # A6 knobs
    a6_rank_true: Optional[int] = None
    a6_rank_fit: Optional[int] = None
    a6_nonlin_rho: Optional[float] = None
    nontransfer_scale: Optional[float] = None

    # Network knobs
    K_treatments: Optional[int] = None
    graph_type: Optional[str] = None


@dataclass(frozen=True)
class MethodSpec:
    """Method specification with feasibility labeling."""
    method: str
    feasibility: str  # "FeasibleRestricted" | "OracleTargetTreated" | "InfeasibleByDesign"
    uses_target_placebo: bool
    uses_target_treated: bool
    uses_source_data: bool = True


@dataclass
class RepResult:
    """Single replicate result."""
    scenario_id: str
    benchmark_id: str
    rep: int
    method: str
    feasibility: str

    # Core metrics
    pehe: Optional[float] = None
    tau_corr: Optional[float] = None
    ate_hat: Optional[float] = None
    ate_abs_err: Optional[float] = None
    mu0_rmse: Optional[float] = None
    mu1_rmse: Optional[float] = None
    mu0_calib_rmse: Optional[float] = None
    policy_regret: Optional[float] = None
    qini_auc: Optional[float] = None

    # Diagnostics
    stage2_lambda: Optional[float] = None
    stage2_n_selected: Optional[int] = None
    runtime_sec: Optional[float] = None

    # Uncertainty
    ate_se_if: Optional[float] = None
    ate_se_boot: Optional[float] = None
    ate_ci_low: Optional[float] = None
    ate_ci_high: Optional[float] = None
    ate_covered_95: Optional[int] = None


@dataclass(frozen=True)
class PlotSpec:
    """Plot specification for automated figure generation."""
    name: str
    df: str  # "results_rep" or "results_agg"
    plot_type: str  # "line" | "bar" | "heatmap" | "violin" | "scatter"
    x: str
    y: str
    hue: Optional[str] = None
    facet: Optional[str] = None
    yerr: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None  # column -> allowed values / (min, max)
```

---

## 3. Plot Specifications

### 3.1 Gold-Budget Sweep (Main Paper Figure 1)

| Plot | df | x | y | yerr | hue | facet | type |
|------|-----|---|---|------|-----|-------|------|
| PEHE vs m0 | `results_agg` | `m0` | `pehe_mean` | `pehe_sd` | `method` | `m1` (opt) | line |
| μ₀ RMSE vs m0 | `results_agg` | `m0` | `mu0_rmse_mean` | `mu0_rmse_sd` | `method` | | line |
| n_selected vs m0 | `results_agg` | `m0` | `stage2_n_selected_mean` | `stage2_n_selected_sd` | `method` | | line |

### 3.2 Proxy-Budget Sweep

| Plot | df | x | y | yerr | hue | type |
|------|-----|---|---|------|-----|------|
| PEHE vs n_proxy | `results_agg` | `n_proxy_total` | `pehe_mean` | `pehe_sd` | `method` | line |
| Runtime vs n_proxy | `results_agg` | `n_proxy_total` | `runtime_sec_mean` | | `method` | line |

### 3.3 Site Imbalance Sweep

| Plot | df | x | y | yerr | hue | type |
|------|-----|---|---|------|-----|------|
| PEHE vs imbalance | `results_agg` | `imbalance_ratio` | `pehe_mean` | `pehe_sd` | `method` | line |

### 3.4 Covariate Shift Sweep (Main Figure 3 candidate)

| Plot | df | x | y | yerr | hue | type |
|------|-----|---|---|------|-----|------|
| PEHE vs shift (measured) | `results_agg` | `shift_metric_w1` | `pehe_mean` | `pehe_sd` | `method` | line |
| ESS vs shift | `results_agg` | `shift_metric_w1` | `ess_weights_mean` | | `method` | line |

### 3.5 Overlap Stress-Test

| Plot | df | x | y | yerr | hue | type |
|------|-----|---|---|------|-----|------|
| ATE error vs overlap | `results_agg` | `overlap_strength` | `ate_abs_err_mean` | `ate_abs_err_sd` | `method` | line |
| Max weight vs overlap | `results_agg` | `overlap_strength` | `max_weight_p99_mean` | | `method` | line |

### 3.6 A5 Dense Correction (Main Figure 2 panel)

| Plot | df | x | y | yerr | hue | type |
|------|-----|---|---|------|-----|------|
| PEHE vs sparsity | `results_agg` | `a5_effective_sparsity` | `pehe_mean` | `pehe_sd` | `method` | line |
| n_selected vs sparsity | `results_agg` | `a5_effective_sparsity` | `stage2_n_selected_mean` | | `method` | line |

### 3.7 A5 Nonlinear Correction

| Plot | df | x | y | yerr | hue | facet | type |
|------|-----|---|---|------|-----|-------|------|
| PEHE vs nonlin strength | `results_agg` | `a5_nonlin_strength` | `pehe_mean` | `pehe_sd` | `method` | `a5_nonlin_type` | line |

### 3.8 A6 Rank Mismatch (Main Figure 2 panel)

| Plot | df | x | y | type |
|------|-----|---|---|------|
| PEHE heatmap | `results_agg` (ProposedB only) | `a6_rank_fit` (cols) | `a6_rank_true` (rows) | heatmap |

**Values:** `pehe_delta_vs_proxy_mean` or `pehe_mean`

### 3.9 A6 Nonlinear Mapping

| Plot | df | x | y | yerr | hue | type |
|------|-----|---|---|------|-----|------|
| PEHE vs ρ | `results_agg` | `a6_nonlin_rho` | `pehe_mean` | `pehe_sd` | `method` | line |

### 3.10 Baseline Regime Comparison (Main Figure 3)

| Plot | df | x | y | hue | type |
|------|-----|---|---|-----|------|
| Grouped bars by regime | `results_agg` | `regime_id` | `pehe_mean` | `method` | bar |

**Annotation:** Stripe by `feasibility`

### 3.11 Coverage / Uncertainty (Appendix)

| Plot | df | x | y | type |
|------|-----|---|---|------|
| Coverage vs m0 | `results_agg` | `m0` | `ate_covered_95_mean` | line |
| IF-SE vs Boot-SE | `results_rep` | `ate_se_if` | `ate_se_boot` | scatter |

### 3.12 Lambda Stability (Appendix)

| Plot | df | x | y | type |
|------|-----|---|---|------|
| Lambda distribution | `results_rep` | `m0` | `stage2_lambda` | violin |
| Lambda vs PEHE | `results_rep` | `stage2_lambda` | `pehe` | scatter |

---

## 4. Reviewer-Facing Table Templates

### Template A: Sweep Table (Gold/Proxy/Shift/Overlap)

| sweep_knob | method | feasibility | pehe_mean (sd) | μ₀_rmse_mean (sd) | ate_err_mean (sd) | Δ_pehe | q |
|------------|--------|-------------|----------------|-------------------|-------------------|--------|---|
| ... | ... | ... | ... | ... | ... | ... | ... |

### Template B: Misspec Table (A5/A6)

| misspec_knob | method | pehe_mean (sd) | Δ_vs_proxy | q | n_selected_mean (sd) |
|--------------|--------|----------------|------------|---|----------------------|
| ... | ... | ... | ... | ... | ... |

### Template C: Baseline Regime Table

| regime_id | method | feasibility | pehe_mean (sd) | ate_err_mean (sd) | μ₀_rmse_mean (sd) | ess_mean | runtime_mean |
|-----------|--------|-------------|----------------|-------------------|-------------------|----------|--------------|
| ... | ... | ... | ... | ... | ... | ... | ... |

---

## 5. Method Names (Whitelist)

### Core Methods

| Method Name | Feasibility (Restricted) | Feasibility (Oracle) |
|-------------|--------------------------|----------------------|
| `NoTransfer` | FeasibleRestricted | OracleTargetTreated |
| `ProxyOnly` | FeasibleRestricted | FeasibleRestricted |
| `AnchorOnly` | FeasibleRestricted | OracleTargetTreated |
| `ProposedA` | OracleTargetTreated | OracleTargetTreated |
| `ProposedB_LinearStepB` | FeasibleRestricted | FeasibleRestricted |
| `ProposedB_KernelStepB` | FeasibleRestricted | FeasibleRestricted |

### Baseline Methods

| Method Name | Feasibility | Notes |
|-------------|-------------|-------|
| `IPD_RE` | OracleTargetTreated | Random effects hierarchical |
| `AIPWTransport` | FeasibleRestricted | Transport AIPW |
| `EntropyBalancing` | FeasibleRestricted | Covariate balancing |
| `DRLearner_PooledWithSite` | OracleTargetTreated | With site ID feature |
| `DRLearner_PooledNoSite` | OracleTargetTreated | Without site ID |
| `TARNet` | OracleTargetTreated | Representation learning |

---

## 6. Validation Function

```python
import pandas as pd
import numpy as np

REQUIRED_ID_COLS = ['benchmark_id', 'scenario_id', 'rep', 'method', 'feasibility']
REQUIRED_METRIC_COLS = ['pehe', 'ate_abs_err', 'mu0_rmse']

BENCHMARK_REQUIRED_COLS = {
    'gold_sweep': ['m0', 'm1', 'n_proxy_total'],
    'proxy_sweep': ['n_proxy_total', 'm0'],
    'site_imbalance': ['n_proxy_total', 'm0'],  # + imbalance_ratio OR dirichlet_alpha
    'covariate_shift': ['shift_strength', 'shift_metric_w1', 'm0', 'n_proxy_total'],
    'overlap_stress': ['overlap_strength', 'm0', 'n_proxy_total'],
    'a5_dense': ['a5_effective_sparsity', 'm0', 'n_proxy_total'],
    'a5_nonlinear': ['a5_nonlin_type', 'a5_nonlin_strength', 'm0', 'n_proxy_total'],
    'a6_rank': ['a6_rank_true', 'a6_rank_fit', 'm0', 'n_proxy_total'],
    'a6_nonlinear': ['a6_nonlin_rho', 'm0', 'n_proxy_total'],
    'disconnected_graph': ['K_treatments', 'graph_type', 'm0'],
    'coverage': ['ate_ci_low', 'ate_ci_high', 'ate_covered_95'],
    'lambda_stability': ['m0', 'stage2_lambda', 'stage2_n_selected'],
}

FEASIBILITY_VALUES = {'FeasibleRestricted', 'OracleTargetTreated', 'InfeasibleByDesign'}

def validate_results_rep(df: pd.DataFrame, benchmark_id: str) -> None:
    """Validate rep-level results DataFrame."""
    # Check required ID columns
    missing_id = set(REQUIRED_ID_COLS) - set(df.columns)
    if missing_id:
        raise ValueError(f"Missing ID columns: {missing_id}")
    
    # Check benchmark-specific columns
    if benchmark_id in BENCHMARK_REQUIRED_COLS:
        required = BENCHMARK_REQUIRED_COLS[benchmark_id]
        missing = set(required) - set(df.columns)
        if missing:
            raise ValueError(f"Benchmark '{benchmark_id}' missing columns: {missing}")
    
    # Check feasibility values
    invalid_feas = set(df['feasibility'].unique()) - FEASIBILITY_VALUES
    if invalid_feas:
        raise ValueError(f"Invalid feasibility values: {invalid_feas}")
    
    # Check at least one metric present
    metrics_present = set(REQUIRED_METRIC_COLS) & set(df.columns)
    if not metrics_present:
        raise ValueError(f"No required metrics found. Need at least one of: {REQUIRED_METRIC_COLS}")
    
    print(f"✓ Validation passed for benchmark '{benchmark_id}'")
```

---

*Last updated: 2026-01-30*
