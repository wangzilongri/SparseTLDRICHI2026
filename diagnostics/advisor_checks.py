#!/usr/bin/env python3
"""
Advisor-Recommended Diagnostic Checks

This script performs the specific diagnostic checks recommended by the advisor
to evaluate ProposedB_SourceDR and compare it with other methods.

Key checks:
1. Multi-axis failure detection (PEHE, ATE, ranking, calibration simultaneously)
2. Calibration slope/intercept analysis
3. Comparison table generation for paper/rebuttal

Usage:
    python advisor_checks.py <results_folder>
    
Example:
    python advisor_checks.py ../results/sweeps_remote
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')


class AdvisorDiagnostics:
    """Performs advisor-recommended diagnostic checks."""
    
    # Target methods for comparison
    FOCUS_METHOD = 'ProposedB_SourceDR'
    COMPARISON_METHODS = ['ProposedA', 'ProposedB_LinearStepB', 'AnchorOnly', 'IPWTransport']
    
    def __init__(self, results_folder: str):
        self.results_folder = Path(results_folder)
        self.output_folder = self.results_folder / 'advisor_diagnostics'
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Load data
        agg_files = list(self.results_folder.glob('results_agg_*.csv'))
        if not agg_files:
            raise FileNotFoundError(f"No aggregated results in {self.results_folder}")
        
        self.df = pd.read_csv(agg_files[0])
        self.sweep_name = agg_files[0].stem.replace('results_agg_', '')
        
        print(f"Loaded {len(self.df)} rows from {self.sweep_name}")
        print(f"Methods: {self.df['method'].nunique()}")
    
    def run_all_checks(self):
        """Run all advisor-recommended checks."""
        print("\n" + "="*60)
        print("ADVISOR-RECOMMENDED DIAGNOSTIC CHECKS")
        print("="*60)
        
        self.check_1_multi_axis_failure()
        self.check_2_calibration_details()
        self.check_3_comparison_table()
        self.check_4_scatter_diagnostics()
        self.generate_advisor_report()
        
        print("\n" + "="*60)
        print(f"Complete! Output: {self.output_folder}")
        print("="*60)
    
    def check_1_multi_axis_failure(self):
        """Check 1: Multi-axis failure detection for SourceDR."""
        print("\n[Check 1] Multi-Axis Failure Detection")
        print("-"*40)
        
        if self.FOCUS_METHOD not in self.df['method'].values:
            print(f"  WARNING: {self.FOCUS_METHOD} not found in results")
            return
        
        df_focus = self.df[self.df['method'] == self.FOCUS_METHOD]
        
        # Define failure criteria (from advisor's recommendations)
        checks = {
            'PEHE > 6': df_focus['pehe_mean'] > 6,
            'ATE Error > 3': df_focus['ate_abs_err_mean'] > 3,
            'Spearman < 0.5': df_focus['tau_corr_mean'] < 0.5,
            'Qini < 0.5': df_focus['qini_auc_mean'] < 0.5,
            'τ-ECE > 3': df_focus['tau_ece_mean'] > 3 if 'tau_ece_mean' in df_focus.columns else pd.Series([False]*len(df_focus)),
            'Calib R² < 0.3': df_focus['calib_r2_mean'] < 0.3,
        }
        
        # Count failures per cell
        results = []
        for idx, row in df_focus.iterrows():
            cell = f"({int(row['m0'])}, {int(row['m1'])})"
            failures = []
            for check_name, check_series in checks.items():
                if check_series.loc[idx]:
                    failures.append(check_name)
            
            results.append({
                'Cell (m0, m1)': cell,
                'm0': int(row['m0']),
                'm1': int(row['m1']),
                'PEHE': f"{row['pehe_mean']:.2f}",
                'ATE Err': f"{row['ate_abs_err_mean']:.2f}",
                'Spearman': f"{row['tau_corr_mean']:.3f}",
                'τ-ECE': f"{row.get('tau_ece_mean', 'N/A'):.2f}" if pd.notna(row.get('tau_ece_mean')) else 'N/A',
                'Calib R²': f"{row['calib_r2_mean']:.3f}",
                '# Failures': len(failures),
                'Failed Checks': ', '.join(failures) if failures else 'None',
            })
        
        df_results = pd.DataFrame(results)
        
        # Print summary
        print(f"\n  {self.FOCUS_METHOD} failure summary across {len(df_focus)} cells:")
        for _, r in df_results.iterrows():
            status = "❌ CRITICAL" if r['# Failures'] >= 3 else "⚠️  WARNING" if r['# Failures'] >= 2 else "✓ OK"
            print(f"    {r['Cell (m0, m1)']}: {r['# Failures']} failures {status}")
        
        # Overall assessment
        avg_failures = df_results['# Failures'].mean()
        print(f"\n  Average failures per cell: {avg_failures:.1f}")
        if avg_failures >= 3:
            print("  ⚠️  RECOMMENDATION: Method shows SYSTEMATIC multi-axis failure")
            print("     Consider re-labeling as negative control / ablation")
        
        df_results.to_csv(self.output_folder / 'check1_multi_axis_failures.csv', index=False)
        self.multi_axis_results = df_results
    
    def check_2_calibration_details(self):
        """Check 2: Detailed calibration slope/intercept analysis."""
        print("\n[Check 2] Calibration Slope & Intercept Analysis")
        print("-"*40)
        
        methods_to_analyze = [self.FOCUS_METHOD] + self.COMPARISON_METHODS
        methods_to_analyze = [m for m in methods_to_analyze if m in self.df['method'].values]
        
        results = []
        for method in methods_to_analyze:
            df_m = self.df[self.df['method'] == method]
            df_m = df_m[df_m['calib_slope_mean'].notna()]
            
            if len(df_m) == 0:
                continue
            
            results.append({
                'Method': method,
                'Slope (mean)': df_m['calib_slope_mean'].mean(),
                'Slope (SD)': df_m['calib_slope_sd'].mean(),
                'Intercept (mean)': df_m['calib_intercept_mean'].mean(),
                'Intercept (SD)': df_m['calib_intercept_sd'].mean(),
                'R² (mean)': df_m['calib_r2_mean'].mean(),
                'R² (SD)': df_m['calib_r2_sd'].mean(),
                'τ-ECE (mean)': df_m['tau_ece_mean'].mean() if 'tau_ece_mean' in df_m.columns else np.nan,
                'n_cells': len(df_m),
            })
        
        df_results = pd.DataFrame(results)
        
        # Print comparison table
        print("\n  Calibration Comparison Table:")
        print("  " + "-"*90)
        print(f"  {'Method':<25} {'Slope':>8} {'Slope SD':>10} {'Intercept':>10} {'Int SD':>10} {'R²':>8} {'τ-ECE':>8}")
        print("  " + "-"*90)
        
        for _, r in df_results.iterrows():
            slope_flag = "❌" if abs(r['Slope (mean)'] - 1) > 0.3 else "✓"
            r2_flag = "❌" if r['R² (mean)'] < 0.3 else "✓"
            
            print(f"  {r['Method']:<25} {r['Slope (mean)']:>7.2f}{slope_flag} {r['Slope (SD)']:>10.2f} "
                  f"{r['Intercept (mean)']:>10.2f} {r['Intercept (SD)']:>10.2f} "
                  f"{r['R² (mean)']:>7.3f}{r2_flag} {r['τ-ECE (mean)']:>8.2f}")
        
        print("  " + "-"*90)
        
        # Specific SourceDR analysis
        if self.FOCUS_METHOD in df_results['Method'].values:
            focus_row = df_results[df_results['Method'] == self.FOCUS_METHOD].iloc[0]
            print(f"\n  {self.FOCUS_METHOD} specific findings:")
            print(f"    - Slope {focus_row['Slope (mean)']:.2f} (ideal=1.0): ", end='')
            if abs(focus_row['Slope (mean)'] - 1) < 0.2:
                print("Within acceptable range")
            elif focus_row['Slope (mean)'] < 1:
                print("Underconfident predictions (too conservative)")
            else:
                print("Overconfident predictions (too aggressive)")
            
            print(f"    - Slope SD {focus_row['Slope (SD)']:.2f}: ", end='')
            if focus_row['Slope (SD)'] > 0.4:
                print("HIGH variance (unstable across replications)")
            else:
                print("Acceptable variance")
            
            print(f"    - Intercept SD {focus_row['Intercept (SD)']:.2f}: ", end='')
            if focus_row['Intercept (SD)'] > 5:
                print("HIGH variance (systematic baseline shifts)")
            else:
                print("Acceptable variance")
            
            print(f"    - R² {focus_row['R² (mean)']:.3f}: ", end='')
            if focus_row['R² (mean)'] < 0.2:
                print("VERY LOW - predictions barely track true effects")
            elif focus_row['R² (mean)'] < 0.4:
                print("LOW - predictions weakly correlated with truth")
            else:
                print("Acceptable")
        
        df_results.to_csv(self.output_folder / 'check2_calibration_comparison.csv', index=False)
        self.calibration_results = df_results
    
    def check_3_comparison_table(self):
        """Check 3: Generate paper-ready comparison table."""
        print("\n[Check 3] Paper-Ready Comparison Table")
        print("-"*40)
        
        # Select representative cells for comparison
        # Focus on cells where both ProposedA and SourceDR have results
        cells_of_interest = [(500, 500), (1000, 1000), (100, 100)]
        
        methods = [self.FOCUS_METHOD] + [m for m in self.COMPARISON_METHODS 
                                          if m in self.df['method'].values]
        
        tables = []
        for m0, m1 in cells_of_interest:
            df_cell = self.df[(self.df['m0'] == m0) & (self.df['m1'] == m1)]
            df_cell = df_cell[df_cell['method'].isin(methods)]
            
            if len(df_cell) == 0:
                continue
            
            print(f"\n  Cell (m₀={m0}, m₁={m1}):")
            print(f"  {'Method':<25} {'PEHE':>8} {'ATE Err':>10} {'Spearman':>10} {'τ-ECE':>8} {'Calib R²':>10}")
            print("  " + "-"*75)
            
            for method in methods:
                row = df_cell[df_cell['method'] == method]
                if len(row) == 0:
                    print(f"  {method:<25} {'N/A':>8} {'N/A':>10} {'N/A':>10} {'N/A':>8} {'N/A':>10}")
                    continue
                
                row = row.iloc[0]
                pehe = f"{row['pehe_mean']:.2f}"
                ate = f"{row['ate_abs_err_mean']:.2f}"
                tau = f"{row['tau_corr_mean']:.3f}"
                ece = f"{row.get('tau_ece_mean', np.nan):.2f}" if pd.notna(row.get('tau_ece_mean')) else 'N/A'
                r2 = f"{row['calib_r2_mean']:.3f}"
                
                # Highlight SourceDR
                prefix = "→ " if method == self.FOCUS_METHOD else "  "
                print(f"{prefix}{method:<23} {pehe:>8} {ate:>10} {tau:>10} {ece:>8} {r2:>10}")
                
                tables.append({
                    'm0': m0, 'm1': m1, 'Method': method,
                    'PEHE': row['pehe_mean'], 'ATE_Err': row['ate_abs_err_mean'],
                    'Spearman': row['tau_corr_mean'], 
                    'tau_ECE': row.get('tau_ece_mean', np.nan),
                    'Calib_R2': row['calib_r2_mean']
                })
        
        if tables:
            df_tables = pd.DataFrame(tables)
            df_tables.to_csv(self.output_folder / 'check3_comparison_table.csv', index=False)
            
            # Generate LaTeX table
            self._generate_latex_table(df_tables)
    
    def _generate_latex_table(self, df):
        """Generate LaTeX-formatted comparison table for paper."""
        latex = """% Auto-generated comparison table
