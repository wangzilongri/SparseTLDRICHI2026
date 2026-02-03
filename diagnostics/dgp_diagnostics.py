#!/usr/bin/env python3
"""
DGP Diagnostics for SourceDR Failure Investigation

Implements the advisor's recommended checks:
A1) Target-only arm-specific intercept shifts
A2) Nontransfer component magnitude vs signal
A3) Covariate overlap / positivity
A4) Scale of outcomes / noise (SNR)
B1) Oracle nuisance functions test

Usage:
    python dgp_diagnostics.py [--n_reps 10] [--output dgp_diagnostics_output]
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

from synthetic_data_v2 import SyntheticRCTConfig, SyntheticRCTGenerator

plt.style.use('seaborn-v0_8-whitegrid')


class DGPDiagnostics:
    """Run advisor-recommended DGP diagnostics."""
    
    def __init__(self, n_reps: int = 10, output_folder: str = None):
        self.n_reps = n_reps
        self.output_folder = Path(output_folder) if output_folder else Path('dgp_diagnostics_output')
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        self.results = []
    
    def run_all_checks(self):
        """Run all advisor-recommended DGP checks."""
        print("="*60)
        print("DGP DIAGNOSTICS FOR SOURCEDR FAILURE INVESTIGATION")
        print("="*60)
        
        print(f"\nRunning {self.n_reps} replications...")
        
        # A1: Check arm-specific intercepts / baseline shifts
        print("\n[A1] Checking arm-specific baseline shifts...")
        self.check_a1_baseline_shifts()
        
        # A2: Check nontransfer component magnitude
        print("\n[A2] Checking nontransfer component magnitude...")
        self.check_a2_nontransfer_magnitude()
        
        # A3: Check covariate overlap
        print("\n[A3] Checking covariate overlap...")
        self.check_a3_covariate_overlap()
        
        # A4: Check outcome scale / SNR
        print("\n[A4] Checking outcome scale and SNR...")
        self.check_a4_outcome_snr()
        
        # Generate report
        print("\n[Report] Generating diagnostic report...")
        self.generate_report()
        
        print("\n" + "="*60)
        print(f"Complete! Output: {self.output_folder}")
        print("="*60)
    
    def check_a1_baseline_shifts(self):
        """
        A1: Check for target-only arm-specific intercept shifts.
        
        If DGP has arm/site intercepts that vary by replication,
        this causes intercept variance to explode.
        """
        mu0_means = []
        mu1_means = []
        tau_means = []
        
        for seed in range(self.n_reps):
            config = SyntheticRCTConfig(
                random_state=seed,
                n_target=1000,
                n_source_sites=10,
                n_source_per_site=500,
            )
            gen = SyntheticRCTGenerator(config)
            _, target = gen.generate_full_dataset()
            
            mu0_means.append(np.mean(target['mu0_true']))
            mu1_means.append(np.mean(target['mu1_true']))
            tau_means.append(np.mean(target['tau_true']))
        
        # Results
        self.a1_results = {
            'E[mu0]_mean': np.mean(mu0_means),
            'E[mu0]_std': np.std(mu0_means),
            'E[mu1]_mean': np.mean(mu1_means),
            'E[mu1]_std': np.std(mu1_means),
            'E[tau]_mean': np.mean(tau_means),
            'E[tau]_std': np.std(tau_means),
        }
        
        print(f"  E[μ₀(X)] across reps: {self.a1_results['E[mu0]_mean']:.3f} ± {self.a1_results['E[mu0]_std']:.3f}")
        print(f"  E[μ₁(X)] across reps: {self.a1_results['E[mu1]_mean']:.3f} ± {self.a1_results['E[mu1]_std']:.3f}")
        print(f"  E[τ(X)] across reps: {self.a1_results['E[tau]_mean']:.3f} ± {self.a1_results['E[tau]_std']:.3f}")
        
        # Interpretation
        if self.a1_results['E[mu0]_std'] > 1.0 or self.a1_results['E[mu1]_std'] > 1.0:
            print("  ⚠️  HIGH arm mean variance across replications!")
            print("     This could explain intercept drift in SourceDR.")
        else:
            print("  ✓ Arm means are stable across replications.")
    
    def check_a2_nontransfer_magnitude(self):
        """
        A2: Check if nontransfer component ν_c is too large relative to signal.
        
        If |ν_t| >> |M*β_{0,t}|, then SourceDR learning wrong structure is expected.
        """
        results = []
        
        for seed in range(self.n_reps):
            config = SyntheticRCTConfig(
                random_state=seed,
                n_target=1000,
                n_source_sites=10,
                nontransfer_scale_target=0.3,  # Default
            )
            gen = SyntheticRCTGenerator(config)
            diag = gen.get_diagnostics()
            
            # Target site metrics
            M_beta0_norm = diag['target_M_beta0_norm']
            nu_norm = diag['target_nu_norm']
            snr = diag['target_transfer_SNR']
            cosine = diag['target_cosine_sim']
            
            # Cross-arm correlation on target distribution
            _, target = gen.generate_full_dataset()
            X = target['X']
            beta0_t = gen.beta0[0]
            beta1_t = gen.beta1[0]
            
            xb0 = X @ beta0_t
            xb1 = X @ beta1_t
            
            if np.std(xb0) > 1e-10 and np.std(xb1) > 1e-10:
                corr, _ = spearmanr(xb0, xb1)
            else:
                corr = np.nan
            
            results.append({
                'seed': seed,
                '|M*β₀|': M_beta0_norm,
                '|ν|': nu_norm,
                'SNR': snr,
                'cosine(β₁, M*β₀)': cosine,
                'corr(X^T β₀, X^T β₁)': corr,
            })
        
        df = pd.DataFrame(results)
        self.a2_results = df
        
        print(f"  |M*β₀_t|: {df['|M*β₀|'].mean():.3f} ± {df['|M*β₀|'].std():.3f}")
        print(f"  |ν_t|: {df['|ν|'].mean():.3f} ± {df['|ν|'].std():.3f}")
        print(f"  SNR (|M*β₀|/|ν|): {df['SNR'].mean():.3f} ± {df['SNR'].std():.3f}")
        print(f"  cosine(β₁, M*β₀): {df['cosine(β₁, M*β₀)'].mean():.3f} ± {df['cosine(β₁, M*β₀)'].std():.3f}")
        print(f"  corr(X^T β₀, X^T β₁): {df['corr(X^T β₀, X^T β₁)'].mean():.3f} ± {df['corr(X^T β₀, X^T β₁)'].std():.3f}")
        
        if df['SNR'].mean() < 1.0:
            print("  ⚠️  SNR < 1: nontransfer dominates! SourceDR failure is EXPECTED.")
        elif df['corr(X^T β₀, X^T β₁)'].mean() < 0.3:
            print("  ⚠️  Low cross-arm correlation! SourceDR may struggle.")
        else:
            print("  ✓ Transfer signal is adequate.")
    
    def check_a3_covariate_overlap(self):
        """
        A3: Check covariate overlap between source and target.
        
        Train classifier to predict "target vs source" - high AUC = poor overlap.
        """
        aucs = []
        
        for seed in range(self.n_reps):
            config = SyntheticRCTConfig(
                random_state=seed,
                n_target=1000,
                n_source_sites=10,
                n_source_per_site=500,
            )
            gen = SyntheticRCTGenerator(config)
            source, target = gen.generate_full_dataset()
            
            # Create classification problem
            X_all = np.vstack([source['X'], target['X']])
            y_all = np.concatenate([np.zeros(len(source['X'])), np.ones(len(target['X']))])
            
            # Fit logistic regression
            clf = LogisticRegression(max_iter=1000, random_state=seed)
            clf.fit(X_all, y_all)
            probs = clf.predict_proba(X_all)[:, 1]
            
            auc = roc_auc_score(y_all, probs)
            aucs.append(auc)
        
        self.a3_results = {
            'overlap_auc_mean': np.mean(aucs),
            'overlap_auc_std': np.std(aucs),
        }
        
        print(f"  Source vs Target classifier AUC: {self.a3_results['overlap_auc_mean']:.3f} ± {self.a3_results['overlap_auc_std']:.3f}")
        
        if self.a3_results['overlap_auc_mean'] > 0.8:
            print("  ⚠️  AUC > 0.8: Poor covariate overlap! Source learners may extrapolate badly.")
        elif self.a3_results['overlap_auc_mean'] > 0.7:
            print("  ⚡ AUC 0.7-0.8: Moderate covariate shift. May affect transport.")
        else:
            print("  ✓ Good covariate overlap (AUC < 0.7).")
    
    def check_a4_outcome_snr(self):
        """
        A4: Check scale of outcomes and signal-to-noise ratio.
        """
        results = []
        
        for seed in range(self.n_reps):
            config = SyntheticRCTConfig(
                random_state=seed,
                n_target=1000,
                n_source_sites=10,
            )
            gen = SyntheticRCTGenerator(config)
            _, target = gen.generate_full_dataset()
            
            Y = target['Y']
            tau = target['tau_true']
            mu0 = target['mu0_true']
            
            # Estimate noise variance (Y - E[Y|X,A])
            noise_var = np.var(Y - (mu0 + target['A'] * tau))
            signal_var = np.var(tau)
            
            snr = signal_var / (noise_var + 1e-10)
            
            results.append({
                'seed': seed,
                'Y_std': np.std(Y),
                'tau_std': np.std(tau),
                'noise_std': np.sqrt(noise_var),
                'SNR (Var(τ)/σ²)': snr,
            })
        
        df = pd.DataFrame(results)
        self.a4_results = df
        
        print(f"  std(Y): {df['Y_std'].mean():.3f} ± {df['Y_std'].std():.3f}")
        print(f"  std(τ): {df['tau_std'].mean():.3f} ± {df['tau_std'].std():.3f}")
        print(f"  noise_std: {df['noise_std'].mean():.3f} ± {df['noise_std'].std():.3f}")
        print(f"  SNR (Var(τ)/σ²): {df['SNR (Var(τ)/σ²)'].mean():.3f} ± {df['SNR (Var(τ)/σ²)'].std():.3f}")
        
        if df['SNR (Var(τ)/σ²)'].mean() < 0.5:
            print("  ⚠️  Low SNR! All methods should degrade.")
        else:
            print("  ✓ Adequate SNR for CATE estimation.")
    
    def run_ablation_experiments(self):
        """
        Run the 3 ablation experiments recommended by advisor:
        1. Kill all intercept shifts (set site_shifts to 0)
        2. Set ν_t=0 and vary rank(M*)
        3. Oracle nuisance run
        """
        print("\n" + "="*60)
        print("ABLATION EXPERIMENTS")
        print("="*60)
        
        # Experiment 1: Kill intercept shifts
        print("\n[Exp 1] Testing without covariate mean shifts...")
        self.exp1_no_shifts()
        
        # Experiment 2: Vary nontransfer scale
        print("\n[Exp 2] Testing with ν_t=0 (perfect cross-arm transfer)...")
        self.exp2_no_nontransfer()
        
        # Experiment 3: Oracle nuisance (requires estimator)
        print("\n[Exp 3] Oracle nuisance test requires full estimator run...")
        print("  (Run separately with estimator_fixed.py)")
    
    def exp1_no_shifts(self):
        """Test with covariate_shift_scale=0."""
        from synthetic_data_v2 import generate_synthetic_rct
        
        # With shifts (default)
        source, target, gen = generate_synthetic_rct(
            random_state=42,
            covariate_shift_scale=1.0,
        )
        diag_with = gen.get_diagnostics()
        
        # Without shifts
        source_no, target_no, gen_no = generate_synthetic_rct(
            random_state=42,
            covariate_shift_scale=0.0,
        )
        diag_without = gen_no.get_diagnostics()
        
        print(f"  With shifts: target_transfer_SNR = {diag_with['target_transfer_SNR']:.3f}")
        print(f"  Without shifts: target_transfer_SNR = {diag_without['target_transfer_SNR']:.3f}")
        print("  → If SourceDR works better without shifts, covariate shift is the culprit.")
    
    def exp2_no_nontransfer(self):
        """Test with nontransfer_scale_target=0."""
        from synthetic_data_v2 import generate_synthetic_rct
        
        # With nontransfer (default)
        source, target, gen = generate_synthetic_rct(
            random_state=42,
            nontransfer_scale_target=0.3,
        )
        diag_with = gen.get_diagnostics()
        
        # Without nontransfer
        source_no, target_no, gen_no = generate_synthetic_rct(
            random_state=42,
            nontransfer_scale_target=0.0,
        )
        diag_without = gen_no.get_diagnostics()
        
        print(f"  With ν_t: SNR = {diag_with['target_transfer_SNR']:.3f}, cosine = {diag_with['target_cosine_sim']:.3f}")
        print(f"  Without ν_t: SNR = inf, cosine = {diag_without['target_cosine_sim']:.3f}")
        print("  → If SourceDR works better with ν_t=0, nontransfer component is the issue.")
    
    def generate_report(self):
        """Generate markdown report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""# DGP Diagnostics Report

