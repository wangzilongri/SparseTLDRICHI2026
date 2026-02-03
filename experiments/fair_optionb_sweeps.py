"""
Fair OptionB Evaluation Sweeps

Implements advisor-recommended sweep design for evaluating OptionB (ProposedB_SourceDR)
in its intended validity regime.

Three structured sweeps:
1. Cross-arm validity (SNR ladder) - primary
2. Overlap stress (AUC ladder)
3. Drift stress (intercept ladder)

Each sweep isolates ONE axis while holding others at fair values.

Usage:
    python experiments/fair_optionb_sweeps.py --sweep cross_arm_validity --n_rep 20
    python experiments/fair_optionb_sweeps.py --all --n_rep 20
"""

import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from synthetic_data_v2_fair import (
    FairSyntheticRCTConfig, 
    FairSyntheticRCTGenerator,
    FAIR_SWEEP_CONFIGS,
)
from estimator_fixed import PlaceboAnchoredDRLearner
from metrics import (
    pehe, 
    ate_error, 
    cate_rank_correlation,
    cate_calibration_slope_intercept,
    cate_ece,
    qini_auc,
    topk_uplift_capture,
)


@dataclass
class FairSweepResult:
    """Result from one sweep cell."""
    sweep_name: str
    sweep_param: str
    sweep_value: float
    rep: int
    method: str
    
    # Fairness diagnostics
    target_SNR: float
    overlap_auc: float
    intercept_drift_scale: float
    cross_arm_corr: float
    fair_for_optionB: bool
    
    # Performance metrics
    pehe: float
    ate_error: float
    ate_bias: float
    spearman: float
    kendall: float
    calib_slope: float
    calib_intercept: float
    calib_r2: float
    tau_ece: float
    qini_auc: float
    topk_10_ratio: float
    topk_20_ratio: float


