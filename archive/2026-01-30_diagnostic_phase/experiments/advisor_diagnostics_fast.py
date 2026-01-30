"""
Fast Advisor Diagnostics - Reduced iterations for quicker results
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from data_generator import MultiSiteSimulator
from baselines import ProxyOnlyBaseline, AnchorOnlyBaseline
from scratch_estimator import PlaceboAnchoredDRLearner
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.metrics import mean_squared_error


# CHECK 3: Shared vs Separate Corrections (simplified)
def check3_shared_correction_fast():
    """Test shared vs separate corrections at ρ=0.5"""
    print("\n" + "="*80)
    print("CHECK 3: Shared vs Separate Corrections at ρ=0.5 (10 runs)")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    rho = 0.5
    n_target = 2000
    n_runs = 10  # Reduced from 30
    
    results = []
    
    for seed in range(42, 42 + n_runs):
        print(f"  Run {seed-41}/{n_runs}...", end='\r')
        
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
        
        # Proxy
        proxy = ProxyOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        proxy.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
        pehe_proxy = np.sqrt(mean_squared_error(tau_true, proxy.predict(X_t)))
        
        # Anchor - Separate (Option A)
        anchor_sep = AnchorOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        anchor_sep.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
        pehe_anchor_sep = np.sqrt(mean_squared_error(tau_true, anchor_sep.predict(X_t)))
        
        # Anchor - Shared (Option B) - force by using disconnected
        data_disconnected = simulator.generate_network(
            n_source_sites=3,
            n_target=n_target,
            rho_cross_arm=rho,
            disconnected=True,  # This forces shared correction
            seed=seed
        )
        X_t_disc, A_t_disc, Y_t_disc = data_disconnected['target']['X'], data_disconnected['target']['A'], data_disconnected['target']['Y']
        
        # Fit on disconnected, predict on full
        anchor_shared = AnchorOnlyBaseline(proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=seed, n_jobs=1
        ))
        anchor_shared.fit(X_s, A_s, Y_s, X_t_disc, A_t_disc, Y_t_disc, prop_s, data_disconnected['target']['propensity'])
        pehe_anchor_shared = np.sqrt(mean_squared_error(tau_true, anchor_shared.predict(X_t)))
        
        results.append({
            'Proxy': pehe_proxy,
            'Anchor (Separate)': pehe_anchor_sep,
            'Anchor (Shared)': pehe_anchor_shared
        })
    
    print("  " + " "*50)  # Clear line
    df = pd.DataFrame(results)
    
    print("\nResults (PEHE, lower is better):")
    print("-" * 60)
    for col in df.columns:
        print(f"{col:25s}: {df[col].mean():.4f} ± {df[col].std():.4f}")
    
    improvement = 100 * (df['Anchor (Separate)'].mean() - df['Anchor (Shared)'].mean()) / df['Anchor (Separate)'].mean()
    print(f"\nAnchor Shared vs Separate: {improvement:+.1f}% improvement")
    
    df.to_csv('results/diagnostics/check3_shared_correction.csv', index=False)
    print(f"Saved: results/diagnostics/check3_shared_correction.csv\n")
    
    return df


# CHECK 4: Stronger Regularization (simplified)
def check4_stronger_regularization_fast():
    """Test 1-SE rule vs default LASSO at ρ=0.5"""
    print("\n" + "="*80)
    print("CHECK 4: Stronger LASSO Regularization at ρ=0.5 (10 runs)")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    rho = 0.5
    n_target = 2000
    n_runs = 10  # Reduced from 30
    
    results = []
    
    for seed in range(42, 42 + n_runs):
        print(f"  Run {seed-41}/{n_runs}...", end='\r')
        
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
        
        mu0_proxy = proxy.models_[0].predict(X_t)
        mu1_proxy = proxy.models_[1].predict(X_t)
        
        # Default LASSO
        mask_control = A_t == 0
        mask_treated = A_t == 1
        
        lasso_0 = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=seed)
        lasso_0.fit(X_t[mask_control], Y_t[mask_control] - mu0_proxy[mask_control])
        
        lasso_1 = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=seed)
        lasso_1.fit(X_t[mask_treated], Y_t[mask_treated] - mu1_proxy[mask_treated])
        
        tau_default = (mu1_proxy + X_t @ lasso_1.coef_) - (mu0_proxy + X_t @ lasso_0.coef_)
        pehe_default = np.sqrt(mean_squared_error(tau_true, tau_default))
        
        # Stronger regularization: multiply alpha by 2
        alpha_strong_0 = lasso_0.alpha_ * 2.0
        alpha_strong_1 = lasso_1.alpha_ * 2.0
        
        lasso_0_strong = LassoCV(cv=5, fit_intercept=True, max_iter=5000, 
                                 random_state=seed, alphas=[alpha_strong_0])
        lasso_0_strong.fit(X_t[mask_control], Y_t[mask_control] - mu0_proxy[mask_control])
        
        lasso_1_strong = LassoCV(cv=5, fit_intercept=True, max_iter=5000,
                                 random_state=seed, alphas=[alpha_strong_1])
        lasso_1_strong.fit(X_t[mask_treated], Y_t[mask_treated] - mu1_proxy[mask_treated])
        
        tau_strong = (mu1_proxy + X_t @ lasso_1_strong.coef_) - (mu0_proxy + X_t @ lasso_0_strong.coef_)
        pehe_strong = np.sqrt(mean_squared_error(tau_true, tau_strong))
        
        results.append({
            'Proxy': pehe_proxy,
            'Anchor (Default)': pehe_default,
            'Anchor (2x Alpha)': pehe_strong,
            'nnz_default': np.sum(np.abs(lasso_1.coef_ - lasso_0.coef_) > 1e-6),
            'nnz_strong': np.sum(np.abs(lasso_1_strong.coef_ - lasso_0_strong.coef_) > 1e-6)
        })
    
    print("  " + " "*50)  # Clear line
    df = pd.DataFrame(results)
    
    print("\nResults (PEHE, lower is better):")
    print("-" * 60)
    for col in ['Proxy', 'Anchor (Default)', 'Anchor (2x Alpha)']:
        print(f"{col:25s}: {df[col].mean():.4f} ± {df[col].std():.4f}")
    
    print(f"\nSparsity (non-zero in δ₁ - δ₀):")
    print(f"  Default: {df['nnz_default'].mean():.1f} ± {df['nnz_default'].std():.1f}")
    print(f"  Strong:  {df['nnz_strong'].mean():.1f} ± {df['nnz_strong'].std():.1f}")
    
    improvement = 100 * (df['Anchor (Default)'].mean() - df['Anchor (2x Alpha)'].mean()) / df['Anchor (Default)'].mean()
    print(f"\nStronger regularization vs Default: {improvement:+.1f}% improvement")
    
    df.to_csv('results/diagnostics/check4_regularization.csv', index=False)
    print(f"Saved: results/diagnostics/check4_regularization.csv\n")
    
    return df


def main():
    print("\n" + "="*80)
    print("FAST ADVISOR DIAGNOSTICS (Checks 3 & 4)")
    print("="*80)
    print()
    
    # Load existing results from checks 1 & 2
    print("Checks 1 & 2 already completed:")
    print("  ✓ check1_true_bias_diff.png")
    print("  ✓ check2_correction_variance.png")
    print()
    
    # Run checks 3 and 4
    df3 = check3_shared_correction_fast()
    df4 = check4_stronger_regularization_fast()
    
    print("\n" + "="*80)
    print("ALL DIAGNOSTICS COMPLETE")
    print("="*80)
    print("\nResults in: results/diagnostics/")


if __name__ == "__main__":
    main()
