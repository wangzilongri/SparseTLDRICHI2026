#!/usr/bin/env python3
"""
Core Component Ablation Study (Parallel Execution)

Compares:
1. No-Transfer: Target placebo only
2. Proxy-Only: Pooled sources without anchoring
3. Anchor-Only: Anchoring without DR correction
4. Proposed: Full three-stage method

With statistical testing (Friedman, Wilcoxon) and parallel Monte Carlo runs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['mathtext.fontset'] = 'cm'  # Use Computer Modern font for math
matplotlib.rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
import warnings

# Import our modules
from src.data_generator import MultiSiteSimulator
from src.scratch_estimator import PlaceboAnchoredDRLearner
from src.baselines import NoTransferBaseline, ProxyOnlyBaseline, AnchorOnlyBaseline
from src.evaluation import evaluate_all_metrics, statistical_summary, print_statistical_summary


def run_single_iteration(run, n_features, n_effect_modifiers, n_source_sites, 
                        n_target, source_per_site, disconnected, seed):
    """
    Run a single Monte Carlo iteration.
    
    Returns list of results for all methods for this iteration.
    
    NOTE: Each iteration creates fresh model instances with DIFFERENT random states
    to avoid state sharing across parallel workers.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        
        # Initialize simulator
        simulator = MultiSiteSimulator(n_features=n_features, 
                                       n_effect_modifiers=n_effect_modifiers)
        
        # Methods to compare - use run-specific random states
        methods = {
            'No-Transfer': NoTransferBaseline(),
            'Proxy-Only': ProxyOnlyBaseline(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20,
                    random_state=seed + run * 1000,  # ← Different per run!
                    n_jobs=1  # Avoid nested parallelism
                )
            ),
            'Anchor-Only': AnchorOnlyBaseline(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20,
                    random_state=seed + run * 1000 + 1,  # ← Different!
                    n_jobs=1
                )
            ),
            'Proposed (Full)': PlaceboAnchoredDRLearner(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20,
                    random_state=seed + run * 1000 + 2,  # ← Different!
                    n_jobs=1
                ),
                cate_model=RandomForestRegressor(
                    n_estimators=200, max_depth=5, min_samples_leaf=10,
                    random_state=seed + run * 1000 + 3,  # ← Different!
                    n_jobs=1
                ),
                option='B' if disconnected else 'A',
                n_folds_dr=3,
                random_state=seed + run * 1000 + 4,  # ← Different!
                verbose=False
            )
        }
        
        # Generate data
        data = simulator.generate_network(
            n_source_sites=n_source_sites,
            n_target=n_target,
            source_patients_per_site=source_per_site,
            disconnected=disconnected,
            covariate_shift_scale=0.5,
            bias_sparsity=2,
            seed=seed + run
        )
        
        # Pool sources
        X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
        X_t = data['target']['X']
        A_t = data['target']['A']
        Y_t = data['target']['Y']
        prop_t = data['target']['propensity']
        
        # Ground truth
        tau_true = data['target']['tau']
        mu0_true = data['target']['mu_0']
        mu1_true = data['target']['mu_1']
        
        # Evaluate each method
        iteration_results = []
        for method_name, model in methods.items():
            try:
                # Fit
                model.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, prop_t)
                
                # Predict
                tau_pred = model.predict(X_t)
                
                # Get counterfactuals if available
                if hasattr(model, 'predict_counterfactuals'):
                    mu0_pred, mu1_pred = model.predict_counterfactuals(X_t)
                else:
                    mu0_pred, mu1_pred = None, None
                
                # Evaluate
                metrics = evaluate_all_metrics(
                    tau_pred, tau_true, mu0_pred, mu1_pred, mu0_true, mu1_true
                )
                
                iteration_results.append({
                    'Method': method_name,
                    'Run': run,
                    **metrics
                })
                
            except Exception as e:
                # Record failure
                iteration_results.append({
                    'Method': method_name,
                    'Run': run,
                    'PEHE': np.nan,
                    'ATE_Error': np.nan,
                    'Bias_ATE': np.nan,
                    'R2_CATE': np.nan,
                    'Cal_RMSE_mu0': np.nan,
                    'Cal_RMSE_mu1': np.nan
                })
        
        return iteration_results


def run_core_ablation(n_runs=100, n_features=10, n_effect_modifiers=3,
                      n_source_sites=3, n_target=200, source_per_site=500,
                      disconnected=True, seed=42, verbose=True, n_jobs=-1):
    """
    Run core component ablation study with parallel execution.
    
    Parameters:
    -----------
    n_runs : int
        Number of Monte Carlo runs (100 for publication quality)
    n_jobs : int
        Number of parallel jobs (-1 uses all cores)
    """
    
    if verbose:
        print(f"Running ablation study: {n_runs} runs, disconnected={disconnected}")
        print(f"Features: {n_features}, Effect modifiers: {n_effect_modifiers}")
        print(f"Parallel jobs: {n_jobs if n_jobs > 0 else 'all cores'}")
        print("")
    
    # Parallel execution
    all_results = Parallel(n_jobs=n_jobs, verbose=10 if verbose else 0)(
        delayed(run_single_iteration)(
            run, n_features, n_effect_modifiers, n_source_sites,
            n_target, source_per_site, disconnected, seed
        ) for run in range(n_runs)
    )
    
    # Flatten results
    all_results = [item for sublist in all_results for item in sublist]
    
    # Convert to DataFrame
    results_df = pd.DataFrame(all_results)
    
    return results_df