def run_single_cell(
    config_kwargs: Dict,
    sweep_name: str,
    sweep_param: str,
    sweep_value: float,
    rep: int,
    methods: List[str],
    random_seed: int,
) -> List[FairSweepResult]:
    """Run all methods for one cell of the sweep."""
    
    # Update random state for replication
    config_kwargs = config_kwargs.copy()
    config_kwargs['random_state'] = random_seed
    
    # Generate data
    config = FairSyntheticRCTConfig(**config_kwargs)
    gen = FairSyntheticRCTGenerator(config)
    source_data, target_data = gen.generate_full_dataset()
    
    # Get fairness diagnostics
    diag = gen.get_fairness_diagnostics()
    
    # Prepare benchmark data format
    X_source = source_data['X']
    A_source = source_data['A']
    Y_source = source_data['Y']
    c_source = source_data['c']
    
    X_target = target_data['X']
    A_target = target_data['A']
    Y_target = target_data['Y']
    tau_true = target_data['tau_true']
    
    # Propensity (RCT)
    propensity_target = np.full(len(X_target), config.treatment_prob)
    if config.target_treated_frac is not None:
        propensity_target = np.full(len(X_target), config.target_treated_frac)
    elif config.treatment_prob_target is not None:
        propensity_target = np.full(len(X_target), config.treatment_prob_target)
    
    results = []
    
    for method_name in methods:
        try:
            # Determine estimator config
            if method_name == 'ProposedB_SourceDR':
                variant = 'proposed_B_source_dr'
                uses_target_treated = False
            elif method_name == 'ProposedB_LinearStepB':
                variant = 'proposed_B'
                uses_target_treated = True
            elif method_name == 'ProposedA':
                variant = 'proposed_A'
                uses_target_treated = True
            elif method_name == 'OracleTarget':
                variant = None  # Special case
                uses_target_treated = True
            else:
                continue
            
            # Filter data for method
            if uses_target_treated:
                X_method = X_target
                A_method = A_target
                Y_method = Y_target
                prop_method = propensity_target
                
                # Skip if no treated in target (for methods that need it)
                if np.sum(A_target) == 0:
                    continue
            else:
                # SourceDR uses all target data but doesn't need treated outcomes
                X_method = X_target
                A_method = A_target
                Y_method = Y_target
                prop_method = propensity_target
            
            # Fit estimator
            if method_name == 'OracleTarget':
                # Simple oracle: train T-learner directly on target
                from sklearn.linear_model import Ridge
                
                mask0 = A_target == 0
                mask1 = A_target == 1
                
                if np.sum(mask0) > 0 and np.sum(mask1) > 0:
                    m0 = Ridge(alpha=1.0).fit(X_target[mask0], Y_target[mask0])
                    m1 = Ridge(alpha=1.0).fit(X_target[mask1], Y_target[mask1])
                    tau_hat = m1.predict(X_target) - m0.predict(X_target)
                else:
                    continue
            else:
                estimator = PlaceboAnchoredDRLearner(
                    variant=variant,
                    n_folds=2,
                )
                
                estimator.fit(
                    X_source=X_source,
                    A_source=A_source,
                    Y_source=Y_source,
                    c_source=c_source,
                    X_target=X_method,
                    A_target=A_method,
                    Y_target=Y_method,
                    propensity_target=prop_method,
                )
                
                tau_hat = estimator.predict(X_target)
            
            # Compute metrics
            pehe_val = pehe(tau_true, tau_hat)
            ate_err = ate_error(tau_true, tau_hat)
            ate_bias_val = np.mean(tau_hat) - np.mean(tau_true)
            
            # Rank correlation (returns tuple (corr, pval))
            spearman_val, _ = cate_rank_correlation(tau_true, tau_hat, method='spearman')
            kendall_val, _ = cate_rank_correlation(tau_true, tau_hat, method='kendall')
            
            # Calibration (returns tuple: intercept, slope, r_squared, degenerate)
            calib_intercept_val, calib_slope_val, calib_r2_val, _ = cate_calibration_slope_intercept(tau_true, tau_hat)
            
            tau_ece_result = cate_ece(tau_true, tau_hat, n_bins=10)
            tau_ece_val = tau_ece_result[0] if isinstance(tau_ece_result, tuple) else tau_ece_result
            
            try:
                qini_val = qini_auc(tau_true, tau_hat, Y_target, A_target)
            except:
                qini_val = np.nan
            
            try:
                topk_10 = topk_uplift_capture(tau_true, tau_hat, k_fraction=0.1)
            except:
                topk_10 = np.nan
            
            try:
                topk_20 = topk_uplift_capture(tau_true, tau_hat, k_fraction=0.2)
            except:
                topk_20 = np.nan
            
            result = FairSweepResult(
                sweep_name=sweep_name,
                sweep_param=sweep_param,
                sweep_value=sweep_value,
                rep=rep,
                method=method_name,
                
                target_SNR=diag.get('target_SNR', np.nan),
                overlap_auc=diag.get('overlap_auc', np.nan),
                intercept_drift_scale=config.intercept_drift_scale,
                cross_arm_corr=diag.get('cross_arm_corr', np.nan),
                fair_for_optionB=diag.get('fair_for_optionB', False),
                
                pehe=pehe_val,
                ate_error=ate_err,
                ate_bias=ate_bias_val,
                spearman=spearman_val,
                kendall=kendall_val,
                calib_slope=calib_slope_val,
                calib_intercept=calib_intercept_val,
                calib_r2=calib_r2_val,
                tau_ece=tau_ece_val,
                qini_auc=qini_val,
                topk_10_ratio=topk_10,
                topk_20_ratio=topk_20,
            )
            results.append(result)
            
        except Exception as e:
            print(f"Error in {method_name} rep {rep}: {e}")
            continue
    
    return results