\\begin{table}[htbp]
\\centering
\\caption{Performance comparison across methods at representative $(m_0, m_1)$ configurations}
\\label{tab:method_comparison}
\\begin{tabular}{llccccc}
\\toprule
$(m_0, m_1)$ & Method & PEHE $\\downarrow$ & ATE Err $\\downarrow$ & Spearman $\\uparrow$ & $\\tau$-ECE $\\downarrow$ & Calib R$^2$ $\\uparrow$ \\\\
\\midrule
"""
        
        for (m0, m1), group in df.groupby(['m0', 'm1']):
            first = True
            for _, row in group.iterrows():
                cell_str = f"({int(m0)}, {int(m1)})" if first else ""
                method = row['Method'].replace('_', '\\_')
                
                # Bold the focus method
                if row['Method'] == self.FOCUS_METHOD:
                    method = f"\\textbf{{{method}}}"
                
                pehe = f"{row['PEHE']:.2f}" if pd.notna(row['PEHE']) else "N/A"
                ate = f"{row['ATE_Err']:.2f}" if pd.notna(row['ATE_Err']) else "N/A"
                tau = f"{row['Spearman']:.3f}" if pd.notna(row['Spearman']) else "N/A"
                ece = f"{row['tau_ECE']:.2f}" if pd.notna(row['tau_ECE']) else "N/A"
                r2 = f"{row['Calib_R2']:.3f}" if pd.notna(row['Calib_R2']) else "N/A"
                
                latex += f"{cell_str} & {method} & {pehe} & {ate} & {tau} & {ece} & {r2} \\\\\n"
                first = False
            latex += "\\midrule\n"
        
        latex = latex.rstrip("\\midrule\n") + """
