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
        'description': 'Absolute difference between estimated and true average treatment effect. '
                      'Measures population-level accuracy.',
        'interpretation': 'Important for policy decisions about whether to adopt treatment broadly.'
    },
    'tau_corr': {
        'name': 'Spearman Rank Correlation',
        'formula': r'$\rho(\text{rank}(\hat{\tau}), \text{rank}(\tau))$',
        'direction': 'higher is better',
        'description': 'Rank correlation between predicted and true treatment effects. '
                      'Measures ability to correctly rank individuals by treatment benefit.',
        'interpretation': 'A correlation of 1.0 means perfect ranking; 0.0 means random ranking. '
                        'Critical for targeting interventions to high-benefit individuals.'
    },
    'mu0_rmse': {
        'name': 'μ₀ RMSE (Control Outcome)',
        'formula': r'$\sqrt{\frac{1}{n}\sum_i (\hat{\mu}_0(x_i) - \mu_0(x_i))^2}$',
        'direction': 'lower is better',
        'description': 'RMSE of predicted control outcomes. Measures quality of nuisance estimation.',
        'interpretation': 'Important diagnostic; poor μ₀ estimation can propagate to CATE errors.'
    }
}


# =============================================================================
# Sweep Configurations
# =============================================================================

DEFAULT_METHODS = ['NoTransfer', 'ProxyOnly', 'AnchorOnly', 'ProposedA', 'ProposedB_LinearStepB']