def visualize_results(results_df, save_path='results/ablation_core/ablation_comparison.png'):
    """Create comprehensive visualization of results"""
    
    methods = results_df['Method'].unique()
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    colors = ['#ff9999', '#ffcc99', '#99ccff', '#99ff99']
    
    # PEHE
    pehe_data = [results_df[results_df['Method'] == m]['PEHE'].values for m in methods]
    bp = axes[0].boxplot(pehe_data, tick_labels=methods, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors[:len(methods)]):
        patch.set_facecolor(color)
    axes[0].set_ylabel('PEHE', fontsize=12)
    axes[0].set_title('Precision in HTE Estimation', fontsize=14, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].set_xticklabels(methods, rotation=45, ha='right')
    
    # ATE Error
    ate_data = [results_df[results_df['Method'] == m]['ATE_Error'].values for m in methods]
    bp = axes[1].boxplot(ate_data, tick_labels=methods, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors[:len(methods)]):
        patch.set_facecolor(color)
    axes[1].set_ylabel('ATE Error', fontsize=12)
    axes[1].set_title('Average Treatment Effect Error', fontsize=14, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_xticklabels(methods, rotation=45, ha='right')
    
    # R² CATE
    r2_data = [results_df[results_df['Method'] == m]['R2_CATE'].values for m in methods]
    bp = axes[2].boxplot(r2_data, tick_labels=methods, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors[:len(methods)]):
        patch.set_facecolor(color)
    axes[2].set_ylabel('R² CATE', fontsize=12)
    axes[2].set_title('Heterogeneity Explanation', fontsize=14, fontweight='bold')
    axes[2].grid(axis='y', alpha=0.3)
    axes[2].axhline(y=0, color='red', linestyle='--', alpha=0.5, linewidth=1)
    axes[2].set_xticklabels(methods, rotation=45, ha='right')
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    
    return fig


def main():
    """Main entry point"""
    print("=" * 80)
    print("CORE COMPONENT ABLATION STUDY (PARALLEL)")
    print("=" * 80)
    print()
    
    # Create results directory
    os.makedirs('results/ablation_core', exist_ok=True)
    
    # Run experiment
    results_df = run_core_ablation(
        n_runs=100,  # Publication quality
        n_features=10,
        n_effect_modifiers=3,
        disconnected=True,
        seed=42,
        verbose=True,
        n_jobs=-1  # Use all cores
    )
    
    # Statistical summary
    print("\n")
    print("=" * 80)
    summary = statistical_summary(results_df, metrics=['PEHE', 'ATE_Error', 'R2_CATE'])
    print_statistical_summary(summary)
    
    # Save results
    csv_path = 'results/ablation_core/ablation_results.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"\nResults saved to {csv_path}")
    
    # Save summary statistics as CSV
    summary_path = 'results/ablation_core/summary_statistics.csv'
    summary['descriptive'].to_csv(summary_path)
    print(f"Summary statistics saved to {summary_path}")
    
    # Save pairwise comparisons
    for metric, tests in summary['hypothesis_tests'].items():
        if tests['pairwise'] is not None:
            pairwise_path = f'results/ablation_core/pairwise_{metric.lower()}.csv'
            tests['pairwise'].to_csv(pairwise_path, index=False)
            print(f"Pairwise comparisons ({metric}) saved to {pairwise_path}")
    
    # Visualize
    print("\nGenerating visualizations...")
    fig_path = 'results/ablation_core/ablation_comparison.png'
    fig = visualize_results(results_df, save_path=fig_path)
    
    # Also save individual metric plots
    for metric in ['PEHE', 'ATE_Error', 'R2_CATE']:
        fig_single = plt.figure(figsize=(8, 6))
        ax = fig_single.add_subplot(111)
        methods = results_df['Method'].unique()
        data = [results_df[results_df['Method'] == m][metric].values for m in methods]
        bp = ax.boxplot(data, tick_labels=methods, patch_artist=True)
        colors = ['#ff9999', '#ffcc99', '#99ccff', '#99ff99']
        for patch, color in zip(bp['boxes'], colors[:len(methods)]):
            patch.set_facecolor(color)
        ax.set_ylabel(metric, fontsize=12)
        ax.set_title(f'{metric} Comparison Across Methods', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        ax.set_xticklabels(methods, rotation=45, ha='right')
        plt.tight_layout()
        single_path = f'results/ablation_core/{metric.lower()}_boxplot.png'
        plt.savefig(single_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  {metric} plot saved to {single_path}")
    
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("All results saved to results/ablation_core/")
    print("=" * 80)


if __name__ == '__main__':
    main()