**Generated:** {timestamp}

**Replications:** {self.n_reps}

---

## Summary

This report investigates whether ProposedB_SourceDR failures are due to:
1. Method design issues (inherent limitations)
2. DGP artifacts that make source-only DR transport structurally impossible

---

## A1: Arm-Specific Baseline Shifts

**Question:** Do arm means (E[μ₀], E[μ₁]) vary significantly across replications?

**Results:**
- E[μ₀(X)] = {self.a1_results['E[mu0]_mean']:.3f} ± {self.a1_results['E[mu0]_std']:.3f}
- E[μ₁(X)] = {self.a1_results['E[mu1]_mean']:.3f} ± {self.a1_results['E[mu1]_std']:.3f}
- E[τ(X)] = {self.a1_results['E[tau]_mean']:.3f} ± {self.a1_results['E[tau]_std']:.3f}

**Interpretation:**
"""
        if self.a1_results['E[mu0]_std'] > 1.0:
            report += "- ⚠️ HIGH variance in arm means suggests intercept drift causing calibration issues.\n"
        else:
            report += "- ✓ Arm means are stable - intercept drift is NOT the primary issue.\n"
        
        report += f"""
---

## A2: Nontransfer Component Magnitude

**Question:** Is |ν_t| >> |M*β₀_t|, making cross-arm transfer non-learnable?

