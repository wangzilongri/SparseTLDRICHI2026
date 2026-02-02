"""
Benchmark Plots: Automated plot generation from PlotSpec.

This module provides a systematic way to generate publication-ready
figures from benchmark results using standardized PlotSpec definitions.
"""

import os
import sys
import warnings
from typing import Optional, Dict, List, Any, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_schema import PlotSpec, Feasibility


# =============================================================================
# Color and Style Configuration
# =============================================================================

# Consistent colors for each method
# Proposed methods (A and B) use green shades to show they're related
METHOD_COLORS = {
    'NoTransfer': '#d62728',           # Red
    'ProxyOnly': '#ff7f0e',            # Orange  
    'AnchorOnly': '#1f77b4',           # Blue
    'ProposedA': '#2ca02c',            # Green (dark) - Option A
    'ProposedB_LinearStepB': '#98df8a', # Green (light) - Option B Linear
    'ProposedB_KernelStepB': '#c7e9c0', # Green (very light) - Option B Kernel
    'IPD_RE': '#e377c2',               # Pink
    'AIPWTransport': '#7f7f7f',        # Gray
    'EntropyBalancing': '#bcbd22',     # Yellow-green
    'DRLearner_PooledWithSite': '#17becf',  # Cyan
    'DRLearner_PooledNoSite': '#aec7e8',    # Light blue
    'TARNet': '#9467bd',               # Purple
}

# Markers for each method
METHOD_MARKERS = {
    'NoTransfer': 'X',
    'ProxyOnly': 's',
    'AnchorOnly': '^',
    'ProposedA': 'o',
    'ProposedB_LinearStepB': 'D',
    'ProposedB_KernelStepB': 'p',
    'IPD_RE': 'v',
    'AIPWTransport': '<',
    'EntropyBalancing': '>',
    'DRLearner_PooledWithSite': 'h',
    'DRLearner_PooledNoSite': 'H',
    'TARNet': '*',
}

# Line styles for feasibility
FEASIBILITY_LINESTYLES = {
    'FeasibleRestricted': '-',
    'OracleTargetTreated': '--',
    'InfeasibleByDesign': ':',
}

# Hatches for bar plots
FEASIBILITY_HATCHES = {
    'FeasibleRestricted': '',
    'OracleTargetTreated': '//',
    'InfeasibleByDesign': 'xx',
}


def get_method_color(method: str) -> str:
    """Get color for method, with fallback."""
    return METHOD_COLORS.get(method, '#333333')


def get_method_marker(method: str) -> str:
    """Get marker for method, with fallback."""
    return METHOD_MARKERS.get(method, 'o')


def get_feasibility_linestyle(feasibility: str) -> str:
    """Get linestyle for feasibility."""
    return FEASIBILITY_LINESTYLES.get(feasibility, '-')


# =============================================================================
# Plot Style Setup
# =============================================================================

