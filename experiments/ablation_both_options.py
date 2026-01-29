"""
Core Component Ablation Study - Both Options A and B
=====================================================

This script runs ablation studies for BOTH:
- Option A: Connected target (has treated arm, can estimate both δ₀ and δ₁)
- Option B: Disconnected target (no treated arm, assumes shared bias δ₁ = δ₀)

Key Differences:
- Option A: Anchoring should improve BOTH calibration AND CATE
- Option B: Anchoring improves calibration but CATE is preserved (corrections cancel)

See docs/DESIGN.md for theoretical details.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
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
                        n_target, source_per_site, disconnected, option_name, seed):
    """
    Run a single Monte Carlo iteration for one option (A or B).
    
    Args:
        option_name: 'A' or 'B' for labeling
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
                    random_state=seed + run * 1000,
                    n_jobs=1
                )
            ),
            'Anchor-Only': AnchorOnlyBaseline(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20,
                    random_state=seed + run * 1000 + 1,
                    n_jobs=1
                )
            ),
            'Proposed (Full)': PlaceboAnchoredDRLearner(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20,
                    random_state=seed + run * 1000 + 2,
                    n_jobs=1
                ),
                cate_model=RandomForestRegressor(
                    n_estimators=200, max_depth=5, min_samples_leaf=10,
                    random_state=seed + run * 1000 + 3,
                    n_jobs=1
                ),
                option='B' if disconnected else 'A',
                n_folds_dr=3,
                random_state=seed + run * 1000 + 4,
                verbose=False
            )
        }
        
        # Generate data
        data = simulator.generate_network(
            n_source_sites=n_source_sites,
            n_target=n_target,
            source_patients_per_site=source_per_site,
            disconnected=disconnected,
            seed=seed + run
        )
        
        # Pool source data
        X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
        X_t, A_t, Y_t = data['target']['X'], data['target']['A'], data['target']['Y']
        prop_t = data['target']['propensity']
        
        # Ground truth
        tau_true = data['target']['tau']
        mu0_true = data['target']['mu_0']
        mu1_true = data['target']['mu_1']
        
        # Evaluate each method
        results = []
        for method_name, model in methods.items():
            model.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, prop_t)
            tau_pred = model.predict(X_t)
            
            # Compute counterfactuals if available
            if hasattr(model, 'predict_counterfactuals'):
                mu0_pred, mu1_pred = model.predict_counterfactuals(X_t)
            else:
                mu0_pred, mu1_pred = None, None
            
            metrics = evaluate_all_metrics(
                tau_pred, tau_true, mu0_pred, mu1_pred, mu0_true, mu1_true
            )
            
            results.append({
                'Run': run,
                'Method': method_name,
                'Option': option_name,
                **metrics
            })
        
        return results


def run_option_comparison(n_runs=100, n_features=10, n_effect_modifiers=3,
                         n_source_sites=3, n_target=500, source_per_site=500,
                         seed=42, verbose=True, n_jobs=-1):
    """
    Run ablation for BOTH Option A and Option B.
    
    Returns:
        results_a: DataFrame with Option A results
        results_b: DataFrame with Option B results
        combined: Combined DataFrame with all results
    """
    print("="*80)
    print("OPTION A vs OPTION B COMPARISON")
    print("="*80)
    print()
    
    # Run Option A (connected target)
    print("--- OPTION A: Connected Target (has treated arm) ---")
    print(f"Running {n_runs} iterations with disconnected=False...")
    print()
    
    all_results_a = Parallel(n_jobs=n_jobs, verbose=10 if verbose else 0)(
        delayed(run_single_iteration)(
            run, n_features, n_effect_modifiers, n_source_sites,
            n_target, source_per_site, disconnected=False, 
            option_name='A', seed=seed
        ) for run in range(n_runs)
    )
    
    # Flatten results
    results_a = []
    for run_results in all_results_a:
        results_a.extend(run_results)
    results_a = pd.DataFrame(results_a)
    
    # Run Option B (disconnected target)
    print()
    print("--- OPTION B: Disconnected Target (no treated arm) ---")
    print(f"Running {n_runs} iterations with disconnected=True...")
    print()
    
    all_results_b = Parallel(n_jobs=n_jobs, verbose=10 if verbose else 0)(
        delayed(run_single_iteration)(
            run, n_features, n_effect_modifiers, n_source_sites,
            n_target, source_per_site, disconnected=True, 
            option_name='B', seed=seed + 10000  # Different seed
        ) for run in range(n_runs)
    )
    
    # Flatten results
    results_b = []
    for run_results in all_results_b:
        results_b.extend(run_results)
    results_b = pd.DataFrame(results_b)
    
    # Combine
    combined = pd.concat([results_a, results_b], ignore_index=True)
    
    return results_a, results_b, combined


