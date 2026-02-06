# A5 Violation Sensitivity Analysis

**Purpose**: Test how our sparse linear correction method degrades when Assumption A5 is violated.

**Status**: Implementation complete in `src/synthetic_data_v2_fair.py`

---

## 1. Background: What is Assumption A5?

Assumption A5 states that the **site-specific deviation** (the difference between source and target outcome models) is **sparse and linear**:

$$
\mu_{a,c}(x) = \mu_a^{\text{proxy}}(x) + x^\top \beta_{a,c}
$$

Where:
- $\mu_a^{\text{proxy}}(x)$ is the shared (proxy) outcome model learned from sources
- $\beta_{a,c}$ is a **sparse** coefficient vector (most entries are zero)
- The correction is **linear** in $x$

**Why this matters**: Our method uses LASSO to estimate $\beta_{a,c}$. If A5 is violated (dense or nonlinear correction), LASSO may fail to capture the true deviation, degrading performance.

---

## 2. Two Axes of A5 Violation

The advisor identified two ways A5 can be violated:

### A. Non-Sparse Violations (Dense Coefficients)

The correction $\beta$ has many non-zero entries instead of being sparse.

| Violation Type | Description | Parameters |
|----------------|-------------|------------|
| **Dense support** | Many features have non-zero coefficients | `a5_sparsity_ratio` |
| **Slow decay** | Coefficients don't decay fast (approximately sparse) | `a5_decay_alpha` |
| **Dense residual** | Sparse component + dense noise | `a5_violation_eta` |

### B. Nonlinear Violations

The correction is not linear in $x$:

$$
\delta(x) = (1 - \lambda) \cdot x^\top \beta + \lambda \cdot g(x)
$$

Where $g(x)$ is a nonlinear function. We test three families:

| Nonlinear Type | Function $g(x)$ | Difficulty |
|----------------|-----------------|------------|
| **Additive** | $\sum_j a_j \sin(\omega x_j)$ | Mild (smooth) |
| **Interaction** | $\sum_{j,k} a_{jk} x_j x_k$ | Moderate (epistatic) |
| **Threshold** | $\sum_j a_j \mathbf{1}\{x_j > t_j\}$ | Hard (discontinuous) |

---

## 3. Parameters Added to `FairSyntheticRCTConfig`

### Non-Sparse Parameters

```python
# A5.1: Sparsity ratio s/p
# 0.05 = sparse (5% non-zero), 1.0 = fully dense
a5_sparsity_ratio: float = 0.05  # Default: sparse (A5 holds)

# A5.2: Coefficient decay α
# |β|_(j) ∝ j^(-α), where α=2 is near-sparse, α=0 is flat/uniform
a5_decay_alpha: float = 2.0  # Default: fast decay (A5 holds)

# A5.3: Dense residual ratio η = ||β^⊥||_2 / ||β^(s)||_2
# β = β^(sparse) + β^(dense), η controls dense component size
a5_violation_eta: float = 0.0  # Default: no dense residual
```

### Nonlinear Parameters

```python
# A5.4: Linear/nonlinear mixture weight λ
# δ(x) = (1-λ)·x^T β + λ·g(x)
# λ=0 is pure linear, λ=1 is pure nonlinear
a5_nonlin_lambda: float = 0.0  # Default: linear (A5 holds)

# A5.5: Nonlinear function type
# Options: 'additive', 'interaction', 'threshold'
a5_nonlin_type: str = 'additive'

# A5.6: How many features the nonlinearity touches
a5_nonlin_support: Optional[int] = None  # Default: use a5_sparsity_ratio * p

# A5.7: Nonlinear component strength
# Scales Var(g(X)) to be comparable to Var(x^T β)
a5_nonlin_strength: float = 1.0

# A5.8: Frequency for additive sin() nonlinearity
a5_nonlin_omega: float = 2.0
```

---

## 4. Available Sweep Configurations

All configs are in `A5_SWEEP_CONFIGS` dictionary in `src/synthetic_data_v2_fair.py`.

### Single-Axis Sweeps

