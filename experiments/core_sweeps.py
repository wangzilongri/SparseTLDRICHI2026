"""
Core Sweeps: Gold-budget, Proxy-budget, and Site Imbalance benchmarks.

These are the highest-priority sweeps for addressing reviewer concerns:
1. Gold-budget (m0): Shows value of scarce target data
2. Proxy-budget (n_proxy): Shows interaction with proxy data size
3. Site imbalance: Shows robustness to unequal site sizes

Usage:
    python experiments/core_sweeps.py --sweep gold --n_rep 50 --output results/sweeps
    python experiments/core_sweeps.py --sweep proxy --n_rep 50 --output results/sweeps
    python experiments/core_sweeps.py --sweep imbalance --n_rep 50 --output results/sweeps
    python experiments/core_sweeps.py --sweep all --n_rep 20 --output results/sweeps
    
    # Parallel execution (recommended):n
    python experiments/core_sweeps.py --sweep all --n_rep 20 --n_jobs -1  # Use all cores
    python experiments/core_sweeps.py --sweep gold --n_rep 50 --n_jobs 8  # Use 8 cores
"""

import os
import sys
import argparse
import warnings
import time
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from benchmark_schema import (
    Scenario, RepResult, Feasibility,
    generate_seed, validate_results_rep,
    METHOD_REGISTRY, get_method_spec
)
from benchmark_aggregation import (
    aggregate_results, find_best_methods, save_aggregated_results, create_latex_table
)
from benchmark_plots import (
    plot_line, generate_benchmark_plots, setup_plot_style, PlotSpec, execute_plot_spec
)
from benchmark_adapters import (
    create_data_generator, create_metric_computer, create_method_factories
)


# =============================================================================
# Metric Definitions (for reports)
# =============================================================================

METRIC_DEFINITIONS = {
    # =========================================================================
    # POINT ESTIMATION METRICS
    # =========================================================================
    'pehe': {
        'name': 'PEHE (Precision in Estimating Heterogeneous Effects)',
        'formula': r'$\sqrt{\frac{1}{n}\sum_i (\hat{\tau}(x_i) - \tau(x_i))^2}$',
        'direction': 'lower is better',
        'description': 'Root mean squared error of CATE predictions. Measures how accurately '
                      'the estimator predicts individual treatment effects.',
        'interpretation': 'A PEHE of 0.5 means predictions are off by 0.5 units on average.'
    },
    'ate_abs_err': {
        'name': 'ATE Absolute Error',
        'formula': r'$|\hat{\text{ATE}} - \text{ATE}|$',
        'direction': 'lower is better',
        'description': 'Absolute difference between estimated and true average treatment effect.',
        'interpretation': 'Important for policy decisions about whether to adopt treatment broadly.'
    },
    'ate_bias': {
        'name': 'ATE Bias (Signed)',
        'formula': r'$\hat{\text{ATE}} - \text{ATE}$',
        'direction': 'closer to 0 is better',
        'description': 'Signed bias in ATE estimate. Positive = overestimate, negative = underestimate.',
        'interpretation': 'Shows systematic over/under-estimation tendencies.'
    },
    
    # =========================================================================
    # RANKING / HETEROGENEITY DISCOVERY METRICS
    # =========================================================================
    'tau_corr': {
        'name': 'Spearman Rank Correlation',
        'formula': r'$\rho(\text{rank}(\hat{\tau}), \text{rank}(\tau))$',
        'direction': 'higher is better',
        'description': 'Rank correlation between predicted and true treatment effects.',
        'interpretation': '1.0 = perfect ranking, 0.0 = random. Critical for targeting interventions.'
    },
    'tau_kendall': {
        'name': 'Kendall Rank Correlation',
        'formula': r'$\tau_K(\hat{\tau}, \tau)$',
        'direction': 'higher is better',
        'description': 'Kendall tau-b correlation. More robust to ties than Spearman.',
        'interpretation': 'Alternative ranking metric; useful when ties are common.'
    },
    'qini_auc': {
        'name': 'Qini AUC (Oracle)',
        'formula': r'Normalized AUC of cumulative uplift curve',
        'direction': 'higher is better',
        'description': 'Area under the Qini curve. Measures ranking quality for treatment targeting.',
        'interpretation': '1.0 = oracle ranking, 0.0 = random. Simulation-only metric using true τ.'
    },
    'topk_10_ratio': {
        'name': 'Top-10% Uplift Capture Ratio',
        'formula': r'$\frac{\bar{\tau}_{top10\%\ by\ \hat{\tau}}}{\bar{\tau}_{top10\%\ by\ \tau}}$',
        'direction': 'higher is better',
        'description': 'Fraction of maximum uplift captured when treating top 10% by predicted CATE.',
        'interpretation': '1.0 = oracle selection. Measures targeting efficiency for top patients.'
    },
    'topk_20_ratio': {
        'name': 'Top-20% Uplift Capture Ratio',
        'formula': r'$\frac{\bar{\tau}_{top20\%\ by\ \hat{\tau}}}{\bar{\tau}_{top20\%\ by\ \tau}}$',
        'direction': 'higher is better',
        'description': 'Fraction of maximum uplift captured when treating top 20% by predicted CATE.',
        'interpretation': '1.0 = oracle selection. Less stringent than top-10%.'
    },
    'topk_30_ratio': {
        'name': 'Top-30% Uplift Capture Ratio',
        'formula': r'$\frac{\bar{\tau}_{top30\%\ by\ \hat{\tau}}}{\bar{\tau}_{top30\%\ by\ \tau}}$',
        'direction': 'higher is better',
        'description': 'Fraction of maximum uplift captured when treating top 30%.',
        'interpretation': 'Less stringent targeting metric.'
    },
    
    # =========================================================================
    # CALIBRATION METRICS
    # =========================================================================
    'calib_slope': {
        'name': 'Calibration Slope',
        'formula': r'$\beta$ in $\tau = \alpha + \beta \hat{\tau}$',
        'direction': 'closer to 1 is better',
        'description': 'Slope of regression of true τ on predicted τ̂. Ideal = 1.0.',
        'interpretation': '<1 = overconfident predictions, >1 = underconfident.'
    },
    'calib_r2': {
        'name': 'Calibration R²',
        'formula': r'$R^2$ of calibration regression',
        'direction': 'higher is better',
        'description': 'Variance explained by predictions. Measures calibration quality.',
        'interpretation': 'Higher R² means predictions track true effects well.'
    },
    'tau_ece': {
        'name': 'CATE ECE (Expected Calibration Error)',
        'formula': r'$\sum_b \frac{n_b}{n} |E[\tau | \hat{\tau} \in b] - E[\hat{\tau} | \hat{\tau} \in b]|$',
        'direction': 'lower is better',
        'description': 'Expected calibration error for CATE. Binned average miscalibration.',
        'interpretation': 'Lower ECE means better calibration across prediction ranges.'
    },
    
    # =========================================================================
    # DECISION-FOCUSED METRICS
    # =========================================================================
    'policy_value': {
        'name': 'Policy Value (Treat if τ̂ > 0)',
        'formula': r'$E[\mu_0 + \pi(\hat{\tau}) \cdot \tau]$ where $\pi(\hat{\tau}) = 1\{\hat{\tau} > 0\}$',
        'direction': 'higher is better',
        'description': 'Expected outcome under threshold-based treatment policy.',
        'interpretation': 'Higher value = better treatment decisions based on predictions.'
    },
    'policy_regret': {
        'name': 'Policy Regret vs Oracle',
        'formula': r'$V(\pi^*) - V(\hat{\pi})$',
        'direction': 'lower is better',
        'description': 'Gap between oracle policy value and estimated policy value.',
        'interpretation': 'Lower regret = closer to optimal treatment decisions.'
    },
    'policy_value_top20': {
        'name': 'Policy Value (Treat Top 20%)',
        'formula': r'$E[\mu_0 + \pi_{top20\%}(\hat{\tau}) \cdot \tau]$',
        'direction': 'higher is better',
        'description': 'Expected outcome when treating top 20% by predicted CATE.',
        'interpretation': 'Budget-constrained policy evaluation.'
    },
    'policy_regret_top20': {
        'name': 'Policy Regret (Top 20% Budget)',
        'formula': r'$V(\pi^*_{top20\%}) - V(\hat{\pi}_{top20\%})$',
        'direction': 'lower is better',
        'description': 'Regret compared to oracle top-20% policy.',
        'interpretation': 'Budget-constrained regret.'
    },
    
    # =========================================================================
    # DIAGNOSTIC METRICS
    # =========================================================================
    'mu0_rmse': {
        'name': 'μ₀ RMSE (Control Outcome)',
        'formula': r'$\sqrt{\frac{1}{n}\sum_i (\hat{\mu}_0(x_i) - \mu_0(x_i))^2}$',
        'direction': 'lower is better',
        'description': 'RMSE of predicted control outcomes. Measures nuisance estimation quality.',
        'interpretation': 'Important diagnostic; poor μ₀ estimation can propagate to CATE errors.'
    }
}


# =============================================================================
# Sweep Configurations
# =============================================================================

# ═══════════════════════════════════════════════════════════════════════════
# METHOD LISTS - Updated to reflect CORRECTED data requirements
# ═══════════════════════════════════════════════════════════════════════════

# Methods for disconnected target (m1=0, placebo-only)
# CRITICAL: Only methods that DON'T require target treated for Stage 3!
DEFAULT_METHODS_OPTION_B = [
    # Our methods that work with placebo-only
    'ProxyOnly',           # Source proxy only
    'AnchorPlugin',        # Placebo anchor, plug-in CATE (no DR)
    'ProposedB_SourceDR',  # TRUE disconnected method: Step B + source-DR
    
    # Transport baselines (don't require target treated)
    # NOTE: For CATE prediction, HongTwoStage≈IPWTransport (both weighted),
    # and AIPWTransport≈OutcomeModelTransport≈IPD_RE (all unweighted).
    # We keep representative methods from each category.
    'IPWTransport',           # Hong: weighted outcome models
    'EntropyBalancing',       # Entropy balancing weights (different from IPW)
    'OutcomeModelTransport',  # Rott: unweighted outcome models (reference)
]

# Methods for connected target (m1>0, has target treated)
# Can use methods that require target treated for Stage 3
DEFAULT_METHODS_OPTION_A = [
    # Baselines
    'TargetOnlyDR',        # Target-only DR (renamed from NoTransfer)
    'ProxyOnly',           # Source proxy only
    
    # Anchor ablations
    'AnchorOnly',          # Placebo anchor + DR (needs target treated!)
    'AnchorPlugin',        # Placebo anchor, plug-in (no DR) - for comparison
    
    # Proposed methods - Residual mode (default)
    'ProposedA',           # Separate proxy, separate correction, residual
    'ProposedA_Together',  # Separate proxy, joint correction δ(X, A)
    'ProposedA_JointProxy', # Joint proxy μ(X, A), separate correction
    'ProposedA_FullyJoint', # Joint proxy AND joint correction
    
    # Proposed methods - Direct mode (fit on Y directly)
    'ProposedA_Direct',           # Separate, direct fitting
    'ProposedA_Together_Direct',  # Joint correction, direct fitting
    'ProposedA_FullyDirect',      # Fully joint + direct
    
    # Proposed methods - No cross-fitting variants
    'ProposedA_NoCrossfit',                # Residual, no cross-fitting
    'ProposedA_Direct_NoCrossfit',         # Direct, no cross-fitting
    'ProposedA_Together_NoCrossfit',       # Joint + no cross-fitting
    'ProposedA_Together_Direct_NoCrossfit', # Joint + direct + no cross-fitting
    
    # Option B variants
    'ProposedB_LinearStepB',  # Step B + target-DR
    'ProposedB_SourceDR',  # Step B + source-DR (for comparison)
    
    # Transport baselines (non-redundant for CATE)
    # NOTE: HongTwoStage≈IPWTransport, AIPWTransport≈OutcomeModelTransport≈IPD_RE
    'IPWTransport',           # Weighted outcome models
    'EntropyBalancing',       # Entropy balancing
    'OutcomeModelTransport',  # Unweighted outcome models
    'DRLearner_PooledWithSite', 'DRLearner_PooledNoSite',
]

