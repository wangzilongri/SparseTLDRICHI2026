"""
Evaluation Metrics and Statistical Testing

Implements:
- PEHE (Precision in Estimation of Heterogeneous Effects)
- ATE Error
- Calibration RMSE
- Statistical hypothesis tests (Friedman, Wilcoxon)
- Effect sizes (Cohen's d)
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import friedmanchisquare, wilcoxon
from itertools import combinations


def compute_pehe(tau_true, tau_pred):
    """Precision in Estimation of Heterogeneous Effects"""
    return np.sqrt(mean_squared_error(tau_true, tau_pred))


def compute_ate_error(tau_true, tau_pred):
    """Absolute error in average treatment effect"""
    ate_true = np.mean(tau_true)
    ate_pred = np.mean(tau_pred)
    return np.abs(ate_true - ate_pred)


def compute_calibration_rmse(mu_true, mu_pred):
    """Calibration RMSE for outcome models"""
    return np.sqrt(mean_squared_error(mu_true, mu_pred))


def evaluate_all_metrics(tau_true, tau_pred, mu0_true=None, mu0_pred=None,
                         mu1_true=None, mu1_pred=None):
    """
    Comprehensive evaluation metrics.
    
    Returns:
    --------
    metrics : dict with keys:
        - 'PEHE': Precision in Estimation of Heterogeneous Effects
        - 'ATE_Error': Absolute error in average treatment effect
        - 'Bias_ATE': Signed bias in ATE
        - 'R2_CATE': R² for CATE predictions
        - 'Cal_RMSE_mu0': Calibration RMSE for placebo (if provided)
        - 'Cal_RMSE_mu1': Calibration RMSE for treated (if provided)
    """
    # PEHE
    pehe = compute_pehe(tau_true, tau_pred)
    
    # ATE metrics
    ate_true = np.mean(tau_true)
    ate_pred = np.mean(tau_pred)
    ate_error = np.abs(ate_true - ate_pred)
    bias_ate = ate_pred - ate_true
    
    # R² for heterogeneity
    r2_cate = r2_score(tau_true, tau_pred) if np.var(tau_true) > 0 else 0.0
    
    metrics = {
        'PEHE': pehe,
        'ATE_Error': ate_error,
        'Bias_ATE': bias_ate,
        'R2_CATE': r2_cate
    }
    
    # Calibration metrics (if provided)
    if mu0_true is not None and mu0_pred is not None:
        metrics['Cal_RMSE_mu0'] = compute_calibration_rmse(mu0_true, mu0_pred)
    
    if mu1_true is not None and mu1_pred is not None:
        metrics['Cal_RMSE_mu1'] = compute_calibration_rmse(mu1_true, mu1_pred)
    
    return metrics


def cohens_d(group1, group2):
    """Compute Cohen's d effect size"""
    mean_diff = np.mean(group1) - np.mean(group2)
    pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
    return mean_diff / pooled_std if pooled_std > 0 else 0.0


def friedman_test_methods(results_df, metric='PEHE'):
    """
    Friedman test: H0 = all methods perform equally.
    
    Args:
        results_df: DataFrame with columns ['Method', 'Run', 'PEHE', ...]
        metric: which metric to test on
    
    Returns:
        stat, pvalue, effect_size
    """
    methods = results_df['Method'].unique()
    
    # Organize data by method
    method_groups = []
    for method in methods:
        values = results_df[results_df['Method'] == method][metric].values
        method_groups.append(values)
    
    # Friedman test
    stat, pval = friedmanchisquare(*method_groups)
    
    # Effect size (Kendall's W)
    k = len(methods)
    n = len(method_groups[0])
    w = stat / (n * (k - 1))  # Kendall's W
    
    return {
        'statistic': stat,
        'pvalue': pval,
        'effect_size_w': w
    }


