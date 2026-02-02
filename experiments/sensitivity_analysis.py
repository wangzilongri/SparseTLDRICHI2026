#!/usr/bin/env python
"""
Sensitivity Analysis Framework for Placebo-Anchored DR-Learner

Implements the following sweeps:
1. Outcome misspecification sensitivity
2. Propensity + overlap stress (TARGET-SPECIFIC)
3. Covariate shift magnitude sensitivity
4. A5 sparsity sensitivity
5. A6 transfer validity sensitivity (nontransfer sweep)
6. Gold budget sensitivity (Stage 2 sample size)

Usage:
    python experiments/sensitivity_analysis.py --sweep misspec --n_mc 50
    python experiments/sensitivity_analysis.py --sweep all --n_mc 100
    
IMPORTANT NOTES:
- "Proposed-A" uses Option A: learns beta_1 directly from target treated
- "Proposed-B (StepB)" uses Option B: learns M* from sources, applies M* @ beta_0
- All evaluation is on TARGET TEST SET only (target-only regime)
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Callable, Any, Optional
from itertools import product
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synthetic_data_v2 import SyntheticRCTGenerator, SyntheticRCTConfig
from estimator_fixed import PlaceboAnchoredDRLearner
from ablations import ProxyOnlyBaseline, AnchorOnlyBaseline, NoTransferBaseline
from metrics import (
    pehe, ate_error, cate_rank_correlation, qini_auc,
    cate_calibration_slope_intercept, cate_ece, policy_metrics,
    save_results_csv
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SweepConfig:
    """Configuration for a sensitivity sweep."""
    name: str
    param_name: str
    param_values: List[Any]
    base_config: Dict = field(default_factory=dict)
    n_mc: int = 50
    test_frac: float = 0.5
    random_seed: int = 42
    
    # For multi-parameter sweeps
    param_name_2: str = None
    param_values_2: List[Any] = None


# =============================================================================
# Core Sweep Function
# =============================================================================

def compute_all_metrics(tau_true: np.ndarray, tau_pred: np.ndarray,
                        mu0_true: np.ndarray, mu1_true: np.ndarray) -> Dict[str, float]:
    """
    Compute all evaluation metrics.
    
    Returns np.nan for failed metrics (not 0/1) to avoid masking failures.
    """
    metrics = {}
    
    # Basic accuracy
    try:
        metrics['pehe'] = pehe(tau_true, tau_pred)
    except:
        metrics['pehe'] = np.nan
        
    try:
        metrics['ate_error'] = ate_error(tau_true, tau_pred)
    except:
        metrics['ate_error'] = np.nan
    
    # Ranking - keep NaN if computation fails
    try:
        rho, _ = cate_rank_correlation(tau_true, tau_pred, method='spearman')
        metrics['spearman'] = rho  # May be NaN if constant input
    except:
        metrics['spearman'] = np.nan
    
    try:
        metrics['qini_auc'] = qini_auc(tau_true, tau_pred)
    except:
        metrics['qini_auc'] = np.nan
    
    # Calibration (note: function returns intercept, slope, r2, degenerate)
    try:
        intercept, slope, r2, calib_degenerate = cate_calibration_slope_intercept(tau_true, tau_pred)
        metrics['cal_slope'] = slope
        metrics['cal_intercept'] = intercept
        metrics['cal_r2'] = r2
        metrics['cal_degenerate'] = calib_degenerate
    except:
        metrics['cal_slope'] = np.nan
        metrics['cal_intercept'] = np.nan
        metrics['cal_degenerate'] = True
        metrics['cal_r2'] = np.nan
    
    try:
        metrics['cate_ece'] = cate_ece(tau_true, tau_pred)
    except:
        metrics['cate_ece'] = np.nan
    
    # Policy (oracle-based, uses true mu0/mu1)
    try:
        pm = policy_metrics(tau_true, tau_pred, mu0_true, mu1_true)
        metrics['policy_value'] = pm['policy_value']
        metrics['policy_regret'] = pm['policy_regret']
    except:
        metrics['policy_value'] = np.nan
        metrics['policy_regret'] = np.nan
    
    return metrics


def split_target_data(target_data: Dict, test_frac: float, seed: int) -> Tuple[Dict, Dict]:
    """Split target data into train/test, stratified by treatment."""
    from sklearn.model_selection import train_test_split
    
    n = len(target_data['Y'])
    indices = np.arange(n)
    
    # Stratify by treatment if possible
    A = target_data['A']
    if len(np.unique(A)) > 1:
        train_idx, test_idx = train_test_split(
            indices, test_size=test_frac, stratify=A, random_state=seed
        )
    else:
        train_idx, test_idx = train_test_split(
            indices, test_size=test_frac, random_state=seed
        )
    
    train_data = {k: v[train_idx] for k, v in target_data.items()}
    test_data = {k: v[test_idx] for k, v in target_data.items()}
    
    return train_data, test_data


def subsample_placebo(target_data: Dict, m0: int, seed: int) -> Dict:
    """Subsample placebo arm to size m0, keep all treated."""
    rng = np.random.default_rng(seed)
    
    placebo_idx = np.where(target_data['A'] == 0)[0]
    treated_idx = np.where(target_data['A'] == 1)[0]
    
    # Subsample placebo
    if len(placebo_idx) > m0:
        placebo_subsample = rng.choice(placebo_idx, size=m0, replace=False)
    else:
        placebo_subsample = placebo_idx
    
    # Combine
    keep_idx = np.concatenate([placebo_subsample, treated_idx])
    keep_idx = np.sort(keep_idx)
    
    return {k: v[keep_idx] for k, v in target_data.items()}


def create_method_factories(random_state: int = 42) -> Dict[str, Callable]:
    """
    Create factory functions for all estimator methods.
    
    Returns callables that create fresh instances (avoids state leakage).
    
    NOTE on naming:
    - "Proposed-A": Option A - learns beta_1 directly from target treated
    - "Proposed-B (StepB)": Option B - learns M* from sources, applies transfer
    """
    return {
        'No-Transfer': lambda: NoTransferBaseline(random_state=random_state),
        'Proxy-Only': lambda: ProxyOnlyBaseline(random_state=random_state),
        'Anchor-Only': lambda: AnchorOnlyBaseline(option='A', random_state=random_state),
        'Proposed-A': lambda: PlaceboAnchoredDRLearner(option='A', n_folds=3, random_state=random_state, verbose=False),
        'Proposed-B (StepB)': lambda: PlaceboAnchoredDRLearner(option='B', n_folds=3, random_state=random_state, verbose=False),
    }


def compute_transfer_snr(gen: SyntheticRCTGenerator, target_site_id: int = 0) -> float:
    """Compute transfer SNR: ||M* @ beta0[target]|| / ||nu[target]||."""
    try:
        beta0 = gen.beta0.get(target_site_id, np.zeros(gen.config.n_features))
        nu = gen.nu.get(target_site_id, np.zeros(gen.config.n_features))
        
        M_beta0_norm = np.linalg.norm(gen.M_star @ beta0)
        nu_norm = np.linalg.norm(nu)
        
        if nu_norm < 1e-10:
            return np.inf  # Perfect transfer
        return M_beta0_norm / nu_norm
    except:
        return np.nan


def run_single_mc(config_dict: Dict, method_factories: Dict[str, Callable], 
                  test_frac: float, seed: int, 
                  m0_subsample: int = None) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """
    Run a single Monte Carlo replicate.
    
    Returns:
        (method_results, diagnostics) where diagnostics includes:
        - n_placebo_train, n_treated_train
        - m0_effective (for gold budget sweep)
        - transfer_snr
        - overlap_min (min propensity)
    """
    
    # Generate data
    config = SyntheticRCTConfig(**config_dict)
    gen = SyntheticRCTGenerator(config)
    source_data, target_data = gen.generate_full_dataset()
    
    # Split target
    target_train, target_test = split_target_data(target_data, test_frac, seed)
    
    # Track original counts before subsampling
    n_placebo_orig = np.sum(target_train['A'] == 0)
    n_treated_orig = np.sum(target_train['A'] == 1)
    
    # Subsample placebo if requested (for gold budget sweep)
    m0_effective = n_placebo_orig
    if m0_subsample is not None:
        target_train = subsample_placebo(target_train, m0_subsample, seed)
        m0_effective = np.sum(target_train['A'] == 0)
    
    # Diagnostics
    diagnostics = {
        'n_placebo_train': np.sum(target_train['A'] == 0),
        'n_treated_train': np.sum(target_train['A'] == 1),
        'm0_effective': m0_effective,
        'transfer_snr': compute_transfer_snr(gen, target_site_id=0),
        'overlap_min': min(
            config_dict.get('treatment_prob_target', config_dict.get('treatment_prob', 0.5)),
            1 - config_dict.get('treatment_prob_target', config_dict.get('treatment_prob', 0.5))
        )
    }
    
    # Ground truth on test
    X_test = target_test['X']
    tau_true = target_test['tau_true']
    mu0_true = target_test['mu0_true']
    mu1_true = target_test['mu1_true']
    
    # Fit and evaluate each method using factories
    results = {}
    for name, make_method in method_factories.items():
        try:
            # Create fresh instance from factory
            m = make_method()
            
            # Fit (all methods get source + target data; they decide what to use)
            m.fit(
                source_data['X'], source_data['A'], source_data['Y'], source_data['c'],
                target_train['X'], target_train['A'], target_train['Y']
            )
            
            # Predict
            tau_pred = m.predict(X_test)
            
            # Metrics
            results[name] = compute_all_metrics(tau_true, tau_pred, mu0_true, mu1_true)
            
        except Exception as e:
            # Return NaN metrics on failure (not fake values!)
            results[name] = {
                'pehe': np.nan, 'ate_error': np.nan, 'spearman': np.nan,
                'qini_auc': np.nan, 'cal_slope': np.nan, 'cal_intercept': np.nan,
                'cal_r2': np.nan, 'cate_ece': np.nan, 'policy_value': np.nan,
                'policy_regret': np.nan
            }
    
    return results, diagnostics


def run_sweep(sweep_config: SweepConfig, verbose: bool = True) -> pd.DataFrame:
    """
    Run a full sensitivity sweep.
    
    Returns DataFrame with columns: param_value, method, metric, mean, std, se, n_valid
    Also includes diagnostic columns (transfer_snr, overlap_min, m0_effective).
    """
    results_list = []
    
    # Build grid
    if sweep_config.param_name_2 is not None:
        grid = list(product(sweep_config.param_values, sweep_config.param_values_2))
        param_names = [sweep_config.param_name, sweep_config.param_name_2]
    else:
        grid = [(v,) for v in sweep_config.param_values]
        param_names = [sweep_config.param_name]
    
    total_runs = len(grid) * sweep_config.n_mc
    run_count = 0
    
    # Base values for normalization (used in sparsity sweep)
    base_sparsity = sweep_config.base_config.get('dev_sparsity', 2)
    base_scale = sweep_config.base_config.get('dev_scale', 0.4)
    
    for grid_point in grid:
        # Build config for this grid point
        config_dict = sweep_config.base_config.copy()
        for pname, pval in zip(param_names, grid_point):
            if pname == 'm0_subsample':
                continue  # Handle separately
            config_dict[pname] = pval
        
        # ═══════════════════════════════════════════════════════════════
        # Sparsity normalization: keep total deviation energy comparable
        # dev_scale = base_scale * sqrt(base_sparsity / dev_sparsity)
        # ═══════════════════════════════════════════════════════════════
        if sweep_config.name == 'sparsity' and 'dev_sparsity' in config_dict:
            s = config_dict['dev_sparsity']
            config_dict['dev_scale'] = base_scale * np.sqrt(base_sparsity / s)
        
        # Check for m0_subsample (gold budget sweep)
        m0_subsample = None
        if 'm0_subsample' in param_names:
            idx = param_names.index('m0_subsample')
            m0_subsample = grid_point[idx]
        
        # Run MC replicates
        mc_results = []
        mc_diagnostics = []
        
        for rep in range(sweep_config.n_mc):
            seed = sweep_config.random_seed + rep
            
            try:
                rep_results, rep_diag = run_single_mc(
                    config_dict, 
                    create_method_factories(seed),
                    sweep_config.test_frac,
                    seed,
                    m0_subsample
                )
                mc_results.append(rep_results)
                mc_diagnostics.append(rep_diag)
            except Exception as e:
                if verbose:
                    print(f"  MC rep {rep} failed: {e}")
            
            run_count += 1
            if verbose and run_count % 10 == 0:
                print(f"  Progress: {run_count}/{total_runs} ({100*run_count/total_runs:.0f}%)")
        
        # Aggregate across MC
        if len(mc_results) == 0:
            continue
        
        # Aggregate diagnostics
        avg_diagnostics = {}
        for key in mc_diagnostics[0].keys():
            vals = [d[key] for d in mc_diagnostics if not np.isnan(d.get(key, np.nan))]
            avg_diagnostics[key] = np.mean(vals) if vals else np.nan
            
        methods = list(mc_results[0].keys())
        metrics = list(mc_results[0][methods[0]].keys())
        
        for method in methods:
            for metric in metrics:
                values = []
                for r in mc_results:
                    val = r[method][metric]
                    if val is not None and isinstance(val, (int, float)) and not np.isnan(val):
                        values.append(val)
                
                if len(values) > 0:
                    result_row = {
                        'method': method,
                        'metric': metric,
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'se': np.std(values) / np.sqrt(len(values)),
                        'n_valid': len(values)
                    }
                    # Add grid point values
                    for pname, pval in zip(param_names, grid_point):
                        result_row[pname] = pval
                    
                    # Add diagnostics
                    result_row['transfer_snr'] = avg_diagnostics.get('transfer_snr', np.nan)
                    result_row['overlap_min'] = avg_diagnostics.get('overlap_min', np.nan)
                    result_row['m0_effective'] = avg_diagnostics.get('m0_effective', np.nan)
                    
                    # For sparsity sweep, also log effective dev_scale
                    if sweep_config.name == 'sparsity':
                        result_row['dev_scale_used'] = config_dict.get('dev_scale', np.nan)
                    
                    results_list.append(result_row)
    
    return pd.DataFrame(results_list)


# =============================================================================
# Sweep Configurations
# =============================================================================

def get_base_config() -> Dict:
    """Get base DGP configuration."""
    return {
        'n_features': 5,
        'n_source_sites': 10,
        'n_target': 400,
        'n_source_per_site': 200,
        'treatment_prob': 0.5,
        'noise_std': 0.5,
        'covariate_shift_scale': 1.0,
        'target_shift_multiplier': 1.5,
        'dev_sparsity': 2,
        'dev_scale': 0.4,
        'transfer_rank': 1,
        'transfer_strength': 1.0,
        'nontransfer_scale_source': 0.05,
        'nontransfer_scale_target': 0.3,
        'misspec_scale': 0.0,
        'misspec_nonlinear': False,
        'proxy_nonlinear_scale': 0.3,
        'random_state': 42
    }


def sweep_1_misspecification(n_mc: int = 50) -> SweepConfig:
    """Sweep 1: Outcome misspecification sensitivity."""
    base = get_base_config()
    base['target_treated_frac'] = 0.5  # Keep treated for fair comparison
    
    return SweepConfig(
        name='misspecification',
        param_name='misspec_scale',
        param_values=[0.0, 0.1, 0.2, 0.4, 0.8],
        param_name_2='misspec_nonlinear',
        param_values_2=[False, True],
        base_config=base,
        n_mc=n_mc
    )


def sweep_2_propensity(n_mc: int = 50) -> SweepConfig:
    """
    Sweep 2: Propensity / overlap stress (TARGET-SPECIFIC).
    
    Varies treatment_prob_target while keeping source propensity fixed at 0.5.
    This isolates overlap stress to the target site only.
    """
    base = get_base_config()
    # CRITICAL: Keep source propensity fixed, only vary target
    base['treatment_prob_source'] = 0.5
    
    return SweepConfig(
        name='propensity',
        param_name='treatment_prob_target',  # Changed from treatment_prob
        param_values=[0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9],
        base_config=base,
        n_mc=n_mc
    )


def sweep_3_covariate_shift(n_mc: int = 50) -> SweepConfig:
    """Sweep 3: Covariate shift magnitude."""
    base = get_base_config()
    
    return SweepConfig(
        name='covariate_shift',
        param_name='target_shift_multiplier',
        param_values=[1.0, 1.25, 1.5, 2.0, 3.0],
        base_config=base,
        n_mc=n_mc
    )


def sweep_4_sparsity(n_mc: int = 50) -> SweepConfig:
    """Sweep 4: A5 sparsity sensitivity."""
    base = get_base_config()
    base_sparsity = 2
    base_scale = 0.4
    
    # Note: dev_scale will be adjusted per sparsity level
    return SweepConfig(
        name='sparsity',
        param_name='dev_sparsity',
        param_values=[1, 2, 3, 4, 5],
        base_config=base,
        n_mc=n_mc
    )


def sweep_5_nontransfer(n_mc: int = 50) -> SweepConfig:
    """Sweep 5: A6 transfer validity (nontransfer magnitude)."""
    base = get_base_config()
    base['target_treated_frac'] = 0.0  # Disconnected target for Step B testing
    
    return SweepConfig(
        name='nontransfer',
        param_name='nontransfer_scale_target',
        param_values=[0.0, 0.1, 0.2, 0.4, 0.8],
        base_config=base,
        n_mc=n_mc
    )


def sweep_6_gold_budget(n_mc: int = 50) -> SweepConfig:
    """Sweep 6: Gold budget (Stage 2 sample size)."""
    base = get_base_config()
    base['n_target'] = 800  # Larger target to allow subsampling
    
    return SweepConfig(
        name='gold_budget',
        param_name='m0_subsample',
        param_values=[25, 50, 100, 200, 400],
        base_config=base,
        n_mc=n_mc
    )


# =============================================================================
# Plotting Functions
# =============================================================================

def plot_sweep_results(df: pd.DataFrame, sweep_name: str, output_dir: str,
                       metrics_to_plot: List[str] = None):
    """Generate plots for a sweep with proper multi-parameter labels."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    os.makedirs(output_dir, exist_ok=True)
    
    if metrics_to_plot is None:
        metrics_to_plot = ['pehe', 'spearman', 'cate_ece', 'policy_regret']
    
    # Get parameter column(s) - exclude non-parameter columns
    exclude_cols = {'method', 'metric', 'mean', 'std', 'se', 'n_valid',
                    'transfer_snr', 'overlap_min', 'm0_effective', 'dev_scale_used'}
    param_cols = [c for c in df.columns if c not in exclude_cols]
    
    methods = df['method'].unique()
    
    # Use standardized colors
    from metrics import get_method_colors
    colors = dict(zip(methods, get_method_colors(list(methods))))
    
    # Higher is better for these metrics
    higher_better = {'spearman', 'qini_auc', 'cal_r2', 'policy_value'}
    
    for metric in metrics_to_plot:
        metric_df = df[df['metric'] == metric]
        if len(metric_df) == 0:
            continue
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Handle multi-parameter sweeps (e.g., misspec_scale x misspec_nonlinear)
        if len(param_cols) >= 2:
            param2_vals = metric_df[param_cols[1]].unique()
            linestyles = ['-', '--', ':', '-.']
            
            # Create legend entries
            legend_handles = []
            legend_labels = []
            
            for i, p2 in enumerate(param2_vals):
                subset = metric_df[metric_df[param_cols[1]] == p2]
                ls = linestyles[i % len(linestyles)]
                
                for method in methods:
                    method_df = subset[subset['method'] == method]
                    if len(method_df) == 0:
                        continue
                    
                    x = method_df[param_cols[0]].values
                    y = method_df['mean'].values
                    yerr = method_df['se'].values * 1.96
                    
                    # FIXED: Include param2 in label for all lines
                    label = f"{method} ({param_cols[1]}={p2})"
                    line = ax.errorbar(x, y, yerr=yerr, fmt='o-', label=label,
                                      color=colors[method], linestyle=ls, 
                                      capsize=3, markersize=6, linewidth=1.5)
            
            # Adjust legend
            ax.legend(loc='best', fontsize=8, ncol=2)
        else:
            # Single parameter sweep
            for method in methods:
                method_df = metric_df[metric_df['method'] == method]
                if len(method_df) == 0:
                    continue
                
                # Sort by parameter for clean lines
                method_df = method_df.sort_values(param_cols[0])
                
                x = method_df[param_cols[0]].values
                y = method_df['mean'].values
                yerr = method_df['se'].values * 1.96
                
                ax.errorbar(x, y, yerr=yerr, fmt='o-', label=method,
                           color=colors[method], capsize=3, markersize=8, linewidth=2)
            
            ax.legend(loc='best', fontsize=9)
        
        direction = "↑" if metric in higher_better else "↓"
        ax.set_xlabel(param_cols[0], fontsize=12)
        ax.set_ylabel(f"{metric} {direction}", fontsize=12)
        ax.set_title(f"{sweep_name}: {metric}", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        for fmt in ['png', 'pdf']:
            save_path = os.path.join(output_dir, f"{sweep_name}_{metric}.{fmt}")
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close(fig)
    
    # Also plot transfer_snr if available in nontransfer sweep
    if 'transfer_snr' in df.columns and sweep_name == 'nontransfer':
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Get one row per grid point (all methods have same SNR)
        snr_df = df[df['method'] == methods[0]][param_cols + ['transfer_snr']].drop_duplicates()
        snr_df = snr_df.sort_values(param_cols[0])
        
        ax.plot(snr_df[param_cols[0]], snr_df['transfer_snr'], 'ko-', linewidth=2, markersize=8)
        ax.set_xlabel(param_cols[0], fontsize=12)
        ax.set_ylabel('Transfer SNR (||M*β₀|| / ||ν||)', fontsize=12)
        ax.set_title('Transfer Signal-to-Noise Ratio', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        for fmt in ['png', 'pdf']:
            save_path = os.path.join(output_dir, f"{sweep_name}_transfer_snr.{fmt}")
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    
    print(f"  Plots saved to {output_dir}")


def generate_sweep_report(df: pd.DataFrame, sweep_name: str, output_dir: str):
    """Generate a markdown report for a sweep with diagnostics."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Exclude diagnostic columns from parameters
    exclude_cols = {'method', 'metric', 'mean', 'std', 'se', 'n_valid',
                    'transfer_snr', 'overlap_min', 'm0_effective', 'dev_scale_used'}
    param_cols = [c for c in df.columns if c not in exclude_cols]
    
    report_path = os.path.join(output_dir, f"{sweep_name}_report.md")
    
    with open(report_path, 'w') as f:
        f.write(f"# Sensitivity Analysis: {sweep_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Important notes
        f.write("## Notes\n\n")
        f.write("- **Proposed-A**: Option A - learns β₁ directly from target treated\n")
        f.write("- **Proposed-B (StepB)**: Option B - learns M* from sources, applies M* @ β₀\n")
        f.write("- All evaluation is on TARGET TEST SET only\n")
        f.write("- Values shown as mean ± standard error (95% CI = ±1.96×SE)\n\n")
        
        # Diagnostics summary if available
        if 'transfer_snr' in df.columns or 'overlap_min' in df.columns:
            f.write("## Diagnostics\n\n")
            
            # Get one row per grid point
            diag_cols = [c for c in ['transfer_snr', 'overlap_min', 'm0_effective', 'dev_scale_used'] 
                        if c in df.columns]
            if diag_cols:
                methods = df['method'].unique()
                diag_df = df[df['method'] == methods[0]][param_cols + diag_cols].drop_duplicates()
                
                f.write("| " + " | ".join(param_cols + diag_cols) + " |\n")
                f.write("|" + "---|" * (len(param_cols) + len(diag_cols)) + "\n")
                
                for _, row in diag_df.iterrows():
                    vals = [str(row[c]) if pd.notna(row[c]) else 'N/A' for c in param_cols]
                    vals += [f"{row[c]:.3f}" if pd.notna(row[c]) else 'N/A' for c in diag_cols]
                    f.write("| " + " | ".join(vals) + " |\n")
                f.write("\n")
        
        # Summary table for key metrics
        f.write("## Results\n\n")
        
        for metric in ['pehe', 'spearman', 'policy_regret', 'cate_ece']:
            metric_df = df[df['metric'] == metric]
            if len(metric_df) == 0:
                continue
            
            f.write(f"### {metric}\n\n")
            
            methods = metric_df['method'].unique()
            
            # Create table header
            header = "| " + " | ".join(param_cols) + " | " + " | ".join(methods) + " |\n"
            sep = "|" + "---|" * (len(param_cols) + len(methods)) + "\n"
            f.write(header)
            f.write(sep)
            
            # Group by parameters
            grouped = metric_df.groupby(param_cols, sort=True)
            for params, group in grouped:
                if not isinstance(params, tuple):
                    params = (params,)
                row = "| " + " | ".join(str(p) for p in params) + " |"
                for method in methods:
                    m_row = group[group['method'] == method]
                    if len(m_row) > 0:
                        mean = m_row['mean'].values[0]
                        se = m_row['se'].values[0]
                        n_valid = m_row['n_valid'].values[0]
                        if pd.notna(mean):
                            row += f" {mean:.3f}±{se:.3f} |"
                        else:
                            row += " N/A |"
                    else:
                        row += " N/A |"
                f.write(row + "\n")
            
            f.write("\n")
        
        # Embed plots
        f.write("## Visualizations\n\n")
        for metric in ['pehe', 'spearman', 'cate_ece', 'policy_regret', 'transfer_snr']:
            plot_file = f"{sweep_name}_{metric}.png"
            if os.path.exists(os.path.join(output_dir, plot_file)):
                f.write(f"### {metric}\n\n")
                f.write(f"![{metric}]({plot_file})\n\n")
        
        # Implementation notes
        f.write("---\n\n")
        f.write("## Implementation Notes\n\n")
        f.write("- DGP uses `synthetic_data_v2.py` with A5/A6 structure\n")
        f.write("- Estimators from `estimator_fixed.py` with all advisor fixes\n")
        f.write("- Misspecification parameters are site/arm-fixed (deterministic μ_{a,c}(x))\n")
        
        if sweep_name == 'propensity':
            f.write("- Propensity varies TARGET only; sources fixed at e=0.5\n")
        if sweep_name == 'sparsity':
            f.write("- dev_scale normalized: dev_scale = 0.4 * sqrt(2/s) to keep energy comparable\n")
    
    print(f"  Report saved to {report_path}")


# =============================================================================
# Main
# =============================================================================

def run_all_sweeps(n_mc: int = 50, output_base: str = 'results/sensitivity'):
    """Run all sensitivity analyses."""
    
    sweeps = [
        ('1_misspecification', sweep_1_misspecification(n_mc)),
        ('2_propensity', sweep_2_propensity(n_mc)),
        ('3_covariate_shift', sweep_3_covariate_shift(n_mc)),
        ('4_sparsity', sweep_4_sparsity(n_mc)),
        ('5_nontransfer', sweep_5_nontransfer(n_mc)),
        ('6_gold_budget', sweep_6_gold_budget(n_mc)),
    ]
    
    for sweep_id, sweep_config in sweeps:
        output_dir = os.path.join(output_base, sweep_id)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Running sweep: {sweep_config.name}")
        print(f"{'='*60}")
        
        # Run sweep
        df = run_sweep(sweep_config, verbose=True)
        
        # Save results
        csv_path = os.path.join(output_dir, f"{sweep_config.name}_results.csv")
        df.to_csv(csv_path, index=False)
        print(f"  Results saved to {csv_path}")
        
        # Generate plots
        plot_sweep_results(df, sweep_config.name, output_dir)
        
        # Generate report
        generate_sweep_report(df, sweep_config.name, output_dir)
    
    print(f"\n{'='*60}")
    print("All sweeps complete!")
    print(f"Results saved to: {output_base}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='Run sensitivity analyses')
    parser.add_argument('--sweep', type=str, default='all',
                        choices=['all', 'misspec', 'propensity', 'covariate', 
                                 'sparsity', 'nontransfer', 'gold'],
                        help='Which sweep to run')
    parser.add_argument('--n_mc', type=int, default=50,
                        help='Number of Monte Carlo replicates')
    parser.add_argument('--output', type=str, default='results/sensitivity',
                        help='Output directory')
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    if args.sweep == 'all':
        run_all_sweeps(args.n_mc, args.output)
    else:
        sweep_map = {
            'misspec': ('1_misspecification', sweep_1_misspecification),
            'propensity': ('2_propensity', sweep_2_propensity),
            'covariate': ('3_covariate_shift', sweep_3_covariate_shift),
            'sparsity': ('4_sparsity', sweep_4_sparsity),
            'nontransfer': ('5_nontransfer', sweep_5_nontransfer),
            'gold': ('6_gold_budget', sweep_6_gold_budget),
        }
        
        sweep_id, sweep_fn = sweep_map[args.sweep]
        sweep_config = sweep_fn(args.n_mc)
        output_dir = os.path.join(args.output, sweep_id)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Running sweep: {sweep_config.name}")
        print(f"{'='*60}")
        
        df = run_sweep(sweep_config, verbose=True)
        
        csv_path = os.path.join(output_dir, f"{sweep_config.name}_results.csv")
        df.to_csv(csv_path, index=False)
        print(f"  Results saved to {csv_path}")
        
        plot_sweep_results(df, sweep_config.name, output_dir)
        generate_sweep_report(df, sweep_config.name, output_dir)


if __name__ == '__main__':
    main()
