"""
Advisor-Suggested Diagnostic Checks

Implements 4 key analyses:
1. Plot |δ₁ - δ₀| vs ρ (true bias difference)
2. Report variance of (δ̂₁ - δ̂₀)ᵀX across runs
3. Test "shared correction" (force δ̂₁ = δ̂₀) in Option A
4. Test stronger LASSO regularization (1-SE rule)
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['mathtext.fontset'] = 'cm'  # Use Computer Modern font for math
matplotlib.rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from joblib import Parallel, delayed

from data_generator import MultiSiteSimulator
from baselines import ProxyOnlyBaseline, AnchorOnlyBaseline
from scratch_estimator import PlaceboAnchoredDRLearner
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.metrics import mean_squared_error


# ============================================================================
# CHECK 1: Plot |δ₁ - δ₀| vs ρ (TRUE bias difference)
# ============================================================================

def check1_true_bias_difference():
    """
    Measure true |δ₁ - δ₀| in the DGP across ρ values.
    This should explain why PEHE patterns emerge.
    """
    print("="*80)
    print("CHECK 1: True Bias Difference |δ₁ - δ₀| vs ρ")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    rho_values = [0.0, 0.3, 0.5, 0.8, 1.0]
    results = []
    
    for rho in rho_values:
        print(f"ρ = {rho:.1f}:")
        
        # Generate 20 networks to get distribution
        bias_diffs = []
        for seed in range(42, 42 + 20):
            data = simulator.generate_network(
                n_source_sites=3,
                n_target=100,  # Size doesn't matter for this check
                rho_cross_arm=rho,
                disconnected=False,
                seed=seed
            )
            
            # Extract true biases for target site
            delta_0_true = data['target']['delta_0']  # Control arm
            delta_1_true = data['target']['delta_1']  # Treated arm
            
            # Compute difference
            diff = delta_1_true - delta_0_true
            
            # L2 norm of difference
            l2_diff = np.linalg.norm(diff)
            
            # L1 norm (sum of absolute values)
            l1_diff = np.sum(np.abs(diff))
            
            # Max absolute component
            linf_diff = np.max(np.abs(diff))
            
            bias_diffs.append({
                'rho': rho,
                'l2_norm': l2_diff,
                'l1_norm': l1_diff,
                'linf_norm': linf_diff
            })
        
        df = pd.DataFrame(bias_diffs)
        
        print(f"  |δ₁ - δ₀|₂ = {df['l2_norm'].mean():.4f} ± {df['l2_norm'].std():.4f}")
        print(f"  |δ₁ - δ₀|₁ = {df['l1_norm'].mean():.4f} ± {df['l1_norm'].std():.4f}")
        print(f"  |δ₁ - δ₀|∞ = {df['linf_norm'].mean():.4f} ± {df['linf_norm'].std():.4f}")
        print()
        
        results.append({
            'rho': rho,
            'l2_mean': df['l2_norm'].mean(),
            'l2_std': df['l2_norm'].std(),
            'l1_mean': df['l1_norm'].mean(),
            'linf_mean': df['linf_norm'].mean()
        })
    
    # Plot
    df_summary = pd.DataFrame(results)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_summary['rho'], df_summary['l2_mean'], 
            marker='o', markersize=10, linewidth=2.5, label='L2 norm')
    ax.fill_between(df_summary['rho'], 
                     df_summary['l2_mean'] - df_summary['l2_std'],
                     df_summary['l2_mean'] + df_summary['l2_std'],
                     alpha=0.3)
    
    ax.set_xlabel(r'Cross-Arm Coupling ($\rho$)', fontsize=14)
    ax.set_ylabel(r'$|\delta_1 - \delta_0|_2$ (True Bias Difference)', fontsize=14)
    ax.set_title(r'True CATE-Bias Component vs $\rho$' + '\n' + r'(Lower $\rho$ → Larger Differential Bias)', 
                 fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    plt.tight_layout()
    
    Path('results/diagnostics').mkdir(parents=True, exist_ok=True)
    plt.savefig('results/diagnostics/check1_true_bias_diff.png', dpi=300, bbox_inches='tight')
    print(f"Saved: results/diagnostics/check1_true_bias_diff.png")
    plt.close()
    
    return df_summary


# ============================================================================
# CHECK 2: Variance of (δ̂₁ - δ̂₀)ᵀX across runs
# ============================================================================

def check2_correction_variance():
    """
    Measure variance of estimated correction difference.
    Should blow up at low ρ for Anchor-Only.
    """
    print("\n" + "="*80)
    print("CHECK 2: Variance of (δ̂₁ - δ̂₀)ᵀX Across Runs")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    rho_values = [0.3, 0.5, 0.8, 1.0]
    n_target = 2000
    
    results = []
    
    for rho in rho_values:
        print(f"ρ = {rho:.1f} (20 runs)...")
        
        # Store correction predictions across runs
        proxy_preds_list = []
        anchor_preds_list = []
        proposed_preds_list = []
        
        for seed in range(42, 42 + 20):
            data = simulator.generate_network(
                n_source_sites=3,
                n_target=n_target,
                rho_cross_arm=rho,
                disconnected=False,
                seed=seed
            )
            
            X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
            X_t, A_t, Y_t = data['target']['X'], data['target']['A'], data['target']['Y']
            
            # Proxy
            proxy = ProxyOnlyBaseline(proxy_model=RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
            ))
            proxy.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
            proxy_preds_list.append(proxy.predict(X_t))
            
            # Anchor
            anchor = AnchorOnlyBaseline(proxy_model=RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
            ))
            anchor.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
            anchor_preds_list.append(anchor.predict(X_t))
            
            # Proposed
            try:
                proposed = PlaceboAnchoredDRLearner(
                    proxy_model=RandomForestRegressor(
                        n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
                    ),
                    cate_model=RandomForestRegressor(
                        n_estimators=200, max_depth=5, min_samples_leaf=10, random_state=seed+1, n_jobs=1
                    ),
                    option='A',
                    n_folds_dr=3,
                    random_state=seed
                )
                proposed.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
                proposed_preds_list.append(proposed.predict(X_t))
            except:
                proposed_preds_list.append(np.nan * np.ones(len(X_t)))
        
        # Compute pointwise variance across runs
        proxy_var = np.mean(np.var(np.array(proxy_preds_list), axis=0))
        anchor_var = np.mean(np.var(np.array(anchor_preds_list), axis=0))
        proposed_var = np.mean(np.var(np.array(proposed_preds_list), axis=0))
        
        print(f"  Proxy variance:    {proxy_var:.6f}")
        print(f"  Anchor variance:   {anchor_var:.6f} ({anchor_var/proxy_var:.2f}x Proxy)")
        print(f"  Proposed variance: {proposed_var:.6f} ({proposed_var/proxy_var:.2f}x Proxy)")
        print()
        
        results.append({
            'rho': rho,
            'Proxy': proxy_var,
            'Anchor': anchor_var,
            'Proposed': proposed_var
        })
    
    # Plot
    df = pd.DataFrame(results)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for method, color in [('Proxy', '#2ecc71'), ('Anchor', '#e74c3c'), ('Proposed', '#3498db')]:
        ax.plot(df['rho'], df[method], marker='o', markersize=10,
                linewidth=2.5, label=method, color=color)
    
    ax.set_xlabel('Cross-Arm Coupling (ρ)', fontsize=14)
    ax.set_ylabel('Mean Pointwise Variance (across 20 runs)', fontsize=14)
    ax.set_title('Prediction Variance vs ρ (n=2000)\nLower ρ → Higher Anchor/Proposed Variance',
                 fontsize=16, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig('results/diagnostics/check2_correction_variance.png', dpi=300, bbox_inches='tight')
    print(f"Saved: results/diagnostics/check2_correction_variance.png")
    plt.close()
    
    return df


# ============================================================================
# CHECK 3: Shared Correction (force δ̂₁ = δ̂₀) in Option A
# ============================================================================

def check3_shared_correction():
    """
    Test if forcing shared correction helps at low ρ.
    Should make Anchor-Only less catastrophic.
    """
    print("\n" + "="*80)
    print("CHECK 3: Shared vs Separate Corrections at ρ=0.5")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    rho = 0.5
    n_target = 2000
    n_runs = 30
    
    print(f"Testing at ρ={rho} (differential bias regime)")
    print(f"Running {n_runs} Monte Carlo iterations...")
    print()
    
    results = []
    
    for seed in range(42, 42 + n_runs):
        data = simulator.generate_network(
            n_source_sites=3,
            n_target=n_target,
            rho_cross_arm=rho,
            disconnected=False,
            seed=seed
        )
        
        X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
        X_t, A_t, Y_t = data['target']['X'], data['target']['A'], data['target']['Y']
        tau_true = data['target']['tau']
        
        # Proxy-Only (baseline)
        proxy = ProxyOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        proxy.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
        pehe_proxy = np.sqrt(mean_squared_error(tau_true, proxy.predict(X_t)))
        
        # Anchor-Only with SEPARATE corrections (Option A)
        anchor_sep = AnchorOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        anchor_sep.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
        pehe_anchor_sep = np.sqrt(mean_squared_error(tau_true, anchor_sep.predict(X_t)))
        
        # Anchor-Only with SHARED correction (force Option B even with both arms)
        # Modify fit to force sharing
        anchor_shared = AnchorOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        # Temporarily make target look disconnected to force sharing
        A_t_temp = A_t.copy()
        A_t_ones = A_t == 1
        A_t[A_t_ones] = 0  # Temporarily hide treated arm
        anchor_shared.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
        A_t[:] = A_t_temp  # Restore
        pehe_anchor_shared = np.sqrt(mean_squared_error(tau_true, anchor_shared.predict(X_t)))
        
        # Proposed with SEPARATE (default)
        try:
            proposed_sep = PlaceboAnchoredDRLearner(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
                ),
                cate_model=RandomForestRegressor(
                    n_estimators=200, max_depth=5, min_samples_leaf=10, random_state=seed+1, n_jobs=1
                ),
                option='A',
                n_folds_dr=3,
                random_state=seed
            )
            proposed_sep.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
            pehe_proposed_sep = np.sqrt(mean_squared_error(tau_true, proposed_sep.predict(X_t)))
        except:
            pehe_proposed_sep = np.nan
        
        # Proposed with SHARED (Option B)
        try:
            proposed_shared = PlaceboAnchoredDRLearner(
                proxy_model=RandomForestRegressor(
                    n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
                ),
                cate_model=RandomForestRegressor(
                    n_estimators=200, max_depth=5, min_samples_leaf=10, random_state=seed+1, n_jobs=1
                ),
                option='B',  # Force shared
                n_folds_dr=3,
                random_state=seed
            )
            proposed_shared.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
            pehe_proposed_shared = np.sqrt(mean_squared_error(tau_true, proposed_shared.predict(X_t)))
        except:
            pehe_proposed_shared = np.nan
        
        results.append({
            'Proxy': pehe_proxy,
            'Anchor (Separate)': pehe_anchor_sep,
            'Anchor (Shared)': pehe_anchor_shared,
            'Proposed (Separate)': pehe_proposed_sep,
            'Proposed (Shared)': pehe_proposed_shared
        })
    
    df = pd.DataFrame(results)
    
    print("Results (PEHE, lower is better):")
    print("-" * 60)
    for col in df.columns:
        mean_val = df[col].mean()
        std_val = df[col].std()
        print(f"{col:25s}: {mean_val:.4f} ± {std_val:.4f}")
    
    print("\nKey Comparisons:")
    print("-" * 60)
    anchor_sep_mean = df['Anchor (Separate)'].mean()
    anchor_shared_mean = df['Anchor (Shared)'].mean()
    improvement = 100 * (anchor_sep_mean - anchor_shared_mean) / anchor_sep_mean
    print(f"Anchor Shared vs Separate: {improvement:+.1f}% improvement")
    
    proposed_sep_mean = df['Proposed (Separate)'].mean()
    proposed_shared_mean = df['Proposed (Shared)'].mean()
    improvement2 = 100 * (proposed_sep_mean - proposed_shared_mean) / proposed_sep_mean
    print(f"Proposed Shared vs Separate: {improvement2:+.1f}% improvement")
    
    # Save
    df.to_csv('results/diagnostics/check3_shared_correction.csv', index=False)
    print(f"\nSaved: results/diagnostics/check3_shared_correction.csv")
    
    return df


# ============================================================================
# CHECK 4: Stronger LASSO Regularization (1-SE rule)
# ============================================================================

def check4_stronger_regularization():
    """
    Test if stronger regularization helps at low ρ.
    Use alpha at 1-SE instead of min CV error.
    """
    print("\n" + "="*80)
    print("CHECK 4: Stronger LASSO Regularization at ρ=0.5")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    rho = 0.5
    n_target = 2000
    n_runs = 30
    
    print(f"Comparing default LassoCV vs 1-SE rule at ρ={rho}")
    print(f"Running {n_runs} iterations...")
    print()
    
    results = []
    
    for seed in range(42, 42 + n_runs):
        data = simulator.generate_network(
            n_source_sites=3,
            n_target=n_target,
            rho_cross_arm=rho,
            disconnected=False,
            seed=seed
        )
        
        X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
        X_t, A_t, Y_t = data['target']['X'], data['target']['A'], data['target']['Y']
        tau_true = data['target']['tau']
        
        # Proxy baseline
        proxy = ProxyOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        proxy.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
        pehe_proxy = np.sqrt(mean_squared_error(tau_true, proxy.predict(X_t)))
        
        # Manual Anchor with default LASSO
        mu0_proxy = proxy.models_[0].predict(X_t)
        mu1_proxy = proxy.models_[1].predict(X_t)
        
        # Control arm correction - default
        mask_control = A_t == 0
        resid_0 = Y_t[mask_control] - mu0_proxy[mask_control]
        lasso_0_default = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=seed)
        lasso_0_default.fit(X_t[mask_control], resid_0)
        delta_0_default = lasso_0_default.coef_
        
        # Treated arm correction - default
        mask_treated = A_t == 1
        resid_1 = Y_t[mask_treated] - mu1_proxy[mask_treated]
        lasso_1_default = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=seed)
        lasso_1_default.fit(X_t[mask_treated], resid_1)
        delta_1_default = lasso_1_default.coef_
        
        tau_anchor_default = (mu1_proxy + X_t @ delta_1_default) - (mu0_proxy + X_t @ delta_0_default)
        pehe_anchor_default = np.sqrt(mean_squared_error(tau_true, tau_anchor_default))
        
        # Control arm correction - 1-SE rule
        alphas_0 = lasso_0_default.alphas_
        mse_path_0 = lasso_0_default.mse_path_.mean(axis=1)
        best_idx_0 = np.argmin(mse_path_0)
        best_mse_0 = mse_path_0[best_idx_0]
        se_0 = lasso_0_default.mse_path_.std(axis=1)[best_idx_0] / np.sqrt(5)
        
        # Find largest alpha within 1 SE
        within_1se_0 = mse_path_0 <= (best_mse_0 + se_0)
        if np.any(within_1se_0):
            alpha_1se_0 = alphas_0[within_1se_0][0]  # Largest alpha within 1-SE
        else:
            alpha_1se_0 = lasso_0_default.alpha_
        
        lasso_0_1se = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=seed, 
                              alphas=[alpha_1se_0])
        lasso_0_1se.fit(X_t[mask_control], resid_0)
        delta_0_1se = lasso_0_1se.coef_
        
        # Treated arm correction - 1-SE rule
        alphas_1 = lasso_1_default.alphas_
        mse_path_1 = lasso_1_default.mse_path_.mean(axis=1)
        best_idx_1 = np.argmin(mse_path_1)
        best_mse_1 = mse_path_1[best_idx_1]
        se_1 = lasso_1_default.mse_path_.std(axis=1)[best_idx_1] / np.sqrt(5)
        
        within_1se_1 = mse_path_1 <= (best_mse_1 + se_1)
        if np.any(within_1se_1):
            alpha_1se_1 = alphas_1[within_1se_1][0]
        else:
            alpha_1se_1 = lasso_1_default.alpha_
        
        lasso_1_1se = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=seed,
                              alphas=[alpha_1se_1])
        lasso_1_1se.fit(X_t[mask_treated], resid_1)
        delta_1_1se = lasso_1_1se.coef_
        
        tau_anchor_1se = (mu1_proxy + X_t @ delta_1_1se) - (mu0_proxy + X_t @ delta_0_1se)
        pehe_anchor_1se = np.sqrt(mean_squared_error(tau_true, tau_anchor_1se))
        
        results.append({
            'Proxy': pehe_proxy,
            'Anchor (Default LASSO)': pehe_anchor_default,
            'Anchor (1-SE Rule)': pehe_anchor_1se,
            'nnz_default': np.sum(np.abs(delta_1_default - delta_0_default) > 1e-6),
            'nnz_1se': np.sum(np.abs(delta_1_1se - delta_0_1se) > 1e-6)
        })
    
    df = pd.DataFrame(results)
    
    print("Results (PEHE, lower is better):")
    print("-" * 60)
    for col in ['Proxy', 'Anchor (Default LASSO)', 'Anchor (1-SE Rule)']:
        mean_val = df[col].mean()
        std_val = df[col].std()
        print(f"{col:25s}: {mean_val:.4f} ± {std_val:.4f}")
    
    print("\nSparsity (non-zero in δ₁ - δ₀):")
    print(f"  Default: {df['nnz_default'].mean():.1f} ± {df['nnz_default'].std():.1f}")
    print(f"  1-SE:    {df['nnz_1se'].mean():.1f} ± {df['nnz_1se'].std():.1f}")
    
    improvement = 100 * (df['Anchor (Default LASSO)'].mean() - df['Anchor (1-SE Rule)'].mean()) / df['Anchor (Default LASSO)'].mean()
    print(f"\n1-SE vs Default: {improvement:+.1f}% improvement")
    
    df.to_csv('results/diagnostics/check4_regularization.csv', index=False)
    print(f"\nSaved: results/diagnostics/check4_regularization.csv")
    
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("ADVISOR-SUGGESTED DIAGNOSTIC CHECKS")
    print("="*80)
    print()
    print("Running 4 key analyses to confirm the bias-variance diagnosis:")
    print("  1. True |δ₁ - δ₀| vs ρ (mechanism)")
    print("  2. Correction variance across runs (variance explosion)")
    print("  3. Shared vs separate corrections (cancellation effect)")
    print("  4. Stronger regularization (overfit mitigation)")
    print()
    
    # Run all checks
    df1 = check1_true_bias_difference()
    df2 = check2_correction_variance()
    df3 = check3_shared_correction()
    df4 = check4_stronger_regularization()
    
    print("\n" + "="*80)
    print("ALL DIAGNOSTICS COMPLETE")
    print("="*80)
    print()
    print("Results saved to: results/diagnostics/")
    print("  - check1_true_bias_diff.png")
    print("  - check2_correction_variance.png")
    print("  - check3_shared_correction.csv")
    print("  - check4_regularization.csv")
    print()
    print("Key findings will be summarized in ADVISOR_RESPONSE.md")


if __name__ == "__main__":
    main()
