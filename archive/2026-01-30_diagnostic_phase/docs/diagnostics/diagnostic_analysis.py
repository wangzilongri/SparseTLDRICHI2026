"""
Diagnostic Analysis: Why is Proposed Underperforming?

This script runs detailed diagnostics to identify issues with the Proposed method.
"""

import sys
sys.path.insert(0, '/Users/zilongwang/Sparse_TL_DR_ICHI2026/src')

import numpy as np
import pandas as pd
from data_generator import MultiSiteSimulator
from scratch_estimator import PlaceboAnchoredDRLearner
from baselines import ProxyOnlyBaseline, AnchorOnlyBaseline

# Single run with detailed inspection
np.random.seed(42)

print("=" * 80)
print("DIAGNOSTIC ANALYSIS: Why is Proposed Underperforming?")
print("=" * 80)

# Generate one dataset
simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
data = simulator.generate_network(
    n_source_sites=3,
    n_target=200,
    source_patients_per_site=500,
    disconnected=True,
    covariate_shift_scale=0.5,
    bias_sparsity=2,
    seed=42
)

X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
X_t = data['target']['X']
A_t = data['target']['A']
Y_t = data['target']['Y']
prop_t = data['target']['propensity']
tau_true = data['target']['tau']
mu0_true = data['target']['mu_0']
mu1_true = data['target']['mu_1']

print(f"\nData Summary:")
print(f"  Source: {len(X_s)} samples ({np.sum(A_s==0)} placebo, {np.sum(A_s==1)} treated)")
print(f"  Target: {len(X_t)} samples ({np.sum(A_t==0)} placebo, {np.sum(A_t==1)} treated)")
print(f"  Features: {X_t.shape[1]}, Effect modifiers: 3")
print(f"  True ATE: {np.mean(tau_true):.3f}")
print(f"  True CATE std: {np.std(tau_true):.3f}")

# ============================================================================
# ISSUE 1: Check LASSO Feature Selection
# ============================================================================
print("\n" + "=" * 80)
print("ISSUE 1: Is LASSO Selecting Any Features?")
print("=" * 80)

# Fit Anchor-Only to inspect LASSO
anchor = AnchorOnlyBaseline()
anchor.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, prop_t)

print(f"\nAnchor-Only LASSO Correction:")
print(f"  ||δ_0||_0 (non-zero features): {np.sum(np.abs(anchor.delta_0_) > 1e-6)}")
print(f"  ||δ_0||_2 (L2 norm): {np.linalg.norm(anchor.delta_0_):.4f}")
print(f"  Intercept: {anchor.intercept_0_:.4f}")
print(f"\n  Top 5 features by |coefficient|:")
feature_importance = np.abs(anchor.delta_0_)
top_features = np.argsort(feature_importance)[::-1][:5]
for i, feat_idx in enumerate(top_features):
    print(f"    Feature {feat_idx}: {anchor.delta_0_[feat_idx]:+.4f}")

# True transport bias for comparison
true_delta_0 = data['target']['delta_0']
print(f"\n  True Transport Bias:")
print(f"    ||δ_0^*||_0: {np.sum(np.abs(true_delta_0) > 1e-6)}")
print(f"    ||δ_0^*||_2: {np.linalg.norm(true_delta_0):.4f}")
print(f"\n  Top 5 true bias features:")
true_importance = np.abs(true_delta_0)
true_top = np.argsort(true_importance)[::-1][:5]
for i, feat_idx in enumerate(true_top):
    print(f"    Feature {feat_idx}: {true_delta_0[feat_idx]:+.4f}")

# ============================================================================
# ISSUE 2: Check Proxy Model Quality
# ============================================================================
print("\n" + "=" * 80)
print("ISSUE 2: Are Proxy Models Accurate Enough?")
print("=" * 80)

proxy = ProxyOnlyBaseline()
proxy.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, prop_t)

# Evaluate proxy on target
mu0_proxy = proxy.models_[0].predict(X_t)
mu1_proxy = proxy.models_[1].predict(X_t)

rmse_mu0 = np.sqrt(np.mean((mu0_proxy - mu0_true)**2))
rmse_mu1 = np.sqrt(np.mean((mu1_proxy - mu1_true)**2))

print(f"\nProxy Model Calibration on Target:")
print(f"  RMSE(μ_0): {rmse_mu0:.3f}")
print(f"  RMSE(μ_1): {rmse_mu1:.3f}")
print(f"  Bias(μ_0): {np.mean(mu0_proxy - mu0_true):+.3f}")
print(f"  Bias(μ_1): {np.mean(mu1_proxy - mu1_true):+.3f}")