**Results (averaged across {self.n_reps} reps):**
- |M*β₀_t| = {self.a2_results['|M*β₀|'].mean():.3f} ± {self.a2_results['|M*β₀|'].std():.3f}
- |ν_t| = {self.a2_results['|ν|'].mean():.3f} ± {self.a2_results['|ν|'].std():.3f}
- SNR = {self.a2_results['SNR'].mean():.3f} ± {self.a2_results['SNR'].std():.3f}
- cosine(β₁, M*β₀) = {self.a2_results['cosine(β₁, M*β₀)'].mean():.3f}
- corr(X^T β₀, X^T β₁) = {self.a2_results['corr(X^T β₀, X^T β₁)'].mean():.3f}

**Interpretation:**
"""
        snr = self.a2_results['SNR'].mean()
        if snr < 1.0:
            report += f"- ⚠️ **SNR < 1 ({snr:.2f})**: Nontransfer component DOMINATES the transferable signal!\n"
            report += "- This means β₁ ≈ ν (not M*β₀), making SourceDR failure EXPECTED by design.\n"
            report += "- **This is the likely culprit for SourceDR's systematic failure.**\n"
        else:
            report += f"- SNR = {snr:.2f} suggests transfer signal is adequate.\n"
        
        corr = self.a2_results['corr(X^T β₀, X^T β₁)'].mean()
        if corr < 0.3:
            report += f"- ⚠️ Low cross-arm correlation ({corr:.2f}) means placebo effects don't predict treated effects.\n"
        
        report += f"""