| Sweep Name | Varies | Values | Tests |
|------------|--------|--------|-------|
| `a5_sparsity` | `a5_sparsity_ratio` | {0.02, 0.05, 0.10, 0.20, 0.50, 1.00} | Sparse → Dense |
| `a5_decay` | `a5_decay_alpha` | {2.0, 1.0, 0.5, 0.0} | Fast decay → Flat |
| `a5_dense_residual` | `a5_violation_eta` | {0, 0.25, 0.5, 1.0, 2.0} | No noise → Dominant noise |
| `a5_nonlinear_additive` | `a5_nonlin_lambda` | {0, 0.25, 0.5, 0.75, 1.0} | Linear → Smooth nonlinear |
| `a5_nonlinear_interaction` | `a5_nonlin_lambda` | {0, 0.25, 0.5, 0.75, 1.0} | Linear → Interactions |
| `a5_nonlinear_threshold` | `a5_nonlin_lambda` | {0, 0.25, 0.5, 0.75, 1.0} | Linear → Discontinuous |

### Combined Sweeps (Reviewer-Proof Grid)

| Sweep Name | Grid | Total Scenarios | Description |
|------------|------|-----------------|-------------|
| `a5_sparsity_x_nonlin` | 3×3 | 9 | Sparsity {0.05, 0.2, 1.0} × Nonlinearity {0, 0.5, 1.0} |
| `a5_full_grid` | 3×3×2 | 18 | Above × Nonlin type {additive, interaction} |

---

## 5. Diagnostics Reported

The `get_fairness_diagnostics()` method now reports A5-specific metrics:

```python
diag = generator.get_fairness_diagnostics()

# Sparsity metrics
diag['a5_effective_sparsity']  # Fraction of significant coefficients
diag['a5_n_for_90pct_mass']    # How many coefficients for 90% of L1 mass
diag['a5_mass_concentration']  # 0 = concentrated (sparse), 1 = diffuse (dense)

# Nonlinearity metrics
diag['a5_nonlin_lambda']       # Current λ setting
diag['a5_nonlin_type']         # Current nonlinear function type
diag['a5_var_linear']          # Var(x^T β)
diag['a5_var_nonlinear']       # Var(g(x))
diag['a5_nonlin_var_ratio']    # Var(g)/Var(linear)

# Config values (for reference)
diag['a5_sparsity_ratio_config']
diag['a5_decay_alpha_config']
diag['a5_violation_eta_config']
```

---

## 6. How to Run (Not Yet in core_sweeps.py)

Currently, A5 sweeps must be run manually. Example:

```python
from src.synthetic_data_v2_fair import (
    FairSyntheticRCTConfig, 
    FairSyntheticRCTGenerator,
    A5_SWEEP_CONFIGS
)

# Get sweep config
config_name = 'a5_sparsity'
sweep_config = A5_SWEEP_CONFIGS[config_name]

# Run sweep
results = []
for sparsity_ratio in sweep_config['sweep']['a5_sparsity_ratio']:
    # Create config with this sparsity
    cfg = FairSyntheticRCTConfig(
        a5_sparsity_ratio=sparsity_ratio,
        **sweep_config['fixed']
    )
    
    # Generate data and run estimators
    gen = FairSyntheticRCTGenerator(cfg)
    source, target = gen.generate_full_dataset()
    diag = gen.get_fairness_diagnostics()
    
    # ... run estimators and collect metrics ...
    results.append({
        'a5_sparsity_ratio': sparsity_ratio,
        'effective_sparsity': diag['a5_effective_sparsity'],
        # ... other metrics ...
    })
```

---

## 7. Expected Results & Interpretation

### What We Expect to See

1. **When A5 holds** (sparse, linear): Our method should perform well
2. **As sparsity increases**: Gradual degradation (LASSO struggles with dense signals)
3. **As nonlinearity increases**: Gradation degradation (linear model misspecified)
4. **Interactions worse than additive**: Epistatic effects harder to capture
5. **Thresholds worst**: Discontinuities break smooth methods

### The Narrative for Reviewers

> "We systematically test A5 violations across two axes: sparsity and nonlinearity. 
> Our method degrades gracefully as violations increase, remaining competitive for 
> moderate violations (s/p < 0.2, λ < 0.5). For severe violations, we recommend 
> using flexible correction methods (RF/GBM) at the cost of interpretability."

### Key Plots to Generate