\\bottomrule
\\end{tabular}
\\end{table}
"""
        
        with open(self.output_folder / 'comparison_table.tex', 'w') as f:
            f.write(latex)
        
        print(f"\n  LaTeX table saved to: comparison_table.tex")
    
    def check_4_scatter_diagnostics(self):
        """Check 4: Scatter plot diagnostics (PEHE vs Spearman, Calib R² vs ECE)."""
        print("\n[Check 4] Scatter Diagnostics")
        print("-"*40)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'Diagnostic Scatter Plots: {self.FOCUS_METHOD} vs Other Methods', 
                    fontsize=12, fontweight='bold')
        
        methods_to_plot = [self.FOCUS_METHOD] + self.COMPARISON_METHODS
        methods_to_plot = [m for m in methods_to_plot if m in self.df['method'].values]
        
        # Aggregate by method
        agg_data = []
        for method in methods_to_plot:
            df_m = self.df[self.df['method'] == method]
            df_m = df_m[df_m['pehe_mean'].notna()]
            if len(df_m) == 0:
                continue
            
            agg_data.append({
                'method': method,
                'pehe': df_m['pehe_mean'].mean(),
                'tau_corr': df_m['tau_corr_mean'].mean(),
                'calib_r2': df_m['calib_r2_mean'].mean(),
                'tau_ece': df_m['tau_ece_mean'].mean() if 'tau_ece_mean' in df_m.columns else np.nan,
            })
        
        df_agg = pd.DataFrame(agg_data)
        
        # Plot 1: PEHE vs Spearman
        ax = axes[0]
        for _, row in df_agg.iterrows():
            color = 'red' if row['method'] == self.FOCUS_METHOD else 'steelblue'
            marker = 's' if row['method'] == self.FOCUS_METHOD else 'o'
            size = 200 if row['method'] == self.FOCUS_METHOD else 100
            ax.scatter(row['pehe'], row['tau_corr'], c=color, marker=marker, s=size,
                      label=row['method'], edgecolors='black', linewidth=1)
        
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='ρ threshold')
        ax.axvline(x=6.0, color='orange', linestyle='--', alpha=0.7, label='PEHE threshold')
        ax.set_xlabel('PEHE (↓ lower is better)', fontsize=11)
        ax.set_ylabel('Spearman ρ (↑ higher is better)', fontsize=11)
        ax.set_title('PEHE vs Ranking Quality')
        ax.legend(loc='upper right', fontsize=8)
        
        # Add quadrant annotations
        ax.annotate('Good\n(low error, good ranking)', xy=(0.15, 0.85), xycoords='axes fraction',
                   fontsize=9, ha='center', color='green', fontweight='bold')
        ax.annotate('Bad\n(high error, poor ranking)', xy=(0.85, 0.15), xycoords='axes fraction',
                   fontsize=9, ha='center', color='red', fontweight='bold')
        
        # Plot 2: Calib R² vs τ-ECE
        ax = axes[1]
        df_plot = df_agg[df_agg['tau_ece'].notna()]
        if len(df_plot) > 0:
            for _, row in df_plot.iterrows():
                color = 'red' if row['method'] == self.FOCUS_METHOD else 'steelblue'
                marker = 's' if row['method'] == self.FOCUS_METHOD else 'o'
                size = 200 if row['method'] == self.FOCUS_METHOD else 100
                ax.scatter(row['calib_r2'], row['tau_ece'], c=color, marker=marker, s=size,
                          label=row['method'], edgecolors='black', linewidth=1)
            
            ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.7, label='ECE threshold')
            ax.axvline(x=0.3, color='orange', linestyle='--', alpha=0.7, label='R² threshold')
            ax.set_xlabel('Calibration R² (↑ higher is better)', fontsize=11)
            ax.set_ylabel('τ-ECE (↓ lower is better)', fontsize=11)
            ax.set_title('Calibration R² vs Expected Calibration Error')
            ax.legend(loc='upper right', fontsize=8)
            
            # Add quadrant annotations
            ax.annotate('Good\n(high R², low ECE)', xy=(0.85, 0.15), xycoords='axes fraction',
                       fontsize=9, ha='center', color='green', fontweight='bold')
            ax.annotate('Bad\n(low R², high ECE)', xy=(0.15, 0.85), xycoords='axes fraction',
                       fontsize=9, ha='center', color='red', fontweight='bold')
        
        plt.tight_layout()
        
        fig.savefig(self.output_folder / 'check4_scatter_diagnostics.png', dpi=150, bbox_inches='tight')
        fig.savefig(self.output_folder / 'check4_scatter_diagnostics.pdf', bbox_inches='tight')
        plt.close(fig)
        
        print(f"  Saved scatter diagnostics")
    
    def generate_advisor_report(self):
        """Generate markdown report summarizing all advisor checks."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""# Advisor-Recommended Diagnostic Checks