SWEEP_CONFIGS = {
    'gold': {
        'benchmark_id': 'gold_sweep',
        'description': 'Target placebo (m₀) budget sweep',
        'base_scenario': {
            'n_proxy_total': 2000,
            'C_sources': 10,
            'nontransfer_scale': 0.3,
        },
        'sweep_param': 'm0',
        'sweep_values': [25, 50, 100, 200, 500],
        
        # Detailed documentation for report
        'motivation': """
**Research Question:** How does the amount of target placebo data (m₀) affect estimator performance?

**Why This Matters:**
- In clinical trials, placebo/control arms are expensive and ethically constrained
- Real-world target data is often limited (e.g., 50-200 patients)
- Transfer learning methods aim to leverage proxy data to compensate for limited target data
- This sweep tests whether our estimator maintains accuracy with small m₀

**Expected Behavior:**
- **ProxyOnly** should be insensitive to m₀ (uses only source data)
- **AnchorOnly** should improve with m₀ (relies solely on target data)
- **Proposed** should improve with m₀ but remain competitive even at low m₀ due to transfer
- At very small m₀, Proposed should outperform AnchorOnly
- At very large m₀, AnchorOnly may catch up as target data becomes sufficient
""",
        'dgp_description': """
**Data Generating Process:**

The simulation generates data from a multi-site RCT setting where treatment effects
differ between source sites and the target population.

**Fixed Parameters:**
- **Covariates:** $X \\in \\mathbb{R}^{10}$, drawn from $\\mathcal{N}(0, I_{10})$
- **Source sites:** C = 10 sites with 2,000 total observations
- **Site allocation:** Uniform across source sites
- **Treatment assignment:** 50% probability (randomized)
- **Non-transfer component:** $\\sigma_{\\text{nontransfer}} = 0.3$ (moderate)

**Outcome Model:**
$$Y = \\mu_0(X) + T \\cdot \\tau(X) + \\epsilon, \\quad \\epsilon \\sim \\mathcal{N}(0, 1)$$

**CATE Structure:**
- Source sites: $\\tau^{(c)}(x) = \\beta_c^\\top x$ (linear, heterogeneous across sites)
- Target: $\\tau_0(x) = M \\beta_{\\text{proxy}}^\\top x + \\delta^\\top x$ where:
  - $M$ is a low-rank transfer operator (captures systematic transport)
  - $\\delta$ is a sparse correction (captures target-specific effects)

**What Varies:**
- **m₀** (target placebo sample size): 25 → 500
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
}


# =============================================================================
# Core Sweep Runner
# =============================================================================

def run_sweep(
    sweep_name: str,
    n_rep: int = 50,
    seed0: int = 42,
    methods: List[str] = None,
    output_dir: str = 'results/sweeps',
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
        methods = DEFAULT_METHODS
    
    if verbose:
        print("=" * 70)
        print(f"Sweep: {config['description']}")
        print(f"Benchmark ID: {benchmark_id}")
        print(f"Sweep param: {config['sweep_param']} ∈ {config['sweep_values']}")
        print(f"Methods: {methods}")
        print(f"Reps: {n_rep}")
        print("=" * 70)
    
    # Setup
    data_generator = create_data_generator()
    metric_computer = create_metric_computer()
    
    all_results = []
    
    # Generate scenarios
    scenarios = []
    for val in config['sweep_values']:
        scenario_params = config['base_scenario'].copy()
        scenario_params[config['sweep_param']] = val
        scenario = Scenario(benchmark_id=benchmark_id, **scenario_params)
        scenarios.append(scenario)
    
    # Run
    total_runs = len(scenarios) * n_rep * len(methods)
    pbar = tqdm(total=total_runs, desc="Running", disable=not verbose)
    
    for scenario in scenarios:
        for rep in range(n_rep):
            seed = generate_seed(scenario.scenario_id, rep, seed0)
            
            # Generate data
            try:
                data = data_generator(scenario, seed)
            except Exception as e:
                warnings.warn(f"Data generation failed: {e}")
                pbar.update(len(methods))
                continue
            
            # Create method factories (fresh for each rep)
            method_factories = create_method_factories(seed)
            
            for method_name in methods:
                pbar.update(1)
                
                if method_name not in method_factories:
                    continue
                
                method_spec = get_method_spec(method_name)
                feasibility = method_spec.feasibility_restricted.value
                
                t0 = time.time()
                try:
                    # Create estimator
                    estimator = method_factories[method_name]()
                    
                    # Fit
                    estimator.fit(
                        X_source=data['X_source'],
                        A_source=data['A_source'],
                        Y_source=data['Y_source'],
                        c_source=data['c_source'],
                        X_target=data['X_target'],
                        A_target=data['A_target'],
                        Y_target=data['Y_target'],
                        propensity_target=data.get('propensity_target')
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
                    'n_proxy_total': scenario.n_proxy_total,
                    'C_sources': scenario.C_sources,
                    'nontransfer_scale': scenario.nontransfer_scale,
                    
                    # Metrics
                    'pehe': metrics.get('pehe', np.nan),
                    'tau_corr': metrics.get('tau_corr', np.nan),
                    'ate_hat': metrics.get('ate_hat', np.nan),
                    'ate_abs_err': metrics.get('ate_abs_err', np.nan),
                    'qini_auc': metrics.get('qini_auc', np.nan),
                    'calib_slope': metrics.get('calib_slope', np.nan),
                    'calib_r2': metrics.get('calib_r2', np.nan),
                    'tau_ece': metrics.get('tau_ece', np.nan),
                    'policy_regret': metrics.get('policy_regret', np.nan),
                    
                    # Diagnostics
                    'stage2_lambda': stage2_lambda,
                    'stage2_n_selected': stage2_n_selected,
                    'stepb_M_fro_norm': stepb_fro,
                    'stepb_M_effective_rank': stepb_rank,
                    'runtime_sec': runtime,
                }
                
                all_results.append(result)
    
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
    
    setup_plot_style()
    
    os.makedirs(output_dir, exist_ok=True)
    
    # PEHE plot
    if verbose:
        print(f"\nGenerating plots for {benchmark_id}...")
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # 1. PEHE vs sweep param
    fig = plot_line(
        df_agg, 
        x=sweep_param, 
        y='pehe_mean', 
        hue='method',
        yerr='pehe_sd',
        title=f'PEHE vs {sweep_param}',
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
            title=f'ATE Error vs {sweep_param}',
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
            title=f'Spearman Correlation vs {sweep_param}',
            xlabel=sweep_param,
            ylabel='Spearman ρ'
        )
        fig.savefig(os.path.join(output_dir, f'{benchmark_id}_corr.png'), dpi=150)
        plt.close(fig)
    
    if verbose:
        print(f"✓ Plots saved to {output_dir}")


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
        best = find_best_methods(df_agg, metrics=['pehe', 'ate_abs_err', 'tau_corr'])
        f.write("| Metric | Best Method | Value | Direction |\n")
        f.write("|--------|-------------|-------|----------|\n")
        for metric, info in best.items():
            direction = "↓ lower is better" if metric in ['pehe', 'ate_abs_err', 'mu0_rmse'] else "↑ higher is better"
            f.write(f"| {metric} | **{info['method']}** | {info['value']:.4f} | {direction} |\n")
        f.write("\n")
        
        # =====================================================================
        # 7. DETAILED RESULTS TABLE
        # =====================================================================
        f.write("### Full Results Table\n\n")
        f.write(f"| {sweep_param} | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) |\n")
        f.write("|---|---|---|---|---|\n")
        
        # Sort for readability
        df_sorted = df_agg.sort_values([sweep_param, 'method'])
        
        for _, row in df_sorted.iterrows():
            pehe_str = f"{row['pehe_mean']:.3f} ± {row['pehe_sd']:.3f}" if not np.isnan(row.get('pehe_mean', np.nan)) else "N/A"
            ate_str = f"{row['ate_abs_err_mean']:.3f} ± {row['ate_abs_err_sd']:.3f}" if not np.isnan(row.get('ate_abs_err_mean', np.nan)) else "N/A"
            corr_str = f"{row['tau_corr_mean']:.3f} ± {row['tau_corr_sd']:.3f}" if not np.isnan(row.get('tau_corr_mean', np.nan)) else "N/A"
            
            f.write(f"| {row[sweep_param]} | {row['method']} | {pehe_str} | {ate_str} | {corr_str} |\n")
        
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
        'ProposedA': 'Proposed (Option A): requires target treated',
        'ProposedB_LinearStepB': 'Proposed (Option B): placebo-anchored with linear Step B',
        'ProposedB_KernelStepB': 'Proposed (Option B): placebo-anchored with kernel Step B',
    }
    return descriptions.get(method, 'See documentation')


def _generate_findings(sweep_name: str, df_agg: pd.DataFrame, config: dict) -> List[str]:
    """Auto-generate key findings from results."""
    findings = []
    sweep_param = config['sweep_param']
    sweep_values = config['sweep_values']
    
    # Find best method overall
    best_pehe_idx = df_agg['pehe_mean'].idxmin()
    best_method = df_agg.loc[best_pehe_idx, 'method'] if not pd.isna(best_pehe_idx) else "Unknown"
    best_pehe = df_agg.loc[best_pehe_idx, 'pehe_mean'] if not pd.isna(best_pehe_idx) else np.nan
    findings.append(f"**Best overall PEHE:** {best_method} achieves lowest average PEHE ({best_pehe:.3f})")
    
    # Check if Proposed beats ProxyOnly
    proposed_pehe = df_agg[df_agg['method'].str.contains('Proposed', na=False)]['pehe_mean'].mean()
    proxy_pehe = df_agg[df_agg['method'] == 'ProxyOnly']['pehe_mean'].mean()
    if not np.isnan(proposed_pehe) and not np.isnan(proxy_pehe):
        if proposed_pehe < proxy_pehe:
            pct_improvement = (proxy_pehe - proposed_pehe) / proxy_pehe * 100
            findings.append(f"**Proposed vs ProxyOnly:** Proposed reduces PEHE by {pct_improvement:.1f}% on average")
        else:
            findings.append(f"**Proposed vs ProxyOnly:** ProxyOnly outperforms Proposed in this setting")
    
    # Check trend with sweep parameter
    for method in df_agg['method'].unique():
        method_data = df_agg[df_agg['method'] == method].sort_values(sweep_param)
        if len(method_data) >= 2:
            first_pehe = method_data.iloc[0]['pehe_mean']
            last_pehe = method_data.iloc[-1]['pehe_mean']
            if not np.isnan(first_pehe) and not np.isnan(last_pehe):
                if last_pehe < first_pehe * 0.8:  # >20% improvement
                    findings.append(f"**{method}:** PEHE improves substantially as {sweep_param} increases")
                elif last_pehe > first_pehe * 1.2:  # >20% degradation
                    findings.append(f"**{method}:** PEHE degrades as {sweep_param} increases")
    
    # Check ranking correlation
    best_corr_idx = df_agg['tau_corr_mean'].idxmax()
    if not pd.isna(best_corr_idx):
        best_corr_method = df_agg.loc[best_corr_idx, 'method']
        best_corr = df_agg.loc[best_corr_idx, 'tau_corr_mean']
        findings.append(f"**Best ranking:** {best_corr_method} achieves highest Spearman correlation ({best_corr:.3f})")
    
    if not findings:
        findings.append("*No significant patterns detected. Review plots for visual inspection.*")
    
    return findings


# =============================================================================
# Run All Sweeps
# =============================================================================

def run_all_sweeps(
    n_rep: int = 20,
    seed0: int = 42,
    methods: List[str] = None,
    output_dir: str = 'results/sweeps',
    verbose: bool = True
) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    """Run all core sweeps."""
    
    results = {}
    
    for sweep_name in ['gold', 'proxy', 'imbalance']:
        if verbose:
            print(f"\n{'='*70}")
            print(f"Running {sweep_name} sweep...")
            print('='*70)
        
        df_rep, df_agg = run_sweep(
            sweep_name, n_rep=n_rep, seed0=seed0, 
            methods=methods, output_dir=output_dir, verbose=verbose
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
    parser = argparse.ArgumentParser(description="Run core benchmark sweeps")
    parser.add_argument('--sweep', type=str, default='all',
                       choices=['gold', 'proxy', 'imbalance', 'all'],
                       help='Sweep to run')
    parser.add_argument('--n_rep', type=int, default=20,
                       help='Number of MC replicates')
    parser.add_argument('--seed', type=int, default=42,
                       help='Master seed')
    parser.add_argument('--output', type=str, default='results/sweeps',
                       help='Output directory')
    parser.add_argument('--methods', type=str, nargs='+', default=None,
                       help='Methods to run')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')
    
    args = parser.parse_args()
    
    if args.sweep == 'all':
        run_all_sweeps(
            n_rep=args.n_rep,
            seed0=args.seed,
            methods=args.methods,
            output_dir=args.output,
            verbose=not args.quiet
        )
    else:
        df_rep, df_agg = run_sweep(
            args.sweep,
            n_rep=args.n_rep,
            seed0=args.seed,
            methods=args.methods,
            output_dir=args.output,
            verbose=not args.quiet
        )
        generate_sweep_plots(args.sweep, df_agg, args.output, verbose=not args.quiet)
        generate_sweep_report(args.sweep, df_rep, df_agg, args.output)


if __name__ == "__main__":
    main()