1. **PEHE vs Sparsity Ratio** (line plot): Shows degradation curve
2. **PEHE vs Nonlinearity λ** (line plot, one per nonlin type): Shows nonlinear robustness
3. **Heatmap: Sparsity × Nonlinearity** (for compact summary)

---

## 8. Design Decisions

### Why L2 Norm is Held Constant

When varying sparsity, we keep $\|\beta\|_2$ constant so that:
- The "signal strength" is the same across settings
- We're only measuring the effect of sparsity, not magnitude
- Reviewers can't say "you just made the problem harder"

### Why We Normalize Nonlinear Variance

The nonlinear component $g(x)$ is scaled so that:
$$
\text{Var}(g(X)) \approx \text{Var}(x^\top \beta)
$$

This ensures $\lambda$ truly controls the mixture, not just the signal-to-noise ratio.

### Why Three Nonlinear Families

1. **Additive**: Tests mild misspecification (still separable across features)
2. **Interaction**: Tests moderate misspecification (pairwise dependencies)
3. **Threshold**: Tests severe misspecification (non-smooth, hard boundaries)

This covers the spectrum from "LASSO might still work" to "LASSO definitely fails."

---

## 9. Integration with core_sweeps.py ✅

**Status: COMPLETE**

The A5 violation sweep is now fully integrated with the benchmark runner:

1. ✅ A5 parameters added to `Scenario` dataclass in `benchmark_schema.py`
2. ✅ `a5_violation` sweep added to `SWEEP_CONFIGS` in `core_sweeps.py`
3. ✅ A5 params passed through to `FairSyntheticRCTConfig` via `benchmark_adapters.py`
4. ✅ Generates 2D heatmaps (Sparsity × Nonlinearity)

### Running the Integrated Sweep

```bash
# Run the A5 violation sweep (3×3 = 9 scenarios)
python -m experiments.core_sweeps --sweep a5_violation --n_rep 50 --output results/a5_violation

# With more parallelism for cluster
python -m experiments.core_sweeps --sweep a5_violation --n_rep 100 --n_jobs 40 \
    --output results/a5_violation_production
```

### What the Sweep Tests

| X-axis: Sparsity (s/p) | Y-axis: Nonlinearity (λ) |
|------------------------|--------------------------|
| 0.05 (sparse, A5 holds) | 0.0 (linear, A5 holds) |
| 0.20 (moderate) | 0.5 (mixture) |
| 1.0 (dense, A5 violated) | 1.0 (nonlinear, A5 violated) |

**Output:** Heatmaps for PEHE, ATE error, and Spearman correlation, showing graceful degradation from (0.05, 0.0) to (1.0, 1.0).

---

## 10. Quick Test

```bash
cd /path/to/Sparse_TL_DR_ICHI2026
python -c "
from src.synthetic_data_v2_fair import (
    FairSyntheticRCTConfig, 
    FairSyntheticRCTGenerator,
    A5_SWEEP_CONFIGS
)

# Test dense coefficients
cfg = FairSyntheticRCTConfig(a5_sparsity_ratio=1.0, a5_decay_alpha=0.0)
gen = FairSyntheticRCTGenerator(cfg)
diag = gen.get_fairness_diagnostics()
print(f'Dense: effective_sparsity = {diag[\"a5_effective_sparsity\"]:.2f}')

# Test nonlinear
cfg = FairSyntheticRCTConfig(a5_nonlin_lambda=0.5, a5_nonlin_type='interaction')
gen = FairSyntheticRCTGenerator(cfg)
diag = gen.get_fairness_diagnostics()
print(f'Nonlinear: var_ratio = {diag[\"a5_nonlin_var_ratio\"]:.2f}')

print('\\nAvailable sweeps:', list(A5_SWEEP_CONFIGS.keys()))
"
```

---

## Summary

| Aspect | Details |
|--------|---------|
| **Goal** | Test robustness to A5 assumption violations |
| **Two axes** | Non-sparse (dense) and Nonlinear corrections |
| **Parameters** | 8 new config parameters in `FairSyntheticRCTConfig` |
| **Sweeps** | 6 single-axis + 2 combined grids |
| **Minimal grid** | 3×3×2 = 18 scenarios (reviewer-proof) |
| **Key narrative** | "Degrades gracefully; competitive for moderate violations" |