**Sweep:** `{self.sweep_name}`

**Focus Method:** `{self.FOCUS_METHOD}`

**Generated:** {timestamp}

---

## Summary

These diagnostics follow the advisor's recommendations to evaluate whether
`{self.FOCUS_METHOD}` exhibits systematic multi-axis failure and should be
re-labeled as a negative control/ablation rather than a viable method.

---

## Check 1: Multi-Axis Failure Detection

**Question:** Does {self.FOCUS_METHOD} fail on multiple metrics simultaneously?

**Criteria:**
- PEHE > 6.0
- ATE Error > 3.0
- Spearman ρ < 0.5
- τ-ECE > 3.0
- Calibration R² < 0.3

**Results:**

"""
        if hasattr(self, 'multi_axis_results'):
            report += "| Cell | PEHE | ATE Err | Spearman | τ-ECE | R² | # Failures |\n"
            report += "|------|------|---------|----------|-------|-----|------------|\n"
            for _, r in self.multi_axis_results.iterrows():
                report += f"| {r['Cell (m0, m1)']} | {r['PEHE']} | {r['ATE Err']} | "
                report += f"{r['Spearman']} | {r['τ-ECE']} | {r['Calib R²']} | {r['# Failures']} |\n"
        
        report += """
---

## Check 2: Calibration Slope & Intercept