def setup_plot_style():
    """Set up consistent plot style."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.figsize': (8, 6),
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
    })


# =============================================================================
# Core Plot Functions
# =============================================================================

def plot_line(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str = 'method',
    yerr: Optional[str] = None,
    facet_col: Optional[str] = None,
    facet_row: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    xscale: Optional[str] = None,
    yscale: Optional[str] = None,
    hline: Optional[float] = None,
    legend_loc: str = 'best',
    figsize: Tuple[float, float] = (8, 6),
    ax: Optional[plt.Axes] = None
) -> plt.Figure:
    """
    Create line plot with error bars.
    
    Parameters
    ----------
    df : pd.DataFrame
        Data to plot
    x : str
        X-axis column
    y : str
        Y-axis column
    hue : str
        Grouping column (typically 'method')
    yerr : str, optional
        Column for error bars
    facet_col : str, optional
        Column for faceting columns
    facet_row : str, optional
        Column for faceting rows
    title : str, optional
        Plot title
    xlabel : str, optional
        X-axis label
    ylabel : str, optional
        Y-axis label
    xscale : str, optional
        X-axis scale ('log', 'linear')
    yscale : str, optional
        Y-axis scale
    hline : float, optional
        Horizontal reference line
        
    Returns
    -------
    plt.Figure
        The figure object
    """
    setup_plot_style()
    
    # Handle faceting
    if facet_col or facet_row:
        return _plot_line_faceted(
            df, x, y, hue, yerr, facet_col, facet_row,
            title, xlabel, ylabel, xscale, yscale, hline
        )
    
    # Single plot
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
    
    # Get unique hue values
    hue_values = df[hue].unique() if hue in df.columns else [None]
    
    for hue_val in hue_values:
        if hue_val is not None:
            subset = df[df[hue] == hue_val].sort_values(x)
            color = get_method_color(hue_val)
            marker = get_method_marker(hue_val)
            label = hue_val
            
            # Get feasibility for linestyle
            if 'feasibility' in subset.columns:
                feas = subset['feasibility'].iloc[0]
                linestyle = get_feasibility_linestyle(feas)
            else:
                linestyle = '-'
        else:
            subset = df.sort_values(x)
            color = '#1f77b4'
            marker = 'o'
            label = None
            linestyle = '-'
        
        x_vals = subset[x].values
        y_vals = subset[y].values
        
        if yerr and yerr in subset.columns:
            yerr_vals = subset[yerr].values
            ax.errorbar(x_vals, y_vals, yerr=yerr_vals, 
                       color=color, marker=marker, linestyle=linestyle,
                       label=label, capsize=3, markersize=6)
        else:
            ax.plot(x_vals, y_vals, color=color, marker=marker, 
                   linestyle=linestyle, label=label, markersize=6)
    
    # Reference line
    if hline is not None:
        ax.axhline(hline, color='gray', linestyle='--', alpha=0.7, label=f'Reference ({hline})')
    
    # Styling
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    if title:
        ax.set_title(title)
    
    if xscale:
        ax.set_xscale(xscale)
    if yscale:
        ax.set_yscale(yscale)
    
    if hue_values[0] is not None:
        ax.legend(loc=legend_loc)
    
    ax.grid(True, alpha=0.3)
    
    return fig


def _plot_line_faceted(
    df: pd.DataFrame,
    x: str, y: str, hue: str, yerr: Optional[str],
    facet_col: Optional[str], facet_row: Optional[str],
    title: Optional[str], xlabel: Optional[str], ylabel: Optional[str],
    xscale: Optional[str], yscale: Optional[str], hline: Optional[float]
) -> plt.Figure:
    """Create faceted line plot."""
    
    col_vals = df[facet_col].unique() if facet_col else [None]
    row_vals = df[facet_row].unique() if facet_row else [None]
    
    n_cols = len(col_vals)
    n_rows = len(row_vals)
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows), squeeze=False)
    
    for i, row_val in enumerate(row_vals):
        for j, col_val in enumerate(col_vals):
            ax = axes[i, j]
            
            # Filter data
            subset = df.copy()
            if facet_row and row_val is not None:
                subset = subset[subset[facet_row] == row_val]
            if facet_col and col_val is not None:
                subset = subset[subset[facet_col] == col_val]
            
            # Plot
            plot_line(subset, x, y, hue, yerr, ax=ax,
                     xlabel=xlabel, ylabel=ylabel, xscale=xscale, yscale=yscale, hline=hline)
            
            # Facet title
            facet_title = []
            if facet_row and row_val is not None:
                facet_title.append(f"{facet_row}={row_val}")
            if facet_col and col_val is not None:
                facet_title.append(f"{facet_col}={col_val}")
            if facet_title:
                ax.set_title(" | ".join(facet_title))
    
    if title:
        fig.suptitle(title, y=1.02)
    
    plt.tight_layout()
    return fig


def plot_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str = 'method',
    yerr: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    show_feasibility: bool = True,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Create grouped bar chart.
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    x_vals = df[x].unique()
    hue_vals = df[hue].unique()
    n_groups = len(x_vals)
    n_bars = len(hue_vals)
    
    bar_width = 0.8 / n_bars
    x_positions = np.arange(n_groups)
    
    for i, hue_val in enumerate(hue_vals):
        subset = df[df[hue] == hue_val]
        
        # Match order of x_vals
        y_vals = []
        yerr_vals = []
        hatches = []
        
        for x_val in x_vals:
            row = subset[subset[x] == x_val]
            if len(row) > 0:
                y_vals.append(row[y].iloc[0])
                if yerr and yerr in row.columns:
                    yerr_vals.append(row[yerr].iloc[0])
                else:
                    yerr_vals.append(0)
                
                if show_feasibility and 'feasibility' in row.columns:
                    hatches.append(FEASIBILITY_HATCHES.get(row['feasibility'].iloc[0], ''))
                else:
                    hatches.append('')
            else:
                y_vals.append(np.nan)
                yerr_vals.append(0)
                hatches.append('')
        
        positions = x_positions + i * bar_width - (n_bars - 1) * bar_width / 2
        color = get_method_color(hue_val)
        
        bars = ax.bar(positions, y_vals, bar_width, 
                     label=hue_val, color=color, 
                     yerr=yerr_vals if any(yerr_vals) else None,
                     capsize=3)
        
        # Add hatches for feasibility
        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
    
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_vals)
    
    if title:
        ax.set_title(title)
    
    # Legend with feasibility explanation
    handles, labels = ax.get_legend_handles_labels()
    
    if show_feasibility:
        # Add feasibility legend
        feas_handles = [
            Patch(facecolor='white', edgecolor='black', hatch='', label='Feasible'),
            Patch(facecolor='white', edgecolor='black', hatch='//', label='Oracle'),
        ]
        handles.extend(feas_handles)
        labels.extend(['Feasible', 'Oracle'])
    
    ax.legend(handles, labels, loc='best', ncol=2)
    
    plt.tight_layout()
    return fig


def plot_heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    values: str,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    cmap: str = 'RdYlBu_r',
    annot: bool = True,
    fmt: str = '.3f',
    figsize: Tuple[float, float] = (8, 6)
) -> plt.Figure:
    """
    Create heatmap (e.g., for rank mismatch grid).
    """
    setup_plot_style()
    
    # Pivot to matrix form
    pivot = df.pivot(index=y, columns=x, values=values)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(pivot, annot=annot, fmt=fmt, cmap=cmap, ax=ax,
               cbar_kws={'label': values})
    
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    
    if title:
        ax.set_title(title)
    
    plt.tight_layout()
    return fig


def plot_violin(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Create violin plot (e.g., for lambda stability).
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if hue:
        palette = {m: get_method_color(m) for m in df[hue].unique()}
        sns.violinplot(data=df, x=x, y=y, hue=hue, palette=palette, ax=ax)
    else:
        sns.violinplot(data=df, x=x, y=y, ax=ax)
    
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    
    if title:
        ax.set_title(title)
    
    plt.tight_layout()
    return fig


def plot_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    add_diagonal: bool = False,
    figsize: Tuple[float, float] = (8, 6)
) -> plt.Figure:
    """
    Create scatter plot (e.g., for SE comparison).
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if hue and hue in df.columns:
        for hue_val in df[hue].unique():
            subset = df[df[hue] == hue_val]
            color = get_method_color(hue_val)
            marker = get_method_marker(hue_val)
            ax.scatter(subset[x], subset[y], c=color, marker=marker, 
                      label=hue_val, alpha=0.7, s=30)
        ax.legend()
    else:
        ax.scatter(df[x], df[y], alpha=0.7, s=30)
    
    if add_diagonal:
        lims = [
            min(ax.get_xlim()[0], ax.get_ylim()[0]),
            max(ax.get_xlim()[1], ax.get_ylim()[1])
        ]
        ax.plot(lims, lims, 'k--', alpha=0.5, label='y=x')
    
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    
    if title:
        ax.set_title(title)
    
    plt.tight_layout()
    return fig


