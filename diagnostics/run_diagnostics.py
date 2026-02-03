#!/usr/bin/env python3
"""
Comprehensive Sweep Diagnostics Runner

This script runs all diagnostic checks on sweep results and generates
a complete diagnostic report with visualizations and compiled PDF.

Usage:
    python run_diagnostics.py <results_folder> [--output <output_folder>]
    
Example:
    python run_diagnostics.py ../results/sweeps_remote
    python run_diagnostics.py ../results/sweeps_remote --output ../diagnostics_output/remote
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


class SweepDiagnostics:
    """Main diagnostics class for analyzing sweep results."""
    
    # Methods of interest for diagnostics
    PROPOSED_METHODS = ['ProposedA', 'ProposedB_LinearStepB', 'ProposedB_SourceDR']
    BASELINE_METHODS = ['AnchorOnly', 'ProxyOnly', 'IPWTransport', 'OutcomeModelTransport', 
                        'DRLearner_PooledWithSite', 'DRLearner_PooledNoSite']
    
    # Key metrics for diagnostics
    KEY_METRICS = {
        'pehe': {'name': 'PEHE', 'direction': 'lower', 'threshold_bad': 6.0},
        'ate_abs_err': {'name': 'ATE Error', 'direction': 'lower', 'threshold_bad': 3.0},
        'tau_corr': {'name': 'Spearman ρ', 'direction': 'higher', 'threshold_bad': 0.5},
        'qini_auc': {'name': 'Qini AUC', 'direction': 'higher', 'threshold_bad': 0.5},
        'tau_ece': {'name': 'τ-ECE', 'direction': 'lower', 'threshold_bad': 3.0},
        'calib_slope': {'name': 'Calib Slope', 'direction': 'closer_to_1', 'threshold_bad': 0.3},
        'calib_r2': {'name': 'Calib R²', 'direction': 'higher', 'threshold_bad': 0.3},
    }
    
    def __init__(self, results_folder: str, output_folder: str = None):
        """Initialize diagnostics with results folder path."""
        self.results_folder = Path(results_folder)
        self.output_folder = Path(output_folder) if output_folder else self.results_folder / 'diagnostics'
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self.df_agg = None
        self.df_rep = None
        self.sweep_name = None
        self._load_data()
        
        # Store figures for PDF compilation
        self.figures = []
        
    def _load_data(self):
        """Load aggregated and replicate-level results."""
        # Find CSV files
        agg_files = list(self.results_folder.glob('results_agg_*.csv'))
        rep_files = list(self.results_folder.glob('results_rep_*.csv'))
        
        if not agg_files:
            raise FileNotFoundError(f"No aggregated results found in {self.results_folder}")
        
        # Use first found (usually only one per folder)
        agg_file = agg_files[0]
        self.sweep_name = agg_file.stem.replace('results_agg_', '')
        
        print(f"Loading results from: {self.results_folder}")
        print(f"  Sweep name: {self.sweep_name}")
        
        self.df_agg = pd.read_csv(agg_file)
        print(f"  Aggregated data: {len(self.df_agg)} rows")
        
        if rep_files:
            self.df_rep = pd.read_csv(rep_files[0])
            print(f"  Replicate data: {len(self.df_rep)} rows")
        
        # Extract unique methods and cells
        self.methods = self.df_agg['method'].unique().tolist()
        self.m0_values = sorted(self.df_agg['m0'].dropna().unique().tolist())
        self.m1_values = sorted(self.df_agg['m1'].dropna().unique().tolist())
        
        print(f"  Methods: {len(self.methods)}")
        print(f"  m0 values: {self.m0_values}")
        print(f"  m1 values: {self.m1_values}")
    
    def run_all_diagnostics(self):
        """Run all diagnostic checks and generate report."""
        print("\n" + "="*60)
        print("RUNNING SWEEP DIAGNOSTICS")
        print("="*60)
        
        # 1. Calibration Analysis
        print("\n[1/5] Running calibration analysis...")
        self.calibration_analysis()
        
        # 2. Multi-axis failure detection
        print("\n[2/5] Running multi-axis failure detection...")
        self.multi_axis_failure_check()
        
        # 3. Method comparison heatmaps
        print("\n[3/5] Generating method comparison heatmaps...")
        self.method_comparison_heatmaps()
        
        # 4. Performance vs budget analysis
        print("\n[4/5] Running performance vs budget analysis...")
        self.performance_vs_budget()
        
        # 5. Generate report
        print("\n[5/5] Generating diagnostic report...")
        self.generate_report()
        
        print("\n" + "="*60)
        print("DIAGNOSTICS COMPLETE")
        print(f"Output folder: {self.output_folder}")
        print("="*60)
    
    def calibration_analysis(self):
        """Analyze calibration metrics: slope, intercept, R²."""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Calibration Diagnostics', fontsize=14, fontweight='bold')
        
        methods_to_plot = [m for m in self.PROPOSED_METHODS + ['AnchorOnly', 'IPWTransport'] 
                          if m in self.methods]
        
        # Filter for methods with valid calibration data
        df_calib = self.df_agg[self.df_agg['method'].isin(methods_to_plot)].copy()
        df_calib = df_calib[df_calib['calib_slope_mean'].notna()]
        
        if len(df_calib) == 0:
            print("  Warning: No calibration data available")
            return
        
        # Plot 1: Calibration Slope by Method
        ax = axes[0, 0]
        df_plot = df_calib.groupby('method')['calib_slope_mean'].mean().sort_values()
        colors = ['red' if abs(v - 1) > 0.3 else 'steelblue' for v in df_plot.values]
        bars = ax.barh(df_plot.index, df_plot.values, color=colors)
        ax.axvline(x=1.0, color='green', linestyle='--', linewidth=2, label='Ideal (1.0)')
        ax.set_xlabel('Mean Calibration Slope')
        ax.set_title('Calibration Slope by Method')
        ax.legend()
        
        # Plot 2: Calibration Intercept by Method
        ax = axes[0, 1]
        df_plot = df_calib.groupby('method')['calib_intercept_mean'].mean().sort_values()
        colors = ['red' if abs(v) > 2 else 'steelblue' for v in df_plot.values]
        ax.barh(df_plot.index, df_plot.values, color=colors)
        ax.axvline(x=0.0, color='green', linestyle='--', linewidth=2, label='Ideal (0.0)')
        ax.set_xlabel('Mean Calibration Intercept')
        ax.set_title('Calibration Intercept by Method')
        ax.legend()
        
        # Plot 3: Calibration R² by Method
        ax = axes[0, 2]
        df_plot = df_calib.groupby('method')['calib_r2_mean'].mean().sort_values()
        colors = ['red' if v < 0.3 else 'steelblue' for v in df_plot.values]
        ax.barh(df_plot.index, df_plot.values, color=colors)
        ax.axvline(x=0.5, color='orange', linestyle='--', linewidth=2, label='Threshold (0.5)')
        ax.set_xlabel('Mean Calibration R²')
        ax.set_title('Calibration R² by Method')
        ax.set_xlim(0, 1)
        ax.legend()
        
        # Plot 4: Slope SD (variance) by Method
        ax = axes[1, 0]
        df_plot = df_calib.groupby('method')['calib_slope_sd'].mean().sort_values(ascending=False)
        colors = ['red' if v > 0.4 else 'steelblue' for v in df_plot.values]
        ax.barh(df_plot.index, df_plot.values, color=colors)
        ax.axvline(x=0.3, color='orange', linestyle='--', linewidth=2, label='High variance')
        ax.set_xlabel('Mean Slope Standard Deviation')
        ax.set_title('Calibration Slope Variance')
        ax.legend()
        
        # Plot 5: Intercept SD (variance) by Method
        ax = axes[1, 1]
        df_plot = df_calib.groupby('method')['calib_intercept_sd'].mean().sort_values(ascending=False)
        colors = ['red' if v > 5 else 'steelblue' for v in df_plot.values]
        ax.barh(df_plot.index, df_plot.values, color=colors)
        ax.axvline(x=4.0, color='orange', linestyle='--', linewidth=2, label='High variance')
        ax.set_xlabel('Mean Intercept Standard Deviation')
        ax.set_title('Calibration Intercept Variance')
        ax.legend()
        
        # Plot 6: τ-ECE by Method
        ax = axes[1, 2]
        if 'tau_ece_mean' in df_calib.columns:
            df_plot = df_calib.groupby('method')['tau_ece_mean'].mean().sort_values(ascending=False)
            colors = ['red' if v > 3 else 'steelblue' for v in df_plot.values]
            ax.barh(df_plot.index, df_plot.values, color=colors)
            ax.axvline(x=2.0, color='orange', linestyle='--', linewidth=2, label='Poor calibration')
            ax.set_xlabel('Mean τ-ECE')
            ax.set_title('CATE Expected Calibration Error')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'τ-ECE not available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('CATE Expected Calibration Error')
        
        plt.tight_layout()
        
        # Save
        fig.savefig(self.output_folder / 'calibration_analysis.png', dpi=150, bbox_inches='tight')
        fig.savefig(self.output_folder / 'calibration_analysis.pdf', bbox_inches='tight')
        self.figures.append(('Calibration Analysis', fig))
        plt.close(fig)
        
        # Generate calibration comparison table
        self._generate_calibration_table()
    
    def _generate_calibration_table(self):
        """Generate detailed calibration comparison table."""
        methods_of_interest = [m for m in self.PROPOSED_METHODS + ['AnchorOnly', 'IPWTransport'] 
                               if m in self.methods]
        
        df_calib = self.df_agg[self.df_agg['method'].isin(methods_of_interest)].copy()
        
        # Create summary table
        rows = []
        for method in methods_of_interest:
            df_m = df_calib[df_calib['method'] == method]
            if len(df_m) == 0:
                continue
            
            rows.append({
                'Method': method,
                'Slope (mean)': f"{df_m['calib_slope_mean'].mean():.2f}",
                'Slope (SD)': f"{df_m['calib_slope_sd'].mean():.2f}",
                'Intercept (mean)': f"{df_m['calib_intercept_mean'].mean():.2f}",
                'Intercept (SD)': f"{df_m['calib_intercept_sd'].mean():.2f}",
                'R² (mean)': f"{df_m['calib_r2_mean'].mean():.3f}",
                'τ-ECE (mean)': f"{df_m['tau_ece_mean'].mean():.2f}" if 'tau_ece_mean' in df_m.columns else 'N/A',
                'n_cells': len(df_m),
            })
        
        df_table = pd.DataFrame(rows)
        df_table.to_csv(self.output_folder / 'calibration_summary.csv', index=False)
        self.calibration_summary = df_table
    
    def multi_axis_failure_check(self):
        """Check for multi-axis failures (methods failing on multiple metrics)."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        fig.suptitle('Multi-Axis Failure Detection', fontsize=14, fontweight='bold')
        
        methods_to_check = [m for m in self.PROPOSED_METHODS + self.BASELINE_METHODS 
                           if m in self.methods]
        
        # Compute failure scores
        failure_scores = []
        for method in methods_to_check:
            df_m = self.df_agg[self.df_agg['method'] == method]
            if len(df_m) == 0:
                continue
            
            scores = {'method': method}
            
            # PEHE failure (higher is worse)
            if 'pehe_mean' in df_m.columns:
                pehe_mean = df_m['pehe_mean'].mean()
                scores['pehe'] = pehe_mean
                scores['pehe_fail'] = pehe_mean > self.KEY_METRICS['pehe']['threshold_bad']
            
            # ATE Error failure
            if 'ate_abs_err_mean' in df_m.columns:
                ate_err = df_m['ate_abs_err_mean'].mean()
                scores['ate_err'] = ate_err
                scores['ate_fail'] = ate_err > self.KEY_METRICS['ate_abs_err']['threshold_bad']
            
            # Ranking failure (lower Spearman is worse)
            if 'tau_corr_mean' in df_m.columns:
                tau_corr = df_m['tau_corr_mean'].mean()
                scores['tau_corr'] = tau_corr
                scores['ranking_fail'] = tau_corr < self.KEY_METRICS['tau_corr']['threshold_bad']
            
            # Calibration failure (lower R² is worse)
            if 'calib_r2_mean' in df_m.columns:
                calib_r2 = df_m['calib_r2_mean'].mean()
                scores['calib_r2'] = calib_r2
                scores['calib_fail'] = calib_r2 < self.KEY_METRICS['calib_r2']['threshold_bad']
            
            # τ-ECE failure (higher is worse)
            if 'tau_ece_mean' in df_m.columns:
                tau_ece = df_m['tau_ece_mean'].mean()
                scores['tau_ece'] = tau_ece
                scores['ece_fail'] = tau_ece > self.KEY_METRICS['tau_ece']['threshold_bad']
            
            # Count failures
            fail_cols = [c for c in scores.keys() if c.endswith('_fail')]
            scores['n_failures'] = sum(scores.get(c, False) for c in fail_cols)
            scores['failure_rate'] = scores['n_failures'] / len(fail_cols) if fail_cols else 0
            
            failure_scores.append(scores)
        
        df_failures = pd.DataFrame(failure_scores)
        df_failures = df_failures.sort_values('n_failures', ascending=False)
        
        # Plot 1: Failure count by method
        ax = axes[0, 0]
        colors = ['red' if n >= 3 else 'orange' if n >= 2 else 'steelblue' 
                  for n in df_failures['n_failures']]
        ax.barh(df_failures['method'], df_failures['n_failures'], color=colors)
        ax.set_xlabel('Number of Failed Metrics')
        ax.set_title('Multi-Axis Failure Count')
        ax.axvline(x=2, color='orange', linestyle='--', label='Warning threshold')
        ax.axvline(x=3, color='red', linestyle='--', label='Critical threshold')
        ax.legend()
        
        # Plot 2: Radar chart of key metrics (normalized)
        ax = axes[0, 1]
        metrics_to_radar = ['pehe', 'ate_err', 'tau_corr', 'calib_r2', 'tau_ece']
        available_metrics = [m for m in metrics_to_radar if m in df_failures.columns]
        
        if len(available_metrics) >= 3:
            # Normalize metrics (0-1 scale, higher = better)
            df_norm = df_failures.copy()
            for m in available_metrics:
                if m in ['pehe', 'ate_err', 'tau_ece']:  # Lower is better
                    max_val = df_norm[m].max()
                    df_norm[f'{m}_norm'] = 1 - (df_norm[m] / max_val if max_val > 0 else 0)
                else:  # Higher is better
                    max_val = df_norm[m].max()
                    df_norm[f'{m}_norm'] = df_norm[m] / max_val if max_val > 0 else 0
            
            # Select methods for radar
            radar_methods = ['ProposedA', 'ProposedB_LinearStepB', 'ProposedB_SourceDR', 'IPWTransport']
            radar_methods = [m for m in radar_methods if m in df_norm['method'].values]
            
            if radar_methods:
                angles = np.linspace(0, 2*np.pi, len(available_metrics), endpoint=False).tolist()
                angles += angles[:1]
                
                for method in radar_methods:
                    row = df_norm[df_norm['method'] == method].iloc[0]
                    values = [row.get(f'{m}_norm', 0) for m in available_metrics]
                    values += values[:1]
                    ax.plot(angles, values, 'o-', linewidth=2, label=method)
                    ax.fill(angles, values, alpha=0.1)
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels([m.upper() for m in available_metrics])
                ax.set_title('Performance Radar (normalized, higher=better)')
                ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1))
        else:
            ax.text(0.5, 0.5, 'Insufficient metrics for radar', ha='center', va='center')
            ax.set_title('Performance Radar')
        
        # Plot 3: PEHE vs Spearman scatter
        ax = axes[1, 0]
        if 'pehe' in df_failures.columns and 'tau_corr' in df_failures.columns:
            for _, row in df_failures.iterrows():
                color = 'red' if row['method'] == 'ProposedB_SourceDR' else 'steelblue'
                marker = 's' if 'Proposed' in row['method'] else 'o'
                ax.scatter(row['pehe'], row['tau_corr'], c=color, marker=marker, s=100, 
                          label=row['method'])
            
            ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7)
            ax.axvline(x=6.0, color='orange', linestyle='--', alpha=0.7)
            ax.set_xlabel('PEHE (↓ lower is better)')
            ax.set_ylabel('Spearman ρ (↑ higher is better)')
            ax.set_title('PEHE vs Ranking Quality')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            
            # Add quadrant labels
            ax.text(0.95, 0.95, 'Good', transform=ax.transAxes, ha='right', va='top', 
                   fontweight='bold', color='green')
            ax.text(0.05, 0.05, 'Bad', transform=ax.transAxes, ha='left', va='bottom', 
                   fontweight='bold', color='red')
        
        # Plot 4: Calibration R² vs τ-ECE
        ax = axes[1, 1]
        if 'calib_r2' in df_failures.columns and 'tau_ece' in df_failures.columns:
            for _, row in df_failures.iterrows():
                color = 'red' if row['method'] == 'ProposedB_SourceDR' else 'steelblue'
                marker = 's' if 'Proposed' in row['method'] else 'o'
                ax.scatter(row['calib_r2'], row['tau_ece'], c=color, marker=marker, s=100,
                          label=row['method'])
            
            ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.7)
            ax.axvline(x=0.3, color='orange', linestyle='--', alpha=0.7)
            ax.set_xlabel('Calibration R² (↑ higher is better)')
            ax.set_ylabel('τ-ECE (↓ lower is better)')
            ax.set_title('Calibration R² vs ECE')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            
            # Add quadrant labels
            ax.text(0.95, 0.05, 'Good', transform=ax.transAxes, ha='right', va='bottom',
                   fontweight='bold', color='green')
            ax.text(0.05, 0.95, 'Bad', transform=ax.transAxes, ha='left', va='top',
                   fontweight='bold', color='red')
        
        plt.tight_layout()
        
        fig.savefig(self.output_folder / 'multi_axis_failure.png', dpi=150, bbox_inches='tight')
        fig.savefig(self.output_folder / 'multi_axis_failure.pdf', bbox_inches='tight')
        self.figures.append(('Multi-Axis Failure Detection', fig))
        plt.close(fig)
        
        # Save failure summary
        df_failures.to_csv(self.output_folder / 'failure_summary.csv', index=False)
        self.failure_summary = df_failures
    
    def method_comparison_heatmaps(self):
        """Generate heatmaps comparing methods across (m0, m1) cells."""
        metrics_to_plot = ['pehe_mean', 'ate_abs_err_mean', 'tau_corr_mean', 
                          'tau_ece_mean', 'calib_r2_mean', 'qini_auc_mean']
        metrics_to_plot = [m for m in metrics_to_plot if m in self.df_agg.columns]
        
        methods_to_compare = [m for m in self.PROPOSED_METHODS if m in self.methods]
        
        for metric in metrics_to_plot:
            metric_name = metric.replace('_mean', '')
            fig, axes = plt.subplots(1, len(methods_to_compare), figsize=(5*len(methods_to_compare), 4))
            if len(methods_to_compare) == 1:
                axes = [axes]
            
            fig.suptitle(f'{metric_name.upper()} Comparison Across Methods', fontsize=12, fontweight='bold')
            
            # Determine color scale (shared across methods)
            all_values = []
            for method in methods_to_compare:
                df_m = self.df_agg[self.df_agg['method'] == method]
                all_values.extend(df_m[metric].dropna().tolist())
            
            if not all_values:
                continue
                
            vmin, vmax = min(all_values), max(all_values)
            
            # Determine colormap direction
            lower_better = metric_name in ['pehe', 'ate_abs_err', 'tau_ece', 'policy_regret']
            cmap = 'RdYlGn_r' if lower_better else 'RdYlGn'
            
            for idx, method in enumerate(methods_to_compare):
                ax = axes[idx]
                df_m = self.df_agg[self.df_agg['method'] == method]
                
                # Pivot to create heatmap matrix
                pivot = df_m.pivot_table(index='m1', columns='m0', values=metric, aggfunc='mean')
                
                if pivot.empty:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(method)
                    continue
                
                # Sort indices
                pivot = pivot.sort_index(ascending=False)
                pivot = pivot.reindex(columns=sorted(pivot.columns))
                
                sns.heatmap(pivot, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax,
                           annot=True, fmt='.2f', cbar=(idx == len(methods_to_compare)-1))
                ax.set_title(method)
                ax.set_xlabel('m₀ (target placebo)')
                ax.set_ylabel('m₁ (target treated)' if idx == 0 else '')
            
            plt.tight_layout()
            
            fig.savefig(self.output_folder / f'heatmap_{metric_name}.png', dpi=150, bbox_inches='tight')
            fig.savefig(self.output_folder / f'heatmap_{metric_name}.pdf', bbox_inches='tight')
            self.figures.append((f'Heatmap: {metric_name}', fig))
            plt.close(fig)
    
    def performance_vs_budget(self):
        """Analyze how performance changes with target data budget."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Performance vs Target Data Budget', fontsize=14, fontweight='bold')
        
        methods_to_plot = ['ProposedA', 'ProposedB_LinearStepB', 'ProposedB_SourceDR', 
                          'AnchorOnly', 'IPWTransport']
        methods_to_plot = [m for m in methods_to_plot if m in self.methods]
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(methods_to_plot)))
        method_colors = dict(zip(methods_to_plot, colors))
        
        # Plot 1: PEHE vs total target budget (m0 + m1)
        ax = axes[0, 0]
        for method in methods_to_plot:
            df_m = self.df_agg[self.df_agg['method'] == method].copy()
            df_m['total_target'] = df_m['m0'] + df_m['m1']
            df_m = df_m.groupby('total_target')['pehe_mean'].mean().reset_index()
            
            if len(df_m) > 0:
                ax.plot(df_m['total_target'], df_m['pehe_mean'], 'o-', 
                       label=method, color=method_colors[method], linewidth=2, markersize=8)
        
        ax.set_xlabel('Total Target Budget (m₀ + m₁)')
        ax.set_ylabel('PEHE (↓ lower is better)')
        ax.set_title('PEHE vs Total Budget')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.set_xscale('log')
        
        # Plot 2: PEHE at m1=0 (disconnected target) vs m0
        ax = axes[0, 1]
        df_m1_0 = self.df_agg[self.df_agg['m1'] == 0].copy()
        for method in methods_to_plot:
            df_m = df_m1_0[df_m1_0['method'] == method]
            if len(df_m) > 0:
                df_m = df_m.sort_values('m0')
                ax.plot(df_m['m0'], df_m['pehe_mean'], 'o-', 
                       label=method, color=method_colors[method], linewidth=2, markersize=8)
        
        ax.set_xlabel('Target Placebo (m₀)')
        ax.set_ylabel('PEHE (↓ lower is better)')
        ax.set_title('PEHE at m₁=0 (Disconnected Target)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot 3: Spearman vs m1 (holding m0 constant at max)
        ax = axes[1, 0]
        max_m0 = max(self.m0_values) if self.m0_values else 100
        df_max_m0 = self.df_agg[self.df_agg['m0'] == max_m0].copy()
        for method in methods_to_plot:
            df_m = df_max_m0[df_max_m0['method'] == method]
            if len(df_m) > 0:
                df_m = df_m.sort_values('m1')
                ax.plot(df_m['m1'], df_m['tau_corr_mean'], 'o-', 
                       label=method, color=method_colors[method], linewidth=2, markersize=8)
        
        ax.set_xlabel(f'Target Treated (m₁) at m₀={max_m0}')
        ax.set_ylabel('Spearman ρ (↑ higher is better)')
        ax.set_title(f'Ranking Quality vs m₁ (m₀={max_m0})')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot 4: τ-ECE vs total budget
        ax = axes[1, 1]
        if 'tau_ece_mean' in self.df_agg.columns:
            for method in methods_to_plot:
                df_m = self.df_agg[self.df_agg['method'] == method].copy()
                df_m['total_target'] = df_m['m0'] + df_m['m1']
                df_m = df_m.groupby('total_target')['tau_ece_mean'].mean().reset_index()
                
                if len(df_m) > 0:
                    ax.plot(df_m['total_target'], df_m['tau_ece_mean'], 'o-', 
                           label=method, color=method_colors[method], linewidth=2, markersize=8)
            
            ax.set_xlabel('Total Target Budget (m₀ + m₁)')
            ax.set_ylabel('τ-ECE (↓ lower is better)')
            ax.set_title('Calibration Error vs Budget')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.set_xscale('log')
        else:
            ax.text(0.5, 0.5, 'τ-ECE not available', ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
        
        fig.savefig(self.output_folder / 'performance_vs_budget.png', dpi=150, bbox_inches='tight')
        fig.savefig(self.output_folder / 'performance_vs_budget.pdf', bbox_inches='tight')
        self.figures.append(('Performance vs Budget', fig))
        plt.close(fig)
    
    def generate_report(self):
        """Generate comprehensive markdown report with embedded images."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""# Sweep Diagnostics Report