# After anchoring
mu0_anchored = mu0_proxy + X_t @ anchor.delta_0_ + anchor.intercept_0_
rmse_mu0_anchored = np.sqrt(np.mean((mu0_anchored - mu0_true)**2))
print(f"\n  After Anchoring:")
print(f"    RMSE(μ_0): {rmse_mu0_anchored:.3f} (improvement: {rmse_mu0 - rmse_mu0_anchored:+.3f})")
print(f"    Bias(μ_0): {np.mean(mu0_anchored - mu0_true):+.3f}")

# ============================================================================
# ISSUE 3: Check Cross-Fitting Impact
# ============================================================================
print("\n" + "=" * 80)
print("ISSUE 3: Is Cross-Fitting Introducing Too Much Variance?")
print("=" * 80)

# Fit Proposed with verbose diagnostics
proposed = PlaceboAnchoredDRLearner(option='B', n_folds_dr=5, verbose=False)
proposed.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, prop_t)

print(f"\nProposed Method (5-fold cross-fitting):")
print(f"  Pseudo-outcomes: mean={np.mean(proposed.pseudo_outcomes_):.3f}, "
      f"std={np.std(proposed.pseudo_outcomes_):.3f}")
print(f"  True CATE: mean={np.mean(tau_true):.3f}, std={np.std(tau_true):.3f}")
print(f"\n  Pseudo-outcome diagnostics:")
print(f"    Min: {np.min(proposed.pseudo_outcomes_):.3f}")
print(f"    Q1:  {np.percentile(proposed.pseudo_outcomes_, 25):.3f}")
print(f"    Med: {np.median(proposed.pseudo_outcomes_):.3f}")
print(f"    Q3:  {np.percentile(proposed.pseudo_outcomes_, 75):.3f}")
print(f"    Max: {np.max(proposed.pseudo_outcomes_):.3f}")

# Check for outliers in pseudo-outcomes
outlier_threshold = 3 * np.std(tau_true)
n_outliers = np.sum(np.abs(proposed.pseudo_outcomes_ - np.mean(tau_true)) > outlier_threshold)
print(f"\n  Outliers (>3σ from true mean): {n_outliers}/{len(proposed.pseudo_outcomes_)} ({100*n_outliers/len(proposed.pseudo_outcomes_):.1f}%)")

# Inspect fold-specific corrections
print(f"\n  Fold-specific LASSO corrections:")
for fold_idx, fold_model in enumerate(proposed.fold_models_):
    delta_0 = fold_model['delta_0']
    sparsity = np.sum(np.abs(delta_0) > 1e-6)
    l2_norm = np.linalg.norm(delta_0)
    print(f"    Fold {fold_idx}: ||δ_0||_0={sparsity}, ||δ_0||_2={l2_norm:.4f}")

# ============================================================================
# ISSUE 4: Compare Predictions
# ============================================================================
print("\n" + "=" * 80)
print("ISSUE 4: How Do Predictions Compare?")
print("=" * 80)

tau_proxy = proxy.predict(X_t)
tau_anchor = anchor.predict(X_t)
tau_proposed = proposed.predict(X_t)

def compute_metrics(tau_pred, tau_true):
    pehe = np.sqrt(np.mean((tau_pred - tau_true)**2))
    ate_error = np.abs(np.mean(tau_pred) - np.mean(tau_true))
    r2 = 1 - np.sum((tau_pred - tau_true)**2) / np.sum((tau_true - np.mean(tau_true))**2)
    return pehe, ate_error, r2

metrics = {
    'Proxy-Only': compute_metrics(tau_proxy, tau_true),
    'Anchor-Only': compute_metrics(tau_anchor, tau_true),
    'Proposed': compute_metrics(tau_proposed, tau_true)
}

print(f"\n{'Method':<15} {'PEHE':<8} {'ATE Err':<8} {'R² CATE':<8}")
print("-" * 45)
for method, (pehe, ate, r2) in metrics.items():
    print(f"{method:<15} {pehe:<8.3f} {ate:<8.3f} {r2:<8.3f}")

# Correlation analysis
print(f"\n  Prediction Correlations with True CATE:")
print(f"    Proxy-Only:  r={np.corrcoef(tau_proxy, tau_true)[0,1]:.3f}")
print(f"    Anchor-Only: r={np.corrcoef(tau_anchor, tau_true)[0,1]:.3f}")
print(f"    Proposed:    r={np.corrcoef(tau_proposed, tau_true)[0,1]:.3f}")