# =============================================================================
# PlotSpec Execution
# =============================================================================

def execute_plot_spec(
    spec: PlotSpec,
    df_rep: Optional[pd.DataFrame] = None,
    df_agg: Optional[pd.DataFrame] = None,
    output_dir: Optional[str] = None,
    formats: List[str] = ['png', 'pdf']
) -> plt.Figure:
    """
    Execute a PlotSpec to generate a figure.
    
    Parameters
    ----------
    spec : PlotSpec
        Plot specification
    df_rep : pd.DataFrame, optional
        Rep-level results
    df_agg : pd.DataFrame, optional
        Aggregated results
    output_dir : str, optional
        If provided, save figure to this directory
    formats : list of str
        Output formats
        
    Returns
    -------
    plt.Figure
        The generated figure
    """
    # Select data source
    if spec.df_source == 'results_rep':
        df = df_rep
    elif spec.df_source == 'results_agg':
        df = df_agg
    else:
        raise ValueError(f"Unknown df_source: {spec.df_source}")
    
    if df is None:
        raise ValueError(f"Data source '{spec.df_source}' not provided")
    
    # Apply filters
    if spec.filters:
        for col, val in spec.filters.items():
            if isinstance(val, (list, tuple)):
                df = df[df[col].isin(val)]
            else:
                df = df[df[col] == val]
    
    # Generate plot
    plot_funcs = {
        'line': plot_line,
        'bar': plot_bar,
        'heatmap': plot_heatmap,
        'violin': plot_violin,
        'scatter': plot_scatter,
    }
    
    if spec.plot_type not in plot_funcs:
        raise ValueError(f"Unknown plot_type: {spec.plot_type}")
    
    plot_func = plot_funcs[spec.plot_type]
    
    # Build kwargs
    kwargs = {
        'df': df,
        'x': spec.x,
        'y': spec.y,
        'title': spec.title,
        'xlabel': spec.xlabel,
        'ylabel': spec.ylabel,
    }
    
    if spec.hue:
        kwargs['hue'] = spec.hue
    if spec.yerr:
        kwargs['yerr'] = spec.yerr
    if spec.facet_col and spec.plot_type == 'line':
        kwargs['facet_col'] = spec.facet_col
    if spec.facet_row and spec.plot_type == 'line':
        kwargs['facet_row'] = spec.facet_row
    if spec.xscale and spec.plot_type == 'line':
        kwargs['xscale'] = spec.xscale
    if spec.yscale and spec.plot_type == 'line':
        kwargs['yscale'] = spec.yscale
    if spec.hline is not None and spec.plot_type == 'line':
        kwargs['hline'] = spec.hline
    
    fig = plot_func(**kwargs)
    
    # Save
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for fmt in formats:
            path = os.path.join(output_dir, f"{spec.name}.{fmt}")
            fig.savefig(path)
            print(f"  Saved: {path}")
    
    return fig


