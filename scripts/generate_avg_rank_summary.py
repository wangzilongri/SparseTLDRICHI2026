#!/usr/bin/env python3
"""
Generate Paper/.../Tables/P3_Avg_Rank_Summary.tex from combined results_agg CSVs.

Use after running synthetic sweeps (dim, sources, A5, disconnected) so that
AnchorPlugin is not in the method list. This script excludes AnchorPlugin if
present and computes average rank (1 = best) per metric across all scenarios.

Usage:
  # From repo root, with results in results/sweeps/
  python scripts/generate_avg_rank_summary.py --input-dir results/sweeps

  # Or explicit files
  python scripts/generate_avg_rank_summary.py \\
    --input results/sweeps/results_agg_gold_fair_dim_sweep.csv \\
            results/sweeps/results_agg_gold_fair_sources_sweep.csv \\
            results/sweeps/results_agg_a5_violation_sweep.csv

  # Output path (default: Paper/.../Tables/P3_Avg_Rank_Summary.tex)
  python scripts/generate_avg_rank_summary.py --input-dir results/sweeps --output Paper/.../Tables/P3_Avg_Rank_Summary.tex
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# Repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, 'src'))

# Default output path (paper tables)
DEFAULT_OUTPUT = os.path.join(
    REPO_ROOT,
    'Paper', 'Transfer-Learning-for-Individual-Patient-Data-for-Clinical-Trials',
    'Tables', 'P3_Avg_Rank_Summary.tex'
)

# Metrics for the table: internal name -> (display header, lower_is_better)
# Slope: best = closest to 1, so we rank by |slope - 1| (lower is better)
TABLE_METRICS = [
    ('pehe', 'PEHE', True),
    ('ate_abs_err', 'ATE', True),
    ('tau_corr', r'$\tau$', False),   # higher is better
    ('policy_regret', 'Regret', True),
    ('calib_slope', 'Slope', None),   # special: closest to 1
    ('calib_r2', r'R$^2$', False),
    ('tau_ece', 'ECE', True),
]

METHOD_ORDER = [
    'TargetOnly', 'ProxyOnly', 'IPW-Transport', 'OM-Transport', 'EntropyBal',
    'AnchorOnly', 'Proposed', 'Proposed-CF', 'Proposed-B'
]

EXCLUDE_METHODS_DEFAULT = ['AnchorPlugin']


def load_agg_csvs(paths: list[str]) -> pd.DataFrame:
    """Load and concatenate results_agg CSVs. Ensure scenario_id exists."""
    dfs = []
    for p in paths:
        if not os.path.isfile(p):
            raise FileNotFoundError(p)
        df = pd.read_csv(p)
        if 'scenario_id' not in df.columns:
            # Build scenario_id from benchmark_id + param columns
            id_cols = [c for c in df.columns if c not in {'method', 'feasibility'}
                       and not c.endswith('_mean') and not c.endswith('_sd')
                       and not c.endswith('_n') and not c.endswith('_median')]
            df = df.copy()
            df['scenario_id'] = df[id_cols].astype(str).agg('_'.join, axis=1)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True, sort=False)


def compute_avg_ranks(
    df_agg: pd.DataFrame,
    metrics: list[tuple[str, str, bool | None]],
    exclude_methods: list[str],
) -> pd.DataFrame:
    """Compute average rank per method per metric. Returns DataFrame methods x metrics."""
    df = df_agg[~df_agg['method'].isin(exclude_methods)].copy()
    if df.empty:
        raise ValueError("No rows left after excluding methods")

    if 'scenario_id' not in df.columns:
        raise ValueError("df_agg must have scenario_id")

    rankings = []
    for metric_key, _label, lower_better in metrics:
        mean_col = f'{metric_key}_mean'
        if mean_col not in df.columns:
            continue

        for sid in df['scenario_id'].unique():
            sub = df[df['scenario_id'] == sid].copy()
            if sub[mean_col].isna().all():
                continue

            if metric_key == 'calib_slope':
                # Best = closest to 1
                sub = sub.copy()
                sub['_rank_val'] = np.abs(sub[mean_col] - 1.0)
                sub['rank'] = sub['_rank_val'].rank(ascending=True)
            else:
                ascending = lower_better if lower_better is not None else True
                sub = sub.copy()
                sub['rank'] = sub[mean_col].rank(ascending=ascending)

            for _, row in sub.iterrows():
                rankings.append({
                    'method': row['method'],
                    'metric': metric_key,
                    'rank': row['rank']
                })

    if not rankings:
        return pd.DataFrame()

    rank_df = pd.DataFrame(rankings)
    avg = rank_df.groupby(['method', 'metric'])['rank'].mean().unstack()
    return avg


def write_latex(avg_ranks: pd.DataFrame, output_path: str) -> None:
    """Write LaTeX table. Bold best (min) per column."""
    # Column order: match TABLE_METRICS
    metric_cols = [m[0] for m in TABLE_METRICS if m[0] in avg_ranks.columns]
    avg = avg_ranks[metric_cols].copy()

    # Row order: METHOD_ORDER, then any other methods
    present = [m for m in METHOD_ORDER if m in avg.index]
    others = [m for m in avg.index if m not in METHOD_ORDER]
    avg = avg.reindex(present + others)

    # Best per column (min rank)
    best_per_col = avg.min(axis=0)

    lines = [
        r'\begin{table}[t]',
        r'\centering',
        r'\caption{Average rank per metric across all sweeps (1 = best). Calibration: Slope (ideal=1), R$^2$, ECE (Expected Calibration Error).}',
        r'\label{tab:avg_rank_summary}',
        r'\scriptsize',
        r'\setlength{\tabcolsep}{2pt}',
        r'\begin{tabular}{@{}l|cccc|ccc@{}}',
        r'\toprule',
        r' & \multicolumn{4}{c|}{Performance} & \multicolumn{3}{c}{Calibration} \\',
        r'\midrule',
    ]

    headers = [m[1] for m in TABLE_METRICS if m[0] in metric_cols]
    header_line = 'Method & ' + ' & '.join(headers) + r' \\'
    lines.append(header_line)
    lines.append(r'\midrule')

    for method in avg.index:
        row_vals = []
        for c in metric_cols:
            val = avg.loc[method, c]
            if pd.isna(val):
                row_vals.append('--')
            else:
                s = f'{val:.1f}'
                if val == best_per_col[c]:
                    s = r'\textbf{' + s + '}'
                row_vals.append(s)
        lines.append(method + ' & ' + ' & '.join(row_vals) + r' \\')

    lines.append(r'\bottomrule')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Wrote {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate P3_Avg_Rank_Summary.tex from results_agg CSVs (excluding AnchorPlugin).'
    )
    parser.add_argument(
        '--input',
        nargs='+',
        help='Paths to results_agg_*.csv files'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Directory to glob for results_agg_*.csv (used if --input not set)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT,
        help=f'Output .tex path (default: {DEFAULT_OUTPUT})'
    )
    parser.add_argument(
        '--exclude-methods',
        nargs='*',
        default=EXCLUDE_METHODS_DEFAULT,
        help='Methods to exclude from ranking (default: AnchorPlugin)'
    )
    args = parser.parse_args()

    if args.input:
        paths = args.input
    elif args.input_dir:
        import glob
        pattern = os.path.join(args.input_dir, 'results_agg_*.csv')
        paths = sorted(glob.glob(pattern))
        if not paths:
            print(f"No results_agg_*.csv in {args.input_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Provide --input <files> or --input-dir <dir>", file=sys.stderr)
        sys.exit(1)

    df_agg = load_agg_csvs(paths)
    print(f"Loaded {len(df_agg)} rows from {len(paths)} file(s). Methods: {sorted(df_agg['method'].unique())}")

    avg_ranks = compute_avg_ranks(df_agg, TABLE_METRICS, args.exclude_methods)
    if avg_ranks.empty:
        print("No rankings computed (missing metric columns?).", file=sys.stderr)
        sys.exit(1)

    write_latex(avg_ranks, args.output)


if __name__ == '__main__':
    main()