# ============================================================================
# ISSUE 5: Check Hyperparameters
# ============================================================================
print("\n" + "=" * 80)
print("ISSUE 5: Are Hyperparameters Reasonable?")
print("=" * 80)

print(f"\nCurrent Hyperparameters:")
print(f"  Proxy Model (RF):")
print(f"    n_estimators: 200")
print(f"    max_depth: 6 (Proposed) vs 8 (Baselines)")
print(f"    min_samples_leaf: 10 (Proposed) vs 20 (Baselines)")
print(f"  CATE Model (GBM):")
print(f"    n_estimators: 100")
print(f"    max_depth: 3")
print(f"  Cross-fitting: {proposed.n_folds_dr} folds")
print(f"  LASSO CV: {proposed.lasso_cv_folds} folds")

print(f"\n⚠️  INCONSISTENCY DETECTED:")
print(f"  Proposed uses DIFFERENT hyperparameters than baselines!")
print(f"  Proxy model is MORE COMPLEX (max_depth=6 vs 8, min_samples_leaf=10 vs 20)")
print(f"  This may cause overfitting in Stage 1, leading to poor anchoring.")

# ============================================================================
# ISSUE 6: Check Sample Sizes Per Fold
# ============================================================================
print("\n" + "=" * 80)
print("ISSUE 6: Are Sample Sizes Sufficient for Cross-Fitting?")
print("=" * 80)

n_target = len(X_t)
n_placebo = np.sum(A_t == 0)
n_per_fold = n_placebo // proposed.n_folds_dr

print(f"\nTarget Sample Sizes:")
print(f"  Total target: {n_target}")
print(f"  Target placebo: {n_placebo}")
print(f"  Placebo per fold (training): ~{n_per_fold * (proposed.n_folds_dr-1) // proposed.n_folds_dr}")
print(f"  Placebo per fold (validation): ~{n_per_fold}")

print(f"\n⚠️  POTENTIAL ISSUE:")
print(f"  With only ~{n_per_fold * 4 // 5} placebo samples per training fold,")
print(f"  LASSO may be unstable or underfit.")
print(f"  Consider reducing n_folds_dr from 5 to 3.")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

print(f"""
KEY FINDINGS:

1. LASSO Feature Selection:
   - Anchor-Only selects {np.sum(np.abs(anchor.delta_0_) > 1e-6)} features (true: {np.sum(np.abs(true_delta_0) > 1e-6)})
   - If zero features selected, anchoring has no effect
   
2. Proxy Model Quality:
   - RMSE before anchoring: {rmse_mu0:.3f}
   - RMSE after anchoring: {rmse_mu0_anchored:.3f}
   - Improvement: {rmse_mu0 - rmse_mu0_anchored:+.3f}
   
3. Cross-Fitting Variance:
   - Pseudo-outcomes std: {np.std(proposed.pseudo_outcomes_):.3f}
   - True CATE std: {np.std(tau_true):.3f}
   - Ratio: {np.std(proposed.pseudo_outcomes_) / np.std(tau_true):.2f}x
   - Outliers: {n_outliers}/{len(proposed.pseudo_outcomes_)} ({100*n_outliers/len(proposed.pseudo_outcomes_):.1f}%)
   
4. Prediction Quality:
   - Proposed PEHE: {metrics['Proposed'][0]:.3f} vs Anchor-Only: {metrics['Anchor-Only'][0]:.3f}
   - Correlation with truth: {np.corrcoef(tau_proposed, tau_true)[0,1]:.3f}
   
5. Hyperparameter Mismatch:
   - Proposed uses DIFFERENT proxy hyperparameters than baselines
   - This makes comparison unfair!
   
6. Sample Size:
   - ~{n_per_fold * 4 // 5} placebo per training fold
   - May be too small for stable LASSO + DR

RECOMMENDED FIXES:

Priority 1 (Critical):
- [ ] Make Proposed use SAME proxy hyperparameters as baselines
- [ ] Reduce n_folds_dr from 5 to 3 (more data per fold)

Priority 2 (Important):  
- [ ] Add outlier clipping to pseudo-outcomes (e.g., clip at ±3σ)
- [ ] Try different CATE model (RF instead of GBM)
- [ ] Increase target sample size to 500

Priority 3 (Nice to have):
- [ ] Hyperparameter tuning via cross-validation
- [ ] Increase Monte Carlo runs to 100
- [ ] Add confidence intervals
""")

print("=" * 80)