def run_sweep(
    sweep_name: str,
    n_rep: int = 20,
    n_jobs: int = 4,
    methods: List[str] = None,
) -> pd.DataFrame:
    """
    Run one of the advisor-recommended sweeps.
    
    Args:
        sweep_name: One of 'cross_arm_validity', 'overlap_stress', 'drift_stress', 'fair_grid'
        n_rep: Number of replications per cell
        n_jobs: Parallel jobs
        methods: Methods to evaluate
    """
    
    if methods is None:
        methods = ['ProposedA', 'ProposedB_LinearStepB', 'ProposedB_SourceDR', 'OracleTarget']
    
    sweep_config = FAIR_SWEEP_CONFIGS[sweep_name]
    fixed_params = sweep_config.get('fixed', {})
    sweep_params = sweep_config['sweep']
    
    # Generate all cells
    cells = []
    
    if len(sweep_params) == 1:
        # 1D sweep
        param_name = list(sweep_params.keys())[0]
        param_values = sweep_params[param_name]
        
        for val in param_values:
            for rep in range(n_rep):
                config_kwargs = {**fixed_params, param_name: val}
                cells.append((config_kwargs, sweep_name, param_name, val, rep))
    
    elif len(sweep_params) == 2:
        # 2D grid
        import itertools
        param_names = list(sweep_params.keys())
        
        for vals in itertools.product(*sweep_params.values()):
            config_kwargs = dict(zip(param_names, vals))
            config_kwargs.update(fixed_params)
            
            # Use first param as "main" sweep param
            sweep_param = f"{param_names[0]}={vals[0]:.2f}"
            sweep_value = vals[0]  # Primary axis
            
            for rep in range(n_rep):
                cells.append((config_kwargs, sweep_name, sweep_param, sweep_value, rep))
    
    print(f"Running {sweep_name} sweep: {len(cells)} cells")
    print(f"Description: {sweep_config['description']}")
    
    # Run in parallel
    all_results = []
    base_seed = 12345
    
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        futures = {}
        for i, (config_kwargs, sn, sp, sv, rep) in enumerate(cells):
            seed = base_seed + i
            future = executor.submit(
                run_single_cell, 
                config_kwargs, sn, sp, sv, rep, methods, seed
            )
            futures[future] = (config_kwargs, sn, sp, sv, rep)
        
        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                print(f"Cell failed: {e}")
    
    # Convert to DataFrame
    df = pd.DataFrame([r.__dict__ for r in all_results])
    
    return df