# Default for backward compatibility
DEFAULT_METHODS = DEFAULT_METHODS_OPTION_B

SWEEP_CONFIGS = {
    'gold': {
        'benchmark_id': 'gold_sweep',
        'description': 'Target budget 2D grid sweep (m₀ × m₁)',
        'base_scenario': {
            'n_proxy_total': 20000,
            'C_sources': 10,
            'nontransfer_scale': 0.3,
        },
        # 2D grid sweep over m0 and m1
        'sweep_type': 'grid_2d',
        'sweep_param': 'm0',  # Primary for line plots
        'sweep_param_2': 'm1',  # Secondary for grid
        'sweep_values': [100, 500, 1000],  # m0 values
        'm1_values': [0, 100, 500, 1000],  # m1 values (0 = disconnected, >0 = Option A enabled)
        'methods': DEFAULT_METHODS_OPTION_A,  # Include all methods; infeasible ones will be skipped
        
        # Detailed documentation for report
        'motivation': """
**Research Question:** How does the amount of target data (m₀ placebo, m₁ treated) jointly affect estimator performance?

**Why This Matters:**
- In clinical trials, placebo/control arms are expensive and ethically constrained
- The amount of treated data in target varies: from 0 (external control) to balanced RCT
- This 2D sweep shows the full landscape of performance vs data availability
- m₁ = 0 row shows "disconnected target" scenario (only Option B feasible)
- m₁ > 0 rows show "connected target" scenarios (Option A also feasible)

**Expected Behavior:**
- **ProxyOnly** should be insensitive to both m₀ and m₁ (uses only source data)
- **AnchorOnly/ProposedB** should improve with m₀ but be insensitive to m₁
- **ProposedA** should improve with both m₀ AND m₁
- At m₁ = 0, ProposedA is infeasible (NaN)
- At large m₁, ProposedA should outperform ProposedB
""",
        'dgp_description': """
**Data Generating Process:**

The simulation generates data from a multi-site RCT setting where treatment effects
differ between source sites and the target population.

**Fixed Parameters:**
- **Covariates:** $X \\in \\mathbb{R}^{30}$
- **Source sites:** C = 10 sites with 2,000 total observations
- **Non-transfer component:** $\\sigma_{\\text{nontransfer}} = 0.3$ (moderate)

**What Varies (2D Grid):**
- **m₀** (target placebo): {25, 50, 100, 200}
- **m₁** (target treated): {0, 25, 50, 100}
- Total: 16 scenarios per method
"""
    },
    'proxy': {
        'benchmark_id': 'proxy_sweep',
        'description': 'Proxy (source) data budget sweep',
        'base_scenario': {
            'm0': 100,
            'C_sources': 10,
            'nontransfer_scale': 0.3,
        },
        'sweep_param': 'n_proxy_total',
        'sweep_values': [500, 1000, 2000, 5000, 10000],
        
        'motivation': """
**Research Question:** How does the amount of proxy/source data affect estimator performance?

**Why This Matters:**
- Source data (e.g., from external trials, EHR) is often abundant but imperfect
- More source data should improve transfer learning—but only if the transfer model is correct
- This sweep tests the value of additional proxy data vs. diminishing returns

**Expected Behavior:**
- **ProxyOnly** should improve with n_proxy (more data → better proxy estimate)
- **AnchorOnly** should be insensitive to n_proxy (ignores source data)
- **NoTransfer** should be insensitive to n_proxy (ignores source data)
- **Proposed** should improve with n_proxy and dominate as source data grows
- Proposed should show the largest relative gains from additional proxy data
""",
        'dgp_description': """
**Data Generating Process:**

Same multi-site RCT setting as the gold-budget sweep.

**Fixed Parameters:**
- **Target placebo:** m₀ = 100 (moderate)
- **Source sites:** C = 10 sites
- **Covariates:** $X \\in \\mathbb{R}^{10}$
- **Non-transfer component:** $\\sigma_{\\text{nontransfer}} = 0.3$

**What Varies:**
- **n_proxy_total** (total source observations): 500 → 10,000
- Source observations are distributed uniformly across the 10 sites

**Interpretation:**
- At n_proxy = 500: ~50 per site (noisy source estimates)
- At n_proxy = 10,000: ~1,000 per site (precise source estimates)
"""
    },
    'imbalance': {
        'benchmark_id': 'site_imbalance',
        'description': 'Site size imbalance sweep',
        'base_scenario': {
            'm0': 100,
            'n_proxy_total': 2000,
            'nontransfer_scale': 0.3,
        },
        'sweep_param': 'imbalance_ratio',
        'sweep_values': [1.0, 2.0, 5.0, 10.0, 20.0],  # max/min site ratio
        
        'motivation': """
**Research Question:** How does unequal site sizes affect estimator robustness?

**Why This Matters:**
- Real multi-site trials often have vastly different enrollment across sites
- Some sites may contribute 10× more data than others
- Imbalanced data can lead to:
  - Overfitting to large sites
  - Poor estimation for small sites
  - Biased transfer if large sites are unrepresentative

**Expected Behavior:**
- **ProxyOnly** may degrade if large sites dominate and are unrepresentative
- **Proposed** should be more robust due to sparse correction mechanism
- High imbalance (ratio = 20) is a stress test for all methods
- Methods that pool naively may suffer; methods that adapt should be stable
""",
        'dgp_description': """
**Data Generating Process:**

Same multi-site RCT setting, but with unequal site sizes.

**Fixed Parameters:**
- **Target placebo:** m₀ = 100
- **Total source:** n_proxy = 2,000
- **Source sites:** C = 10 sites
- **Non-transfer component:** $\\sigma_{\\text{nontransfer}} = 0.3$

**What Varies:**
- **imbalance_ratio:** Ratio of largest to smallest site size
- Site sizes follow a geometric progression from min_size to max_size

**Example (imbalance_ratio = 10):**
- Smallest site: ~50 observations
- Largest site: ~500 observations
- Other sites: geometrically interpolated

**Stress Test:**
- At ratio = 1.0: All sites equal (~200 each)
- At ratio = 20.0: Extreme imbalance (~30 smallest, ~600 largest)
"""
    },
    
    # =========================================================================
    # FAIR SWEEPS: For OptionB (ProposedB_SourceDR) evaluation
    # =========================================================================
    'gold_fair': {
        'benchmark_id': 'gold_fair_sweep',
        'description': 'Fair OptionB evaluation: m₀ × m₁ grid with controlled DGP',
        'base_scenario': {
            'n_proxy_total': 20000,
            'C_sources': 10,
            'nontransfer_scale': 0.1,  # SNR ≈ 3-4 (fair, not adversarial)
            'use_fair_dgp': True,
            'overlap_lambda': 0.25,    # AUC ≈ 0.7-0.8 (moderate overlap)
            'intercept_drift_scale': 0.5,  # Controlled drift
        },
        'sweep_type': 'grid_2d',
        'sweep_param': 'm0',
        'sweep_param_2': 'm1',
        'sweep_values': [100, 500, 1000],
        'm1_values': [0, 100, 500, 1000],
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How does OptionB (ProposedB_SourceDR) perform when its assumptions are *approximately satisfied*?

**Why This Matters:**
- Previous sweeps used adversarial DGP settings (SNR < 1, AUC = 1.0, high drift)
- This led to "catastrophic failure" for OptionB that was structurally guaranteed
- This sweep uses **fair settings** where OptionB assumptions hold:
  - SNR ≥ 2 (cross-arm transfer signal present)
  - Overlap AUC ~ 0.75 (moderate, not degenerate)
  - Intercept drift controlled (σ_α = 0.5)

**Expected Behavior:**
- **ProposedB_SourceDR** should show moderate performance (not catastrophic failure)
- At m₁ = 0, ProposedB_SourceDR is the only Proposed variant that works
- As m₁ increases, ProposedA should outperform ProposedB variants
- The gap between ProposedA and ProposedB_SourceDR reflects the value of target treated data
""",
        'dgp_description': """
**Fair DGP for OptionB Evaluation:**

Uses `FairSyntheticRCTConfig` with advisor-recommended settings:

**Cross-arm Transfer (A6):**
- `nontransfer_scale_target = 0.1` → SNR ≈ 3-4
- This means: ‖M*β₀‖ >> ‖ν‖ (transfer signal dominates)

**Covariate Overlap:**
- `overlap_lambda = 0.25` → AUC ≈ 0.75
- This means: Source models can generalize to target (not pure extrapolation)

**Intercept Drift:**
- `intercept_drift_scale = 0.5` → σ_α = 0.5
- This means: Arm means are stable across replications

**Outcome Model:**
$$\\mu_{a,c}(x) = \\alpha_{a,c} + x^\\top b_a + x^\\top \\beta_{a,c} + \\text{nonlin}(x)$$

where $\\beta_{1,c} = M^* \\beta_{0,c} + \\nu_c$ with small $\\nu_c$.
"""
    },
    
    'snr_ladder': {
        'benchmark_id': 'snr_ladder_sweep',
        'description': 'Cross-arm validity sweep: varying nontransfer strength (SNR)',
        'base_scenario': {
            'n_proxy_total': 10000,
            'C_sources': 10,
            'm0': 500,
            'm1': 0,  # Disconnected target for OptionB
            'use_fair_dgp': True,
            'overlap_lambda': 0.25,  # Fixed moderate overlap
            'intercept_drift_scale': 0.5,  # Fixed low drift
        },
        'sweep_param': 'nontransfer_scale',
        'sweep_values': [0.0, 0.05, 0.1, 0.2, 0.3, 0.4],  # SNR: ∞ → 6 → 3 → 1.5 → 1 → 0.8
        'methods': DEFAULT_METHODS_OPTION_B,
        
        'motivation': """
**Research Question:** Where does ProposedB_SourceDR break down as cross-arm transfer weakens?

**Why This Matters:**
- OptionB relies on β₁ ≈ M*β₀ (cross-arm structure)
- As nontransfer component ν grows, SNR = ‖M*β₀‖/‖ν‖ decreases
- This sweep identifies the **SNR threshold** below which OptionB fails

**Expected Behavior:**
- SNR ≥ 2: OptionB performs reasonably
- SNR ≈ 1: Boundary - significant degradation
- SNR < 1: Assumption violated - expected failure

**Fairness Note:** Other factors (overlap, drift) are held at fair values.
""",
        'dgp_description': """
**Swept Parameter:** `nontransfer_scale_target`

| Value | Approx SNR | Expected |
|-------|------------|----------|
| 0.00 | ∞ | Best (perfect transfer) |
| 0.05 | ~6 | Good |
| 0.10 | ~3 | Moderate |
| 0.20 | ~1.5 | Degraded |
| 0.30 | ~1 | Boundary |
| 0.40 | ~0.8 | Failed (assumption violated) |

**Fixed Parameters:**
- overlap_lambda = 0.25 (moderate overlap)
- intercept_drift_scale = 0.5 (controlled drift)
"""
    },
    
    'overlap_ladder': {
        'benchmark_id': 'overlap_ladder_sweep',
        'description': 'Overlap stress sweep: varying covariate shift',
        'base_scenario': {
            'n_proxy_total': 10000,
            'C_sources': 10,
            'm0': 500,
            'm1': 0,
            'use_fair_dgp': True,
            'nontransfer_scale': 0.0,  # Perfect transfer
            'intercept_drift_scale': 0.5,  # Fixed low drift
        },
        'sweep_param': 'overlap_lambda',
        'sweep_values': [0.0, 0.25, 0.5, 0.75, 1.0],  # AUC: 0.5 → 0.75 → 0.9 → 0.95 → 1.0
        'methods': DEFAULT_METHODS_OPTION_B,
        
        'motivation': """
**Research Question:** How does OptionB degrade as source/target covariate distributions diverge?

**Why This Matters:**
- OptionB trains on source pseudo-outcomes and predicts on target X
- If source and target X have no overlap, this is pure extrapolation
- This sweep identifies the **overlap threshold** for generalization

**Expected Behavior:**
- AUC < 0.8: Reasonable generalization
- AUC ≈ 0.9: Degraded performance
- AUC > 0.95: Extrapolation failure (assumption violated)
""",
        'dgp_description': """
**Swept Parameter:** `overlap_lambda`

| Value | Approx AUC | Expected |
|-------|------------|----------|
| 0.00 | ~0.55 | Best (same distribution) |
| 0.25 | ~0.75 | Good (realistic) |
| 0.50 | ~0.90 | Degraded |
| 0.75 | ~0.95 | Severe degradation |
| 1.00 | ~1.00 | Failed (no overlap) |

**Fixed Parameters:**
- nontransfer_scale = 0.0 (perfect cross-arm transfer)
- intercept_drift_scale = 0.5 (controlled drift)
"""
    },
    
    'drift_ladder': {
        'benchmark_id': 'drift_ladder_sweep',
        'description': 'Intercept drift stress sweep: varying arm baseline variance',
        'base_scenario': {
            'n_proxy_total': 10000,
            'C_sources': 10,
            'm0': 500,
            'm1': 0,
            'use_fair_dgp': True,
            'nontransfer_scale': 0.0,  # Perfect transfer
            'overlap_lambda': 0.25,  # Fixed moderate overlap
        },
        'sweep_param': 'intercept_drift_scale',
        'sweep_values': [0.0, 0.5, 1.0, 2.0, 4.0],
        'methods': DEFAULT_METHODS_OPTION_B,
        
        'motivation': """
**Research Question:** How robust is OptionB to arm-specific intercept drift?

**Why This Matters:**
- OptionB cannot correct target-specific arm intercepts (no target treated data)
- If α₀,t and α₁,t vary wildly across replications, calibration intercept SD explodes
- This sweep identifies the **drift threshold** for calibration

**Expected Behavior:**
- σ_α ≤ 1: Calibration reasonable
- σ_α = 2: Calibration intercept SD high
- σ_α > 2: Calibration failure
""",
        'dgp_description': """
**Swept Parameter:** `intercept_drift_scale` (σ_α)

Arm intercepts: α_{a,c} ~ N(0, σ_α²)

| Value | Expected |
|-------|----------|
| 0.0 | Best (no drift) |
| 0.5 | Good (controlled) |
| 1.0 | Moderate degradation |
| 2.0 | High calibration variance |
| 4.0 | Severe calibration failure |

**Fixed Parameters:**
- nontransfer_scale = 0.0 (perfect cross-arm transfer)
- overlap_lambda = 0.25 (moderate overlap)
"""
    },
    
    # =========================================================================
    # L1-TCL SWEEP (from arXiv 2305.09126v3)
    # =========================================================================
    'l1tcl': {
        'benchmark_id': 'l1tcl_sweep',
        'description': 'L1-TCL DGP sweep (constant ATE, PS transfer)',
        'base_scenario': {
            'n_proxy_total': 1000,      # Source sample size
            'C_sources': 1,             # Single source domain (L1-TCL structure)
            'p_dim': 2,                 # Only 2 covariates in L1-TCL
            'use_l1tcl_dgp': True,      # Use L1-TCL generator
        },
        'sweep_type': '2d',             # 2D grid: m0 × m1
        'sweep_param': 'm0',
        'sweep_values': [50, 100, 200, 500],
        'm1_values': [0, 50, 100, 200],  # 0 = propensity-only, >0 = use treated
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How do CATE estimators perform on the L1-TCL DGP, which differs fundamentally from our main DGP?

**Why This Matters:**
L1-TCL (arXiv 2305.09126v3) focuses on propensity score transfer with:
1. Constant ATE τ (no heterogeneous treatment effects)
2. Only 2 covariates (X₁, X₂)
3. Single source domain
4. Different propensity score parameters between domains
5. Linear outcome model: Y = τZ + αX₂ + ε

This tests our methods on a fundamentally different DGP where:
- Ranking metrics (tau_corr, Qini) are meaningless (constant τ)
- PEHE reduces to ATE error (since τ(x) = τ for all x)
- The challenge is PS estimation, not outcome model transfer

**DGP Structure (from paper):**
- Treatment: P(Z=1|X₁,X₂) = sigmoid(β₁X₁ + β₂X₂)
- Outcome: Y = τZ + αX₂ + ε
- Target: μ₁=0, μ₂=2, β₁=0.1, β₂=-0.1, τ=-2/30≈-0.067
- Source: μ₁=0, μ₂=1, β₁=0.1, β₂=-0.2 (different PS!)
""",
        
        'expected_findings': """
**Expected Results:**
1. All methods should have similar ranking (meaningless due to constant τ)
2. PEHE ≈ ATE error (no heterogeneity)
3. Methods leveraging source data should improve ATE estimation
4. When m₁=0 (no target treated), only methods using source treated work
5. IPW-based transport methods may perform well on this DGP

**Key Comparisons:**
- ProposedA variants vs transport baselines
- Effect of target sample size (limited data regime)
- Source data value for PS estimation
""",
    },
    
    'l1tcl_source_size': {
        'benchmark_id': 'l1tcl_source_size_sweep',
        'description': 'L1-TCL DGP: Source sample size sweep',
        'base_scenario': {
            'm0': 100,                  # Fixed limited target
            'm1': 0,                    # Propensity-only (no treated in target)
            'C_sources': 1,
            'p_dim': 2,
            'use_l1tcl_dgp': True,
        },
        'sweep_type': '1d',
        'sweep_param': 'n_proxy_total',
        'sweep_values': [100, 250, 500, 1000, 2000, 5000],
        'methods': DEFAULT_METHODS_OPTION_B,  # Disconnected target
        
        'motivation': """
**Research Question:** How does source sample size affect ATE estimation in the limited target data regime?

**Why This Matters:**
L1-TCL emphasizes the value of source data when target is limited (n=100).
With m₁=0 (no target treated), methods must leverage source for treatment effect.

**Expected:** ATE error decreases as source size increases (better PS estimates).
""",
        
        'expected_findings': """
**Expected:**
1. ProposedB_SourceDR benefits from larger source (better transfer)
2. Transport methods (IPWTransport) benefit from better source PS
3. Diminishing returns after source size >> target size
""",
    },
    
    # =========================================================================
    # L1-TCL EXTENDED SWEEPS (matching their full experimental setup)
    # =========================================================================
    
    'l1tcl_dim': {
        'benchmark_id': 'l1tcl_dim_sweep',
        'description': 'L1-TCL Extended: Dimensionality sweep (d)',
        'base_scenario': {
            'm0': 100,
            'm1': 100,
            'n_proxy_total': 5000,      # 10 sites × 500 per site
            'C_sources': 10,            # Multi-site like our main DGP
            'a5_effective_sparsity': 0.15,  # ~15% sparsity in PS diff
            'use_l1tcl_dgp': True,
        },
        'sweep_type': '1d',
        'sweep_param': 'p_dim',
        'sweep_values': [10, 20, 50, 75, 100],  # Paper: d ∈ {10, 20, 50, 75, 100}
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How does covariate dimensionality affect transfer learning performance?

**Why This Matters:**
L1-TCL paper sweeps d ∈ {10, 20, 50, 75, 100}. Higher dimension means:
1. More parameters to estimate in PS model
2. Harder to detect sparse differences
3. Curse of dimensionality in outcome modeling

**Key Difference from Paper:**
We use 10 source sites (like our main DGP) instead of single source.
This tests whether multi-site pooling helps in high dimensions.
""",
        
        'expected_findings': """
**Expected:**
1. Higher d → more variance in all methods
2. Methods with regularization (Lasso) should degrade gracefully
3. Multi-site pooling may help more in high dimensions
""",
    },
    
    'l1tcl_sparsity': {
        'benchmark_id': 'l1tcl_sparsity_sweep',
        'description': 'L1-TCL Extended: PS sparsity sweep (s)',
        'base_scenario': {
            'm0': 100,
            'm1': 100,
            'n_proxy_total': 5000,
            'C_sources': 10,
            'p_dim': 50,                # Fixed medium dimensionality
            'use_l1tcl_dgp': True,
        },
        'sweep_type': '1d',
        'sweep_param': 'a5_effective_sparsity',
        # Paper: s ∈ {1, 3, 5, 7, 10} for d=50 → fractions: 0.02, 0.06, 0.1, 0.14, 0.2
        'sweep_values': [0.02, 0.06, 0.1, 0.14, 0.2],
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How does the sparsity of source-target difference affect transfer?

**Why This Matters:**
L1-TCL assumes Δβ = β_target - β_source is s-sparse.
- Low s: Source and target PS models are similar → transfer helps
- High s: Source and target differ more → transfer may hurt

Paper sweeps s ∈ {1, 3, 5, 7, 10} with d=50.
""",
        
        'expected_findings': """
**Expected:**
1. Lower sparsity (s) → better transfer performance
2. As s increases, methods relying on source PS degrade
3. Target-only methods unaffected by s
4. L1-regularized methods should handle moderate sparsity well
""",
    },
    
    'l1tcl_gold': {
        'benchmark_id': 'l1tcl_gold_sweep',
        'description': 'L1-TCL Extended: Target sample size sweep (gold budget)',
        'base_scenario': {
            'n_proxy_total': 5000,      # 10 sites × 500 per site
            'C_sources': 10,            # Multi-site like our main DGP
            'p_dim': 50,                # Fixed medium dimensionality
            'a5_effective_sparsity': 0.1,  # ~10% sparsity in PS diff
            'use_l1tcl_dgp': True,
        },
        'sweep_type': '1d',
        'sweep_param': 'm0',
        # Paper: n ∈ {100, 200, 500} for target sample size
        # We add smaller sizes to test low-data regime
        'sweep_values': [25, 50, 100, 200, 500],
        # m1 tracks m0 (equal placebo/treated in target)
        'coupled_params': {'m1': 'm0'},
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How does target sample size affect transfer learning performance?

**Why This Matters:**
L1-TCL paper sweeps n (target size) ∈ {100, 200, 500}. Smaller target means:
1. Less anchor data to correct source bias
2. Higher variance in target-only estimators
3. Transfer from source becomes more valuable

**Key Parameters:**
- Target: m₀ = m₁ ∈ {25, 50, 100, 200, 500} (equal placebo/treated)
- Source: 10 sites × 500 = 5000 total (fixed)
- Dimension: d = 50 (fixed)
- PS sparsity: ~10% (fixed)

This tests the fundamental trade-off: when is it better to rely on (potentially biased) 
source data vs. (high-variance) small target data?
""",
        
        'dgp_description': """
**L1-TCL DGP (Extended)**:
- Covariates: X ~ N(0, I_d) with d=50
- Propensity: P(Z=1|X) = sigmoid(X^T β) 
- Source-target difference: Δβ is 10%-sparse
- Outcome: Y = τZ + α^T X + ε with constant τ = -0.067
- 10 source sites with covariate shift between them
""",
        
        'expected_findings': """
**Expected:**
1. Small target (m₀=25): Transfer methods dominate, target-only fails
2. Medium target (m₀=100): Transfer still helps but gap narrows
3. Large target (m₀=500): Target-only methods become competitive
4. ProposedB_SourceDR should shine in low-data regime
5. DR-Learner baselines need sufficient target data
""",
    },
    
    'l1tcl_full': {
        'benchmark_id': 'l1tcl_full_sweep',
        'description': 'L1-TCL Extended: Full d × s grid (paper replication)',
        'base_scenario': {
            'm0': 100,
            'm1': 100,
            'n_proxy_total': 5000,
            'C_sources': 10,
            'use_l1tcl_dgp': True,
        },
        'sweep_type': '2d',
        'sweep_param': 'p_dim',
        'sweep_values': [10, 20, 50, 100],  # d values
        'secondary_param': 'a5_effective_sparsity',
        # s/d ratios: we want s ∈ {1, 3, 5, 7} as fractions
        'secondary_values': [0.05, 0.1, 0.15, 0.2],  # ~s/d
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** Full replication of L1-TCL d × s grid with our multi-site setup.

**Key Grid:**
- Dimension d ∈ {10, 20, 50, 100}
- Sparsity fraction s/d ∈ {0.05, 0.1, 0.15, 0.2}

This allows direct comparison with L1-TCL paper results while using our multi-site structure.
""",
        
        'expected_findings': """
**Expected:** 
Methods should show similar patterns to L1-TCL paper:
1. Transfer helps most when s is small relative to d
2. High d + high s is hardest regime
3. Multi-site pooling may provide additional benefit
""",
    },
    
    'l1tcl_gold_dim': {
        'benchmark_id': 'l1tcl_gold_dim_sweep',
        'description': 'L1-TCL Extended: Gold budget × Dimensionality grid (m0 × d)',
        'base_scenario': {
            'n_proxy_total': 5000,      # 10 sites × 500 per site
            'C_sources': 10,            # Multi-site like our main DGP
            'a5_effective_sparsity': 0.1,  # ~10% sparsity in PS diff (fixed)
            'use_l1tcl_dgp': True,
        },
        'sweep_type': '2d',
        'sweep_param': 'm0',
        'sweep_values': [50, 100, 200, 500],  # Gold budget (m0 = m1)
        'secondary_param': 'p_dim',
        'secondary_values': [10, 20, 50, 100],  # Dimensionality
        # m1 tracks m0 (equal placebo/treated in target)
        'coupled_params': {'m1': 'm0'},
        'methods': DEFAULT_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How do target sample size and dimensionality jointly affect transfer learning?

**Why This Matters:**
This 2D grid explores the interaction between:
1. **Gold budget (m0)**: More target data → less need for transfer
2. **Dimensionality (d)**: Higher d → harder estimation, more benefit from source data

**Key Grid:**
- Target: m₀ = m₁ ∈ {50, 100, 200, 500}
- Dimension: d ∈ {10, 20, 50, 100}
- Total: 4 × 4 = 16 scenarios

**Critical Trade-offs:**
- Small m0 + low d: Transfer dominates (easy problem, limited target data)
- Small m0 + high d: Transfer critical (hard problem, limited target data)
- Large m0 + low d: Target-only competitive (easy problem, ample target data)
- Large m0 + high d: Interesting regime - does transfer still help?
""",
        
        'dgp_description': """
**L1-TCL DGP (Extended)**:
- Covariates: X ~ N(0, I_d) with d ∈ {10, 20, 50, 100}
- Propensity: P(Z=1|X) = sigmoid(X^T β) 
- Source-target difference: Δβ is 10%-sparse
- Outcome: Y = τZ + α^T X + ε with constant τ = -0.067
- 10 source sites with 500 samples each (5000 total)
""",
        
        'expected_findings': """
**Expected:**
1. **Transfer advantage decreases with m0**: Gap between ProposedB and target-only narrows
2. **Transfer advantage increases with d**: High-dim needs more data, source helps more
3. **Interaction effect**: Transfer most valuable in (small m0, high d) quadrant
4. **ProposedB_SourceDR**: Should dominate in low-data/high-dim regime
5. **DR-Learner**: Competitive only when m0 ≥ 200 and d ≤ 20
""",
    },
}


# =============================================================================
# Helper: Create NaN result row
# =============================================================================

def _create_nan_result(benchmark_id, scenario, rep, method_name, feasibility, seed, config):
    """Create a result row with all NaN metrics (for failed/infeasible methods)."""
    return {
        'benchmark_id': benchmark_id,
        'scenario_id': scenario.scenario_id,
        'rep': rep,
        'method': method_name,
        'feasibility': feasibility,
        'seed': seed,
        config['sweep_param']: getattr(scenario, config['sweep_param']),
        'm0': scenario.m0,
        'm1': getattr(scenario, 'm1', None),
        'n_proxy_total': scenario.n_proxy_total,
        'C_sources': scenario.C_sources,
        'nontransfer_scale': scenario.nontransfer_scale,
        # Fair DGP params
        'overlap_lambda': getattr(scenario, 'overlap_lambda', None),
        'intercept_drift_scale': getattr(scenario, 'intercept_drift_scale', None),
        # Point estimation
        'pehe': np.nan, 'ate_hat': np.nan, 'ate_abs_err': np.nan, 'ate_bias': np.nan,
        # Ranking
        'tau_corr': np.nan, 'tau_kendall': np.nan, 'qini_auc': np.nan,
        'topk_10_ratio': np.nan, 'topk_20_ratio': np.nan, 'topk_30_ratio': np.nan,
        'topk_10_captured': np.nan, 'topk_20_captured': np.nan,
        # Calibration
        'calib_slope': np.nan, 'calib_intercept': np.nan, 'calib_r2': np.nan,
        'tau_ece': np.nan, 'tau_mce': np.nan,
        # Decision
        'policy_value': np.nan, 'policy_regret': np.nan,
        'policy_value_top20': np.nan, 'policy_regret_top20': np.nan,
        # Diagnostics
        'stage2_lambda': None, 'stage2_n_selected': None,
        'stepb_M_fro_norm': None, 'stepb_M_effective_rank': None,
        'runtime_sec': 0.0,
    }


# =============================================================================
# Core Sweep Runner - Parallel Worker
# =============================================================================

def _run_single_rep(
    scenario: Scenario,
    rep: int,
    seed: int,
    methods: List[str],
    config: dict,
    benchmark_id: str
) -> List[dict]:
    """
    Worker function for parallel execution.
    Runs all methods for a single (scenario, rep) pair.
    
    Parameters
    ----------
    scenario : Scenario
        The scenario to run
    rep : int
        Replication index
    seed : int
        Random seed for this rep
    methods : list of str
        Methods to run
    config : dict
        Sweep configuration
    benchmark_id : str
        Benchmark identifier
        
    Returns
    -------
    list of dict
        Results for all methods in this rep
    """
    # Import here to avoid pickling issues
    from benchmark_adapters import create_data_generator, create_metric_computer, create_method_factories
    from benchmark_schema import get_method_spec
    
    data_generator = create_data_generator()
    metric_computer = create_metric_computer()
    
    results = []
    
    # Generate data
    try:
        data = data_generator(scenario, seed)
    except Exception as e:
        warnings.warn(f"Data generation failed for scenario {scenario.scenario_id}, rep {rep}: {e}")
        # Return NaN results for all methods
        for method_name in methods:
            results.append(_create_nan_result(
                benchmark_id, scenario, rep, method_name, 'unknown', seed, config
            ))
        return results
    
    # Create method factories (fresh for each rep)
    method_factories = create_method_factories(seed)
    
    for method_name in methods:
        if method_name not in method_factories:
            continue
        
        method_spec = get_method_spec(method_name)
        
        # Check feasibility based on data availability
        has_target_treated = data.get('has_target_treated', False)
        
        # Skip methods that require target treated data when not available
        if method_spec.uses_target_treated and not has_target_treated:
            # Record as infeasible but don't run
            results.append(_create_nan_result(
                benchmark_id, scenario, rep, method_name, 'infeasible_no_target_treated', seed, config
            ))
            continue
        
        feasibility = method_spec.get_feasibility(has_target_treated).value
        
        t0 = time.time()
        try:
            # Create estimator
            estimator = method_factories[method_name]()
            
            # Filter target data based on method's data usage
            # Methods that don't use target treated should only see placebo
            if method_spec.uses_target_treated:
                # Method can use all target data
                X_target_method = data['X_target']
                A_target_method = data['A_target']
                Y_target_method = data['Y_target']
                propensity_method = data.get('propensity_target')
            else:
                # Method should only see target placebo (A=0)
                placebo_mask = (data['A_target'] == 0)
                X_target_method = data['X_target'][placebo_mask]
                A_target_method = data['A_target'][placebo_mask]
                Y_target_method = data['Y_target'][placebo_mask]
                propensity_method = data.get('propensity_target')
                if propensity_method is not None:
                    propensity_method = propensity_method[placebo_mask]
            
            # Fit
            estimator.fit(
                X_source=data['X_source'],
                A_source=data['A_source'],
                Y_source=data['Y_source'],
                c_source=data['c_source'],
                X_target=X_target_method,
                A_target=A_target_method,
                Y_target=Y_target_method,
                propensity_target=propensity_method
            )
            
            # Predict
            tau_pred = estimator.predict(data['X_target_eval'])
            
            # Compute metrics
            metrics = metric_computer(
                tau_true=data['tau_true'],
                tau_pred=tau_pred,
                mu0_true=data['mu0_true'],
                mu1_true=data['mu1_true'],
                ate_true=data['ate_true']
            )
            
            runtime = time.time() - t0
            
            # Get diagnostics
            stage2_lambda = getattr(estimator, 'stage2_lambda_', None)
            stage2_n_selected = getattr(estimator, 'stage2_n_selected_', None)
            
            if hasattr(estimator, 'transfer_diagnostics_'):
                td = estimator.transfer_diagnostics_
                stepb_fro = td.get('M_fro_norm')
                stepb_rank = td.get('M_effective_rank')
            else:
                stepb_fro = None
                stepb_rank = None
            
        except Exception as e:
            warnings.warn(f"Method {method_name} failed: {e}")
            metrics = {'pehe': np.nan, 'ate_abs_err': np.nan}
            runtime = time.time() - t0
            stage2_lambda = None
            stage2_n_selected = None
            stepb_fro = None
            stepb_rank = None
        
        # Create result row
        result = {
            'benchmark_id': benchmark_id,
            'scenario_id': scenario.scenario_id,
            'rep': rep,
            'method': method_name,
            'feasibility': feasibility,
            'seed': seed,
            
            # Scenario params
            config['sweep_param']: getattr(scenario, config['sweep_param']),
            'm0': scenario.m0,
            'm1': getattr(scenario, 'm1', None),
            'n_proxy_total': scenario.n_proxy_total,
            'C_sources': scenario.C_sources,
            'nontransfer_scale': scenario.nontransfer_scale,
            
            # ─────────────────────────────────────────────────────────────────
            # Point Estimation Metrics
            # ─────────────────────────────────────────────────────────────────
            'pehe': metrics.get('pehe', np.nan),
            'ate_hat': metrics.get('ate_hat', np.nan),
            'ate_abs_err': metrics.get('ate_abs_err', np.nan),
            'ate_bias': metrics.get('ate_bias', np.nan),
            
            # ─────────────────────────────────────────────────────────────────
            # Ranking / Heterogeneity Discovery Metrics
            # ─────────────────────────────────────────────────────────────────
            'tau_corr': metrics.get('tau_corr', np.nan),
            'tau_kendall': metrics.get('tau_kendall', np.nan),
            'qini_auc': metrics.get('qini_auc', np.nan),
            'topk_10_ratio': metrics.get('topk_10_ratio', np.nan),
            'topk_20_ratio': metrics.get('topk_20_ratio', np.nan),
            'topk_30_ratio': metrics.get('topk_30_ratio', np.nan),
            'topk_10_captured': metrics.get('topk_10_captured', np.nan),
            'topk_20_captured': metrics.get('topk_20_captured', np.nan),
            
            # ─────────────────────────────────────────────────────────────────
            # Calibration Metrics
            # ─────────────────────────────────────────────────────────────────
            'calib_slope': metrics.get('calib_slope', np.nan),
            'calib_intercept': metrics.get('calib_intercept', np.nan),
            'calib_r2': metrics.get('calib_r2', np.nan),
            'tau_ece': metrics.get('tau_ece', np.nan),
            'tau_mce': metrics.get('tau_mce', np.nan),
            
            # ─────────────────────────────────────────────────────────────────
            # Decision-Focused Metrics
            # ─────────────────────────────────────────────────────────────────
            'policy_value': metrics.get('policy_value', np.nan),
            'policy_regret': metrics.get('policy_regret', np.nan),
            'policy_value_top20': metrics.get('policy_value_top20', np.nan),
            'policy_regret_top20': metrics.get('policy_regret_top20', np.nan),
            
            # ─────────────────────────────────────────────────────────────────
            # Diagnostics
            # ─────────────────────────────────────────────────────────────────
            'stage2_lambda': stage2_lambda,
            'stage2_n_selected': stage2_n_selected,
            'stepb_M_fro_norm': stepb_fro,
            'stepb_M_effective_rank': stepb_rank,
            'runtime_sec': runtime,
        }
        
        results.append(result)
    
    return results


# =============================================================================
# Core Sweep Runner
# =============================================================================

def run_sweep(
    sweep_name: str,
    n_rep: int = 50,
    seed0: int = 42,
    methods: List[str] = None,
    output_dir: str = 'results/sweeps',
    n_jobs: int = 1,
    verbose: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run a single sweep benchmark.
    
    Parameters
    ----------
    sweep_name : str
        One of 'gold', 'proxy', 'imbalance'
    n_rep : int
        Number of Monte Carlo reps per scenario
    seed0 : int
        Master seed
    methods : list of str, optional
        Methods to run. Default: DEFAULT_METHODS
    output_dir : str
        Output directory
    n_jobs : int
        Number of parallel jobs. 
        1 = sequential (default)
        -1 = use all available cores
        > 1 = use that many cores
    verbose : bool
        Print progress
        
    Returns
    -------
    df_rep : pd.DataFrame
        Rep-level results
    df_agg : pd.DataFrame
        Aggregated results
    """
    if sweep_name not in SWEEP_CONFIGS:
        raise ValueError(f"Unknown sweep: {sweep_name}. Available: {list(SWEEP_CONFIGS.keys())}")
    
    config = SWEEP_CONFIGS[sweep_name]
    benchmark_id = config['benchmark_id']
    
    if methods is None:
        # Use sweep-specific methods if defined, otherwise default
        methods = config.get('methods', DEFAULT_METHODS)
    
    # Determine actual number of workers
    if n_jobs == -1:
        actual_n_jobs = multiprocessing.cpu_count()
    elif n_jobs <= 0:
        actual_n_jobs = max(1, multiprocessing.cpu_count() + n_jobs)
    else:
        actual_n_jobs = n_jobs
    
    if verbose:
        print("=" * 70)
        print(f"Sweep: {config['description']}")
        print(f"Benchmark ID: {benchmark_id}")
        sweep_type = config.get('sweep_type', '1d')
        if sweep_type == 'grid_2d':
            print(f"Sweep type: 2D grid (m0 × m1)")
            print(f"m0 values: {config['sweep_values']}")
            print(f"m1 values: {config.get('m1_values', [])}")
            print(f"Total scenarios: {len(config['sweep_values']) * len(config.get('m1_values', [1]))}")
        elif sweep_type == '2d':
            primary = config['sweep_param']
            secondary = config['secondary_param']
            n_primary = len(config['sweep_values'])
            n_secondary = len(config['secondary_values'])
            print(f"Sweep type: 2D grid ({primary} × {secondary})")
            print(f"{primary} values: {config['sweep_values']}")
            print(f"{secondary} values: {config['secondary_values']}")
            print(f"Total scenarios: {n_primary} × {n_secondary} = {n_primary * n_secondary}")
            if config.get('coupled_params'):
                print(f"Coupled params: {config['coupled_params']}")
        else:
            print(f"Sweep param: {config['sweep_param']} ∈ {config['sweep_values']}")
            m1_vals = config.get('m1_values')
            if m1_vals and any(v is not None and v > 0 for v in m1_vals):
                print(f"m1 values: {m1_vals} (Option A enabled)")
            if config.get('coupled_params'):
                print(f"Coupled params: {config['coupled_params']}")
        print(f"Methods: {methods}")
        print(f"Reps: {n_rep}")
        print(f"Parallel jobs: {actual_n_jobs}" + (" (sequential)" if actual_n_jobs == 1 else f" ({multiprocessing.cpu_count()} cores available)"))
        print("=" * 70)
    
    # Generate scenarios
    scenarios = []
    sweep_type = config.get('sweep_type', '1d')
    m1_values = config.get('m1_values', [None] * len(config['sweep_values']))
    coupled_params = config.get('coupled_params', {})
    
    if sweep_type == 'grid_2d':
        # 2D grid: cartesian product of sweep_values (m0) × m1_values
        for m0_val in config['sweep_values']:
            for m1_val in m1_values:
                scenario_params = config['base_scenario'].copy()
                scenario_params['m0'] = m0_val
                scenario_params['m1'] = m1_val if m1_val is not None else 0
                scenario = Scenario(benchmark_id=benchmark_id, **scenario_params)
                scenarios.append(scenario)
    
    elif sweep_type == '2d':
        # 2D grid: cartesian product of sweep_values × secondary_values
        primary_param = config['sweep_param']
        secondary_param = config['secondary_param']
        secondary_values = config['secondary_values']
        
        for primary_val in config['sweep_values']:
            for secondary_val in secondary_values:
                scenario_params = config['base_scenario'].copy()
                scenario_params[primary_param] = primary_val
                scenario_params[secondary_param] = secondary_val
                
                # Handle coupled parameters (e.g., m1 = m0 for gold sweeps)
                for target_param, source_param in coupled_params.items():
                    scenario_params[target_param] = scenario_params.get(source_param, primary_val)
                
                scenario = Scenario(benchmark_id=benchmark_id, **scenario_params)
                scenarios.append(scenario)
    
    else:
        # 1D sweep: m1 co-varies with index
        for i, val in enumerate(config['sweep_values']):
            scenario_params = config['base_scenario'].copy()
            scenario_params[config['sweep_param']] = val
            
            # Set m1 if specified (enables Option A methods when m1 > 0)
            if i < len(m1_values) and m1_values[i] is not None:
                scenario_params['m1'] = m1_values[i]
            
            # Handle coupled parameters (e.g., m1 = m0 for gold sweeps)
            for target_param, source_param in coupled_params.items():
                # target_param tracks source_param's value
                scenario_params[target_param] = scenario_params.get(source_param, val)
            
            scenario = Scenario(benchmark_id=benchmark_id, **scenario_params)
            scenarios.append(scenario)
    
    # Build task list: (scenario, rep, seed) tuples
    tasks = []
    for scenario in scenarios:
        for rep in range(n_rep):
            seed = generate_seed(scenario.scenario_id, rep, seed0)
            tasks.append((scenario, rep, seed))
    
    total_tasks = len(tasks)
    total_runs = total_tasks * len(methods)
    
    if verbose:
        print(f"Total tasks: {total_tasks} (scenario × rep)")
        print(f"Total method evaluations: {total_runs}")
    
    # Execute tasks
    if actual_n_jobs == 1:
        # Sequential execution with progress bar
        all_results = []
        pbar = tqdm(total=total_runs, desc="Running", disable=not verbose)
        
        for scenario, rep, seed in tasks:
            rep_results = _run_single_rep(
                scenario, rep, seed, methods, config, benchmark_id
            )
            all_results.extend(rep_results)
            pbar.update(len(methods))
        
        pbar.close()
    else:
        # Parallel execution using ProcessPoolExecutor
        if verbose:
            print(f"\nStarting parallel execution with {actual_n_jobs} workers...")
        
        all_results = []
        completed = 0
        
        with ProcessPoolExecutor(max_workers=actual_n_jobs) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    _run_single_rep, 
                    scenario, rep, seed, methods, config, benchmark_id
                ): (scenario.scenario_id, rep)
                for scenario, rep, seed in tasks
            }
            
            # Collect results as they complete
            pbar = tqdm(total=total_runs, desc="Running", disable=not verbose)
            
            for future in as_completed(future_to_task):
                task_id = future_to_task[future]
                try:
                    rep_results = future.result()
                    all_results.extend(rep_results)
                    pbar.update(len(methods))
                except Exception as e:
                    warnings.warn(f"Task {task_id} failed: {e}")
                    pbar.update(len(methods))
            
            pbar.close()
    
    # Create DataFrame
    df_rep = pd.DataFrame(all_results)
    
    if verbose:
        print(f"\nCollected {len(df_rep)} results")
    
    # Aggregate
    df_agg = aggregate_results(df_rep, reference_method='ProxyOnly')
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    
    rep_path = os.path.join(output_dir, f'results_rep_{benchmark_id}.csv')
    agg_path = os.path.join(output_dir, f'results_agg_{benchmark_id}.csv')
    
    df_rep.to_csv(rep_path, index=False)
    df_agg.to_csv(agg_path, index=False)
    
    if verbose:
        print(f"✓ Saved: {rep_path}")
        print(f"✓ Saved: {agg_path}")
    
    return df_rep, df_agg