def analyze_and_save(results_a, results_b, combined, output_dir='results/ablation_options'):
    """
    Analyze results and save outputs.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print()
    print("="*80)
    print("STATISTICAL ANALYSIS")
    print("="*80)
    
    # Save raw results
    combined.to_csv(f'{output_dir}/ablation_both_options.csv', index=False)
    results_a.to_csv(f'{output_dir}/option_a_results.csv', index=False)
    results_b.to_csv(f'{output_dir}/option_b_results.csv', index=False)
    
    # Compute summary statistics for each option
    for option_name, df in [('A', results_a), ('B', results_b)]:
        print()
        print(f"{'='*80}")
        print(f"OPTION {option_name}: {'Connected Target' if option_name == 'A' else 'Disconnected Target'}")
        print(f"{'='*80}")
        
        stats = statistical_summary(df)
        print_statistical_summary(stats)
        
        # Save statistics (stats is a dict with keys: 'descriptive', 'tests', 'pairwise')
        if 'descriptive' in stats:
            stats['descriptive'].to_csv(f'{output_dir}/option_{option_name.lower()}_summary.csv')
        if 'pairwise' in stats:
            for metric in ['pehe', 'ate_error']:
                if metric in stats['pairwise']:
                    stats['pairwise'][metric].to_csv(
                        f'{output_dir}/option_{option_name.lower()}_pairwise_{metric}.csv'
                    )
    
    # Create visualizations
    print()
    print("Generating visualizations...")
    create_comparison_plots(results_a, results_b, output_dir)
    
    # Create summary comparison
    create_option_summary(results_a, results_b, output_dir)
    
    print()
    print(f"All results saved to {output_dir}/")


def create_comparison_plots(results_a, results_b, output_dir):
    """
    Create side-by-side comparison plots for Option A vs B.
    """
    metrics = ['PEHE', 'ATE_Error', 'R2_CATE']
    metric_labels = {
        'PEHE': 'PEHE (lower is better)',
        'ATE_Error': 'ATE Error (lower is better)',
        'R2_CATE': 'R² CATE (higher is better)'
    }
    
    # Combined plot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    for col, metric in enumerate(metrics):
        # Option A (top row)
        ax = axes[0, col]
        data_a = results_a.pivot(index='Run', columns='Method', values=metric)
        data_a.boxplot(ax=ax)
        ax.set_title(f'Option A: {metric_labels[metric]}', fontsize=12, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('Value', fontsize=10)
        ax.tick_params(axis='x', rotation=45, labelsize=9)
        ax.grid(axis='y', alpha=0.3)
        
        # Option B (bottom row)
        ax = axes[1, col]
        data_b = results_b.pivot(index='Run', columns='Method', values=metric)
        data_b.boxplot(ax=ax)
        ax.set_title(f'Option B: {metric_labels[metric]}', fontsize=12, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('Value', fontsize=10)
        ax.tick_params(axis='x', rotation=45, labelsize=9)
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/option_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Comparison plot saved to {output_dir}/option_comparison.png")
    
    # Individual metric comparisons
    for metric in metrics:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Option A
        ax = axes[0]
        data_a = results_a.pivot(index='Run', columns='Method', values=metric)
        data_a.boxplot(ax=ax)
        ax.set_title(f'Option A (Connected): {metric_labels[metric]}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Method', fontsize=11)
        ax.set_ylabel('Value', fontsize=11)
        ax.tick_params(axis='x', rotation=45, labelsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        # Option B
        ax = axes[1]
        data_b = results_b.pivot(index='Run', columns='Method', values=metric)
        data_b.boxplot(ax=ax)
        ax.set_title(f'Option B (Disconnected): {metric_labels[metric]}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Method', fontsize=11)
        ax.set_ylabel('Value', fontsize=11)
        ax.tick_params(axis='x', rotation=45, labelsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/{metric.lower()}_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  {metric} comparison saved to {output_dir}/{metric.lower()}_comparison.png")


def create_option_summary(results_a, results_b, output_dir):
    """
    Create a summary table comparing Option A vs B.
    """
    summary_data = []
    
    for method in ['No-Transfer', 'Proxy-Only', 'Anchor-Only', 'Proposed (Full)']:
        # Option A
        subset_a = results_a[results_a['Method'] == method]
        # Option B
        subset_b = results_b[results_b['Method'] == method]
        
        summary_data.append({
            'Method': method,
            'Option': 'A (Connected)',
            'PEHE': f"{subset_a['PEHE'].mean():.3f} ± {subset_a['PEHE'].std():.3f}",
            'ATE_Error': f"{subset_a['ATE_Error'].mean():.3f} ± {subset_a['ATE_Error'].std():.3f}",
            'R2_CATE_median': f"{subset_a['R2_CATE'].median():.3f}",
            'Cal_RMSE_mu0': f"{subset_a['Cal_RMSE_mu0'].mean():.3f}",
        })
        
        summary_data.append({
            'Method': method,
            'Option': 'B (Disconnected)',
            'PEHE': f"{subset_b['PEHE'].mean():.3f} ± {subset_b['PEHE'].std():.3f}",
            'ATE_Error': f"{subset_b['ATE_Error'].mean():.3f} ± {subset_b['ATE_Error'].std():.3f}",
            'R2_CATE_median': f"{subset_b['R2_CATE'].median():.3f}",
            'Cal_RMSE_mu0': f"{subset_b['Cal_RMSE_mu0'].mean():.3f}",
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(f'{output_dir}/option_summary_table.csv', index=False)
    
    print()
    print("="*80)
    print("OPTION COMPARISON SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))
    print()


def main():
    """
    Main execution function.
    """
    results_a, results_b, combined = run_option_comparison(
        n_runs=100,
        n_features=10,
        n_effect_modifiers=3,
        seed=42,
        verbose=True,
        n_jobs=-1
    )
    
    analyze_and_save(results_a, results_b, combined)
    
    print()
    print("="*80)
    print("EXPERIMENT COMPLETE")
    print("="*80)
    print("See results/ablation_options/ for all outputs")
    print()


if __name__ == '__main__':
    main()