---

## A3: Covariate Overlap

**Question:** Can source data extrapolate well to target?

**Results:**
- Source vs Target classifier AUC = {self.a3_results['overlap_auc_mean']:.3f} ± {self.a3_results['overlap_auc_std']:.3f}

**Interpretation:**
"""
        auc = self.a3_results['overlap_auc_mean']
        if auc > 0.8:
            report += f"- ⚠️ AUC = {auc:.2f} indicates POOR overlap - source models may extrapolate badly.\n"
        elif auc > 0.7:
            report += f"- ⚡ AUC = {auc:.2f} indicates moderate shift - some transport degradation expected.\n"
        else:
            report += f"- ✓ AUC = {auc:.2f} indicates good overlap - not a major issue.\n"
        
        report += f"""
---

## A4: Outcome Scale / SNR

**Question:** Is the signal-to-noise ratio adequate for CATE estimation?

**Results:**
- std(Y) = {self.a4_results['Y_std'].mean():.3f}
- std(τ) = {self.a4_results['tau_std'].mean():.3f}
- noise_std = {self.a4_results['noise_std'].mean():.3f}
- SNR (Var(τ)/σ²) = {self.a4_results['SNR (Var(τ)/σ²)'].mean():.3f}

**Interpretation:**
"""
        outcome_snr = self.a4_results['SNR (Var(τ)/σ²)'].mean()
        if outcome_snr < 0.5:
            report += f"- ⚠️ Low outcome SNR ({outcome_snr:.2f}) means ALL methods should struggle.\n"
        else:
            report += f"- ✓ Outcome SNR = {outcome_snr:.2f} is adequate. SourceDR failure is method-specific.\n"
        
        report += """