# =============================================================================
# Plot Generation
# =============================================================================

def generate_sweep_plots(
    sweep_name: str,
    df_agg: pd.DataFrame,
    output_dir: str,
    verbose: bool = True
) -> None:
    """Generate plots for a sweep."""
    
    config = SWEEP_CONFIGS[sweep_name]
    benchmark_id = config['benchmark_id']
    sweep_param = config['sweep_param']
    sweep_type = config.get('sweep_type', '1d')
    
    setup_plot_style()
    
    os.makedirs(output_dir, exist_ok=True)
    
    if verbose:
        print(f"\nGenerating plots for {benchmark_id}...")
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    if sweep_type == 'grid_2d':
        # 2D grid sweep: generate heatmaps for each method
        _generate_heatmap_plots(df_agg, config, output_dir, verbose)
    else:
        # 1D sweep: generate line plots
        _generate_line_plots(df_agg, config, output_dir, verbose)
    
    if verbose:
        print(f"✓ Plots saved to {output_dir}")


def _generate_line_plots(df_agg: pd.DataFrame, config: dict, output_dir: str, verbose: bool):
    """Generate line plots for 1D sweeps."""
    import matplotlib.pyplot as plt
    
    benchmark_id = config['benchmark_id']
    sweep_param = config['sweep_param']
    
    # 1. PEHE vs sweep param
    fig = plot_line(
        df_agg, 
        x=sweep_param, 
        y='pehe_mean', 
        hue='method',
        yerr='pehe_sd',
        title=f'PEHE vs {sweep_param} (↓ lower is better)',
        xlabel=sweep_param,
        ylabel='PEHE'
    )
    fig.savefig(os.path.join(output_dir, f'{benchmark_id}_pehe.png'), dpi=150)
    fig.savefig(os.path.join(output_dir, f'{benchmark_id}_pehe.pdf'))
    plt.close(fig)
    
    # 2. ATE error vs sweep param
    if 'ate_abs_err_mean' in df_agg.columns:
        fig = plot_line(
            df_agg,
            x=sweep_param,
            y='ate_abs_err_mean',
            hue='method',
            yerr='ate_abs_err_sd',
            title=f'ATE Error vs {sweep_param} (↓ lower is better)',
            xlabel=sweep_param,
            ylabel='|ATE Error|'
        )
        fig.savefig(os.path.join(output_dir, f'{benchmark_id}_ate.png'), dpi=150)
        plt.close(fig)
    
    # 3. Rank correlation vs sweep param
    if 'tau_corr_mean' in df_agg.columns:
        fig = plot_line(
            df_agg,
            x=sweep_param,
            y='tau_corr_mean',
            hue='method',
            yerr='tau_corr_sd',
            title=f'Spearman ρ vs {sweep_param} (↑ higher is better)',
            xlabel=sweep_param,
            ylabel='Spearman ρ'
        )
        fig.savefig(os.path.join(output_dir, f'{benchmark_id}_corr.png'), dpi=150)
        plt.close(fig)