def generate_benchmark_plots(
    benchmark_id: str,
    df_rep: pd.DataFrame,
    df_agg: pd.DataFrame,
    output_dir: str,
    plot_specs: Optional[List[PlotSpec]] = None
) -> Dict[str, plt.Figure]:
    """
    Generate all plots for a benchmark.
    
    Parameters
    ----------
    benchmark_id : str
        Benchmark identifier
    df_rep : pd.DataFrame
        Rep-level results
    df_agg : pd.DataFrame
        Aggregated results
    output_dir : str
        Output directory
    plot_specs : list of PlotSpec, optional
        Custom plot specifications. If None, uses defaults.
        
    Returns
    -------
    dict
        {plot_name: figure}
    """
    if plot_specs is None:
        plot_specs = get_default_plot_specs(benchmark_id, df_agg)
    
    figures = {}
    print(f"Generating {len(plot_specs)} plots for {benchmark_id}...")
    
    for spec in plot_specs:
        try:
            fig = execute_plot_spec(spec, df_rep, df_agg, output_dir)
            figures[spec.name] = fig
        except Exception as e:
            warnings.warn(f"Failed to generate plot '{spec.name}': {e}")
    
    plt.close('all')  # Clean up
    return figures


def get_default_plot_specs(benchmark_id: str, df_agg: pd.DataFrame) -> List[PlotSpec]:
    """
    Get default plot specifications for a benchmark.
    """
    specs = []
    
    # Determine sweep column
    sweep_cols = {
        'gold_sweep': 'm0',
        'proxy_sweep': 'n_proxy_total',
        'site_imbalance': 'imbalance_ratio',
        'covariate_shift': 'shift_metric_w1',
        'overlap_stress': 'overlap_strength',
        'a5_dense': 'a5_effective_sparsity',
        'a5_nonlinear': 'a5_nonlin_strength',
        'a6_rank': None,  # Heatmap
        'a6_nonlinear': 'a6_nonlin_rho',
    }
    
    sweep_col = sweep_cols.get(benchmark_id)
    
    # PEHE plot
    if sweep_col:
        specs.append(PlotSpec(
            name=f'{benchmark_id}_pehe',
            df_source='results_agg',
            plot_type='line',
            x=sweep_col,
            y='pehe_mean',
            hue='method',
            yerr='pehe_sd',
            title=f'PEHE vs {sweep_col}',
            xlabel=sweep_col,
            ylabel='PEHE'
        ))
    
    # ATE error plot
    if sweep_col and 'ate_abs_err_mean' in df_agg.columns:
        specs.append(PlotSpec(
            name=f'{benchmark_id}_ate_err',
            df_source='results_agg',
            plot_type='line',
            x=sweep_col,
            y='ate_abs_err_mean',
            hue='method',
            yerr='ate_abs_err_sd',
            title=f'ATE Error vs {sweep_col}',
            xlabel=sweep_col,
            ylabel='|ATE Error|'
        ))
    
    # μ₀ RMSE plot
    if sweep_col and 'mu0_rmse_mean' in df_agg.columns:
        specs.append(PlotSpec(
            name=f'{benchmark_id}_mu0_rmse',
            df_source='results_agg',
            plot_type='line',
            x=sweep_col,
            y='mu0_rmse_mean',
            hue='method',
            yerr='mu0_rmse_sd',
            title=f'μ₀ RMSE vs {sweep_col}',
            xlabel=sweep_col,
            ylabel='μ₀ RMSE'
        ))
    
    # Heatmap for rank mismatch
    if benchmark_id == 'a6_rank' and 'a6_rank_true' in df_agg.columns:
        specs.append(PlotSpec(
            name=f'{benchmark_id}_heatmap',
            df_source='results_agg',
            plot_type='heatmap',
            x='a6_rank_fit',
            y='a6_rank_true',
            title='PEHE: True Rank vs Fitted Rank',
            filters={'method': 'ProposedB_LinearStepB'}
        ))
    
    return specs