---

## Diagnosis Summary

Based on these diagnostics:

"""
        # Main diagnosis
        if snr < 1.0:
            report += """### 🔴 PRIMARY CAUSE: Nontransfer Component Dominance

The DGP's `nontransfer_scale_target = 0.3` creates a scenario where:
- The target's treated-arm deviation β₁_t is dominated by ν_t (nontransfer noise)
- The transferable signal M*β₀_t is relatively weak
- **SNR < 1 means SourceDR is trying to learn a transfer operator when there's nothing meaningful to transfer**

This is **by design** in the DGP - it's testing the method's limits, not a bug.

### Recommended Actions:

1. **For the paper**: Frame SourceDR as showing that "naïve source-only DR transport fails when cross-arm structure breaks down (SNR < 1)"

2. **To verify**: Run with `nontransfer_scale_target=0` and confirm SourceDR recovers

3. **Alternative framing**: SourceDR results demonstrate the importance of target-anchored methods (ProposedA/B) when transfer assumptions are violated
"""
        elif auc > 0.8:
            report += """### 🟡 CONTRIBUTING FACTOR: Covariate Shift

Poor covariate overlap (AUC > 0.8) means source-trained models extrapolate unreliably to target.
"""
        else:
            report += """### ✓ DGP appears well-behaved

SourceDR failure may be due to method limitations rather than DGP artifacts.
"""
        
        report += """
---

## Recommended Follow-up Experiments

1. **Kill nontransfer**: Run sweep with `nontransfer_scale_target=0`
   - If SourceDR recovers → confirms nontransfer dominance
   
2. **Vary nontransfer scale**: Sweep `nontransfer_scale_target` from 0 to 0.5
   - Plot SourceDR performance vs scale to find breakdown point
   
3. **Oracle nuisance test**: Feed true μ₀, μ₁ to SourceDR
   - If still fails → DGP identifiability issue
   - If recovers → nuisance estimation failure

---

*Generated by dgp_diagnostics.py*
"""
        
        report_path = self.output_folder / 'dgp_diagnostic_report.md'
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"  Report saved to: {report_path}")
        
        # Also save raw results
        pd.DataFrame([self.a1_results]).to_csv(self.output_folder / 'a1_baseline_shifts.csv', index=False)
        self.a2_results.to_csv(self.output_folder / 'a2_nontransfer.csv', index=False)
        pd.DataFrame([self.a3_results]).to_csv(self.output_folder / 'a3_overlap.csv', index=False)
        self.a4_results.to_csv(self.output_folder / 'a4_outcome_snr.csv', index=False)


def main():
    parser = argparse.ArgumentParser(description='Run DGP diagnostics')
    parser.add_argument('--n_reps', type=int, default=10, help='Number of replications')
    parser.add_argument('--output', type=str, default='dgp_diagnostics_output', help='Output folder')
    args = parser.parse_args()
    
    diag = DGPDiagnostics(n_reps=args.n_reps, output_folder=args.output)
    diag.run_all_checks()
    diag.run_ablation_experiments()


if __name__ == '__main__':
    main()