def _generate_heatmap_plots(df_agg: pd.DataFrame, config: dict, output_dir: str, verbose: bool):
    """Generate heatmap plots for 2D grid sweeps."""
    import matplotlib.pyplot as plt
    import numpy as np
    
    benchmark_id = config['benchmark_id']
    m0_values = sorted(df_agg['m0'].dropna().unique())
    m1_values = sorted(df_agg['m1'].dropna().unique())
    methods = df_agg['method'].unique()
    
    # Metrics to plot: (column, display_name, colormap, lower_is_better)
    # Core metrics + ranking + decision metrics
    metrics = [
        # Core point estimation
        ('pehe_mean', 'PEHE (↓ lower is better)', 'viridis_r', True),
        ('ate_abs_err_mean', 'ATE Error (↓ lower is better)', 'viridis_r', True),
        # Ranking
        ('tau_corr_mean', 'Spearman ρ (↑ higher is better)', 'viridis', False),
        ('qini_auc_mean', 'Qini AUC (↑ higher is better)', 'viridis', False),
        ('topk_20_ratio_mean', 'Top-20% Capture (↑ higher is better)', 'viridis', False),
        # Decision-focused
        ('policy_regret_mean', 'Policy Regret (↓ lower is better)', 'viridis_r', True),
        # Calibration
        ('tau_ece_mean', 'CATE ECE (↓ lower is better)', 'viridis_r', True),
    ]
    
    for metric_col, metric_name, cmap, lower_better in metrics:
        if metric_col not in df_agg.columns:
            continue
        
        n_methods = len(methods)
        n_cols = min(3, n_methods)
        n_rows = (n_methods + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_methods == 1:
            axes = np.array([[axes]])
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        # Find global min/max for consistent color scale
        vmin = df_agg[metric_col].min()
        vmax = df_agg[metric_col].max()
        
        for idx, method in enumerate(methods):
            row, col = idx // n_cols, idx % n_cols
            ax = axes[row, col]
            
            # Create pivot table for heatmap
            method_data = df_agg[df_agg['method'] == method]
            
            # Build matrix
            matrix = np.full((len(m1_values), len(m0_values)), np.nan)
            for _, row_data in method_data.iterrows():
                m0_idx = m0_values.index(row_data['m0'])
                m1_idx = m1_values.index(row_data['m1'])
                matrix[m1_idx, m0_idx] = row_data[metric_col]
            
            # Plot heatmap (origin='lower' so m1=0 is at bottom)
            im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax, origin='lower')
            
            # Set ticks
            ax.set_xticks(range(len(m0_values)))
            ax.set_xticklabels(m0_values)
            ax.set_yticks(range(len(m1_values)))
            ax.set_yticklabels(m1_values)
            
            ax.set_xlabel('m0 (placebo)')
            ax.set_ylabel('m1 (treated)')
            ax.set_title(f'{method}')
            
            # Add value annotations
            for i in range(len(m1_values)):
                for j in range(len(m0_values)):
                    val = matrix[i, j]
                    if not np.isnan(val):
                        text_color = 'white' if (val - vmin) / (vmax - vmin + 1e-10) > 0.5 else 'black'
                        ax.text(j, i, f'{val:.2f}', ha='center', va='center', 
                               color=text_color, fontsize=8)
                    else:
                        ax.text(j, i, 'N/A', ha='center', va='center', 
                               color='gray', fontsize=8)
        
        # Hide empty subplots
        for idx in range(n_methods, n_rows * n_cols):
            row, col = idx // n_cols, idx % n_cols
            axes[row, col].axis('off')
        
        # Add colorbar
        fig.subplots_adjust(right=0.85)
        cbar_ax = fig.add_axes([0.88, 0.15, 0.03, 0.7])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label(metric_name)
        
        fig.suptitle(f'{metric_name} vs Target Budget (m0 x m1)', fontsize=14, y=1.02)
        
        # Save
        metric_short = metric_col.replace('_mean', '')
        fig.savefig(os.path.join(output_dir, f'{benchmark_id}_{metric_short}.png'), 
                   dpi=150, bbox_inches='tight')
        fig.savefig(os.path.join(output_dir, f'{benchmark_id}_{metric_short}.pdf'),
                   bbox_inches='tight')
        plt.close(fig)
        
        if verbose:
            print(f"  ✓ {metric_name} heatmap saved")