def generate_fair_sweep_report(
    df: pd.DataFrame,
    sweep_name: str,
    output_dir: Path,
) -> None:
    """Generate markdown report for fair sweep results."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sweep_config = FAIR_SWEEP_CONFIGS[sweep_name]
    sweep_params = sweep_config['sweep']
    param_name = list(sweep_params.keys())[0]
    
    # Aggregate by method and sweep value
    metrics_to_report = ['pehe', 'ate_error', 'spearman', 'calib_r2', 'tau_ece']
    
    agg_df = df.groupby(['method', 'sweep_value']).agg({
        **{m: ['mean', 'std'] for m in metrics_to_report},
        'target_SNR': 'mean',
        'overlap_auc': 'mean',
        'intercept_drift_scale': 'mean',
        'fair_for_optionB': 'mean',
    }).reset_index()
    
    # Flatten column names
    agg_df.columns = [
        '_'.join(col).strip('_') if isinstance(col, tuple) else col 
        for col in agg_df.columns.values
    ]
    
    # Write markdown report
    report_path = output_dir / f'{sweep_name}_report.md'
    
    with open(report_path, 'w') as f:
        f.write(f"# Fair OptionB Sweep: {sweep_name}\n\n")
        f.write(f"**Description**: {sweep_config['description']}\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        f.write("## Sweep Configuration\n\n")
        f.write(f"- **Swept parameter**: `{param_name}`\n")
        f.write(f"- **Values**: {sweep_params[param_name]}\n")
        f.write(f"- **Fixed parameters**: {sweep_config.get('fixed', {})}\n\n")
        
        if 'fairness_gate' in sweep_config:
            f.write(f"- **Fairness gate**: `{sweep_config['fairness_gate']}`\n")
            f.write(f"- **Main regime**: {sweep_config.get('main_regime', 'N/A')}\n")
            f.write(f"- **Stress regime**: {sweep_config.get('stress_regime', 'N/A')}\n\n")
        
        # Fairness diagnostics
        f.write("## Fairness Diagnostics by Sweep Value\n\n")
        
        diag_cols = ['sweep_value', 'target_SNR_mean', 'overlap_auc_mean', 
                     'intercept_drift_scale_mean', 'fair_for_optionB_mean']
        diag_df = agg_df[agg_df['method'] == 'ProposedB_SourceDR'][
            [c for c in diag_cols if c in agg_df.columns]
        ].drop_duplicates()
        
        f.write("| Sweep Value | SNR | Overlap AUC | Drift Scale | Fair? |\n")
        f.write("|-------------|-----|-------------|-------------|-------|\n")
        
        for _, row in diag_df.iterrows():
            snr = row.get('target_SNR_mean', np.nan)
            auc = row.get('overlap_auc_mean', np.nan)
            drift = row.get('intercept_drift_scale_mean', np.nan)
            fair = row.get('fair_for_optionB_mean', np.nan)
            
            # Color code fairness
            snr_flag = "✓" if snr >= 1.0 else "✗"
            auc_flag = "✓" if auc < 0.9 else "✗"
            
            f.write(f"| {row['sweep_value']:.2f} | {snr:.2f} {snr_flag} | {auc:.2f} {auc_flag} | {drift:.1f} | {fair*100:.0f}% |\n")
        
        f.write("\n")
        
        # Main results table
        f.write("## Results by Method and Sweep Value\n\n")
        
        # Focus on ProposedB_SourceDR
        f.write("### ProposedB_SourceDR (OptionB Fallback)\n\n")
        
        optb_df = agg_df[agg_df['method'] == 'ProposedB_SourceDR'].copy()
        
        f.write(f"| {param_name} | PEHE | ATE Error | Spearman | Calib R² | τ-ECE |\n")
        f.write("|-------------|------|-----------|----------|----------|-------|\n")
        
        for _, row in optb_df.iterrows():
            val = row['sweep_value']
            pehe = row.get('pehe_mean', np.nan)
            pehe_std = row.get('pehe_std', np.nan)
            ate = row.get('ate_error_mean', np.nan)
            spear = row.get('spearman_mean', np.nan)
            r2 = row.get('calib_r2_mean', np.nan)
            ece = row.get('tau_ece_mean', np.nan)
            
            f.write(f"| {val:.2f} | {pehe:.3f}±{pehe_std:.3f} | {ate:.3f} | {spear:.3f} | {r2:.3f} | {ece:.3f} |\n")
        
        f.write("\n")
        
        # Comparison with other methods
        f.write("### Comparison with Other Methods\n\n")
        
        for method in ['ProposedA', 'ProposedB_LinearStepB', 'OracleTarget']:
            method_df = agg_df[agg_df['method'] == method]
            if len(method_df) > 0:
                f.write(f"**{method}**\n\n")
                
                f.write(f"| {param_name} | PEHE | ATE Error | Spearman | Calib R² |\n")
                f.write("|-------------|------|-----------|----------|----------|\n")
                
                for _, row in method_df.iterrows():
                    val = row['sweep_value']
                    pehe = row.get('pehe_mean', np.nan)
                    ate = row.get('ate_error_mean', np.nan)
                    spear = row.get('spearman_mean', np.nan)
                    r2 = row.get('calib_r2_mean', np.nan)
                    
                    f.write(f"| {val:.2f} | {pehe:.3f} | {ate:.3f} | {spear:.3f} | {r2:.3f} |\n")
                
                f.write("\n")
        
        # Interpretation
        f.write("## Interpretation\n\n")
        
        if sweep_name == 'cross_arm_validity':
            f.write("""
