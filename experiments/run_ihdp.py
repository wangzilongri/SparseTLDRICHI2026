#!/usr/bin/env python
"""
Run IHDP Semi-Synthetic Experiments

This script runs the IHDP experiments and generates tables for the paper.

Usage:
    # Quick test (5 reps)
    python experiments/run_ihdp.py --quick
    
    # Full run (50 reps, parallel)
    python experiments/run_ihdp.py --full --n_jobs -1
    
    # Specific sweep
    python experiments/run_ihdp.py --sweep ihdp_connected --n_rep 50
    
    # Generate tables only (from existing results)
    python experiments/run_ihdp.py --tables_only --output results/ihdp

    # If results are in separate folders (e.g. from remote runs), use parent path:
    #   results/IHDP connected/results_agg_ihdp_connected_sweep.csv
    #   results/IHDP disconnected/results_agg_ihdp_disconnected_sweep.csv
    python experiments/run_ihdp.py --tables_only --output results

    # Run only the A6 diagnostic (no estimator fitting); writes A_IHDP_A6_Diagnostic.tex
    python experiments/run_ihdp.py --diagnostic_only --n_rep 50
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ihdp_sweeps import (
    run_ihdp_sweep, run_ihdp_a6_diagnostic_only,
    IHDP_SWEEP_CONFIGS,
    IHDP_METHODS_OPTION_A, IHDP_METHODS_OPTION_B
)


# =============================================================================
# TABLE GENERATION
# =============================================================================

def _find_ihdp_agg_file(results_dir: str, filename: str) -> str:
    """
    Locate an IHDP aggregated CSV, checking results_dir and common subfolders.
    Remote runs may place connected/disconnected results in separate folders.
    """
    candidates = [
        os.path.join(results_dir, filename),
        os.path.join(results_dir, 'IHDP connected', filename),
        os.path.join(results_dir, 'ihdp_connected', filename),
        os.path.join(results_dir, 'IHDP disconnected', filename),
        os.path.join(results_dir, 'ihdp_disconnected', filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return os.path.join(results_dir, filename)  # return default for error message


def generate_ihdp_latex_tables(results_dir: str, output_dir: str) -> None:
    """
    Generate LaTeX tables from IHDP results.
    
    Looks for aggregated CSVs in results_dir or subfolders
    "IHDP connected" / "ihdp_connected" and "IHDP disconnected" / "ihdp_disconnected".
    
    Creates:
    - P3_IHDP_Connected_PEHE.tex: Main text table for connected regime
    - P3_IHDP_Disconnected_PEHE.tex: Main text table for disconnected regime
    - Appendix: A*_IHDP_Connected_FullMetrics.tex, A*_IHDP_Disconnected_FullMetrics.tex
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Method display names (consistent with paper)
    METHOD_DISPLAY = {
        'TargetOnlyDR': 'TargetOnly',
        'ProxyOnly': 'ProxyOnly',
        'AnchorOnly': 'AnchorOnly',
        'AnchorPlugin': 'AnchorPlugin',
        'IPWTransport': 'IPW-Transport',
        'EntropyBalancing': 'EntropyBal',
        'OutcomeModelTransport': 'OM-Transport',
        'Glmtrans_Auto': 'Proposed',
        'Glmtrans_DR_CrossFit': 'Proposed-CF',
        'Glmtrans_OptionB': 'Proposed-B',
    }
    
    # Primary metrics for main tables
    PRIMARY_METRICS = ['pehe', 'ate_abs_err', 'tau_corr', 'policy_regret', 'tau_ece']
    
    # =========================================================================
    # Connected regime: main PEHE table
    # =========================================================================
    connected_file = _find_ihdp_agg_file(results_dir, 'results_agg_ihdp_connected_sweep.csv')
    if os.path.exists(connected_file):
        df = pd.read_csv(connected_file)
        
        _generate_pehe_table(
            df=df,
            output_path=os.path.join(output_dir, 'P3_IHDP_Connected_PEHE.tex'),
            caption='IHDP connected regime: PEHE across target budgets (mean $\\pm$ SD, 50 realizations).',
            label='tab:ihdp_connected_pehe',
            method_display=METHOD_DISPLAY,
            budget_col='m0',
            use_tuples=True,
        )
        print(f"Generated: P3_IHDP_Connected_PEHE.tex")
        
        # Appendix: full metrics for connected
        _generate_appendix_full_metrics(
            df=df,
            output_path=os.path.join(output_dir, 'A_IHDP_Connected_FullMetrics.tex'),
            caption='IHDP connected regime: full metrics (PEHE, ATE error, Spearman, Policy regret, ECE).',
            label='tab:ihdp_connected_appendix',
            method_display=METHOD_DISPLAY,
            use_tuples=True,
        )
        print(f"Generated: A_IHDP_Connected_FullMetrics.tex")
    else:
        print(f"Warning: {connected_file} not found")
    
    # =========================================================================
    # Disconnected regime: main PEHE table
    # =========================================================================
    disconnected_file = _find_ihdp_agg_file(results_dir, 'results_agg_ihdp_disconnected_sweep.csv')
    if os.path.exists(disconnected_file):
        df = pd.read_csv(disconnected_file)
        
        _generate_pehe_table(
            df=df,
            output_path=os.path.join(output_dir, 'P3_IHDP_Disconnected_PEHE.tex'),
            caption='IHDP disconnected regime ($m_1=0$): PEHE across placebo budgets (mean $\\pm$ SD, 50 realizations).',
            label='tab:ihdp_disconnected_pehe',
            method_display=METHOD_DISPLAY,
            budget_col='m0',
            use_tuples=False,
        )
        print(f"Generated: P3_IHDP_Disconnected_PEHE.tex")
        
        # Appendix: full metrics for disconnected
        _generate_appendix_full_metrics(
            df=df,
            output_path=os.path.join(output_dir, 'A_IHDP_Disconnected_FullMetrics.tex'),
            caption='IHDP disconnected regime ($m_1=0$): full metrics.',
            label='tab:ihdp_disconnected_appendix',
            method_display=METHOD_DISPLAY,
            use_tuples=False,
        )
        print(f"Generated: A_IHDP_Disconnected_FullMetrics.tex")
    else:
        print(f"Warning: {disconnected_file} not found")
    
    # Screening validity (if raw rep-level results with diagnostics exist)
    _generate_screening_validity_if_available(results_dir, output_dir)
    # A6 diagnostic: placebo screening vs CATE transportability (disconnected)
    _generate_a6_diagnostic_if_available(results_dir, output_dir)