# =============================================================================
# Report Generation
# =============================================================================

def generate_sweep_report(
    sweep_name: str,
    df_rep: pd.DataFrame,
    df_agg: pd.DataFrame,
    output_dir: str
) -> str:
    """Generate comprehensive markdown report for a sweep."""
    
    config = SWEEP_CONFIGS[sweep_name]
    benchmark_id = config['benchmark_id']
    sweep_param = config['sweep_param']
    
    report_path = os.path.join(output_dir, f'{benchmark_id}_report.md')
    
    with open(report_path, 'w') as f:
        # Title and metadata
        f.write(f"# {config['description']}\n\n")
        f.write(f"**Benchmark ID:** `{benchmark_id}`\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        # =====================================================================
        # 1. MOTIVATION: Why this sweep?
        # =====================================================================
        f.write("---\n\n")
        f.write("## 1. Motivation\n\n")
        if 'motivation' in config:
            f.write(config['motivation'].strip() + "\n\n")
        else:
            f.write("*No motivation provided.*\n\n")
        
        # =====================================================================
        # 2. SIMULATION SETUP: DGP details
        # =====================================================================
        f.write("---\n\n")
        f.write("## 2. Simulation Setup\n\n")
        if 'dgp_description' in config:
            f.write(config['dgp_description'].strip() + "\n\n")
        
        # Add concrete parameter table
        f.write("### Parameter Summary\n\n")
        f.write("| Parameter | Value | Description |\n")
        f.write("|-----------|-------|-------------|\n")
        f.write(f"| **Sweep param** | `{sweep_param}` | {config['sweep_values']} |\n")
        for param, val in config['base_scenario'].items():
            desc = _get_param_description(param)
            f.write(f"| {param} | {val} | {desc} |\n")
        f.write("\n")
        
        # =====================================================================
        # 3. METRIC DEFINITIONS: What we measure and interpretation
        # =====================================================================
        f.write("---\n\n")
        f.write("## 3. Metrics & Interpretation\n\n")
        f.write("| Metric | Direction | Description |\n")
        f.write("|--------|-----------|-------------|\n")
        for metric_key, metric_info in METRIC_DEFINITIONS.items():
            direction_symbol = "↓" if "lower" in metric_info['direction'] else "↑"
            f.write(f"| **{metric_info['name']}** | {direction_symbol} {metric_info['direction']} | {metric_info['description'][:80]}... |\n")
        f.write("\n")
        
        # Detailed metric explanations
        f.write("### Detailed Metric Definitions\n\n")
        for metric_key, metric_info in METRIC_DEFINITIONS.items():
            f.write(f"**{metric_info['name']}**\n\n")
            f.write(f"- Formula: {metric_info['formula']}\n")
            f.write(f"- Direction: **{metric_info['direction']}**\n")
            f.write(f"- {metric_info['interpretation']}\n\n")
        
        # =====================================================================
        # 4. METHODS COMPARED
        # =====================================================================
        f.write("---\n\n")
        f.write("## 4. Methods Compared\n\n")
        methods_in_sweep = df_rep['method'].unique().tolist()
        f.write("| Method | Uses Target Placebo | Uses Source Data | Description |\n")
        f.write("|--------|---------------------|------------------|-------------|\n")
        for method in methods_in_sweep:
            desc = _get_method_description(method)
            uses_target = "✓" if method in ['AnchorOnly', 'ProposedB_LinearStepB', 'ProposedA'] else "✗"
            uses_source = "✓" if method in ['ProxyOnly', 'ProposedB_LinearStepB', 'ProposedA'] else "✗"
            f.write(f"| **{method}** | {uses_target} | {uses_source} | {desc} |\n")
        f.write("\n")
        
        # =====================================================================
        # 5. EXPERIMENT SUMMARY
        # =====================================================================
        f.write("---\n\n")
        f.write("## 5. Experiment Summary\n\n")
        f.write(f"- **Sweep parameter:** `{sweep_param}` ∈ {config['sweep_values']}\n")
        f.write(f"- **Monte Carlo replicates:** {df_rep['rep'].max() + 1} per scenario\n")
        f.write(f"- **Methods evaluated:** {len(methods_in_sweep)}\n")
        f.write(f"- **Total runs:** {len(df_rep)}\n\n")
        
        # =====================================================================
        # 6. RESULTS: Best methods summary
        # =====================================================================
        f.write("---\n\n")
        f.write("## 6. Results\n\n")
        
        f.write("### Best Methods (averaged across sweep)\n\n")
        
        # Metrics to report and their direction
        metrics_info = [
            # Point estimation
            ('pehe', 'lower', 'PEHE'),
            ('ate_abs_err', 'lower', 'ATE Error'),
            # Ranking
            ('tau_corr', 'higher', 'Spearman ρ'),
            ('tau_kendall', 'higher', 'Kendall τ'),
            ('qini_auc', 'higher', 'Qini AUC'),
            ('topk_10_ratio', 'higher', 'Top-10% Ratio'),
            ('topk_20_ratio', 'higher', 'Top-20% Ratio'),
            # Calibration
            ('calib_r2', 'higher', 'Calibration R²'),
            ('tau_ece', 'lower', 'CATE ECE'),
            # Decision
            ('policy_value', 'higher', 'Policy Value'),
            ('policy_regret', 'lower', 'Policy Regret'),
        ]
        
        # Build lower_is_better dict from metrics_info
        lower_is_better = {m: (d == 'lower') for m, d, _ in metrics_info}
        best = find_best_methods(df_agg, metrics=[m for m, _, _ in metrics_info], lower_is_better=lower_is_better)
        f.write("| Metric | Best Method | Value | Direction |\n")
        f.write("|--------|-------------|-------|----------|\n")
        for metric, direction, display_name in metrics_info:
            if metric in best:
                info = best[metric]
                dir_str = "↓ lower" if direction == 'lower' else "↑ higher"
                f.write(f"| {display_name} | **{info['method']}** | {info['value']:.4f} | {dir_str} |\n")
        f.write("\n")
        
        # =====================================================================
        # 7. DETAILED RESULTS TABLES
        # =====================================================================
        
        # Check if this is a 2D grid sweep (has m1 column with varying values)
        is_2d_sweep = 'm1' in df_agg.columns and df_agg['m1'].nunique() > 1
        
        # Helper function for formatting metric values
        def fmt_metric(row, col, decimals=3):
            mean_col = f'{col}_mean'
            sd_col = f'{col}_sd'
            if mean_col not in row or np.isnan(row.get(mean_col, np.nan)):
                return "N/A"
            mean_val = row[mean_col]
            sd_val = row.get(sd_col, 0)
            if np.isnan(sd_val):
                return f"{mean_val:.{decimals}f}"
            return f"{mean_val:.{decimals}f} ± {sd_val:.{decimals}f}"
        
        # Sort data
        if is_2d_sweep:
            df_sorted = df_agg.sort_values(['m0', 'm1', 'method'])
            index_cols = ['m0', 'm1']
        else:
            df_sorted = df_agg.sort_values([sweep_param, 'method'])
            index_cols = [sweep_param]
        
        # ----- Table 1: Core Metrics -----
        f.write("### Core Metrics\n\n")
        
        header = " | ".join(index_cols + ['Method', 'PEHE (↓)', 'ATE Err (↓)', 'Spearman (↑)', 'Qini (↑)'])
        f.write(f"| {header} |\n")
        f.write("|" + "|".join(["---"] * (len(index_cols) + 4)) + "|\n")
        
        for _, row in df_sorted.iterrows():
            idx_vals = [str(int(row[c])) if c in ['m0', 'm1'] and not np.isnan(row.get(c, np.nan)) else str(row.get(c, 'N/A')) for c in index_cols]
            row_data = idx_vals + [
                row['method'],
                fmt_metric(row, 'pehe'),
                fmt_metric(row, 'ate_abs_err'),
                fmt_metric(row, 'tau_corr'),
                fmt_metric(row, 'qini_auc'),
            ]
            f.write("| " + " | ".join(row_data) + " |\n")
        
        f.write("\n")
        
        # ----- Table 2: Targeting Metrics -----
        f.write("### Targeting / Ranking Metrics\n\n")
        
        header = " | ".join(index_cols + ['Method', 'Top-10% (↑)', 'Top-20% (↑)', 'Kendall (↑)'])
        f.write(f"| {header} |\n")
        f.write("|" + "|".join(["---"] * (len(index_cols) + 4)) + "|\n")
        
        for _, row in df_sorted.iterrows():
            idx_vals = [str(int(row[c])) if c in ['m0', 'm1'] and not np.isnan(row.get(c, np.nan)) else str(row.get(c, 'N/A')) for c in index_cols]
            row_data = idx_vals + [
                row['method'],
                fmt_metric(row, 'topk_10_ratio'),
                fmt_metric(row, 'topk_20_ratio'),
                fmt_metric(row, 'tau_kendall'),
            ]
            f.write("| " + " | ".join(row_data) + " |\n")
        
        f.write("\n")
        
        # ----- Table 3: ATE & Bias Metrics -----
        f.write("### ATE Estimation\n\n")
        
        header = " | ".join(index_cols + ['Method', 'ATE Est', 'ATE Err (↓)', 'ATE Bias'])
        f.write(f"| {header} |\n")
        f.write("|" + "|".join(["---"] * (len(index_cols) + 4)) + "|\n")
        
        for _, row in df_sorted.iterrows():
            idx_vals = [str(int(row[c])) if c in ['m0', 'm1'] and not np.isnan(row.get(c, np.nan)) else str(row.get(c, 'N/A')) for c in index_cols]
            row_data = idx_vals + [
                row['method'],
                fmt_metric(row, 'ate_hat'),
                fmt_metric(row, 'ate_abs_err'),
                fmt_metric(row, 'ate_bias'),
            ]
            f.write("| " + " | ".join(row_data) + " |\n")
        
        f.write("\n")
        
        # ----- Table 4: Policy / Decision Metrics -----
        f.write("### Policy / Decision Metrics\n\n")
        
        header = " | ".join(index_cols + ['Method', 'Policy Value (↑)', 'Regret (↓)', 'Value Top20 (↑)', 'Regret Top20 (↓)'])
        f.write(f"| {header} |\n")
        f.write("|" + "|".join(["---"] * (len(index_cols) + 5)) + "|\n")
        
        for _, row in df_sorted.iterrows():
            idx_vals = [str(int(row[c])) if c in ['m0', 'm1'] and not np.isnan(row.get(c, np.nan)) else str(row.get(c, 'N/A')) for c in index_cols]
            row_data = idx_vals + [
                row['method'],
                fmt_metric(row, 'policy_value'),
                fmt_metric(row, 'policy_regret'),
                fmt_metric(row, 'policy_value_top20'),
                fmt_metric(row, 'policy_regret_top20'),
            ]
            f.write("| " + " | ".join(row_data) + " |\n")
        
        f.write("\n")
        
        # ----- Table 5: Calibration Metrics -----
        f.write("### Calibration Metrics\n\n")
        
        header = " | ".join(index_cols + ['Method', 'Slope (→1)', 'Intercept (→0)', 'R² (↑)', 'ECE (↓)', 'MCE (↓)'])
        f.write(f"| {header} |\n")
        f.write("|" + "|".join(["---"] * (len(index_cols) + 6)) + "|\n")
        
        for _, row in df_sorted.iterrows():
            idx_vals = [str(int(row[c])) if c in ['m0', 'm1'] and not np.isnan(row.get(c, np.nan)) else str(row.get(c, 'N/A')) for c in index_cols]
            row_data = idx_vals + [
                row['method'],
                fmt_metric(row, 'calib_slope'),
                fmt_metric(row, 'calib_intercept'),
                fmt_metric(row, 'calib_r2'),
                fmt_metric(row, 'tau_ece'),
                fmt_metric(row, 'tau_mce'),
            ]
            f.write("| " + " | ".join(row_data) + " |\n")
        
        f.write("\n")
        
        # ----- Table 6: Extended Targeting Metrics -----
        f.write("### Extended Targeting Metrics\n\n")
        
        header = " | ".join(index_cols + ['Method', 'Top-10% Captured', 'Top-20% Captured', 'Top-30% Ratio (↑)'])
        f.write(f"| {header} |\n")
        f.write("|" + "|".join(["---"] * (len(index_cols) + 4)) + "|\n")
        
        for _, row in df_sorted.iterrows():
            idx_vals = [str(int(row[c])) if c in ['m0', 'm1'] and not np.isnan(row.get(c, np.nan)) else str(row.get(c, 'N/A')) for c in index_cols]
            row_data = idx_vals + [
                row['method'],
                fmt_metric(row, 'topk_10_captured'),
                fmt_metric(row, 'topk_20_captured'),
                fmt_metric(row, 'topk_30_ratio'),
            ]
            f.write("| " + " | ".join(row_data) + " |\n")
        
        f.write("\n")
        
        # =====================================================================
        # 8. PLOTS
        # =====================================================================
        f.write("---\n\n")
        f.write("## 7. Plots\n\n")
        
        f.write("### PEHE vs Sweep Parameter (↓ lower is better)\n\n")
        f.write(f"![PEHE]({benchmark_id}_pehe.png)\n\n")
        
        f.write("### ATE Error vs Sweep Parameter (↓ lower is better)\n\n")
        f.write(f"![ATE Error]({benchmark_id}_ate.png)\n\n")
        
        f.write("### Spearman Correlation vs Sweep Parameter (↑ higher is better)\n\n")
        f.write(f"![Correlation]({benchmark_id}_corr.png)\n\n")
        
        # =====================================================================
        # 9. KEY FINDINGS (auto-generated)
        # =====================================================================
        f.write("---\n\n")
        f.write("## 8. Key Findings\n\n")
        
        # Auto-generate some findings based on results
        findings = _generate_findings(sweep_name, df_agg, config)
        for i, finding in enumerate(findings, 1):
            f.write(f"{i}. {finding}\n")
        f.write("\n")
        
        # =====================================================================
        # 10. APPENDIX: Raw config
        # =====================================================================
        f.write("---\n\n")
        f.write("## Appendix: Configuration\n\n")
        f.write("```python\n")
        f.write(f"sweep_param = '{sweep_param}'\n")
        f.write(f"sweep_values = {config['sweep_values']}\n")
        f.write(f"base_scenario = {config['base_scenario']}\n")
        f.write("```\n\n")
    
    return report_path


def _get_param_description(param: str) -> str:
    """Get human-readable description for a DGP parameter."""
    descriptions = {
        'm0': 'Target placebo sample size',
        'm1': 'Target treated sample size (if any)',
        'n_proxy_total': 'Total source/proxy observations',
        'C_sources': 'Number of source sites',
        'nontransfer_scale': 'Scale of non-transferable component (σ)',
        'imbalance_ratio': 'Max/min site size ratio',
        'shift_strength': 'Covariate shift magnitude',
        'overlap_strength': 'Support overlap parameter',
        'a5_nonlin_strength': 'Nonlinearity strength in correction',
        'a6_rank_true': 'True rank of transfer operator',
        'a6_rank_fit': 'Fitted rank of transfer operator',
    }
    return descriptions.get(param, 'See documentation')


def _get_method_description(method: str) -> str:
    """Get human-readable description for a method."""
    descriptions = {
        'NoTransfer': 'Uses only target placebo, no transfer',
        'ProxyOnly': 'Uses only source data, ignores target',
        'AnchorOnly': 'Uses only target placebo data',
        # Residual mode variants
        'ProposedA': 'Proposed: separate proxy + separate correction (residual)',
        'ProposedA_Together': 'Proposed: separate proxy + joint correction (residual)',
        'ProposedA_JointProxy': 'Proposed: joint proxy + separate correction (residual)',
        'ProposedA_FullyJoint': 'Proposed: joint proxy + joint correction (residual)',
        # Direct mode variants
        'ProposedA_Direct': 'Proposed: separate + direct fitting',
        'ProposedA_Together_Direct': 'Proposed: joint correction + direct fitting',
        'ProposedA_JointProxy_Direct': 'Proposed: joint proxy + direct fitting',
        'ProposedA_FullyDirect': 'Proposed: fully joint + direct fitting',
        # No cross-fitting variants
        'ProposedA_NoCrossfit': 'Proposed: residual, no cross-fitting',
        'ProposedA_Direct_NoCrossfit': 'Proposed: direct, no cross-fitting',
        'ProposedA_Together_NoCrossfit': 'Proposed: joint + no cross-fitting',
        'ProposedA_Together_Direct_NoCrossfit': 'Proposed: joint + direct + no cross-fitting',
        # Option B
        'ProposedB_LinearStepB': 'Proposed (Option B): placebo-anchored with linear Step B',
        'ProposedB_SourceDR': 'Proposed (Option B): source-DR for placebo-only target',
        'ProposedB_KernelStepB': 'Proposed (Option B): placebo-anchored with kernel Step B',
    }
    return descriptions.get(method, 'See documentation')


def _generate_findings(sweep_name: str, df_agg: pd.DataFrame, config: dict) -> List[str]:
    """Auto-generate key findings from results."""
    findings = []
    sweep_param = config['sweep_param']
    sweep_values = config['sweep_values']
    
    # Check if it's an L1-TCL DGP (constant tau means ranking metrics are NaN)
    is_l1tcl = 'l1tcl' in sweep_name.lower() or config.get('base_scenario', {}).get('use_l1tcl_dgp', False)
    
    # Find best method overall by PEHE (or ATE error if PEHE is all NaN)
    if 'pehe_mean' in df_agg.columns and not df_agg['pehe_mean'].isna().all():
        best_pehe_idx = df_agg['pehe_mean'].idxmin()
        if pd.notna(best_pehe_idx):
            best_method = df_agg.loc[best_pehe_idx, 'method']
            best_pehe = df_agg.loc[best_pehe_idx, 'pehe_mean']
            findings.append(f"**Best overall PEHE:** {best_method} achieves lowest average PEHE ({best_pehe:.3f})")
    
    # Also report ATE error winner
    if 'ate_abs_err_mean' in df_agg.columns and not df_agg['ate_abs_err_mean'].isna().all():
        best_ate_idx = df_agg['ate_abs_err_mean'].idxmin()
        if pd.notna(best_ate_idx):
            best_ate_method = df_agg.loc[best_ate_idx, 'method']
            best_ate = df_agg.loc[best_ate_idx, 'ate_abs_err_mean']
            findings.append(f"**Best overall ATE Error:** {best_ate_method} achieves lowest average ATE error ({best_ate:.4f})")
    
    # Check if Proposed beats ProxyOnly
    proposed_pehe = df_agg[df_agg['method'].str.contains('Proposed', na=False)]['pehe_mean'].mean()
    proxy_pehe = df_agg[df_agg['method'] == 'ProxyOnly']['pehe_mean'].mean()
    if not np.isnan(proposed_pehe) and not np.isnan(proxy_pehe):
        if proposed_pehe < proxy_pehe:
            pct_improvement = (proxy_pehe - proposed_pehe) / proxy_pehe * 100
            findings.append(f"**Proposed vs ProxyOnly:** Proposed reduces PEHE by {pct_improvement:.1f}% on average")
        else:
            findings.append(f"**Proposed vs ProxyOnly:** ProxyOnly outperforms Proposed in this setting")
    
    # Policy regret winner
    if 'policy_regret_mean' in df_agg.columns and not df_agg['policy_regret_mean'].isna().all():
        best_regret_idx = df_agg['policy_regret_mean'].idxmin()
        if pd.notna(best_regret_idx):
            best_regret_method = df_agg.loc[best_regret_idx, 'method']
            best_regret = df_agg.loc[best_regret_idx, 'policy_regret_mean']
            findings.append(f"**Lowest policy regret:** {best_regret_method} ({best_regret:.4f})")
    
    # Check trend with sweep parameter for top method
    if 'ate_abs_err_mean' in df_agg.columns:
        top_method = df_agg.groupby('method')['ate_abs_err_mean'].mean().idxmin()
        if pd.notna(top_method):
            method_data = df_agg[df_agg['method'] == top_method].sort_values(sweep_param)
            if len(method_data) >= 2:
                first_err = method_data.iloc[0]['ate_abs_err_mean']
                last_err = method_data.iloc[-1]['ate_abs_err_mean']
                if not np.isnan(first_err) and not np.isnan(last_err):
                    if last_err > first_err * 1.5:  # >50% degradation
                        findings.append(f"**Scaling:** {top_method} ATE error increases with higher {sweep_param}")
                    elif last_err < first_err * 0.67:  # >33% improvement
                        findings.append(f"**Scaling:** {top_method} ATE error decreases with higher {sweep_param}")
                    else:
                        findings.append(f"**Scaling:** {top_method} maintains stable performance across {sweep_param} values")
    
    # Check ranking correlation (skip for L1-TCL)
    if not is_l1tcl and 'tau_corr_mean' in df_agg.columns and not df_agg['tau_corr_mean'].isna().all():
        best_corr_idx = df_agg['tau_corr_mean'].idxmax()
        if pd.notna(best_corr_idx):
            best_corr_method = df_agg.loc[best_corr_idx, 'method']
            best_corr = df_agg.loc[best_corr_idx, 'tau_corr_mean']
            findings.append(f"**Best ranking:** {best_corr_method} achieves highest Spearman correlation ({best_corr:.3f})")
    elif is_l1tcl:
        findings.append("**Note:** Ranking metrics (Spearman, Qini) are NaN for L1-TCL DGP due to constant τ")
    
    if not findings:
        findings.append("*No significant patterns detected. Review plots for visual inspection.*")
    
    return findings


# =============================================================================
# Run All Sweeps
# =============================================================================

def _run_sweep_and_report(
    sweep_name: str,
    n_rep: int,
    seed0: int,
    methods: Optional[List[str]],
    output_dir: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Helper function for parallel sweep execution.
    Runs a sweep and generates plots/report.
    """
    df_rep, df_agg = run_sweep(
        sweep_name, n_rep=n_rep, seed0=seed0,
        methods=methods, output_dir=output_dir,
        n_jobs=1,  # Sequential within sweep to avoid nested parallelism
        verbose=False  # Reduce output noise
    )
    generate_sweep_plots(sweep_name, df_agg, output_dir, verbose=False)
    generate_sweep_report(sweep_name, df_rep, df_agg, output_dir)
    return df_rep, df_agg


def run_all_sweeps(
    n_rep: int = 20,
    seed0: int = 42,
    methods: List[str] = None,
    output_dir: str = 'results/sweeps',
    n_jobs: int = 1,
    parallel_sweeps: bool = False,
    verbose: bool = True
) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Run all core sweeps.
    
    Parameters
    ----------
    n_rep : int
        Number of Monte Carlo reps per scenario
    seed0 : int
        Master seed
    methods : list of str, optional
        Methods to run
    output_dir : str
        Output directory
    n_jobs : int
        Number of parallel jobs for each sweep.
        1 = sequential, -1 = all cores
    parallel_sweeps : bool
        If True, run the three sweeps in parallel (each with n_jobs=1 internally
        to avoid nested parallelism). If False, run sweeps sequentially with
        n_jobs parallelism within each sweep.
    verbose : bool
        Print progress
        
    Returns
    -------
    dict
        sweep_name -> (df_rep, df_agg)
    """
    sweep_names = ['gold', 'proxy', 'imbalance']
    
    if parallel_sweeps:
        # Run sweeps in parallel (each sweep runs sequentially internally)
        # This is useful when you have few cores and want to maximize utilization
        if verbose:
            print(f"\n{'='*70}")
            print("Running all sweeps in parallel...")
            print('='*70)
        
        # Determine number of sweep workers (max 3, one per sweep)
        n_sweep_workers = min(3, multiprocessing.cpu_count())
        
        results = {}
        
        with ProcessPoolExecutor(max_workers=n_sweep_workers) as executor:
            future_to_sweep = {
                executor.submit(
                    _run_sweep_and_report,
                    sweep_name, n_rep, seed0, methods, output_dir
                ): sweep_name
                for sweep_name in sweep_names
            }
            
            for future in as_completed(future_to_sweep):
                sweep_name = future_to_sweep[future]
                try:
                    df_rep, df_agg = future.result()
                    results[sweep_name] = (df_rep, df_agg)
                    if verbose:
                        print(f"✓ Completed {sweep_name} sweep")
                except Exception as e:
                    warnings.warn(f"Sweep {sweep_name} failed: {e}")
                    results[sweep_name] = (pd.DataFrame(), pd.DataFrame())
    else:
        # Run sweeps sequentially, with parallelism within each sweep
        results = {}
        
        for sweep_name in sweep_names:
            if verbose:
                print(f"\n{'='*70}")
                print(f"Running {sweep_name} sweep...")
                print('='*70)
            
            df_rep, df_agg = run_sweep(
                sweep_name, n_rep=n_rep, seed0=seed0, 
                methods=methods, output_dir=output_dir,
                n_jobs=n_jobs, verbose=verbose
            )
            
            generate_sweep_plots(sweep_name, df_agg, output_dir, verbose=verbose)
            generate_sweep_report(sweep_name, df_rep, df_agg, output_dir)
            
            results[sweep_name] = (df_rep, df_agg)
    
    if verbose:
        print(f"\n{'='*70}")
        print("All sweeps complete!")
        print(f"Results saved to: {output_dir}")
        print('='*70)
    
    return results


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Run core benchmark sweeps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all sweeps sequentially (default)
  python experiments/core_sweeps.py --sweep all --n_rep 20

  # Run all sweeps with parallel execution within each sweep (recommended)
  python experiments/core_sweeps.py --sweep all --n_rep 50 --n_jobs -1

  # Run a single sweep with 8 parallel workers
  python experiments/core_sweeps.py --sweep gold --n_rep 100 --n_jobs 8

  # Run all sweeps in parallel (sweeps run concurrently, not within)
  python experiments/core_sweeps.py --sweep all --n_rep 20 --parallel_sweeps
        """
    )
    parser.add_argument('--sweep', type=str, default='all',
                       choices=['gold', 'gold_option_a', 'proxy', 'imbalance', 
                                'gold_fair', 'snr_ladder', 'overlap_ladder', 'drift_ladder',
                                'l1tcl', 'l1tcl_source_size', 'l1tcl_dim', 'l1tcl_sparsity', 
                                'l1tcl_gold', 'l1tcl_gold_dim', 'l1tcl_full',
                                'all', 'all_fair'],
                       help='Sweep to run (default: all). Fair sweeps: gold_fair, snr_ladder, overlap_ladder, drift_ladder. '
                            'L1-TCL sweeps: l1tcl, l1tcl_source_size, l1tcl_dim, l1tcl_sparsity, l1tcl_gold, l1tcl_gold_dim, l1tcl_full')
    parser.add_argument('--n_rep', type=int, default=20,
                       help='Number of MC replicates (default: 20)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Master seed (default: 42)')
    parser.add_argument('--output', type=str, default='results/sweeps',
                       help='Output directory (default: results/sweeps)')
    parser.add_argument('--methods', type=str, nargs='+', default=None,
                       help='Methods to run (default: all standard methods)')
    parser.add_argument('--n_jobs', type=int, default=1,
                       help='Number of parallel jobs. 1=sequential (default), '
                            '-1=all cores, N=use N cores')
    parser.add_argument('--parallel_sweeps', action='store_true',
                       help='Run sweeps in parallel (instead of parallel within sweeps). '
                            'Useful when running --sweep all with limited cores.')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')
    
    args = parser.parse_args()
    
    # Report configuration
    if not args.quiet:
        print("\n" + "="*70)
        print("Core Sweeps Benchmark Runner")
        print("="*70)
        print(f"Sweep: {args.sweep}")
        print(f"Reps: {args.n_rep}")
        print(f"Seed: {args.seed}")
        print(f"Output: {args.output}")
        print(f"Methods: {args.methods or 'default'}")
        print(f"Parallel jobs: {args.n_jobs} {'(all cores)' if args.n_jobs == -1 else ''}")
        if args.sweep == 'all':
            print(f"Parallel sweeps: {args.parallel_sweeps}")
        print("="*70 + "\n")
    
    start_time = time.time()
    
    if args.sweep == 'all':
        run_all_sweeps(
            n_rep=args.n_rep,
            seed0=args.seed,
            methods=args.methods,
            output_dir=args.output,
            n_jobs=args.n_jobs,
            parallel_sweeps=args.parallel_sweeps,
            verbose=not args.quiet
        )
    elif args.sweep == 'all_fair':
        # Run all fair sweeps
        fair_sweeps = ['gold_fair', 'snr_ladder', 'overlap_ladder', 'drift_ladder']
        for sweep_name in fair_sweeps:
            if not args.quiet:
                print(f"\n{'='*70}")
                print(f"Running fair sweep: {sweep_name}")
                print('='*70)
            df_rep, df_agg = run_sweep(
                sweep_name=sweep_name,
                n_rep=args.n_rep,
                seed0=args.seed,
                methods=args.methods,
                output_dir=args.output,
                n_jobs=args.n_jobs,
                verbose=not args.quiet
            )
            generate_plots(sweep_name, df_agg, args.output, verbose=not args.quiet)
            generate_sweep_report(sweep_name, df_rep, df_agg, args.output)
    else:
        df_rep, df_agg = run_sweep(
            args.sweep,
            n_rep=args.n_rep,
            seed0=args.seed,
            methods=args.methods,
            output_dir=args.output,
            n_jobs=args.n_jobs,
            verbose=not args.quiet
        )
        generate_sweep_plots(args.sweep, df_agg, args.output, verbose=not args.quiet)
        generate_sweep_report(args.sweep, df_rep, df_agg, args.output)
    
    elapsed = time.time() - start_time
    if not args.quiet:
        print(f"\n{'='*70}")
        print(f"Total runtime: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
