"""
Ablation Study: Evaluate contribution of each component.

Compares four model variants:
1. No-Transfer: Only target placebo, cannot extrapolate
2. Proxy-Only: Source trials without anchoring
3. Anchor-Only: Placebo anchoring without DR
4. Proposed: Full method with all components

Based on paper Table and Figures.
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib
matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt
from pathlib import Path

from synthetic_data import generate_synthetic_rct
from estimator import PlaceboAnchoredDRLearner
from ablations import NoTransferBaseline, ProxyOnlyBaseline, AnchorOnlyBaseline
from metrics import evaluate_cate_model, compare_methods


def run_single_experiment(n_source_sites=3, n_target=200, n_source_per_site=500,
                          covariate_shift_scale=1.0, random_state=42, verbose=False):
    """
    Run single ablation experiment.
    
    Returns
    -------
    results : dict
        Metrics for each method
    """
    # Generate data
    if verbose:
        print("\n" + "=" * 80)
        print("Generating synthetic RCT data...")
        print("=" * 80)
    
    source, target, gen = generate_synthetic_rct(
        n_source_sites=n_source_sites,
        n_target=n_target,
        n_source_per_site=n_source_per_site,
        covariate_shift_scale=covariate_shift_scale,
        random_state=random_state
    )
    
    if verbose:
        print(f"Source: {len(source['X'])} samples from {n_source_sites} sites")
        print(f"Target: {len(target['X'])} samples")
        print(f"Covariate shift scale: {covariate_shift_scale}")
    
    # Extract data
    X_source = source['X']
    A_source = source['A']
    Y_source = source['Y']
    c_source = source['c']
    
    X_target = target['X']
    A_target = target['A']
    Y_target = target['Y']
    tau_target = target['tau_true']
    mu0_target = target['mu0_true']
    mu1_target = target['mu1_true']
    
    results = {}
    
    # =========================================================================
    # 1. No-Transfer Baseline
    # =========================================================================
    if verbose:
        print("\n" + "-" * 80)
        print("1. No-Transfer Baseline")
        print("-" * 80)
    
    no_transfer = NoTransferBaseline(random_state=random_state)
    no_transfer.fit(X_source, A_source, Y_source, c_source,
                    X_target, A_target, Y_target)
    
    results['No-Transfer'] = evaluate_cate_model(
        no_transfer, X_target, tau_target,
        mu0_target, mu1_target, compute_calibration=False
    )
    
    if verbose:
        print(f"  PEHE: {results['No-Transfer']['pehe']:.4f}")
        print(f"  ATE Error: {results['No-Transfer']['ate_error']:.4f}")
    
    # =========================================================================
    # 2. Proxy-Only Baseline
    # =========================================================================
    if verbose:
        print("\n" + "-" * 80)
        print("2. Proxy-Only Baseline")
        print("-" * 80)
    
    proxy_only = ProxyOnlyBaseline(random_state=random_state)
    proxy_only.fit(X_source, A_source, Y_source, c_source,
                   X_target, A_target, Y_target)
    
    results['Proxy-Only'] = evaluate_cate_model(
        proxy_only, X_target, tau_target,
        mu0_target, mu1_target, compute_calibration=True
    )
    
    if verbose:
        print(f"  PEHE: {results['Proxy-Only']['pehe']:.4f}")
        print(f"  ATE Error: {results['Proxy-Only']['ate_error']:.4f}")
        if 'mu0_rmse' in results['Proxy-Only']:
            print(f"  μ₀ RMSE: {results['Proxy-Only']['mu0_rmse']:.4f}")
            print(f"  μ₁ RMSE: {results['Proxy-Only']['mu1_rmse']:.4f}")
    
    # =========================================================================
    # 3. Anchor-Only Baseline
    # =========================================================================
    if verbose:
        print("\n" + "-" * 80)
        print("3. Anchor-Only Baseline")
        print("-" * 80)
    
    anchor_only = AnchorOnlyBaseline(option='A', random_state=random_state, verbose=False)
    anchor_only.fit(X_source, A_source, Y_source, c_source,
                    X_target, A_target, Y_target)
    
    results['Anchor-Only'] = evaluate_cate_model(
        anchor_only, X_target, tau_target,
        mu0_target, mu1_target, compute_calibration=True
    )
    
    if verbose:
        print(f"  PEHE: {results['Anchor-Only']['pehe']:.4f}")
        print(f"  ATE Error: {results['Anchor-Only']['ate_error']:.4f}")
        if 'mu0_rmse' in results['Anchor-Only']:
            print(f"  μ₀ RMSE: {results['Anchor-Only']['mu0_rmse']:.4f}")
            print(f"  μ₁ RMSE: {results['Anchor-Only']['mu1_rmse']:.4f}")
    
    # =========================================================================
    # 4. Proposed Method (Full)
    # =========================================================================
    if verbose:
        print("\n" + "-" * 80)
        print("4. Proposed Method (Full)")
        print("-" * 80)
    
    proposed = PlaceboAnchoredDRLearner(option='A', random_state=random_state, verbose=False)
    proposed.fit(X_source, A_source, Y_source, c_source,
                 X_target, A_target, Y_target)
    
    results['Proposed'] = evaluate_cate_model(
        proposed, X_target, tau_target,
        mu0_target, mu1_target, compute_calibration=True
    )
    
    if verbose:
        print(f"  PEHE: {results['Proposed']['pehe']:.4f}")
        print(f"  ATE Error: {results['Proposed']['ate_error']:.4f}")
        if 'mu0_rmse' in results['Proposed']:
            print(f"  μ₀ RMSE: {results['Proposed']['mu0_rmse']:.4f}")
            print(f"  μ₁ RMSE: {results['Proposed']['mu1_rmse']:.4f}")
    
    return results


def run_multiple_experiments(n_runs=10, **kwargs):
    """
    Run multiple experiments and aggregate results.
    
    Returns
    -------
    results : dict
        Mean and std of metrics for each method
    """
    all_results = {
        'No-Transfer': [],
        'Proxy-Only': [],
        'Anchor-Only': [],
        'Proposed': []
    }
    
    for run in range(n_runs):
        print(f"\nRun {run + 1}/{n_runs}...")
        results = run_single_experiment(random_state=42 + run, verbose=False, **kwargs)
        
        for method in all_results.keys():
            all_results[method].append(results[method])
    
    # Aggregate
    aggregated = {}
    for method in all_results.keys():
        metrics = all_results[method][0].keys()
        aggregated[method] = {}
        
        for metric in metrics:
            values = [r[metric] for r in all_results[method]]
            aggregated[method][f'{metric}_mean'] = np.mean(values)
            aggregated[method][f'{metric}_std'] = np.std(values)
    
    return aggregated


def plot_results(results, save_dir='results/ablation'):
    """Create visualization plots."""
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    methods = list(results.keys())
    metrics = ['pehe', 'ate_error', 'mu0_rmse', 'mu1_rmse']
    metric_labels = ['PEHE', 'ATE Error', r'$\mu_0$ RMSE', r'$\mu_1$ RMSE']
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx]
        
        # Extract values
        values = []
        errors = []
        for method in methods:
            if f'{metric}_mean' in results[method]:
                values.append(results[method][f'{metric}_mean'])
                errors.append(results[method][f'{metric}_std'])
            else:
                values.append(np.nan)
                errors.append(0)
        
        # Bar plot
        x = np.arange(len(methods))
        bars = ax.bar(x, values, yerr=errors, capsize=5, alpha=0.7)
        
        # Color bars
        colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']  # Red, orange, green, blue
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xticks(x)
        ax.set_xticklabels(methods, rotation=15, ha='right')
        ax.set_ylabel(label)
        ax.set_title(f'{label} (Lower is Better)')
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_dir}/ablation_comparison.png', dpi=300, bbox_inches='tight')
    print(f"\nSaved: {save_dir}/ablation_comparison.png")
    
    plt.close()


if __name__ == '__main__':
    print("=" * 80)
    print("ABLATION STUDY")
    print("=" * 80)
    
    # Single experiment (verbose)
    print("\n" + "=" * 80)
    print("Running single experiment (verbose)...")
    print("=" * 80)
    
    results_single = run_single_experiment(
        n_source_sites=3,
        n_target=200,
        n_source_per_site=500,
        covariate_shift_scale=1.0,
        random_state=42,
        verbose=True
    )
    
    print("\n" + "=" * 80)
    print("SINGLE RUN RESULTS")
    print("=" * 80)
    compare_methods(results_single)
    
    # Multiple experiments
    print("\n" + "=" * 80)
    print("Running 20 experiments for statistical reliability...")
    print("=" * 80)
    
    results_multi = run_multiple_experiments(
        n_runs=20,
        n_source_sites=3,
        n_target=200,
        n_source_per_site=500,
        covariate_shift_scale=1.0
    )
    
    print("\n" + "=" * 80)
    print("AGGREGATE RESULTS (20 runs)")
    print("=" * 80)
    
    for method in results_multi.keys():
        print(f"\n{method}:")
        for key, value in results_multi[method].items():
            print(f"  {key}: {value:.4f}")
    
    # Plot results
    plot_results(results_multi)
    
    print("\n" + "=" * 80)
    print("ABLATION STUDY COMPLETE")
    print("=" * 80)