# =============================================================================
# Legend Generation
# =============================================================================

def create_method_legend_figure(
    methods: Optional[List[str]] = None,
    show_feasibility: bool = True,
    figsize: Tuple[float, float] = (6, 4)
) -> plt.Figure:
    """
    Create a standalone legend figure showing all methods.
    
    Useful for multi-panel figures with shared legend.
    """
    if methods is None:
        methods = list(METHOD_COLORS.keys())
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('off')
    
    handles = []
    labels = []
    
    for method in methods:
        color = get_method_color(method)
        marker = get_method_marker(method)
        line, = ax.plot([], [], color=color, marker=marker, linestyle='-', label=method)
        handles.append(line)
        labels.append(method)
    
    if show_feasibility:
        handles.append(plt.Line2D([], [], color='gray', linestyle='-', label='Feasible'))
        handles.append(plt.Line2D([], [], color='gray', linestyle='--', label='Oracle'))
        labels.extend(['Feasible', 'Oracle'])
    
    ax.legend(handles, labels, loc='center', ncol=2, frameon=True)
    
    return fig


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate benchmark plots")
    parser.add_argument('--rep', type=str, help='Rep-level results CSV')
    parser.add_argument('--agg', type=str, help='Aggregated results CSV')
    parser.add_argument('--output', type=str, default='results/figures', help='Output directory')
    parser.add_argument('--benchmark', type=str, default='benchmark', help='Benchmark ID')
    
    args = parser.parse_args()
    
    df_rep = pd.read_csv(args.rep) if args.rep else None
    df_agg = pd.read_csv(args.agg) if args.agg else None
    
    if df_agg is None and df_rep is not None:
        from benchmark_aggregation import aggregate_results
        df_agg = aggregate_results(df_rep)
    
    if df_agg is not None:
        generate_benchmark_plots(args.benchmark, df_rep, df_agg, args.output)
