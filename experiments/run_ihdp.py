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
    run_ihdp_sweep, IHDP_SWEEP_CONFIGS,
    IHDP_METHODS_OPTION_A, IHDP_METHODS_OPTION_B
)


# =============================================================================
# TABLE GENERATION
# =============================================================================

def generate_ihdp_latex_tables(results_dir: str, output_dir: str) -> None:
    """
    Generate LaTeX tables from IHDP results.
    
    Creates:
    - P3_IHDP_Connected_PEHE.tex: Main text table for connected regime
    - P3_IHDP_Disconnected_PEHE.tex: Main text table for disconnected regime
    - Full appendix tables for all metrics
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
    # Connected regime table
    # =========================================================================
    connected_file = os.path.join(results_dir, 'results_agg_ihdp_connected_sweep.csv')
    if os.path.exists(connected_file):
        df = pd.read_csv(connected_file)
        
        # Generate PEHE table
        _generate_pehe_table(
            df=df,
            output_path=os.path.join(output_dir, 'P3_IHDP_Connected_PEHE.tex'),
            caption='IHDP connected regime: PEHE across target budgets (mean $\\pm$ SD, 50 realizations).',
            label='tab:ihdp_connected_pehe',
            method_display=METHOD_DISPLAY,
            budget_col='m0',  # Primary budget column
            use_tuples=True,  # Show (m0, m1) tuples
        )
        print(f"Generated: P3_IHDP_Connected_PEHE.tex")
    else:
        print(f"Warning: {connected_file} not found")
    
    # =========================================================================
    # Disconnected regime table
    # =========================================================================
    disconnected_file = os.path.join(results_dir, 'results_agg_ihdp_disconnected_sweep.csv')
    if os.path.exists(disconnected_file):
        df = pd.read_csv(disconnected_file)
        
        # Generate PEHE table
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
    else:
        print(f"Warning: {disconnected_file} not found")


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
                    row_data.append(f'{mean_val:.2f}{{\\tiny$\\pm${sd_val:.2f}}}')
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
                       help='Output directory')
    parser.add_argument('--tables_only', action='store_true',
                       help='Generate tables from existing results')
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
    for sweep in sweeps:
        print(f"\n>>> Running {sweep}...")
        run_ihdp_sweep(
            sweep_name=sweep,
            n_rep=n_rep,
            n_jobs=args.n_jobs,
            output_dir=args.output,
            base_seed=args.seed,
            verbose=True
        )
    
    # Generate tables
    print("\n>>> Generating LaTeX tables...")
    generate_ihdp_latex_tables(args.output, tables_dir)
    
    print("\n" + "="*60)
    print("IHDP experiments complete!")
    print("="*60)


if __name__ == '__main__':
    main()