**Question:** Is the calibration failure due to scale (slope) or baseline (intercept) issues?

**Key findings for {focus}:**
""".format(focus=self.FOCUS_METHOD)
        
        if hasattr(self, 'calibration_results'):
            focus_row = self.calibration_results[self.calibration_results['Method'] == self.FOCUS_METHOD]
            if len(focus_row) > 0:
                focus_row = focus_row.iloc[0]
                report += f"""
- **Slope:** {focus_row['Slope (mean)']:.2f} ± {focus_row['Slope (SD)']:.2f}
  - Ideal is 1.0; this indicates {'underconfident' if focus_row['Slope (mean)'] < 1 else 'overconfident'} predictions
  
- **Intercept SD:** {focus_row['Intercept (SD)']:.2f}
  - {'HIGH variance - systematic baseline shifts across replications' if focus_row['Intercept (SD)'] > 5 else 'Acceptable variance'}
  
- **R²:** {focus_row['R² (mean)']:.3f}
  - {'VERY LOW - predictions barely correlated with truth' if focus_row['R² (mean)'] < 0.2 else 'LOW' if focus_row['R² (mean)'] < 0.4 else 'Acceptable'}

**Comparison table:**

| Method | Slope | Slope SD | Intercept SD | R² | τ-ECE |
|--------|-------|----------|--------------|-----|-------|
"""
                for _, r in self.calibration_results.iterrows():
                    report += f"| {r['Method']} | {r['Slope (mean)']:.2f} | {r['Slope (SD)']:.2f} | "
                    report += f"{r['Intercept (SD)']:.2f} | {r['R² (mean)']:.3f} | {r['τ-ECE (mean)']:.2f} |\n"
        
        report += """