def _generate_pehe_table(
    df: pd.DataFrame,
    output_path: str,
    caption: str,
    label: str,
    method_display: dict,
    budget_col: str = 'm0',
    use_tuples: bool = False,
    metric: str = 'pehe'
) -> None:
    """Generate a compact PEHE table."""
    
    # Get unique budget values
    if use_tuples and 'm1' in df.columns:
        # Create tuple column for display
        df = df.copy()
        df['budget_tuple'] = df.apply(lambda r: f"({int(r['m0'])},{int(r['m1'])})", axis=1)
        budget_values = df['budget_tuple'].unique()
        budget_values = sorted(budget_values, key=lambda x: eval(x))  # Sort by tuple
        budget_display = budget_values
    else:
        budget_values = sorted(df[budget_col].unique())
        budget_display = [str(int(v)) for v in budget_values]
    
    # Get methods in display order
    methods_in_data = df['method'].unique()
    methods_ordered = [m for m in method_display.keys() if m in methods_in_data]
    
    # Build table data
    rows = []
    for method in methods_ordered:
        row_data = [method_display.get(method, method)]
        
        for i, budget in enumerate(budget_values):
            if use_tuples and 'm1' in df.columns:
                mask = df['budget_tuple'] == budget
            else:
                mask = df[budget_col] == budget
            
            method_mask = mask & (df['method'] == method)
            subset = df[method_mask]
            
            if len(subset) == 0:
                row_data.append('--')
                continue
            
            # Get mean and SD
            mean_col = f'{metric}_mean' if f'{metric}_mean' in subset.columns else metric
            sd_col = f'{metric}_sd' if f'{metric}_sd' in subset.columns else f'{metric}_std'
            
            if mean_col in subset.columns:
                mean_val = subset[mean_col].values[0]
                sd_val = subset[sd_col].values[0] if sd_col in subset.columns else 0
                
                if pd.isna(mean_val):
                    row_data.append('--')
                else:
                    sd_str = f'{sd_val:.2f}' if not (pd.isna(sd_val) or np.isnan(sd_val)) else '--'
                    row_data.append(f'{mean_val:.2f}{{\\tiny$\\pm${sd_str}}}')
            else:
                row_data.append('--')
        
        rows.append(row_data)
    
    # Find best values per column (lowest PEHE)
    best_indices = []
    for col_idx in range(1, len(budget_values) + 1):
        col_values = []
        for row in rows:
            val = row[col_idx]
            if val != '--':
                try:
                    # Extract mean from "mean{...}" format
                    mean_str = val.split('{')[0]
                    col_values.append(float(mean_str))
                except (ValueError, IndexError):
                    col_values.append(np.inf)
            else:
                col_values.append(np.inf)
        
        if col_values:
            best_idx = np.argmin(col_values)
            best_indices.append(best_idx)
        else:
            best_indices.append(-1)
    
    # Bold best values
    for col_idx, best_row_idx in enumerate(best_indices):
        if best_row_idx >= 0 and best_row_idx < len(rows):
            val = rows[best_row_idx][col_idx + 1]
            if val != '--':
                rows[best_row_idx][col_idx + 1] = f'\\textbf{{{val}}}'
    
    # Generate LaTeX
    n_cols = len(budget_values) + 1
    col_spec = '@{}l' + 'r' * len(budget_values) + '@{}'
    
    lines = [
        '\\begin{table}[t]',
        '\\centering',
        f'\\caption{{{caption}}}',
        f'\\label{{{label}}}',
        '\\scriptsize',
        '\\setlength{\\tabcolsep}{3pt}',
        f'\\begin{{tabular}}{{{col_spec}}}',
        '\\toprule',
    ]
    
    # Header
    header = ['Method'] + budget_display
    lines.append(' & '.join(header) + ' \\\\')
    lines.append('\\midrule')
    
    # Data rows
    for row in rows:
        lines.append(' & '.join(row) + ' \\\\')
    
    lines.extend([
        '\\bottomrule',
        '\\end{tabular}',
        '\\end{table}'
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def _generate_appendix_full_metrics(
    df: pd.DataFrame,
    output_path: str,
    caption: str,
    label: str,
    method_display: dict,
    use_tuples: bool = False,
    metrics: list = None,
) -> None:
    """Generate appendix table: one row per (Method, Budget), columns PEHE, ATE, Corr, Regret, ECE. Best per (budget, metric) is bolded."""
    if metrics is None:
        metrics = ['pehe', 'ate_abs_err', 'tau_corr', 'policy_regret', 'tau_ece']
    metric_headers = {'pehe': 'PEHE', 'ate_abs_err': 'ATE err', 'tau_corr': 'Spearman', 'policy_regret': 'Regret', 'tau_ece': 'ECE'}
    lower_is_better = {'pehe': True, 'ate_abs_err': True, 'tau_corr': False, 'policy_regret': True, 'tau_ece': True}
    
    df = df.copy()
    if use_tuples and 'm1' in df.columns:
        df['budget_tuple'] = df.apply(lambda r: f"({int(r['m0'])},{int(r['m1'])})", axis=1)
        budget_col = 'budget_tuple'
    else:
        budget_col = 'm0'
    
    methods_ordered = [m for m in method_display.keys() if m in df['method'].unique()]
    def _budget_key(x):
        if isinstance(x, str) and x.startswith('('):
            return eval(x)
        return x
    budget_values = sorted(df[budget_col].unique(), key=_budget_key)
    
    # Compute best (method, budget) per (budget, metric) for bolding
    best_cells = set()  # (method, budget, metric)
    for budget in budget_values:
        sub = df.loc[df[budget_col] == budget]
        if len(sub) == 0:
            continue
        for met in metrics:
            mean_col = f'{met}_mean' if f'{met}_mean' in sub.columns else met
            if mean_col not in sub.columns:
                continue
            vals = sub.set_index('method')[mean_col]
            vals = vals.replace([np.nan, np.inf, -np.inf], np.nan).dropna()
            if len(vals) == 0:
                continue
            if lower_is_better.get(met, True):
                best_val = vals.min()
            else:
                best_val = vals.max()
            best_methods = vals[vals == best_val].index.tolist()
            for m in best_methods:
                best_cells.add((m, budget, met))
    
    lines = [
        '\\begin{table}[t]',
        '\\centering',
        f'\\caption{{{caption}}}',
        f'\\label{{{label}}}',
        '\\scriptsize',
        '\\setlength{\\tabcolsep}{3pt}',
        f'\\begin{{tabular}}{{{"l" + "r" * (1 + len(metrics))}}}',
        '\\toprule',
        'Method & Budget & ' + ' & '.join(metric_headers.get(m, m) for m in metrics) + ' \\\\',
        '\\midrule',
    ]
    
    for method in methods_ordered:
        for budget in budget_values:
            mask = (df[budget_col] == budget) & (df['method'] == method)
            sub = df.loc[mask]
            if len(sub) == 0:
                continue
            row = [method_display.get(method, method), str(budget) if not isinstance(budget, str) else budget]
            for met in metrics:
                mean_col = f'{met}_mean' if f'{met}_mean' in sub.columns else met
                sd_col = f'{met}_sd' if f'{met}_sd' in sub.columns else f'{met}_std'
                if mean_col in sub.columns:
                    mv = sub[mean_col].values[0]
                    sv = sub[sd_col].values[0] if sd_col in sub.columns else np.nan
                    if pd.isna(mv):
                        row.append('--')
                    else:
                        ss = f'{sv:.2f}' if not (pd.isna(sv) or np.isnan(sv)) else '--'
                        cell = f'{mv:.2f} $\\pm$ {ss}'
                        if (method, budget, met) in best_cells:
                            cell = f'\\textbf{{{cell}}}'
                        row.append(cell)
                else:
                    row.append('--')
            lines.append(' & '.join(row) + ' \\\\')
    
    lines.extend(['\\bottomrule', '\\end{tabular}', '\\end{table}'])
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def _generate_screening_validity_if_available(results_dir: str, output_dir: str) -> None:
    """
    If raw rep-level results exist with diagnostics (e.g. diag_sources_selected),
    write an appendix snippet for screening validity. Otherwise skip.
    """
    for name, filename in [
        ('connected', 'results_rep_ihdp_connected_sweep.csv'),
        ('disconnected', 'results_rep_ihdp_disconnected_sweep.csv'),
    ]:
        path = _find_ihdp_agg_file(results_dir, filename.replace('results_agg_', 'results_rep_'))
        if not os.path.exists(path):
            path = os.path.join(results_dir, filename)
        if not os.path.exists(path):
            continue
        try:
            rep_df = pd.read_csv(path)
            if 'diag_sources_selected' not in rep_df.columns or 'pehe' not in rep_df.columns:
                continue
            # Simple summary: mean number of sources selected per method, and correlation with PEHE
            out_path = os.path.join(output_dir, f'A_IHDP_Screening_Validity_{name}.tex')
            # If diag_sources_selected is string like "1,2,3", count number of sources
            if rep_df['diag_sources_selected'].dtype == object:
                rep_df = rep_df.copy()
                rep_df['n_sources_selected'] = rep_df['diag_sources_selected'].fillna('').str.split(',').str.len()
                sel_col = 'n_sources_selected'
            else:
                sel_col = 'diag_sources_selected'
            by_method = rep_df.groupby('method').agg({
                sel_col: 'mean',
                'pehe': ['mean', 'std', 'count'],
            }).round(2)
            lines = [
                '\\begin{table}[t]',
                '\\centering',
                f'\\caption{{IHDP {name}: mean sources selected (screening) and PEHE by method.}}',
                f'\\label{{tab:ihdp_screening_{name}}}',
                '\\scriptsize',
                '\\begin{tabular}{lrrr}',
                '\\toprule',
                'Method & Mean sources selected & PEHE (mean) & N reps \\\\',
                '\\midrule',
            ]
            for method in by_method.index:
                row = by_method.loc[method]
                # Handle MultiIndex columns
                n_sel = row[(sel_col, 'mean')] if (sel_col, 'mean') in row else row.iloc[0]
                pehe = row[('pehe', 'mean')]
                n_reps = int(row[('pehe', 'count')])
                lines.append(f'{method} & {float(n_sel):.1f} & {float(pehe):.2f} & {n_reps} \\\\')
            lines.extend(['\\bottomrule', '\\end{tabular}', '\\end{table}'])
            with open(out_path, 'w') as f:
                f.write('\n'.join(lines))
            print(f"Generated: A_IHDP_Screening_Validity_{name}.tex")
        except Exception as e:
            pass  # Skip if columns or format differ


def _write_a6_diagnostic_tex(mean_corr: float, sd_corr: float, n_rep: int, output_path: str) -> None:
    """Write A_IHDP_A6_Diagnostic.tex with given summary stats."""
    lines = [
        '\\begin{table}[t]',
        '\\centering',
        '\\caption{IHDP disconnected regime: A6 diagnostic. Spearman correlation between placebo-arm screening score (MSE of source $\\mu_0$ on target placebo) and CATE transport error (PEHE of source $\\tau_c$ on target) across candidate sources. Weak correlation indicates placebo compatibility is not predictive of CATE compatibility (A6 empirically tenuous).}',
        '\\label{tab:ihdp_a6_diagnostic}',
        '\\scriptsize',
        '\\begin{tabular}{lrr}',
        '\\toprule',
        ' & Mean $\\pm$ SD & N \\\\',
        '\\midrule',
        f'Spearman (placebo score vs CATE PEHE) & ${mean_corr:.3f} \\pm {sd_corr:.3f}$ & {n_rep} \\\\',
        '\\bottomrule',
        '\\end{tabular}',
        '\\end{table}',
    ]
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def _generate_a6_diagnostic_if_available(results_dir: str, output_dir: str) -> None:
    """
    If disconnected rep-level results contain diag_a6_spearman_corr (placebo vs CATE
    correlation across sources), write A_IHDP_A6_Diagnostic.tex for the appendix.
    """
    path = _find_ihdp_agg_file(results_dir, 'results_rep_ihdp_disconnected_sweep.csv')
    if not os.path.exists(path):
        return
    try:
        df = pd.read_csv(path)
        if 'diag_a6_spearman_corr' not in df.columns:
            return
        # One value per (rep_id, m0); take first row per (rep_id, m0) to avoid weighting by method count
        dedup = df[['rep_id', 'm0', 'diag_a6_spearman_corr']].drop_duplicates(subset=['rep_id', 'm0'])
        vals = dedup['diag_a6_spearman_corr'].dropna()
        if len(vals) < 2:
            return
        mean_corr = float(vals.mean())
        sd_corr = float(vals.std())
        n_rep = int(len(vals))
        out_path = os.path.join(output_dir, 'A_IHDP_A6_Diagnostic.tex')
        _write_a6_diagnostic_tex(mean_corr, sd_corr, n_rep, out_path)
        print(f"Generated: A_IHDP_A6_Diagnostic.tex")
    except Exception:
        pass


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Run IHDP experiments')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test with 5 reps')
    parser.add_argument('--full', action='store_true',
                       help='Full run with 50 reps')
    parser.add_argument('--sweep', type=str, default=None,
                       help='Specific sweep to run')
    parser.add_argument('--n_rep', type=int, default=None,
                       help='Number of replications')
    parser.add_argument('--n_jobs', type=int, default=1,
                       help='Number of parallel jobs (-1 for all)')
    parser.add_argument('--output', type=str, default='results/ihdp',
                       help='Output directory (or parent of IHDP connected / IHDP disconnected folders)')
    parser.add_argument('--tables_only', action='store_true',
                       help='Generate tables from existing results')
    parser.add_argument('--diagnostic_only', action='store_true',
                       help='Run only A6 diagnostic (data gen + correlation, no estimators); write A_IHDP_A6_Diagnostic.tex')
    parser.add_argument('--tables_output', type=str, default=None,
                       help='Output directory for LaTeX tables')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    
    args = parser.parse_args()
    
    # Determine table output directory
    tables_dir = args.tables_output
    if tables_dir is None:
        # Default: Paper/Transfer-Learning.../Tables/
        tables_dir = os.path.join(
            os.path.dirname(__file__), '..', 
            'Paper', 'Transfer-Learning-for-Individual-Patient-Data-for-Clinical-Trials', 
            'Tables'
        )
    
    # Diagnostic-only mode: run A6 diagnostic without any experiment results
    if args.diagnostic_only:
        n_rep = args.n_rep if args.n_rep is not None else 50
        print(f"Running A6 diagnostic only (n_rep={n_rep}, seed={args.seed})...")
        df = run_ihdp_a6_diagnostic_only(n_rep=n_rep, base_seed=args.seed, verbose=True)
        if df.empty or len(df) < 2:
            print("Warning: Too few diagnostic results; need at least 2.")
            return
        vals = df['diag_a6_spearman_corr'].dropna()
        if len(vals) < 2:
            print("Warning: Too few valid Spearman values.")
            return
        mean_corr = float(vals.mean())
        sd_corr = float(vals.std())
        out_path = os.path.join(tables_dir, 'A_IHDP_A6_Diagnostic.tex')
        os.makedirs(tables_dir, exist_ok=True)
        _write_a6_diagnostic_tex(mean_corr, sd_corr, int(len(vals)), out_path)
        print(f"Wrote {out_path} (mean Spearman = {mean_corr:.3f} ± {sd_corr:.3f}, N = {len(vals)})")
        return
    
    # Tables only mode
    if args.tables_only:
        print("Generating tables from existing results...")
        generate_ihdp_latex_tables(args.output, tables_dir)
        print("Done!")
        return
    
    # Determine n_rep
    if args.n_rep is not None:
        n_rep = args.n_rep
    elif args.quick:
        n_rep = 5
    elif args.full:
        n_rep = 50
    else:
        n_rep = 10  # Default
    
    # Determine sweeps to run
    if args.sweep:
        sweeps = [args.sweep]
    elif args.quick:
        # Quick: just run connected and disconnected
        sweeps = ['ihdp_connected', 'ihdp_disconnected']
    else:
        # Full: all sweeps
        sweeps = list(IHDP_SWEEP_CONFIGS.keys())
    
    print(f"\n{'='*60}")
    print("IHDP Semi-Synthetic Experiments")
    print(f"{'='*60}")
    print(f"Sweeps: {sweeps}")
    print(f"Replications: {n_rep}")
    print(f"Parallel jobs: {args.n_jobs}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\n")
    
    # Run sweeps
    sweep_status = {}
    for sweep in sweeps:
        print(f"\n>>> Running {sweep}...")
        df = run_ihdp_sweep(
            sweep_name=sweep,
            n_rep=n_rep,
            n_jobs=args.n_jobs,
            output_dir=args.output,
            base_seed=args.seed,
            verbose=True
        )
        sweep_status[sweep] = 'OK' if (df is not None and len(df) > 0) else 'EMPTY/FAILED'
    
    # Print sweep status summary
    print(f"\n{'='*60}")
    print("Sweep Status Summary:")
    for sweep, status in sweep_status.items():
        print(f"  {sweep}: {status}")
    print(f"{'='*60}")
    
    # Generate tables
    print("\n>>> Generating LaTeX tables...")
    generate_ihdp_latex_tables(args.output, tables_dir)
    
    print("\n" + "="*60)
    print("IHDP experiments complete!")
    print("="*60)


if __name__ == '__main__':
    main()