This sweep tests ProposedB_SourceDR across the **cross-arm signal strength** ladder (SNR).

**Expected behavior**:
- When SNR ≥ 1 (transfer signal dominates), OptionB should perform reasonably
- When SNR < 1 (nontransfer dominates), OptionB is expected to fail

**Key finding**: If OptionB degrades sharply as SNR drops below 1, this confirms the
method's assumptions are being violated, not that the method is fundamentally broken.
""")
        
        elif sweep_name == 'overlap_stress':
            f.write("""
This sweep tests ProposedB_SourceDR across the **covariate overlap** ladder.

**Expected behavior**:
- When Overlap AUC < 0.85, source-trained models should generalize reasonably
- When Overlap AUC > 0.9, OptionB must extrapolate outside source support

**Key finding**: Degradation at high AUC indicates extrapolation failure, not
a fundamental flaw in the cross-arm transfer logic.
""")
        
        elif sweep_name == 'drift_stress':
            f.write("""
This sweep tests ProposedB_SourceDR across the **intercept drift** ladder.

**Expected behavior**:
- When drift is small (≤ 1), arm-specific baselines don't dominate
- When drift is large (> 2), baseline misalignment causes calibration failure

**Key finding**: Since OptionB cannot correct arm-specific target intercepts (no
target treated data), large drift will cause calibration intercept variance to explode.
""")
        
        f.write("\n\n")
        
        # Recommendation
        f.write("## Recommendation for Paper\n\n")
        f.write("""
When reporting OptionB results:

1. **Primary comparison** (SNR ≥ 1, AUC < 0.85, drift ≤ 1): This is where OptionB's
   assumptions approximately hold. Report these as the main results.

2. **Stress test** (SNR < 1 or AUC > 0.9 or drift > 2): These are explicit assumption
   violations. Report separately as "negative control" or "assumption violated" regimes.

**Suggested sentence for paper**:
> We evaluate the source-only fallback (OptionB) in regimes where cross-arm structure 
> is present (SNR ≥ 1), overlap is moderate, and intercept drift is controlled. Outside 
> these regimes, OptionB serves as a negative control demonstrating the necessity of 
> each assumption.
""")
    
    print(f"Report saved to {report_path}")
    
    # Also save raw aggregated data
    agg_df.to_csv(output_dir / f'{sweep_name}_agg.csv', index=False)
    df.to_csv(output_dir / f'{sweep_name}_raw.csv', index=False)


def main():
    parser = argparse.ArgumentParser(description='Fair OptionB Evaluation Sweeps')
    
    parser.add_argument('--sweep', type=str, default='cross_arm_validity',
                       choices=list(FAIR_SWEEP_CONFIGS.keys()),
                       help='Which sweep to run')
    parser.add_argument('--all', action='store_true',
                       help='Run all sweeps')
    parser.add_argument('--n_rep', type=int, default=20,
                       help='Number of replications per cell')
    parser.add_argument('--n_jobs', type=int, default=4,
                       help='Number of parallel jobs')
    parser.add_argument('--output_dir', type=str, default='results/fair_optionb_sweeps',
                       help='Output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.all:
        sweeps_to_run = list(FAIR_SWEEP_CONFIGS.keys())
    else:
        sweeps_to_run = [args.sweep]
    
    for sweep_name in sweeps_to_run:
        print(f"\n{'='*60}")
        print(f"Running sweep: {sweep_name}")
        print('='*60)
        
        df = run_sweep(
            sweep_name=sweep_name,
            n_rep=args.n_rep,
            n_jobs=args.n_jobs,
        )
        
        generate_fair_sweep_report(df, sweep_name, output_dir)
        
        print(f"\nCompleted {sweep_name}")
        print(f"Results saved to {output_dir}")


if __name__ == '__main__':
    main()