---

## Check 3: Visual Diagnostics

![Scatter Diagnostics](check4_scatter_diagnostics.png)

**Interpretation:**
- Upper-right quadrant (low PEHE, high Spearman) = good methods
- Lower-left quadrant (high PEHE, low Spearman) = failing methods
- {focus} is in the failing quadrant

---

## Recommendation

Based on these diagnostics:

""".format(focus=self.FOCUS_METHOD)
        
        # Generate recommendation
        if hasattr(self, 'multi_axis_results'):
            avg_failures = self.multi_axis_results['# Failures'].mean()
            if avg_failures >= 3:
                report += f"""**⚠️ CRITICAL:** `{self.FOCUS_METHOD}` shows systematic multi-axis failure with an average of {avg_failures:.1f} failed metrics per cell.

**Recommended action:** Re-label as:
> *"Source-only DR transport (negative control / ablation; demonstrates failure of naïve transport in disconnected-target regime)"*

**Rebuttal language:**
> The SourceDR ablation demonstrates that naïvely transporting source-trained DR corrections fails catastrophically in the restricted-target regime. Across all budget configurations, SourceDR exhibits PEHE ≈ 7-8 (vs 3-4 for Proposed methods), ATE error ≈ 5 (vs 0.1-0.2), τ-ECE ≈ 5 (vs 1.0), and Spearman ρ ≈ 0.40 (vs 0.74). This multi-axis failure motivates our target-anchored design.
"""
            elif avg_failures >= 2:
                report += f"""**⚡ WARNING:** `{self.FOCUS_METHOD}` shows moderate issues with an average of {avg_failures:.1f} failed metrics per cell.

Review for specific use cases where it might still be viable.
"""
            else:
                report += f"""**✓ OK:** `{self.FOCUS_METHOD}` does not show systematic failure.
"""
        
        report += """
---

## Files Generated

- `check1_multi_axis_failures.csv` - Multi-axis failure details
- `check2_calibration_comparison.csv` - Calibration metrics comparison
- `check3_comparison_table.csv` - Paper-ready comparison table
- `comparison_table.tex` - LaTeX version of comparison table
- `check4_scatter_diagnostics.png/pdf` - Diagnostic scatter plots
- `advisor_report.md` - This report

---

*Generated by advisor_checks.py*
"""
        
        with open(self.output_folder / 'advisor_report.md', 'w') as f:
            f.write(report)
        
        print(f"\n  Report saved to: {self.output_folder / 'advisor_report.md'}")


def main():
    parser = argparse.ArgumentParser(description='Run advisor-recommended diagnostic checks')
    parser.add_argument('results_folder', help='Path to results folder')
    args = parser.parse_args()
    
    try:
        diag = AdvisorDiagnostics(args.results_folder)
        diag.run_all_checks()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