def pairwise_wilcoxon(results_df, metric='PEHE', alpha=0.05):
    """
    Pairwise Wilcoxon signed-rank tests with Bonferroni correction.
    
    Returns:
        DataFrame with pairwise comparisons
    """
    methods = results_df['Method'].unique()
    comparisons = []
    
    # Bonferroni correction
    n_comparisons = len(list(combinations(methods, 2)))
    alpha_corrected = alpha / n_comparisons
    
    for m1, m2 in combinations(methods, 2):
        val1 = results_df[results_df['Method'] == m1][metric].values
        val2 = results_df[results_df['Method'] == m2][metric].values
        
        # Wilcoxon signed-rank test
        stat, pval = wilcoxon(val1, val2, alternative='two-sided')
        
        # Cohen's d
        d = cohens_d(val1, val2)
        
        # Interpret effect size
        if np.abs(d) < 0.2:
            effect_interp = 'negligible'
        elif np.abs(d) < 0.5:
            effect_interp = 'small'
        elif np.abs(d) < 0.8:
            effect_interp = 'medium'
        else:
            effect_interp = 'large'
        
        comparisons.append({
            'Method1': m1,
            'Method2': m2,
            'Statistic': stat,
            'P-value': pval,
            'P-value (corrected)': pval * n_comparisons,  # Bonferroni
            'Significant': pval < alpha_corrected,
            'Cohens_d': d,
            'Effect_Size': effect_interp,
            'Mean_Diff': np.mean(val1) - np.mean(val2)
        })
    
    return pd.DataFrame(comparisons)


def statistical_summary(results_df, metrics=['PEHE', 'ATE_Error']):
    """
    Generate complete statistical summary with hypothesis testing.
    
    Args:
        results_df: DataFrame with ['Method', 'Run', metrics...]
        metrics: list of metric names to test
    
    Returns:
        summary: dict with descriptive stats and test results
    """
    summary = {}
    
    # Descriptive statistics
    desc_stats = results_df.groupby('Method')[metrics].agg(['mean', 'std', 'median', 'min', 'max'])
    summary['descriptive'] = desc_stats
    
    # Hypothesis tests for each metric
    summary['hypothesis_tests'] = {}
    for metric in metrics:
        # Friedman test
        friedman_result = friedman_test_methods(results_df, metric)
        
        # Pairwise comparisons (if Friedman significant)
        if friedman_result['pvalue'] < 0.05:
            pairwise_result = pairwise_wilcoxon(results_df, metric)
        else:
            pairwise_result = None
        
        summary['hypothesis_tests'][metric] = {
            'friedman': friedman_result,
            'pairwise': pairwise_result
        }
    
    return summary


def print_statistical_summary(summary):
    """Pretty print statistical summary"""
    print("=" * 80)
    print("STATISTICAL SUMMARY")
    print("=" * 80)
    
    print("\n### Descriptive Statistics ###\n")
    print(summary['descriptive'])
    
    print("\n\n### Hypothesis Tests ###\n")
    for metric, tests in summary['hypothesis_tests'].items():
        print(f"\n--- {metric} ---")
        
        friedman = tests['friedman']
        print(f"Friedman test: χ² = {friedman['statistic']:.3f}, "
              f"p = {friedman['pvalue']:.6f}, "
              f"W = {friedman['effect_size_w']:.3f}")
        
        if friedman['pvalue'] < 0.05:
            print("  ✓ Methods differ significantly (p < 0.05)")
            
            if tests['pairwise'] is not None:
                print("\nPairwise comparisons (Bonferroni corrected):")
                df_pair = tests['pairwise']
                for _, row in df_pair.iterrows():
                    sig_marker = "***" if row['Significant'] else ""
                    print(f"  {row['Method1']} vs {row['Method2']}: "
                          f"d = {row['Cohens_d']:.3f} ({row['Effect_Size']}), "
                          f"p = {row['P-value (corrected)']:.6f} {sig_marker}")
        else:
            print("  ✗ No significant difference (p >= 0.05)")