**Sweep:** `{self.sweep_name}`

**Results folder:** `{self.results_folder}`

**Generated:** {timestamp}

---

## Executive Summary

This diagnostic report analyzes the sweep results to identify:
1. **Calibration issues** - Methods with poor slope, intercept, or R²
2. **Multi-axis failures** - Methods failing on multiple metrics simultaneously
3. **Performance patterns** - How methods behave across different (m₀, m₁) configurations

---

## 1. Calibration Analysis

**What this checks:**
- **Calibration Slope**: Should be close to 1.0. Slope < 1 indicates underconfident predictions (predictions are too conservative). Slope > 1 indicates overconfident predictions.
- **Calibration Intercept**: Should be close to 0.0. Non-zero intercepts indicate systematic bias in the baseline prediction level.
- **Calibration R²**: Should be high (>0.5). Low R² means predictions don't track true effects well.
- **τ-ECE (Expected Calibration Error)**: Should be low (<2). High ECE indicates predictions are miscalibrated across deciles.

**Key findings:**

"""
        # Add calibration summary if available
        if hasattr(self, 'calibration_summary'):
            report += "| Method | Slope | Slope SD | Intercept | Intercept SD | R² | τ-ECE | n_cells |\n"
            report += "|--------|-------|----------|-----------|--------------|-----|-------|--------|\n"
            for _, row in self.calibration_summary.iterrows():
                report += f"| {row['Method']} | {row['Slope (mean)']} | {row['Slope (SD)']} | "
                report += f"{row['Intercept (mean)']} | {row['Intercept (SD)']} | "
                report += f"{row['R² (mean)']} | {row['τ-ECE (mean)']} | {row['n_cells']} |\n"
            report += "\n"
        
        report += """
