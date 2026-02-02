"""
Benchmark Aggregation: Statistical aggregation and hypothesis testing.

This module provides functions for aggregating rep-level results into
summary statistics with proper uncertainty quantification and paired tests.
"""

import os
import sys
import warnings
from typing import Optional, Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_schema import (
    CORE_METRIC_COLS, DIAGNOSTIC_COLS, SCENARIO_PARAM_COLS,
    validate_results_rep
)


# =============================================================================
# Aggregation Functions
# =============================================================================

def aggregate_results(
    df_rep: pd.DataFrame,
    group_cols: Optional[List[str]] = None,
    metric_cols: Optional[List[str]] = None,
    reference_method: str = 'ProxyOnly',
    compute_deltas: bool = True,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Aggregate rep-level results to summary statistics.
    
    Parameters
    ----------
    df_rep : pd.DataFrame
        Rep-level results (results_rep schema)
    group_cols : list of str, optional
        Columns to group by. Default: benchmark_id, scenario_id, method, feasibility
        plus all scenario parameters.
    metric_cols : list of str, optional
        Metrics to aggregate. Default: CORE_METRIC_COLS
    reference_method : str
        Reference method for paired comparisons
    compute_deltas : bool
        Whether to compute paired deltas vs reference
    alpha : float
        Significance level for tests
        
    Returns
    -------
    pd.DataFrame
        Aggregated results (results_agg schema)
    """
    if metric_cols is None:
        # Use columns that exist and are numeric
        available_metrics = [c for c in CORE_METRIC_COLS + DIAGNOSTIC_COLS 
                           if c in df_rep.columns and pd.api.types.is_numeric_dtype(df_rep[c])]
        metric_cols = available_metrics
    
    if group_cols is None:
        # Default grouping
        id_cols = ['benchmark_id', 'scenario_id', 'method', 'feasibility']
        param_cols = [c for c in SCENARIO_PARAM_COLS if c in df_rep.columns]
        group_cols = [c for c in id_cols + param_cols if c in df_rep.columns]
    
    # Basic aggregation
    agg_dict = {}
    for col in metric_cols:
        agg_dict[f'{col}_mean'] = (col, lambda x: np.nanmean(x))
        agg_dict[f'{col}_sd'] = (col, lambda x: np.nanstd(x, ddof=1))
        agg_dict[f'{col}_median'] = (col, lambda x: np.nanmedian(x))
        agg_dict[f'{col}_n'] = (col, lambda x: np.sum(~np.isnan(x)))
    
    # Perform aggregation
    df_agg = df_rep.groupby(group_cols, dropna=False).agg(**agg_dict).reset_index()
    
    # Compute paired deltas
    if compute_deltas and reference_method in df_rep['method'].unique():
        df_agg = _add_paired_deltas(
            df_agg, df_rep, 
            group_cols=[c for c in group_cols if c not in ['method', 'feasibility']],
            metric_cols=metric_cols,
            reference_method=reference_method,
            alpha=alpha
        )
    
    return df_agg


def _add_paired_deltas(
    df_agg: pd.DataFrame,
    df_rep: pd.DataFrame,
    group_cols: List[str],
    metric_cols: List[str],
    reference_method: str,
    alpha: float
) -> pd.DataFrame:
    """Add paired delta statistics vs reference method."""
    
    # For each (scenario, rep), compute method - reference
    pivot_cols = group_cols + ['rep']
    
    for metric in metric_cols:
        if metric not in df_rep.columns:
            continue
        
        # Skip if reference method doesn't have this metric
        ref_data = df_rep[df_rep['method'] == reference_method][metric]
        if ref_data.isna().all():
            continue
        
        delta_col = f'{metric}_delta_vs_{reference_method}'
        p_col = f'{metric}_p_value'
        q_col = f'{metric}_q_value'
        
        # Initialize columns
        df_agg[delta_col] = np.nan
        df_agg[p_col] = np.nan
        
        # Compute deltas for each method
        for method in df_agg['method'].unique():
            if method == reference_method:
                continue
            
            # Get paired observations
            method_df = df_rep[df_rep['method'] == method]
            ref_df = df_rep[df_rep['method'] == reference_method]
            
            # For each scenario
            for scenario_id in df_agg['scenario_id'].unique():
                method_vals = method_df[method_df['scenario_id'] == scenario_id][['rep', metric]]
                ref_vals = ref_df[ref_df['scenario_id'] == scenario_id][['rep', metric]]
                
                if method_vals.empty or ref_vals.empty:
                    continue
                
                # Merge on rep
                merged = method_vals.merge(ref_vals, on='rep', suffixes=('_method', '_ref'))
                merged = merged.dropna()
                
                if len(merged) < 2:
                    continue
                
                deltas = merged[f'{metric}_method'] - merged[f'{metric}_ref']
                
                # Mean delta
                mean_delta = deltas.mean()
                
                # Paired t-test (or Wilcoxon if non-normal)
                try:
                    # Use Wilcoxon signed-rank for robustness
                    if len(deltas) >= 10:
                        stat, p_val = stats.wilcoxon(deltas, alternative='two-sided')
                    else:
                        # t-test for small samples
                        stat, p_val = stats.ttest_1samp(deltas, 0)
                except Exception:
                    p_val = np.nan
                
                # Update aggregated df
                mask = (df_agg['method'] == method) & (df_agg['scenario_id'] == scenario_id)
                df_agg.loc[mask, delta_col] = mean_delta
                df_agg.loc[mask, p_col] = p_val
        
        # Holm correction within benchmark
        df_agg[q_col] = _holm_correction(df_agg[p_col].values, alpha)
    
    return df_agg


def _holm_correction(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """
    Apply Holm-Bonferroni correction for multiple comparisons.
    
    Returns adjusted p-values (q-values).
    """
    n = len(p_values)
    q_values = np.full(n, np.nan)
    
    # Get valid (non-nan) p-values
    valid_mask = ~np.isnan(p_values)
    if not valid_mask.any():
        return q_values
    
    valid_p = p_values[valid_mask]
    m = len(valid_p)
    
    # Sort p-values
    sorted_idx = np.argsort(valid_p)
    sorted_p = valid_p[sorted_idx]
    
    # Holm correction: p_i * (m - i + 1)
    adjusted = np.zeros(m)
    cummax = 0
    for i, p in enumerate(sorted_p):
        adj_p = p * (m - i)
        adj_p = max(adj_p, cummax)  # Enforce monotonicity
        adj_p = min(adj_p, 1.0)     # Cap at 1
        adjusted[i] = adj_p
        cummax = adj_p
    
    # Unsort
    unsorted = np.zeros(m)
    unsorted[sorted_idx] = adjusted
    
    # Put back
    q_values[valid_mask] = unsorted
    
    return q_values


# =============================================================================
# Summary Statistics
# =============================================================================

def compute_summary_table(
    df_agg: pd.DataFrame,
    metrics: List[str] = ['pehe', 'ate_abs_err', 'mu0_rmse'],
    reference_method: str = 'ProxyOnly',
    include_delta: bool = True
) -> pd.DataFrame:
    """
    Generate a clean summary table for reporting.
    
    Parameters
    ----------
    df_agg : pd.DataFrame
        Aggregated results
    metrics : list of str
        Metrics to include
    reference_method : str
        Reference method for delta columns
    include_delta : bool
        Include delta and significance columns
        
    Returns
    -------
    pd.DataFrame
        Clean summary table
    """
    # Select columns
    cols = ['scenario_id', 'method', 'feasibility']
    
    for m in metrics:
        mean_col = f'{m}_mean'
        sd_col = f'{m}_sd'
        n_col = f'{m}_n'
        
        if mean_col in df_agg.columns:
            cols.append(mean_col)
        if sd_col in df_agg.columns:
            cols.append(sd_col)
        
        if include_delta:
            delta_col = f'{m}_delta_vs_{reference_method}'
            q_col = f'{m}_q_value'
            if delta_col in df_agg.columns:
                cols.append(delta_col)
            if q_col in df_agg.columns:
                cols.append(q_col)
    
    # Filter to existing columns
    cols = [c for c in cols if c in df_agg.columns]
    
    return df_agg[cols].copy()


def format_mean_sd(mean: float, sd: float, decimals: int = 3) -> str:
    """Format mean ± sd as string."""
    if np.isnan(mean):
        return "N/A"
    if np.isnan(sd):
        return f"{mean:.{decimals}f}"
    return f"{mean:.{decimals}f} ± {sd:.{decimals}f}"


def format_significance(q_value: float, alpha: float = 0.05) -> str:
    """Format significance indicator."""
    if np.isnan(q_value):
        return ""
    if q_value < 0.001:
        return "***"
    if q_value < 0.01:
        return "**"
    if q_value < alpha:
        return "*"
    return ""


def create_latex_table(
    df_agg: pd.DataFrame,
    metrics: List[str] = ['pehe', 'mu0_rmse'],
    sweep_col: Optional[str] = None,
    reference_method: str = 'ProxyOnly',
    caption: str = "Benchmark Results",
    label: str = "tab:results"
) -> str:
    """
    Generate LaTeX table from aggregated results.
    
    Parameters
    ----------
    df_agg : pd.DataFrame
        Aggregated results
    metrics : list of str
        Metrics to include
    sweep_col : str, optional
        Sweep parameter column (e.g., 'm0')
    reference_method : str
        Reference for significance stars
        
    Returns
    -------
    str
        LaTeX table code
    """
    # Determine sweep values
    if sweep_col and sweep_col in df_agg.columns:
        sweep_vals = sorted(df_agg[sweep_col].unique())
    else:
        sweep_vals = [None]
        sweep_col = None
    
    methods = df_agg['method'].unique()
    
    # Build table
    n_cols = 2 + len(metrics)  # method + feasibility + metrics
    if sweep_col:
        n_cols += 1
    
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{" + caption + "}")
    lines.append(r"\label{" + label + "}")
    
    # Column spec
    col_spec = "l" * n_cols
    lines.append(r"\begin{tabular}{" + col_spec + "}")
    lines.append(r"\toprule")
    
    # Header
    header = ["Method", "Feasibility"]
    if sweep_col:
        header.insert(0, sweep_col)
    for m in metrics:
        header.append(m.upper().replace('_', ' '))
    lines.append(" & ".join(header) + r" \\")
    lines.append(r"\midrule")
    
    # Data rows
    for sweep_val in sweep_vals:
        for method in methods:
            if sweep_col:
                mask = (df_agg['method'] == method) & (df_agg[sweep_col] == sweep_val)
            else:
                mask = (df_agg['method'] == method)
            
            row_df = df_agg[mask]
            if row_df.empty:
                continue
            
            row = row_df.iloc[0]
            
            cells = [method, row.get('feasibility', 'N/A')]
            if sweep_col:
                cells.insert(0, str(sweep_val))
            
            for m in metrics:
                mean_val = row.get(f'{m}_mean', np.nan)
                sd_val = row.get(f'{m}_sd', np.nan)
                q_val = row.get(f'{m}_q_value', np.nan)
                
                cell = format_mean_sd(mean_val, sd_val)
                sig = format_significance(q_val)
                if sig and method != reference_method:
                    cell += f" {sig}"
                cells.append(cell)
            
            lines.append(" & ".join(cells) + r" \\")
        
        if sweep_col and sweep_val != sweep_vals[-1]:
            lines.append(r"\midrule")
    
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


# =============================================================================
# Ranking and Best Method Selection
# =============================================================================

def find_best_methods(
    df_agg: pd.DataFrame,
    metrics: List[str] = ['pehe', 'ate_abs_err', 'mu0_rmse'],
    lower_is_better: Optional[Dict[str, bool]] = None,
    feasibility_filter: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Find best method for each metric.
    
    Parameters
    ----------
    df_agg : pd.DataFrame
        Aggregated results
    metrics : list of str
        Metrics to consider
    lower_is_better : dict, optional
        Dict of metric -> bool. Default: all True
    feasibility_filter : str, optional
        Only consider methods with this feasibility
        
    Returns
    -------
    dict
        {metric: {'method': best_method, 'value': best_value, ...}}
    """
    if lower_is_better is None:
        lower_is_better = {m: True for m in metrics}
    
    df = df_agg.copy()
    if feasibility_filter:
        df = df[df['feasibility'] == feasibility_filter]
    
    results = {}
    for metric in metrics:
        mean_col = f'{metric}_mean'
        if mean_col not in df.columns:
            continue
        
        if lower_is_better.get(metric, True):
            best_idx = df[mean_col].idxmin()
        else:
            best_idx = df[mean_col].idxmax()
        
        if pd.isna(best_idx):
            continue
        
        best_row = df.loc[best_idx]
        results[metric] = {
            'method': best_row['method'],
            'value': best_row[mean_col],
            'sd': best_row.get(f'{metric}_sd', np.nan),
            'scenario_id': best_row.get('scenario_id')
        }
    
    return results


def compute_method_rankings(
    df_agg: pd.DataFrame,
    metrics: List[str] = ['pehe', 'ate_abs_err', 'mu0_rmse'],
    lower_is_better: Optional[Dict[str, bool]] = None
) -> pd.DataFrame:
    """
    Compute method rankings for each metric.
    
    Returns DataFrame with method as rows, metrics as columns,
    values are average ranks (lower = better).
    """
    if lower_is_better is None:
        lower_is_better = {m: True for m in metrics}
    
    rankings = []
    
    for metric in metrics:
        mean_col = f'{metric}_mean'
        if mean_col not in df_agg.columns:
            continue
        
        # Rank within each scenario
        for scenario_id in df_agg['scenario_id'].unique():
            scenario_df = df_agg[df_agg['scenario_id'] == scenario_id].copy()
            
            ascending = lower_is_better.get(metric, True)
            scenario_df['rank'] = scenario_df[mean_col].rank(ascending=ascending)
            
            for _, row in scenario_df.iterrows():
                rankings.append({
                    'method': row['method'],
                    'metric': metric,
                    'scenario_id': scenario_id,
                    'rank': row['rank']
                })
    
    if not rankings:
        return pd.DataFrame()
    
    rank_df = pd.DataFrame(rankings)
    
    # Average rank per method per metric
    avg_ranks = rank_df.groupby(['method', 'metric'])['rank'].mean().unstack()
    
    return avg_ranks


# =============================================================================
# I/O
# =============================================================================

def save_aggregated_results(
    df_agg: pd.DataFrame,
    output_dir: str,
    benchmark_id: str,
    formats: List[str] = ['csv', 'latex']
) -> Dict[str, str]:
    """
    Save aggregated results in multiple formats.
    
    Returns dict of format -> filepath.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = {}
    
    if 'csv' in formats:
        path = os.path.join(output_dir, f"results_agg_{benchmark_id}.csv")
        df_agg.to_csv(path, index=False)
        paths['csv'] = path
    
    if 'latex' in formats:
        path = os.path.join(output_dir, f"results_agg_{benchmark_id}.tex")
        latex = create_latex_table(df_agg, caption=f"{benchmark_id} Results")
        with open(path, 'w') as f:
            f.write(latex)
        paths['latex'] = path
    
    return paths


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate benchmark results")
    parser.add_argument('input', type=str, help='Input CSV (results_rep)')
    parser.add_argument('--output', type=str, default=None, help='Output directory')
    parser.add_argument('--reference', type=str, default='ProxyOnly', help='Reference method')
    
    args = parser.parse_args()
    
    # Load
    df_rep = pd.read_csv(args.input)
    print(f"Loaded {len(df_rep)} rows from {args.input}")
    
    # Aggregate
    df_agg = aggregate_results(df_rep, reference_method=args.reference)
    print(f"Aggregated to {len(df_agg)} rows")
    
    # Save
    if args.output:
        benchmark_id = df_rep['benchmark_id'].iloc[0] if 'benchmark_id' in df_rep.columns else 'benchmark'
        paths = save_aggregated_results(df_agg, args.output, benchmark_id)
        print(f"Saved: {paths}")
    else:
        # Print summary
        print("\nSummary:")
        summary = compute_summary_table(df_agg)
        print(summary.to_string())
        
        print("\nBest methods:")
        best = find_best_methods(df_agg)
        for metric, info in best.items():
            print(f"  {metric}: {info['method']} ({info['value']:.4f})")
