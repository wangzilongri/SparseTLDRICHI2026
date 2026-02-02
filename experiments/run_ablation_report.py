#!/usr/bin/env python
"""
Generate comprehensive ablation benchmark report with full methodology.

This script:
1. Runs Monte Carlo experiments with all ablation methods
2. Computes comprehensive metrics (accuracy, ranking, calibration, policy)
3. Generates plots (bar chart, radar, heatmap)
4. Creates a full methodology report with DGP, estimators, and metric definitions
5. Compiles the report to PDF

Usage:
    python experiments/run_ablation_report.py
    python experiments/run_ablation_report.py --n_mc 50 --output results/my_report
"""

import sys
import os
import argparse
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import warnings
warnings.filterwarnings('ignore')


def run_ablation_benchmark(n_mc=30, output_dir='results/ablation_full_report', 
                           verbose=True):
    """
    Run ablation benchmark and generate comprehensive methodology report.
    
    Parameters
    ----------
    n_mc : int
        Number of Monte Carlo replicates
    output_dir : str
        Output directory for all files
    verbose : bool
        Print progress
        
    Returns
    -------
    aggregated_results : dict
        Results dictionary {method: {metric: value}}
    report_path : str
        Path to generated markdown report
    """
    import matplotlib
    matplotlib.use('Agg')
    
    from synthetic_data_v2 import SyntheticRCTGenerator, SyntheticRCTConfig
    from estimator_fixed import PlaceboAnchoredDRLearner
    from ablations import ProxyOnlyBaseline, AnchorOnlyBaseline, NoTransferBaseline
    from metrics import (
        pehe, ate_error, cate_rank_correlation, qini_auc,
        cate_calibration_slope_intercept, cate_ece, policy_metrics,
        topk_uplift_capture
    )
    
    print('=' * 70)
    print('ABLATION BENCHMARK - Full Methodology Report')
    print(f'Monte Carlo replicates: {n_mc}')
    print(f'Output directory: {output_dir}')
    print('=' * 70)
    
    # ═══════════════════════════════════════════════════════════════════════
    # DGP Configuration (matches A5/A6 assumptions)
    # ═══════════════════════════════════════════════════════════════════════
    dgp_config = {
        'n_features': 5,
        'n_source_sites': 10,
        'n_source_per_site': 500,
        'n_target': 400,
        'treatment_prob': 0.5,
        'noise_std': 0.5,
        'covariate_shift_scale': 1.0,
        'target_shift_multiplier': 1.5,
        'dev_sparsity': 2,
        'dev_scale': 0.4,
        'transfer_rank': 2,
        'transfer_strength': 1.0,
        'nontransfer_scale_source': 0.05,
        'nontransfer_scale_target': 0.2,
        'misspec_scale': 0.0,
        'target_treated_frac': 0.0,  # Disconnected target (Step B scenario)
    }
    
    # ═══════════════════════════════════════════════════════════════════════
    # Collect results across MC replicates
    # ═══════════════════════════════════════════════════════════════════════
    all_results = {
        'No-Transfer': [],
        'Proxy-Only': [],
        'Anchor-Only': [],
        'Proposed-A': [],
        'Proposed-B (StepB)': [],
    }
    
    # Track Step B diagnostics
    stepb_diagnostics = []
    
    for mc in range(n_mc):
        seed = 42 + mc
        
        # Generate data
        config = SyntheticRCTConfig(
            n_features=dgp_config['n_features'],
            n_source_sites=dgp_config['n_source_sites'],
            n_source_per_site=dgp_config['n_source_per_site'],
            n_target=dgp_config['n_target'],
            treatment_prob=dgp_config['treatment_prob'],
            noise_std=dgp_config['noise_std'],
            covariate_shift_scale=dgp_config['covariate_shift_scale'],
            target_shift_multiplier=dgp_config['target_shift_multiplier'],
            dev_sparsity=dgp_config['dev_sparsity'],
            dev_scale=dgp_config['dev_scale'],
            transfer_rank=dgp_config['transfer_rank'],
            transfer_strength=dgp_config['transfer_strength'],
            nontransfer_scale_source=dgp_config['nontransfer_scale_source'],
            nontransfer_scale_target=dgp_config['nontransfer_scale_target'],
            misspec_scale=dgp_config['misspec_scale'],
            target_treated_frac=dgp_config['target_treated_frac'],
            random_state=seed
        )
        gen = SyntheticRCTGenerator(config)
        source_data, target_data = gen.generate_full_dataset()
        
        # Split target into train/test (stratified would be ideal but A=0 only here)
        n = len(target_data['X'])
        idx = np.random.RandomState(seed).permutation(n)
        train_idx, test_idx = idx[:n//2], idx[n//2:]
        
        target_train = {k: v[train_idx] for k, v in target_data.items()}
        target_test = {k: v[test_idx] for k, v in target_data.items()}
        
        X_test = target_test['X']
        tau_true = target_test['tau_true']
        mu0_true = target_test['mu0_true']
        mu1_true = target_test['mu1_true']
        
        # Create estimators
        methods = {
            'No-Transfer': NoTransferBaseline(random_state=seed),
            'Proxy-Only': ProxyOnlyBaseline(random_state=seed),
            'Anchor-Only': AnchorOnlyBaseline(option='A', random_state=seed),
            'Proposed-A': PlaceboAnchoredDRLearner(option='A', n_folds=3, random_state=seed, verbose=False),
            'Proposed-B (StepB)': PlaceboAnchoredDRLearner(option='B', n_folds=3, random_state=seed, verbose=False),
        }
        
        for name, est in methods.items():
            try:
                # Fit
                est.fit(
                    source_data['X'], source_data['A'], source_data['Y'], source_data['c'],
                    target_train['X'], target_train['A'], target_train['Y']
                )
                tau_pred = est.predict(X_test)
                
                # Collect Step B diagnostics
                if name == 'Proposed-B (StepB)' and hasattr(est, 'transfer_diagnostics_'):
                    stepb_diagnostics.append(est.transfer_diagnostics_)
                
                # ═══════════════════════════════════════════════════════════════
                # Compute ALL metrics
                # ═══════════════════════════════════════════════════════════════
                metrics = {}
                
                # Accuracy
                metrics['pehe'] = float(pehe(tau_true, tau_pred))
                metrics['ate_error'] = float(ate_error(tau_true, tau_pred))
                
                # Ranking
                try:
                    rho, pval = cate_rank_correlation(tau_true, tau_pred, method='spearman')
                    metrics['spearman_corr'] = float(rho) if not np.isnan(rho) else np.nan
                    metrics['spearman_pval'] = float(pval) if pval is not None else np.nan
                except:
                    metrics['spearman_corr'] = metrics['spearman_pval'] = np.nan
                
                try:
                    metrics['qini_auc'] = float(qini_auc(tau_true, tau_pred))
                except:
                    metrics['qini_auc'] = np.nan
                
                try:
                    metrics['topk_10_ratio'] = float(topk_uplift_capture(tau_true, tau_pred, k=0.1))
                    metrics['topk_30_ratio'] = float(topk_uplift_capture(tau_true, tau_pred, k=0.3))
                except:
                    metrics['topk_10_ratio'] = metrics['topk_30_ratio'] = np.nan
                
                # Calibration (note: function returns intercept, slope, r2, degenerate)
                try:
                    intercept, slope, r2, calib_degenerate = cate_calibration_slope_intercept(tau_true, tau_pred)
                    metrics['calib_slope'] = float(slope) if slope is not None and not np.isnan(slope) else np.nan
                    metrics['calib_intercept'] = float(intercept) if intercept is not None and not np.isnan(intercept) else np.nan
                    metrics['calib_r2'] = float(r2) if r2 is not None and not np.isnan(r2) else np.nan
                    metrics['calib_degenerate'] = calib_degenerate
                except:
                    metrics['calib_slope'] = metrics['calib_intercept'] = metrics['calib_r2'] = np.nan
                    metrics['calib_degenerate'] = True
                
                try:
                    # cate_ece returns (ece, mce, details) tuple
                    ece_result = cate_ece(tau_true, tau_pred)
                    metrics['cate_ece'] = float(ece_result[0])  # ECE
                    metrics['cate_mce'] = float(ece_result[1])  # MCE
                except:
                    metrics['cate_ece'] = metrics['cate_mce'] = np.nan
                
                # Policy (oracle-based using true mu0, mu1)
                try:
                    pm = policy_metrics(tau_true, tau_pred, mu0_true, mu1_true)
                    # Use treat_positive policy (treat if predicted CATE > 0)
                    metrics['policy_value'] = float(pm['value_treat_positive'])
                    metrics['policy_regret'] = float(pm['regret_treat_positive'])
                    metrics['oracle_value'] = float(pm['value_oracle'])
                except:
                    metrics['policy_value'] = metrics['policy_regret'] = metrics['oracle_value'] = np.nan
                
                all_results[name].append(metrics)
                
            except Exception as e:
                if verbose:
                    print(f'  MC {mc}, {name} failed: {e}')
        
        if verbose and (mc + 1) % 10 == 0:
            print(f'  Progress: {mc+1}/{n_mc} MC replicates')
    
    # ═══════════════════════════════════════════════════════════════════════
    # Aggregate results: compute mean (and optionally std) across MC
    # ═══════════════════════════════════════════════════════════════════════
    aggregated_results = {}
    aggregated_std = {}
    
    for method, runs in all_results.items():
        if len(runs) == 0:
            continue
        
        aggregated_results[method] = {}
        aggregated_std[method] = {}
        metric_names = runs[0].keys()
        
        for metric in metric_names:
            values = [r[metric] for r in runs if r.get(metric) is not None and not np.isnan(r.get(metric, np.nan))]
            if len(values) > 0:
                aggregated_results[method][metric] = float(np.mean(values))
                aggregated_std[method][f'{metric}_std'] = float(np.std(values))
            else:
                aggregated_results[method][metric] = np.nan
                aggregated_std[method][f'{metric}_std'] = np.nan
    
    # ═══════════════════════════════════════════════════════════════════════
    # Generate report using metrics.py
    # ═══════════════════════════════════════════════════════════════════════
    os.makedirs(output_dir, exist_ok=True)
    
    from metrics import generate_results_report
    
    report_path = generate_results_report(
        results=aggregated_results,
        output_dir=output_dir,
        experiment_name='ablation_methodology',
        dgp_config=dgp_config,
        save_plots=True,
        embed_images=True,
        embed_csv=True,
        include_methodology=True
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Append additional analysis sections to the report
    # ═══════════════════════════════════════════════════════════════════════
    _append_analysis_section(report_path, aggregated_results, aggregated_std, 
                            stepb_diagnostics, dgp_config, n_mc)
    
    print(f'\n✓ Report generated: {report_path}')
    
    # ═══════════════════════════════════════════════════════════════════════
    # Compile to PDF (always, unless explicitly disabled)
    # ═══════════════════════════════════════════════════════════════════════
    _compile_to_pdf(report_path, output_dir)
    
    print(f'\nFiles in {output_dir}:')
    for f in sorted(os.listdir(output_dir)):
        print(f'  - {f}')
    
    return aggregated_results, report_path


def _append_analysis_section(report_path, results, results_std, stepb_diag, dgp_config, n_mc):
    """Append analysis and interpretation section to the report."""
    
    with open(report_path, 'a') as f:
        f.write('\n---\n\n')
        f.write('## Analysis and Interpretation\n\n')
        
        # Monte Carlo info
        f.write(f'### Monte Carlo Summary\n\n')
        f.write(f'- **Number of replicates:** {n_mc}\n')
        f.write(f'- **Target scenario:** Disconnected (placebo only, `target_treated_frac=0.0`)\n')
        f.write(f'- **This tests Step B:** Cross-arm transfer via learned operator M*\n\n')
        
        # Results with standard deviations
        f.write('### Results with Standard Deviations\n\n')
        f.write('| Method | PEHE | ATE Error | Spearman | Qini AUC |\n')
        f.write('|--------|------|-----------|----------|----------|\n')
        
        for method in ['No-Transfer', 'Proxy-Only', 'Anchor-Only', 'Proposed-A', 'Proposed-B (StepB)']:
            if method not in results:
                continue
            r = results[method]
            s = results_std.get(method, {})
            
            pehe_str = f"{r.get('pehe', np.nan):.3f}±{s.get('pehe_std', 0):.3f}"
            ate_str = f"{r.get('ate_error', np.nan):.3f}±{s.get('ate_error_std', 0):.3f}"
            sp = r.get('spearman_corr', np.nan)
            sp_str = f"{sp:.3f}" if not np.isnan(sp) else "N/A"
            qini = r.get('qini_auc', np.nan)
            qini_str = f"{qini:.3f}" if not np.isnan(qini) else "N/A"
            
            f.write(f'| {method} | {pehe_str} | {ate_str} | {sp_str} | {qini_str} |\n')
        
        f.write('\n')
        
        # Step B diagnostics
        if stepb_diag:
            f.write('### Step B Transfer Operator Diagnostics\n\n')
            
            # Average across MC
            avg_diag = {}
            for key in ['n_sites_used', 'M_fro_norm', 'M_spectral_norm', 'M_effective_rank']:
                vals = [d.get(key, np.nan) for d in stepb_diag if key in d]
                if vals:
                    avg_diag[key] = np.mean([v for v in vals if not np.isnan(v)])
            
            f.write('| Diagnostic | Value |\n')
            f.write('|------------|-------|\n')
            f.write(f"| Sites used for M estimation | {avg_diag.get('n_sites_used', 'N/A'):.0f} |\n")
            f.write(f"| ||M̂||_F (Frobenius norm) | {avg_diag.get('M_fro_norm', np.nan):.3f} |\n")
            f.write(f"| ||M̂||_2 (Spectral norm) | {avg_diag.get('M_spectral_norm', np.nan):.3f} |\n")
            f.write(f"| Effective rank(M̂) | {avg_diag.get('M_effective_rank', np.nan):.1f} |\n")
            f.write('\n')
        
        # Key findings - dynamically compute from actual results
        f.write('### Key Findings\n\n')
        
        # Find best method for each key metric
        valid_pehe = [(m, r.get('pehe', np.inf)) for m, r in results.items() if not np.isnan(r.get('pehe', np.nan))]
        valid_ate = [(m, abs(r.get('ate_error', np.inf))) for m, r in results.items() if not np.isnan(r.get('ate_error', np.nan))]
        valid_spearman = [(m, r.get('spearman_corr', -np.inf)) for m, r in results.items() if not np.isnan(r.get('spearman_corr', np.nan))]
        valid_qini = [(m, r.get('qini_auc', -np.inf)) for m, r in results.items() if not np.isnan(r.get('qini_auc', np.nan))]
        
        best_pehe = min(valid_pehe, key=lambda x: x[1])[0] if valid_pehe else 'N/A'
        best_pehe_val = min(valid_pehe, key=lambda x: x[1])[1] if valid_pehe else np.nan
        best_ate = min(valid_ate, key=lambda x: x[1])[0] if valid_ate else 'N/A'
        best_spearman = max(valid_spearman, key=lambda x: x[1])[0] if valid_spearman else 'N/A'
        best_qini = max(valid_qini, key=lambda x: x[1])[0] if valid_qini else 'N/A'
        
        f.write(f'1. **Best PEHE:** {best_pehe} ({best_pehe_val:.4f}) achieves the lowest prediction error\n')
        f.write(f'2. **Best ATE:** {best_ate} achieves lowest ATE estimation error\n')
        f.write(f'3. **Best Ranking:** {best_spearman} (Spearman), {best_qini} (Qini AUC)\n')
        f.write('4. **Proxy-Only ≈ Anchor-Only:** In disconnected target scenario, both rely on proxy-only predictions\n')
        f.write('5. **No-Transfer fails:** Predicts constant CATE (zero Spearman correlation)\n\n')
        
        # Policy regret interpretation
        f.write('### Policy Regret Interpretation\n\n')
        f.write('**Important:** Policy value/regret is computed w.r.t. the oracle within the *same policy class* ')
        f.write('(treat-if-$\\hat{\\tau}>0$ or budgeted top-$k$).\n\n')
        f.write('A method may show low regret if:\n')
        f.write('- The oracle treats very few individuals (most true $\\tau < 0$)\n')
        f.write('- The learned policy happens to also treat few (conservative)\n')
        f.write('- This does **not** imply good CATE estimation!\n\n')
        f.write('**Always interpret policy metrics alongside PEHE and ranking metrics.**\n\n')
        
        # Why this matters
        f.write('### Why Step B Matters\n\n')
        f.write('In the disconnected target scenario (`target_treated_frac=0.0`):\n\n')
        f.write('- Target has **only placebo** (A=0) samples\n')
        f.write('- Cannot directly estimate treated outcome correction $\\delta_1$\n')
        f.write('- **Step B solution:** Learn $M^*$ from sources where both arms exist\n')
        f.write('- Apply: $\\hat{\\beta}_1 = \\hat{M} \\cdot \\hat{\\beta}_0$ (transfer placebo correction to treated arm)\n\n')
        
        f.write('This is the key innovation tested in this benchmark.\n')


def _compile_to_pdf(report_path, output_dir):
    """Compile markdown to PDF using pandoc (best) or fpdf2 (fallback)."""
    import shutil
    import subprocess
    import os
    
    pdf_path = report_path.replace('.md', '.pdf')
    
    # Try pandoc (produces proper LaTeX rendering)
    pandoc_cmd = shutil.which('pandoc')
    if pandoc_cmd:
        print(f'\nCompiling to PDF with pandoc...')
        try:
            # Run from the output directory so relative image paths work
            result = subprocess.run(
                [pandoc_cmd, 
                 os.path.basename(report_path),  # Just filename
                 '-o', os.path.basename(pdf_path),
                 '--pdf-engine=xelatex',
                 '-V', 'geometry:margin=1in',
                 '-V', 'fontsize=11pt',
                 '--toc'],
                capture_output=True, text=True, timeout=120,
                cwd=output_dir  # Run from output dir for relative paths
            )
            if result.returncode == 0:
                print(f'✓ PDF saved: {pdf_path}')
                if result.stderr:
                    # Show warnings but not as errors
                    warnings = [l for l in result.stderr.split('\n') if 'WARNING' in l]
                    if warnings:
                        print(f'  ({len(warnings)} warnings about fonts/images)')
                return pdf_path
            else:
                print(f'Pandoc error: {result.stderr[:300]}')
        except subprocess.TimeoutExpired:
            print('Pandoc timed out')
        except Exception as e:
            print(f'Pandoc failed: {e}')
    
    # Fallback to fpdf2 (no LaTeX rendering, but works without dependencies)
    print('Falling back to fpdf2 (LaTeX will show as plain text)...')
    try:
        from metrics import compile_report_to_pdf
        pdf_path = compile_report_to_pdf(report_path, pdf_path)
        print(f'✓ PDF saved: {pdf_path}')
        return pdf_path
    except Exception as e:
        print(f'PDF compilation failed: {e}')
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Run ablation benchmark and generate comprehensive methodology report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python experiments/run_ablation_report.py
    python experiments/run_ablation_report.py --n_mc 50
    python experiments/run_ablation_report.py --output results/my_ablation
        """
    )
    parser.add_argument('--n_mc', type=int, default=30, 
                        help='Number of Monte Carlo replicates (default: 30)')
    parser.add_argument('--output', type=str, default='results/ablation_full_report', 
                        help='Output directory (default: results/ablation_full_report)')
    args = parser.parse_args()
    
    run_ablation_benchmark(
        n_mc=args.n_mc, 
        output_dir=args.output
    )


if __name__ == '__main__':
    main()