![Calibration Analysis](calibration_analysis.png)

**Interpretation:**
- Methods with slope far from 1.0 have systematic magnitude errors
- High slope variance indicates instability across replications
- Low R² combined with high τ-ECE indicates fundamental calibration failure

---

## 2. Multi-Axis Failure Detection

**What this checks:**
Identifies methods that fail on multiple metrics simultaneously, indicating fundamental problems rather than minor weaknesses.

**Failure thresholds:**
- PEHE > 6.0 (prediction error too high)
- ATE Error > 3.0 (average effect estimation poor)
- Spearman ρ < 0.5 (ranking quality poor)
- Calibration R² < 0.3 (predictions don't track true effects)
- τ-ECE > 3.0 (calibration is poor)

**Key findings:**

"""
        # Add failure summary if available
        if hasattr(self, 'failure_summary'):
            report += "| Method | PEHE | ATE Err | Spearman | Calib R² | τ-ECE | # Failures |\n"
            report += "|--------|------|---------|----------|----------|-------|------------|\n"
            for _, row in self.failure_summary.iterrows():
                pehe = f"{row.get('pehe', 'N/A'):.2f}" if pd.notna(row.get('pehe')) else 'N/A'
                ate = f"{row.get('ate_err', 'N/A'):.2f}" if pd.notna(row.get('ate_err')) else 'N/A'
                tau = f"{row.get('tau_corr', 'N/A'):.2f}" if pd.notna(row.get('tau_corr')) else 'N/A'
                r2 = f"{row.get('calib_r2', 'N/A'):.3f}" if pd.notna(row.get('calib_r2')) else 'N/A'
                ece = f"{row.get('tau_ece', 'N/A'):.2f}" if pd.notna(row.get('tau_ece')) else 'N/A'
                report += f"| {row['method']} | {pehe} | {ate} | {tau} | {r2} | {ece} | {row['n_failures']} |\n"
            report += "\n"
        
        report += """
![Multi-Axis Failure Detection](multi_axis_failure.png)

**Interpretation:**
- Methods with 3+ failures should be considered **critically broken** for the intended use case
- The scatter plots show whether failures are correlated (e.g., bad PEHE → bad ranking)
- Methods in the "Bad" quadrant of both plots have fundamental issues

---

## 3. Method Comparison Heatmaps

**What this shows:**
Performance of each method across the (m₀, m₁) grid, allowing visual identification of:
- Which (m₀, m₁) cells are problematic
- Whether performance improves with more data
- Differences between methods at the same budget

"""
        # List available heatmaps
        heatmap_files = list(self.output_folder.glob('heatmap_*.png'))
        for hf in sorted(heatmap_files):
            metric_name = hf.stem.replace('heatmap_', '')
            report += f"\n### {metric_name.upper()}\n\n"
            report += f"![{metric_name}]({hf.name})\n"
        
        report += """
---

## 4. Performance vs Budget

**What this shows:**
How each method's performance scales with target data budget (m₀ + m₁).

**Key questions:**
- Does performance improve with more data? (Should for most methods)
- At m₁=0 (disconnected target), which methods are viable?
- Is there diminishing returns at high budget?

![Performance vs Budget](performance_vs_budget.png)

**Interpretation:**
- Methods whose PEHE stays flat with increasing budget likely have **bias issues** (not variance)
- Methods viable at m₁=0 are critical for external control settings
- Sharp improvements with small m₁ indicate the method leverages treated data well

---

## 5. Diagnostic Recommendations

Based on this analysis:

"""
        # Add specific recommendations based on findings
        if hasattr(self, 'failure_summary'):
            critical_failures = self.failure_summary[self.failure_summary['n_failures'] >= 3]
            if len(critical_failures) > 0:
                report += "### ⚠️ Critical Failures Detected\n\n"
                for _, row in critical_failures.iterrows():
                    report += f"- **{row['method']}**: Fails on {row['n_failures']} metrics. "
                    report += "Consider re-labeling as ablation/negative control.\n"
                report += "\n"
            
            moderate_failures = self.failure_summary[(self.failure_summary['n_failures'] >= 2) & 
                                                      (self.failure_summary['n_failures'] < 3)]
            if len(moderate_failures) > 0:
                report += "### ⚡ Moderate Issues\n\n"
                for _, row in moderate_failures.iterrows():
                    report += f"- **{row['method']}**: Fails on {row['n_failures']} metrics. "
                    report += "Review for specific use cases.\n"
                report += "\n"
        
        report += """
---

## Appendix: Files Generated

"""
        # List all generated files
        for f in sorted(self.output_folder.glob('*')):
            if f.is_file():
                report += f"- `{f.name}`\n"
        
        report += f"""
---

*Report generated by sweep diagnostics v1.0*
"""
        
        # Save markdown report
        report_path = self.output_folder / 'diagnostic_report.md'
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"  Saved: {report_path}")
        
        # Compile to PDF
        self._compile_pdf()
    
    def _compile_pdf(self):
        """Compile all figures into a single PDF."""
        pdf_path = self.output_folder / 'diagnostic_report_compiled.pdf'
        
        with PdfPages(pdf_path) as pdf:
            # Title page
            fig = plt.figure(figsize=(11, 8.5))
            fig.text(0.5, 0.6, 'Sweep Diagnostics Report', fontsize=24, 
                    fontweight='bold', ha='center')
            fig.text(0.5, 0.5, f'Sweep: {self.sweep_name}', fontsize=16, ha='center')
            fig.text(0.5, 0.4, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                    fontsize=12, ha='center')
            fig.text(0.5, 0.3, f'Results: {self.results_folder}', fontsize=10, ha='center')
            pdf.savefig(fig)
            plt.close(fig)
            
            # Add all diagnostic figures
            for title, fig_path in [(f.stem, f) for f in sorted(self.output_folder.glob('*.png'))]:
                fig = plt.figure(figsize=(11, 8.5))
                img = plt.imread(fig_path)
                plt.imshow(img)
                plt.axis('off')
                plt.title(title.replace('_', ' ').title(), fontsize=14, fontweight='bold')
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
        
        print(f"  Compiled PDF: {pdf_path}")


def main():
    parser = argparse.ArgumentParser(description='Run sweep diagnostics')
    parser.add_argument('results_folder', help='Path to results folder containing CSV files')
    parser.add_argument('--output', '-o', help='Output folder for diagnostics (default: results_folder/diagnostics)')
    
    args = parser.parse_args()
    
    try:
        diag = SweepDiagnostics(args.results_folder, args.output)
        diag.run_all_diagnostics()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
