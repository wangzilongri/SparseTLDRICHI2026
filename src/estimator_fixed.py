"""
FIXED Three-Stage Placebo-Anchored Doubly Robust Estimator

Key fixes based on advisor feedback:
1. Leak-proof cross-fitting (no global delta fallbacks)
2. Option B with Step B operator transfer (learn M from sources)
3. StratifiedKFold for both arms in each fold
4. Propensity clipping instead of skipping
5. Vectorized pseudo-outcomes
6. Feature scaling for LASSO
7. Proper zero-delta fallback
8. Explicit variant/ablation switch for benchmark reproducibility
9. Artifact persistence via joblib for consistent sweeps
"""

import numpy as np
import os
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV, RidgeCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted, check_array
import warnings


# =============================================================================
# Utility Classes
# =============================================================================

class _ZeroDelta:
    """Fallback predictor for folds with no samples."""
    def __init__(self, n_features):
        self.coef_ = np.zeros(n_features)
        self.intercept_ = 0.0
        self.n_features = n_features
    
    def predict(self, X):
        return np.zeros(len(X))


class _ZeroProxy:
    """Fallback proxy model that predicts zeros (for no_transfer variant)."""
    def __init__(self, n_features=None):
        self.n_features = n_features
    
    def fit(self, X, y):
        self.n_features = X.shape[1] if X is not None else self.n_features
        return self
    
    def predict(self, X):
        return np.zeros(len(X))


class _ScaledDelta:
    """Delta predictor that uses a global scaler (for Option B)."""
    def __init__(self, coef, scaler, intercept=0.0, alpha=None):
        self.coef_ = coef
        self.scaler = scaler
        self.intercept_ = intercept
        self.alpha_ = alpha  # Store LassoCV lambda for diagnostics
    
    def predict(self, X):
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            return X_scaled @ self.coef_ + self.intercept_
        return X @ self.coef_ + self.intercept_


class _TransferredDelta:
    """Delta predictor from transfer operator (for Option B)."""
    def __init__(self, beta, scaler=None, intercept=0.0):
        self.coef_ = beta
        self.scaler = scaler
        self.intercept_ = intercept
    
    def predict(self, X):
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            return X_scaled @ self.coef_ + self.intercept_
        return X @ self.coef_ + self.intercept_


# =============================================================================
# Valid Variants
# =============================================================================

VALID_VARIANTS = [
    'no_transfer',      # Target-only DR learner: fit μ₀, μ₁ on target folds, no source data
    'proxy_only',       # Stage1 on; Stage2 off; Stage3 uses proxy mu's only (delta=0)
    'anchor_only',      # Stage1 on; Stage2 on for placebo only; treated delta = 0
    'anchor_only_A',    # Stage1 on; Stage2 for both arms from target; no Step B transfer
    'proposed_A',       # Stage1 + Stage2(A) + Stage3 (needs target treated)
    'proposed_B',       # Stage1 + StepB + Stage2(B via StepB) + Stage3
]


class PlaceboAnchoredDRLearner(BaseEstimator, RegressorMixin):
    """
    FIXED Three-stage doubly robust learner with placebo anchoring.
    
    Stage 1: Fit proxy models on source trials
    Stage 2: Estimate sparse transport corrections using target placebo (gold)
             Option B: Learn operator M from sources for cross-arm transfer
    Stage 3: Target-only DR CATE with leak-proof cross-fitting
    
    Parameters
    ----------
    proxy_model : sklearn estimator, default=RandomForestRegressor
        Model for Stage 1 proxy fitting
    correction_model : sklearn estimator, default=LassoCV with scaling
        Sparse model for Stage 2 corrections
    cate_model : sklearn estimator, default=RandomForestRegressor
        Model for Stage 3 CATE regression
    option : str, 'A' or 'B', default='A'
        Option A: Estimate separate corrections when target has both arms
        Option B: Transfer via operator M learned from sources
    variant : str, default=None
        Explicit ablation variant. If set, overrides option:
        - 'no_transfer': No source data, target-only naive
        - 'proxy_only': Source proxy only, no target anchoring (delta=0)
        - 'anchor_only': Proxy + placebo anchor, no Step B (treated delta=0)
        - 'proposed_A': Full method with direct target corrections
        - 'proposed_B': Full method with Step B operator transfer
    stage2_mode : str, default='lasso'
        Model for Stage 2 corrections: 'lasso', 'ridge', 'elasticnet'
    n_folds : int, default=5
        Number of folds for cross-fitting in Stage 3
    save_fold_nuisance : bool, default=False
        Whether to save fold-level nuisance models (for diagnostics)
    random_state : int, default=42
    verbose : bool, default=False
    """
    
    def __init__(self, proxy_model=None, correction_model=None, cate_model=None,
                 option='A', variant=None, stage2_mode='lasso', n_folds=5,
                 save_fold_nuisance=False, random_state=42, verbose=False):
        self.proxy_model = proxy_model
        self.correction_model = correction_model
        self.cate_model = cate_model
        self.option = option
        self.variant = variant
        self.stage2_mode = stage2_mode
        self.n_folds = n_folds
        self.save_fold_nuisance = save_fold_nuisance
        self.random_state = random_state
        self.verbose = verbose
    
    def _get_effective_variant(self):
        """
        Get the effective variant, inferring from option if not explicitly set.
        
        Returns
        -------
        variant : str
            One of VALID_VARIANTS
        """
        if self.variant is not None:
            if self.variant not in VALID_VARIANTS:
                raise ValueError(f"Invalid variant: {self.variant}. Valid: {VALID_VARIANTS}")
            return self.variant
        
        # Infer from option (backward compatibility)
        if self.option == 'A':
            return 'proposed_A'
        elif self.option == 'B':
            return 'proposed_B'
        else:
            raise ValueError(f"Invalid option: {self.option}")
    
    def _variant_flags(self):
        """
        Get flags controlling which stages are active based on variant.
        
        Returns
        -------
        flags : dict
            do_stage1: bool - fit proxy models on source
            do_stage2: bool - fit placebo correction (and possibly treated)
            do_stepB: bool - learn/use transfer operator M
            do_stage3: bool - fit CATE model (always True)
        """
        variant = self._get_effective_variant()
        
        return {
            'do_stage1': variant in ['proxy_only', 'anchor_only', 'anchor_only_A', 'proposed_A', 'proposed_B'],
            'do_stage2': variant in ['anchor_only', 'anchor_only_A', 'proposed_A', 'proposed_B'],
            'do_stepB': variant in ['proposed_B'],
            'do_stage3': True,  # Always fit CATE model
        }
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target, Y_target, propensity_target=None):
        """
        Fit the three-stage estimator with leak-proof cross-fitting.
        
        Parameters
        ----------
        X_source : array-like, shape (n_source, p)
            Source covariates
        A_source : array-like, shape (n_source,)
            Source treatment assignments
        Y_source : array-like, shape (n_source,)
            Source outcomes
        c_source : array-like, shape (n_source,)
            Source site indicators (1, 2, ..., C)
        X_target : array-like, shape (n_target, p)
            Target covariates
        A_target : array-like, shape (n_target,)
            Target treatment assignments
        Y_target : array-like, shape (n_target,)
            Target outcomes
        propensity_target : array-like, shape (n_target,), optional
            Target propensity scores (default: 0.5 for RCTs)
        """
        # Get variant flags
        flags = self._variant_flags()
        self._effective_variant_ = self._get_effective_variant()
        
        # Validate inputs
        X_source = check_array(X_source)
        X_target = check_array(X_target)
        A_source = np.asarray(A_source).ravel()
        A_target = np.asarray(A_target).ravel()
        Y_source = np.asarray(Y_source).ravel()
        Y_target = np.asarray(Y_target).ravel()
        c_source = np.asarray(c_source).ravel()
        
        n_source, self.n_features_ = X_source.shape
        n_target = len(X_target)
        
        # Default propensity for RCTs
        if propensity_target is None:
            propensity_target = np.full(n_target, 0.5)
        else:
            propensity_target = np.asarray(propensity_target).ravel()
        
        # Validate propensity (issue 4.1)
        if propensity_target.shape[0] != n_target:
            raise ValueError(f"propensity_target has shape {propensity_target.shape}, "
                           f"expected ({n_target},)")
        if np.any(propensity_target <= 0) or np.any(propensity_target >= 1):
            warnings.warn("propensity_target contains values outside (0,1); will be clipped")
        
        # Initialize models
        if self.proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=100, max_depth=8, random_state=self.random_state, n_jobs=-1
            )
        if self.correction_model is None:
            # Pipeline with StandardScaler + LassoCV (or Ridge based on stage2_mode)
            if self.stage2_mode == 'ridge':
                self.correction_model = Pipeline([
                    ("scaler", StandardScaler()),
                    ("ridge", RidgeCV(cv=5, fit_intercept=True))
                ])
            else:  # default lasso
                self.correction_model = Pipeline([
                    ("scaler", StandardScaler()),
                    ("lasso", LassoCV(cv=5, fit_intercept=True, random_state=self.random_state, n_jobs=-1))
                ])
        if self.cate_model is None:
            self.cate_model = RandomForestRegressor(
                n_estimators=100, max_depth=5, random_state=self.random_state, n_jobs=-1
            )
        
        # Initialize Stage-2 diagnostics tracking
        self.stage2_lambda_folds_ = []
        self.stage2_n_selected_folds_ = []
        
        # ===================================================================
        # STAGE 1: Fit proxy models on source data
        # ===================================================================
        if flags['do_stage1']:
            if self.verbose:
                print(f"Stage 1: Fitting proxy models on source data (variant={self._effective_variant_})...")
            self._fit_proxy_models(X_source, A_source, Y_source)
        else:
            # no_transfer variant: use zero proxies
            if self.verbose:
                print(f"Stage 1: SKIPPED (variant={self._effective_variant_}, using zero proxies)...")
            self.proxy_models_ = {
                0: _ZeroProxy(self.n_features_),
                1: _ZeroProxy(self.n_features_)
            }
        
        # ===================================================================
        # STAGE 2 (Step B): Learn transfer operator M from sources
        # ===================================================================
        if flags['do_stepB']:
            if self.verbose:
                print("Stage 2 (Step B): Learning cross-arm transfer operator M from sources...")
            self._fit_transfer_operator(X_source, A_source, Y_source, c_source)
        else:
            self.M_hat_ = None
            self.global_scaler_ = None
            self.transfer_diagnostics_ = {'fallback': True, 'reason': 'stepB_disabled_by_variant'}
        
        # ===================================================================
        # STAGE 2-3: Target-only corrections + DR with cross-fitting
        # ===================================================================
        if self.verbose:
            print(f"Stage 2-3: Target correction + DR with {self.n_folds}-fold cross-fitting...")
        
        self._fit_target_dr(X_target, A_target, Y_target, propensity_target, flags)
        
        # Aggregate Stage-2 diagnostics
        self.stage2_lambda_ = float(np.nanmedian(self.stage2_lambda_folds_)) if self.stage2_lambda_folds_ else None
        self.stage2_n_selected_ = int(np.nanmedian(self.stage2_n_selected_folds_)) if self.stage2_n_selected_folds_ else None
        
        if self.verbose:
            print(f"Fitting complete. Variant={self._effective_variant_}")
            if self.stage2_lambda_ is not None:
                print(f"  Stage2: λ={self.stage2_lambda_:.4f}, n_selected={self.stage2_n_selected_}")
        
        return self
    
    def _fit_proxy_models(self, X_source, A_source, Y_source):
        """Stage 1: Fit proxy models on pooled source data."""
        self.proxy_models_ = {}
        
        for a in [0, 1]:
            mask = (A_source == a)
            if np.sum(mask) == 0:
                raise ValueError(f"No samples with A={a} in source data")
            
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.proxy_models_[a] = model
            
            if self.verbose:
                print(f"  Proxy model for A={a}: {np.sum(mask)} samples")
    
    def _fit_transfer_operator(self, X_source, A_source, Y_source, c_source):
        """
        Option B Step B: Learn cross-arm transfer operator M from sources.
        
        Mathematical model (aligned with DGP A6):
            β_{1,c} ≈ M* @ β_{0,c} + ν_c
        
        Algorithm:
        1. Fit GLOBAL scaler on all source X (shared coordinate system)
        2. For each source site c with BOTH arms:
           - Fit β_{0,c} on scaled placebo residuals
           - Fit β_{1,c} on scaled treated residuals
        3. Stack ALIGNED matrices: B₀ = [β₀,c₁ ... β₀,cK], B₁ = [β₁,c₁ ... β₁,cK]
        4. Matrix ridge: M̂ = B₁ B₀ᵀ (B₀ B₀ᵀ + λI)⁻¹
        
        CRITICAL FIXES (advisor feedback):
        - FIX #1: Align β₀ and β₁ by site - only use sites with BOTH arms
        - FIX #2: Use GLOBAL scaler so coefficients are comparable across sites
        - FIX #3: Matrix ridge regression (not per-row) for stability
        """
        sites = np.unique(c_source)
        sites = sites[sites > 0]  # Exclude target (c=0)
        p = self.n_features_
        
        if len(sites) < 2:
            warnings.warn("Less than 2 source sites; using M=I fallback")
            self.M_hat_ = np.eye(p)
            self.global_scaler_ = None
            self.transfer_diagnostics_ = {'n_sites_used': 0, 'fallback': True}
            return
        
        # ═══════════════════════════════════════════════════════════════════
        # FIX #2: Fit GLOBAL scaler on all source X (shared coordinate system)
        # ═══════════════════════════════════════════════════════════════════
        self.global_scaler_ = StandardScaler()
        self.global_scaler_.fit(X_source)
        X_source_scaled = self.global_scaler_.transform(X_source)
        
        # ═══════════════════════════════════════════════════════════════════
        # FIX #1: Build dictionaries keyed by site, then intersect
        # ═══════════════════════════════════════════════════════════════════
        beta_0_by_site = {}
        beta_1_by_site = {}
        
        min_samples_per_arm = 10  # Minimum for stable LASSO
        
        for site in sites:
            mask_site = (c_source == site)
            X_c_scaled = X_source_scaled[mask_site]  # Use globally scaled X
            X_c_unscaled = X_source[mask_site]  # For proxy predictions
            A_c = A_source[mask_site]
            Y_c = Y_source[mask_site]
            
            # Try to fit β_{0,c} (placebo correction)
            mask_placebo = (A_c == 0)
            if np.sum(mask_placebo) >= min_samples_per_arm:
                X_p_scaled = X_c_scaled[mask_placebo]
                X_p_unscaled = X_c_unscaled[mask_placebo]
                Y_p = Y_c[mask_placebo]
                
                # Residualize against proxy (proxy was fit on unscaled X)
                mu0_proxy = self.proxy_models_[0].predict(X_p_unscaled)
                resid_p = Y_p - mu0_proxy
                
                # Fit LASSO on scaled X (no pipeline - we use global scaler)
                lasso_0 = LassoCV(cv=5, fit_intercept=True, 
                                  random_state=self.random_state, n_jobs=-1)
                lasso_0.fit(X_p_scaled, resid_p)
                beta_0_by_site[site] = lasso_0.coef_
            
            # Try to fit β_{1,c} (treated correction)
            mask_treated = (A_c == 1)
            if np.sum(mask_treated) >= min_samples_per_arm:
                X_t_scaled = X_c_scaled[mask_treated]
                X_t_unscaled = X_c_unscaled[mask_treated]
                Y_t = Y_c[mask_treated]
                
                # Residualize against proxy
                mu1_proxy = self.proxy_models_[1].predict(X_t_unscaled)
                resid_t = Y_t - mu1_proxy
                
                # Fit LASSO on scaled X
                lasso_1 = LassoCV(cv=5, fit_intercept=True,
                                  random_state=self.random_state, n_jobs=-1)
                lasso_1.fit(X_t_scaled, resid_t)
                beta_1_by_site[site] = lasso_1.coef_
        
        # ═══════════════════════════════════════════════════════════════════
        # Intersection: only sites with BOTH arms (critical alignment!)
        # ═══════════════════════════════════════════════════════════════════
        common_sites = sorted(set(beta_0_by_site.keys()) & set(beta_1_by_site.keys()))
        
        if len(common_sites) < 2:
            warnings.warn(f"Only {len(common_sites)} sites with both arms; using M=I")
            self.M_hat_ = np.eye(p)
            self.transfer_diagnostics_ = {'n_sites_used': len(common_sites), 'fallback': True}
            return
        
        # Stack in SAME ORDER (critical for alignment!)
        B_0 = np.column_stack([beta_0_by_site[c] for c in common_sites])  # p × C
        B_1 = np.column_stack([beta_1_by_site[c] for c in common_sites])  # p × C
        C = len(common_sites)
        
        if self.verbose:
            print(f"  Step B: Using {C} source sites with both arms")
            print(f"  B_0 shape: {B_0.shape}, B_1 shape: {B_1.shape}")
        
        # ═══════════════════════════════════════════════════════════════════
        # FIX #3: Matrix ridge regression (not per-row)
        # M̂ = B₁ B₀ᵀ (B₀ B₀ᵀ + λI)⁻¹
        # ═══════════════════════════════════════════════════════════════════
        
        # Choose λ via leave-one-site-out CV
        sigma_scale = np.linalg.norm(B_0, 'fro') / np.sqrt(C * p) + 1e-6
        lambda_candidates = sigma_scale * np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        
        best_lambda = lambda_candidates[2]  # Default middle value
        best_error = np.inf
        
        # Leave-one-site-out CV for λ selection (only if enough sites)
        if C >= 4:
            for lam in lambda_candidates:
                cv_error = 0.0
                for held_out_site in common_sites:
                    # Leave site out
                    train_sites = [s for s in common_sites if s != held_out_site]
                    B0_train = np.column_stack([beta_0_by_site[s] for s in train_sites])
                    B1_train = np.column_stack([beta_1_by_site[s] for s in train_sites])
                    
                    # Fit M on training sites
                    G = B0_train @ B0_train.T
                    try:
                        M_cv = (B1_train @ B0_train.T) @ np.linalg.inv(G + lam * np.eye(p))
                    except np.linalg.LinAlgError:
                        continue
                    
                    # Predict on held-out site
                    beta0_test = beta_0_by_site[held_out_site]
                    beta1_test = beta_1_by_site[held_out_site]
                    beta1_pred = M_cv @ beta0_test
                    cv_error += np.sum((beta1_test - beta1_pred)**2)
                
                if cv_error < best_error:
                    best_error = cv_error
                    best_lambda = lam
        
        # Final fit with selected λ
        G = B_0 @ B_0.T  # p × p
        try:
            M_hat = (B_1 @ B_0.T) @ np.linalg.inv(G + best_lambda * np.eye(p))
        except np.linalg.LinAlgError:
            warnings.warn("Matrix inversion failed in Step B; using M=I")
            self.M_hat_ = np.eye(p)
            self.transfer_diagnostics_ = {'n_sites_used': C, 'fallback': True}
            return
        
        self.M_hat_ = M_hat
        
        # Compute diagnostics
        svd_vals = np.linalg.svd(M_hat, compute_uv=False)
        self.transfer_diagnostics_ = {
            'n_sites_used': C,
            'sites_used': common_sites,
            'lambda_selected': best_lambda,
            'M_fro_norm': np.linalg.norm(M_hat, 'fro'),
            'M_spectral_norm': np.linalg.norm(M_hat, 2),
            'M_effective_rank': np.sum(svd_vals > 1e-6 * svd_vals[0]),
            'M_condition_number': svd_vals[0] / (svd_vals[-1] + 1e-10),
            'fallback': False
        }
        
        if self.verbose:
            print(f"  λ selected: {best_lambda:.4f}")
            print(f"  ||M||_F = {self.transfer_diagnostics_['M_fro_norm']:.3f}")
            print(f"  ||M||_2 = {self.transfer_diagnostics_['M_spectral_norm']:.3f}")
            print(f"  Effective rank(M) = {self.transfer_diagnostics_['M_effective_rank']}")
    
    def _fit_target_dr(self, X_target, A_target, Y_target, propensity_target, flags=None):
        """
        Stage 2-3: Target corrections + DR with leak-proof cross-fitting.
        
        Key: Every nuisance estimate used for observation i is trained WITHOUT i.
        
        For Option B: Target corrections MUST use the same global scaler as Step B
        to ensure coefficients are in the same coordinate system.
        
        For no_transfer: Fit fold-specific target-only outcome models (true target-only DR).
        
        Parameters
        ----------
        flags : dict, optional
            Variant flags from _variant_flags(). If None, computed from option.
        """
        if flags is None:
            flags = self._variant_flags()
        
        variant = self._get_effective_variant()
        n_target = len(X_target)
        
        # FIXED: StratifiedKFold to ensure both arms in each fold
        skf = StratifiedKFold(
            n_splits=self.n_folds, 
            shuffle=True, 
            random_state=self.random_state
        )
        
        pseudo_outcomes = np.zeros(n_target)
        self.fold_corrections_ = [] if self.save_fold_nuisance else None
        
        # Persist fold splits for reproducibility
        self.folds_ = []
        
        # For Option B, check if we have the global scaler from Step B
        use_global_scaler = (flags['do_stepB'] and 
                            hasattr(self, 'global_scaler_') and 
                            self.global_scaler_ is not None)
        
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_target, A_target)):
            # Store fold indices for reproducibility
            self.folds_.append((train_idx.copy(), val_idx.copy()))
            
            # Training data for this fold
            X_train = X_target[train_idx]
            A_train = A_target[train_idx]
            Y_train = Y_target[train_idx]
            
            # Validation data
            X_val = X_target[val_idx]
            A_val = A_target[val_idx]
            Y_val = Y_target[val_idx]
            e_val = propensity_target[val_idx]
            
            # -----------------------------------------------------------------
            # Variant-specific nuisance estimation
            # -----------------------------------------------------------------
            
            if variant == 'no_transfer':
                # ═══════════════════════════════════════════════════════════════
                # FIX #1: no_transfer is TRUE target-only DR learner
                # Fit fold-specific μ₀, μ₁ on target data only (no source proxy)
                # ═══════════════════════════════════════════════════════════════
                mu_models_fold = {}
                for arm in [0, 1]:
                    mask_arm = (A_train == arm)
                    if mask_arm.sum() >= 5:
                        # Fit target-only outcome model for this arm
                        m = clone(self.proxy_model)  # Reuse proxy_model class/hparams
                        m.fit(X_train[mask_arm], Y_train[mask_arm])
                        mu_models_fold[arm] = m
                    else:
                        # Fallback: predict zero if arm missing in fold
                        mu_models_fold[arm] = _ZeroProxy(self.n_features_)
                
                # No corrections (target-only uses direct mu estimates)
                delta_0_fold = _ZeroDelta(self.n_features_)
                delta_1_fold = _ZeroDelta(self.n_features_)
                
                # Target-only mu predictions (NOT proxy + delta)
                mu0_val = mu_models_fold[0].predict(X_val)
                mu1_val = mu_models_fold[1].predict(X_val)
                
            elif variant == 'proxy_only':
                # Proxy only: use source-fitted proxies, no corrections
                delta_0_fold = _ZeroDelta(self.n_features_)
                delta_1_fold = _ZeroDelta(self.n_features_)
                
                # Proxy predictions only
                mu0_val = self.proxy_models_[0].predict(X_val)
                mu1_val = self.proxy_models_[1].predict(X_val)
                
            elif variant == 'anchor_only':
                # Placebo correction only, treated delta = 0
                delta_0_fold = self._fit_fold_correction(
                    X_train, A_train, Y_train, arm=0, use_global_scaler=False
                )
                delta_1_fold = _ZeroDelta(self.n_features_)
                
                # Anchored predictions
                mu0_val = self.proxy_models_[0].predict(X_val) + delta_0_fold.predict(X_val)
                mu1_val = self.proxy_models_[1].predict(X_val)  # No correction for treated
                
            elif variant == 'anchor_only_A':
                # ═══════════════════════════════════════════════════════════════
                # FIX #6: anchor_only_A - both corrections from target, no Step B
                # Fair comparison when target has both arms
                # ═══════════════════════════════════════════════════════════════
                delta_0_fold = self._fit_fold_correction(
                    X_train, A_train, Y_train, arm=0, use_global_scaler=False
                )
                delta_1_fold = self._fit_fold_correction(
                    X_train, A_train, Y_train, arm=1, use_global_scaler=False
                )
                
                # Anchored predictions
                mu0_val = self.proxy_models_[0].predict(X_val) + delta_0_fold.predict(X_val)
                mu1_val = self.proxy_models_[1].predict(X_val) + delta_1_fold.predict(X_val)
                
            elif variant == 'proposed_A':
                # Option A: Estimate both corrections from target data
                delta_0_fold = self._fit_fold_correction(
                    X_train, A_train, Y_train, arm=0, use_global_scaler=False
                )
                delta_1_fold = self._fit_fold_correction(
                    X_train, A_train, Y_train, arm=1, use_global_scaler=False
                )
                
                # Anchored predictions
                mu0_val = self.proxy_models_[0].predict(X_val) + delta_0_fold.predict(X_val)
                mu1_val = self.proxy_models_[1].predict(X_val) + delta_1_fold.predict(X_val)
                
            elif variant == 'proposed_B':
                # Option B: Placebo correction with global scaler, transfer for treated
                delta_0_fold = self._fit_fold_correction(
                    X_train, A_train, Y_train, arm=0, use_global_scaler=use_global_scaler
                )
                delta_1_fold = self._apply_transfer_operator(delta_0_fold)
                
                # Anchored predictions
                mu0_val = self.proxy_models_[0].predict(X_val) + delta_0_fold.predict(X_val)
                mu1_val = self.proxy_models_[1].predict(X_val) + delta_1_fold.predict(X_val)
                
            else:
                raise ValueError(f"Invalid variant: {variant}")
            
            # Track Stage-2 diagnostics
            self._track_stage2_diagnostics(delta_0_fold, delta_1_fold)
            
            # Store fold corrections for diagnostics (if enabled)
            if self.save_fold_nuisance:
                self.fold_corrections_.append({
                    'delta_0': delta_0_fold,
                    'delta_1': delta_1_fold,
                    'fold_idx': fold_idx
                })
            
            # -----------------------------------------------------------------
            # Stage 3: Compute DR pseudo-outcomes on validation fold
            # -----------------------------------------------------------------
            
            tau_val = mu1_val - mu0_val
            
            # FIXED: Clip propensities + vectorized pseudo-outcomes
            e_clipped = np.clip(e_val, 1e-3, 1 - 1e-3)
            mu_a = np.where(A_val == 1, mu1_val, mu0_val)
            
            psi_val = tau_val + ((A_val - e_clipped) / (e_clipped * (1 - e_clipped))) * (Y_val - mu_a)
            pseudo_outcomes[val_idx] = psi_val
        
        # Fit final CATE model on TARGET pseudo-outcomes only
        self.cate_model_ = clone(self.cate_model)
        self.cate_model_.fit(X_target, pseudo_outcomes)
        
        # Store global corrections (for predict_anchored convenience)
        self._fit_global_corrections(X_target, A_target, Y_target, flags)
        
        return self
    
    def _fit_fold_correction(self, X_train, A_train, Y_train, arm, use_global_scaler=False):
        """
        Fit correction model for one arm on one fold's training data.
        
        Parameters
        ----------
        X_train, A_train, Y_train : arrays
            Training data for this fold
        arm : int
            0 for placebo, 1 for treated
        use_global_scaler : bool
            If True, use global scaler (for Option B compatibility)
            
        Returns
        -------
        delta : correction model with .predict(X) method
        """
        mask = (A_train == arm)
        n_arm = np.sum(mask)
        
        if n_arm < 5:
            if self.verbose:
                print(f"    Arm {arm}: Only {n_arm} samples, using zero correction")
            return _ZeroDelta(self.n_features_)
        
        X_arm = X_train[mask]
        Y_arm = Y_train[mask]
        mu_proxy = self.proxy_models_[arm].predict(X_arm)
        resid = Y_arm - mu_proxy
        
        if use_global_scaler and self.global_scaler_ is not None:
            # Fit in global scaled space for M compatibility
            X_arm_scaled = self.global_scaler_.transform(X_arm)
            lasso = LassoCV(cv=5, fit_intercept=True,
                           random_state=self.random_state, n_jobs=-1)
            lasso.fit(X_arm_scaled, resid)
            # FIX #4: Store alpha_ for diagnostics
            return _ScaledDelta(
                coef=lasso.coef_, 
                scaler=self.global_scaler_, 
                intercept=lasso.intercept_,
                alpha=getattr(lasso, 'alpha_', None)
            )
        else:
            # Use pipeline with local scaler
            delta = clone(self.correction_model)
            delta.fit(X_arm, resid)
            return delta
    
    def _track_stage2_diagnostics(self, delta_0, delta_1):
        """Track Stage-2 LASSO diagnostics from fold corrections."""
        for delta, arm_name in [(delta_0, 'delta_0'), (delta_1, 'delta_1')]:
            lam, nsel = None, None
            
            if isinstance(delta, _ZeroDelta):
                lam, nsel = 0.0, 0
            elif isinstance(delta, _ScaledDelta):
                # FIX #4: Read alpha_ from _ScaledDelta
                lam = float(delta.alpha_) if getattr(delta, 'alpha_', None) is not None else None
                nsel = int((np.abs(delta.coef_) > 1e-8).sum())
            elif isinstance(delta, _TransferredDelta):
                # Transferred delta: no lambda (inherited via transfer)
                nsel = int((np.abs(delta.coef_) > 1e-8).sum())
            elif hasattr(delta, 'named_steps'):
                # Pipeline
                if 'lasso' in delta.named_steps:
                    lasso = delta.named_steps['lasso']
                    lam = float(lasso.alpha_)
                    nsel = int((np.abs(lasso.coef_) > 1e-8).sum())
                elif 'ridge' in delta.named_steps:
                    ridge = delta.named_steps['ridge']
                    lam = float(ridge.alpha_)
                    nsel = self.n_features_  # Ridge doesn't select
            
            if lam is not None:
                self.stage2_lambda_folds_.append(lam)
            if nsel is not None:
                self.stage2_n_selected_folds_.append(nsel)
    
    def _apply_transfer_operator(self, delta_0_fold):
        """
        Apply learned operator M to placebo correction.
        
        Mathematical operation:
            β₁ = M̂ @ β₀
        
        IMPORTANT: β₀ must be in the GLOBAL scaled coordinate system.
        The returned predictor also operates in that system.
        
        Returns a predictor with .predict(X) method.
        
        FIX: Prioritize global scaler (from Step B) over pipeline scaler.
        """
        if isinstance(delta_0_fold, _ZeroDelta):
            return _ZeroDelta(self.n_features_)
        
        if self.M_hat_ is None:
            # Fallback: if M not learned, return zero delta
            warnings.warn("Transfer operator M not available, returning zero delta")
            return _ZeroDelta(self.n_features_)
        
        # Extract β₀ coefficients (should already be in global scaled space)
        if hasattr(delta_0_fold, 'coef_'):
            beta_0 = delta_0_fold.coef_
        elif hasattr(delta_0_fold, 'named_steps') and 'lasso' in delta_0_fold.named_steps:
            beta_0 = delta_0_fold.named_steps['lasso'].coef_
        elif hasattr(delta_0_fold, 'named_steps') and 'ridge' in delta_0_fold.named_steps:
            beta_0 = delta_0_fold.named_steps['ridge'].coef_
        else:
            beta_0 = np.zeros(self.n_features_)
        
        # Apply operator: β₁ = M @ β₀
        beta_1 = self.M_hat_ @ beta_0
        
        # FIX: Prioritize global scaler (critical for Option B consistency)
        scaler = getattr(self, 'global_scaler_', None)
        
        # Only fall back to pipeline scaler if no global scaler
        if scaler is None and hasattr(delta_0_fold, 'named_steps'):
            scaler = delta_0_fold.named_steps.get('scaler')
        
        # FIX #5: Step B maps coefficients only; intercept is NOT justified under A6
        # Set intercept = 0 (absorbed by proxy model / residual centering)
        return _TransferredDelta(beta_1, scaler, intercept=0.0)
    
    def _fit_global_corrections(self, X_target, A_target, Y_target, flags=None):
        """
        Fit global corrections on full target data.
        
        These are NOT used in Stage 3 (leak-proof!), only for:
        - predict_anchored() convenience method
        - Diagnostics and sparsity reporting
        
        For Option B: Global corrections MUST use global scaler to match Step B
        coordinate system.
        
        Parameters
        ----------
        flags : dict, optional
            Variant flags. If None, computed from option.
        """
        if flags is None:
            flags = self._variant_flags()
        
        variant = self._get_effective_variant()
        
        # Handle variants that don't use corrections
        if variant in ['no_transfer', 'proxy_only']:
            self.delta_0_global_ = _ZeroDelta(self.n_features_)
            self.delta_1_global_ = _ZeroDelta(self.n_features_)
            return
        
        # ═══════════════════════════════════════════════════════════════════════
        # FIX #3: For proposed_B, fit delta_0_global_ in GLOBAL scaled space
        # ═══════════════════════════════════════════════════════════════════════
        
        mask_placebo = (A_target == 0)
        
        if variant == 'proposed_B':
            # Must fit in global scaled space for M compatibility
            if self.global_scaler_ is None:
                warnings.warn("proposed_B but global_scaler_ missing; falling back to local correction model")
                if np.sum(mask_placebo) >= 5:
                    X_p = X_target[mask_placebo]
                    Y_p = Y_target[mask_placebo]
                    mu0_p = self.proxy_models_[0].predict(X_p)
                    resid_p = Y_p - mu0_p
                    self.delta_0_global_ = clone(self.correction_model)
                    self.delta_0_global_.fit(X_p, resid_p)
                else:
                    self.delta_0_global_ = _ZeroDelta(self.n_features_)
            else:
                if np.sum(mask_placebo) >= 5:
                    X_p = X_target[mask_placebo]
                    Y_p = Y_target[mask_placebo]
                    mu0_p = self.proxy_models_[0].predict(X_p)
                    resid_p = Y_p - mu0_p
                    
                    # Fit in GLOBAL scaled space
                    X_p_scaled = self.global_scaler_.transform(X_p)
                    lasso = LassoCV(cv=5, fit_intercept=True,
                                   random_state=self.random_state, n_jobs=-1)
                    lasso.fit(X_p_scaled, resid_p)
                    
                    self.delta_0_global_ = _ScaledDelta(
                        coef=lasso.coef_,
                        scaler=self.global_scaler_,
                        intercept=lasso.intercept_,
                        alpha=getattr(lasso, 'alpha_', None)
                    )
                else:
                    self.delta_0_global_ = _ZeroDelta(self.n_features_)
            
            # Transfer via M (in consistent coordinate system)
            self.delta_1_global_ = self._apply_transfer_operator(self.delta_0_global_)
            
        else:
            # Other variants: use local pipeline scaler (anchor_only, anchor_only_A, proposed_A)
            if np.sum(mask_placebo) >= 5:
                X_p = X_target[mask_placebo]
                Y_p = Y_target[mask_placebo]
                mu0_p = self.proxy_models_[0].predict(X_p)
                resid_p = Y_p - mu0_p
                
                self.delta_0_global_ = clone(self.correction_model)
                self.delta_0_global_.fit(X_p, resid_p)
            else:
                self.delta_0_global_ = _ZeroDelta(self.n_features_)
            
            # Treated correction depends on variant
            if variant == 'anchor_only':
                # Anchor-only: no treated correction
                self.delta_1_global_ = _ZeroDelta(self.n_features_)
                
            elif variant in ['anchor_only_A', 'proposed_A']:
                # Both corrections from target
                mask_treated = (A_target == 1)
                if np.sum(mask_treated) >= 5:
                    X_t = X_target[mask_treated]
                    Y_t = Y_target[mask_treated]
                    mu1_t = self.proxy_models_[1].predict(X_t)
                    resid_t = Y_t - mu1_t
                    
                    self.delta_1_global_ = clone(self.correction_model)
                    self.delta_1_global_.fit(X_t, resid_t)
                else:
                    # Fall back to transfer if M available (for proposed_A only)
                    if variant == 'proposed_A' and self.M_hat_ is not None:
                        self.delta_1_global_ = self._apply_transfer_operator(self.delta_0_global_)
                    else:
                        self.delta_1_global_ = _ZeroDelta(self.n_features_)
        
        # Report sparsity
        if self.verbose:
            s0 = self._count_nonzero_coefs(self.delta_0_global_)
            s1 = self._count_nonzero_coefs(self.delta_1_global_)
            print(f"  Global corrections: δ₀ has {s0}/{self.n_features_} nonzero, δ₁ has {s1}/{self.n_features_} nonzero")
    
    def _count_nonzero_coefs(self, delta, threshold=1e-6):
        """Count nonzero coefficients in a correction model."""
        if isinstance(delta, _ZeroDelta):
            return 0
        elif hasattr(delta, 'coef_'):
            return int(np.sum(np.abs(delta.coef_) > threshold))
        elif hasattr(delta, 'named_steps'):
            for name in ['lasso', 'ridge']:
                if name in delta.named_steps:
                    return int(np.sum(np.abs(delta.named_steps[name].coef_) > threshold))
        return 0
    
    def predict(self, X):
        """Predict CATE using Stage 3 DR model (target-only training)."""
        check_is_fitted(self, 'cate_model_')
        X = check_array(X)
        return self.cate_model_.predict(X)
    
    def predict_anchored(self, X):
        """
        Predict CATE using Stage 2 anchored models (plug-in, no DR).
        Uses global corrections fitted on full target data.
        """
        check_is_fitted(self, 'delta_0_global_')
        X = check_array(X)
        
        mu0 = self.proxy_models_[0].predict(X) + self.delta_0_global_.predict(X)
        mu1 = self.proxy_models_[1].predict(X) + self.delta_1_global_.predict(X)
        
        return mu1 - mu0
    
    def get_diagnostics(self):
        """Return diagnostic information about the fit."""
        check_is_fitted(self, 'cate_model_')
        
        diagnostics = {
            'variant': getattr(self, '_effective_variant_', self._get_effective_variant()),
            'option': self.option,
            'n_folds': self.n_folds,
            'n_features': self.n_features_,
        }
        
        # Stage-2 diagnostics
        diagnostics['stage2_lambda'] = getattr(self, 'stage2_lambda_', None)
        diagnostics['stage2_n_selected'] = getattr(self, 'stage2_n_selected_', None)
        
        # Extract β₀ from global correction
        beta_0 = self._extract_coefs(self.delta_0_global_)
        beta_1 = self._extract_coefs(self.delta_1_global_)
        
        diagnostics['sparsity_0'] = int(np.sum(np.abs(beta_0) > 1e-6))
        diagnostics['sparsity_1'] = int(np.sum(np.abs(beta_1) > 1e-6))
        diagnostics['beta_0'] = beta_0
        diagnostics['beta_1'] = beta_1
        diagnostics['l2_norm_beta_0'] = float(np.linalg.norm(beta_0))
        diagnostics['l2_norm_beta_1'] = float(np.linalg.norm(beta_1))
        
        # Transfer diagnostics
        if hasattr(self, 'transfer_diagnostics_'):
            diagnostics['transfer'] = self.transfer_diagnostics_
        
        if hasattr(self, 'M_hat_') and self.M_hat_ is not None:
            diagnostics['M_fro_norm'] = float(np.linalg.norm(self.M_hat_, 'fro'))
            diagnostics['M_spectral_norm'] = float(np.linalg.norm(self.M_hat_, 2))
            svd_vals = np.linalg.svd(self.M_hat_, compute_uv=False)
            diagnostics['M_effective_rank'] = int(np.sum(svd_vals > 1e-6 * svd_vals[0]))
        
        return diagnostics
    
    def _extract_coefs(self, delta):
        """Extract coefficient array from a correction model."""
        if isinstance(delta, _ZeroDelta):
            return np.zeros(self.n_features_)
        elif hasattr(delta, 'coef_'):
            return np.asarray(delta.coef_)
        elif hasattr(delta, 'named_steps'):
            for name in ['lasso', 'ridge']:
                if name in delta.named_steps:
                    return np.asarray(delta.named_steps[name].coef_)
        return np.zeros(self.n_features_)
    
    # =========================================================================
    # Artifact Persistence
    # =========================================================================
    
    def get_artifacts(self):
        """
        Get structured artifact bundle for persistence.
        
        Returns
        -------
        artifacts : dict
            Dictionary containing all fitted components organized by stage
        """
        check_is_fitted(self, 'cate_model_')
        
        return {
            'meta': {
                'variant': getattr(self, '_effective_variant_', self._get_effective_variant()),
                'option': self.option,
                'n_features': self.n_features_,
                'n_folds': self.n_folds,
                'random_state': self.random_state,
                'stage2_mode': self.stage2_mode,
            },
            'stage1': {
                'proxy_models': self.proxy_models_,
            },
            'stepB': {
                'global_scaler': getattr(self, 'global_scaler_', None),
                'M_hat': getattr(self, 'M_hat_', None),
                'transfer_diagnostics': getattr(self, 'transfer_diagnostics_', None),
            },
            'stage2_global': {
                'delta_0_global': getattr(self, 'delta_0_global_', None),
                'delta_1_global': getattr(self, 'delta_1_global_', None),
            },
            'stage2_diagnostics': {
                'lambda': getattr(self, 'stage2_lambda_', None),
                'n_selected': getattr(self, 'stage2_n_selected_', None),
                'lambda_folds': getattr(self, 'stage2_lambda_folds_', None),
                'n_selected_folds': getattr(self, 'stage2_n_selected_folds_', None),
            },
            'stage3': {
                'cate_model': self.cate_model_,
            },
            # FIX #7: Persist fold splits for reproducibility
            'cv': {
                'folds': getattr(self, 'folds_', None),
            },
            'fold_nuisance': getattr(self, 'fold_corrections_', None),
        }
    
    def set_artifacts(self, artifacts):
        """
        Set artifacts from a loaded bundle.
        
        Parameters
        ----------
        artifacts : dict
            Artifact bundle from get_artifacts() or joblib.load()
            
        Returns
        -------
        self
        """
        # Meta
        meta = artifacts.get('meta', {})
        self._effective_variant_ = meta.get('variant')
        self.option = meta.get('option', self.option)
        self.n_features_ = meta.get('n_features')
        self.n_folds = meta.get('n_folds', self.n_folds)
        self.random_state = meta.get('random_state', self.random_state)
        self.stage2_mode = meta.get('stage2_mode', self.stage2_mode)
        
        # Stage 1
        stage1 = artifacts.get('stage1', {})
        self.proxy_models_ = stage1.get('proxy_models', {})
        
        # Step B
        stepB = artifacts.get('stepB', {})
        self.global_scaler_ = stepB.get('global_scaler')
        self.M_hat_ = stepB.get('M_hat')
        self.transfer_diagnostics_ = stepB.get('transfer_diagnostics')
        
        # Stage 2
        stage2 = artifacts.get('stage2_global', {})
        self.delta_0_global_ = stage2.get('delta_0_global')
        self.delta_1_global_ = stage2.get('delta_1_global')
        
        # Stage 2 diagnostics
        diag = artifacts.get('stage2_diagnostics', {})
        self.stage2_lambda_ = diag.get('lambda')
        self.stage2_n_selected_ = diag.get('n_selected')
        self.stage2_lambda_folds_ = diag.get('lambda_folds', [])
        self.stage2_n_selected_folds_ = diag.get('n_selected_folds', [])
        
        # Stage 3
        stage3 = artifacts.get('stage3', {})
        self.cate_model_ = stage3.get('cate_model')
        
        # FIX #7: Restore fold splits for reproducibility
        cv = artifacts.get('cv', {})
        self.folds_ = cv.get('folds')
        
        # Fold nuisance
        self.fold_corrections_ = artifacts.get('fold_nuisance')
        
        return self
    
    def save(self, path):
        """
        Save fitted estimator to disk via joblib.
        
        Parameters
        ----------
        path : str
            Path to save file (typically .joblib)
        """
        import joblib
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        joblib.dump(self.get_artifacts(), path)
        if self.verbose:
            print(f"Saved artifacts to {path}")
    
    @classmethod
    def load(cls, path):
        """
        Load fitted estimator from disk.
        
        Parameters
        ----------
        path : str
            Path to saved file
            
        Returns
        -------
        estimator : PlaceboAnchoredDRLearner
            Loaded and ready-to-use estimator
        """
        import joblib
        artifacts = joblib.load(path)
        
        # Create instance with meta params
        meta = artifacts.get('meta', {})
        obj = cls(
            option=meta.get('option', 'A'),
            variant=meta.get('variant'),
            stage2_mode=meta.get('stage2_mode', 'lasso'),
            n_folds=meta.get('n_folds', 5),
            random_state=meta.get('random_state', 42)
        )
        obj.set_artifacts(artifacts)
        return obj
    
    # =========================================================================
    # Shared Components for Efficient Ablation Runs
    # =========================================================================
    
    def fit_with_shared(self, shared_components,
                        X_target, A_target, Y_target, propensity_target=None):
        """
        Fit estimator using pre-computed shared components.
        
        This avoids refitting Stage 1 and Step B when running multiple ablations
        on the same data with the same seed.
        
        Parameters
        ----------
        shared_components : SharedComponents
            Pre-computed components from SharedComponents.fit()
        X_target, A_target, Y_target : arrays
            Target data
        propensity_target : array, optional
            Target propensities (default 0.5)
            
        Returns
        -------
        self
        """
        flags = self._variant_flags()
        self._effective_variant_ = self._get_effective_variant()
        
        # Validate inputs
        X_target = check_array(X_target)
        A_target = np.asarray(A_target).ravel()
        Y_target = np.asarray(Y_target).ravel()
        
        n_target = len(X_target)
        
        # ===================================================================
        # FIX #8: Validate shared component compatibility
        # ===================================================================
        
        # Dimensional compatibility
        if shared_components.n_features_ != X_target.shape[1]:
            raise ValueError(
                f"SharedComponents n_features ({shared_components.n_features_}) "
                f"mismatch with X_target ({X_target.shape[1]})"
            )
        
        # Variant-specific compatibility checks
        if flags['do_stage1'] and shared_components.proxy_models_ is None:
            raise ValueError(
                f"Variant '{self._effective_variant_}' requires proxy models but "
                "SharedComponents.proxy_models_ is None. Did you fit with fit_proxy=False?"
            )
        
        if flags['do_stepB']:
            if shared_components.M_hat_ is None:
                raise ValueError(
                    f"Variant '{self._effective_variant_}' requires Step B (M_hat_) but "
                    "SharedComponents.M_hat_ is None. Did you fit with fit_stepB=False?"
                )
            if shared_components.global_scaler_ is None:
                warnings.warn(
                    f"Variant '{self._effective_variant_}' uses Step B but "
                    "SharedComponents.global_scaler_ is None. Using identity scaling."
                )
        
        self.n_features_ = shared_components.n_features_
        
        # Default propensity for RCTs
        if propensity_target is None:
            propensity_target = np.full(n_target, 0.5)
        else:
            propensity_target = np.asarray(propensity_target).ravel()
        
        # Initialize models for Stage 3 (if not set)
        if self.cate_model is None:
            self.cate_model = RandomForestRegressor(
                n_estimators=100, max_depth=5, random_state=self.random_state, n_jobs=-1
            )
        if self.correction_model is None:
            if self.stage2_mode == 'ridge':
                self.correction_model = Pipeline([
                    ("scaler", StandardScaler()),
                    ("ridge", RidgeCV(cv=5, fit_intercept=True))
                ])
            else:
                self.correction_model = Pipeline([
                    ("scaler", StandardScaler()),
                    ("lasso", LassoCV(cv=5, fit_intercept=True, random_state=self.random_state, n_jobs=-1))
                ])
        
        # Initialize diagnostics tracking
        self.stage2_lambda_folds_ = []
        self.stage2_n_selected_folds_ = []
        
        # ===================================================================
        # INJECT SHARED COMPONENTS (instead of refitting)
        # ===================================================================
        
        if flags['do_stage1']:
            # Use shared proxy models
            self.proxy_models_ = shared_components.proxy_models_
        else:
            # no_transfer variant: use zero proxies
            self.proxy_models_ = {
                0: _ZeroProxy(self.n_features_),
                1: _ZeroProxy(self.n_features_)
            }
        
        if flags['do_stepB']:
            # Use shared transfer operator
            self.M_hat_ = shared_components.M_hat_
            self.global_scaler_ = shared_components.global_scaler_
            self.transfer_diagnostics_ = shared_components.transfer_diagnostics_
        else:
            self.M_hat_ = None
            self.global_scaler_ = None
            self.transfer_diagnostics_ = {'fallback': True, 'reason': 'stepB_disabled_by_variant'}
        
        # ===================================================================
        # STAGE 2-3: Target-only corrections + DR (this is variant-specific)
        # ===================================================================
        
        self._fit_target_dr(X_target, A_target, Y_target, propensity_target, flags)
        
        # Aggregate Stage-2 diagnostics
        self.stage2_lambda_ = float(np.nanmedian(self.stage2_lambda_folds_)) if self.stage2_lambda_folds_ else None
        self.stage2_n_selected_ = int(np.nanmedian(self.stage2_n_selected_folds_)) if self.stage2_n_selected_folds_ else None
        
        return self


# =============================================================================
# SharedComponents: Fit Once, Use Many Times
# =============================================================================

class SharedComponents:
    """
    Pre-computed shared components for efficient ablation runs.
    
    Fits expensive Stage 1 (proxy models) and Step B (transfer operator) once,
    then multiple ablation variants can reuse them without refitting.
    
    FIX #2: Only fit what is needed by the variants in the run.
    
    Example
    -------
    >>> # Fit shared components once
    >>> shared = SharedComponents(random_state=42)
    >>> shared.fit(X_source, A_source, Y_source, c_source, fit_stepB=True)
    
    >>> # Run all ablations efficiently
    >>> results = {}
    >>> for variant in ['proxy_only', 'anchor_only', 'proposed_B']:
    ...     est = PlaceboAnchoredDRLearner(variant=variant, random_state=42)
    ...     est.fit_with_shared(shared, X_target, A_target, Y_target)
    ...     results[variant] = est.predict(X_eval)
    """
    
    def __init__(self, proxy_model=None, random_state=42, verbose=False):
        """
        Parameters
        ----------
        proxy_model : sklearn estimator, optional
            Model for Stage 1 proxy fitting
        random_state : int
            Random seed
        verbose : bool
            Print progress
        """
        self.proxy_model = proxy_model
        self.random_state = random_state
        self.verbose = verbose
        
        # Will be set by fit()
        self.proxy_models_ = None
        self.M_hat_ = None
        self.global_scaler_ = None
        self.transfer_diagnostics_ = None
        self.n_features_ = None
    
    def fit(self, X_source, A_source, Y_source, c_source, 
            fit_proxy=True, fit_stepB=True):
        """
        Fit shared components on source data.
        
        FIX #2: Conditionally fit proxy models and/or Step B based on what
        variants actually need, avoiding unnecessary computation.
        
        Parameters
        ----------
        X_source, A_source, Y_source, c_source : arrays
            Source data
        fit_proxy : bool, default=True
            Whether to fit Stage 1 proxy models
        fit_stepB : bool, default=True
            Whether to fit Step B transfer operator (requires fit_proxy=True)
            
        Returns
        -------
        self
        """
        X_source = check_array(X_source)
        A_source = np.asarray(A_source).ravel()
        Y_source = np.asarray(Y_source).ravel()
        c_source = np.asarray(c_source).ravel()
        
        n_source, self.n_features_ = X_source.shape
        
        # Validate: Step B requires proxy models
        if fit_stepB and not fit_proxy:
            raise ValueError("fit_stepB=True requires fit_proxy=True (Step B residualizes on proxies)")
        
        # Initialize proxy model
        if self.proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=100, max_depth=8, random_state=self.random_state, n_jobs=-1
            )
        
        # ===================================================================
        # STAGE 1: Fit proxy models (if needed)
        # ===================================================================
        if fit_proxy:
            if self.verbose:
                print("SharedComponents: Fitting Stage 1 proxy models...")
            
            self.proxy_models_ = {}
            for a in [0, 1]:
                mask = (A_source == a)
                if np.sum(mask) == 0:
                    raise ValueError(f"No samples with A={a} in source data")
                
                model = clone(self.proxy_model)
                model.fit(X_source[mask], Y_source[mask])
                self.proxy_models_[a] = model
                
                if self.verbose:
                    print(f"  Proxy model for A={a}: {np.sum(mask)} samples")
        else:
            self.proxy_models_ = None
            if self.verbose:
                print("SharedComponents: SKIPPED Stage 1 (fit_proxy=False)")
        
        # ===================================================================
        # STEP B: Fit transfer operator M (if needed)
        # ===================================================================
        if fit_stepB:
            if self.verbose:
                print("SharedComponents: Fitting Step B transfer operator...")
            
            self._fit_transfer_operator(X_source, A_source, Y_source, c_source)
        else:
            self.M_hat_ = None
            self.global_scaler_ = None
            self.transfer_diagnostics_ = {'fallback': True, 'reason': 'fit_stepB=False'}
            if self.verbose:
                print("SharedComponents: SKIPPED Step B (fit_stepB=False)")
        
        if self.verbose:
            print("SharedComponents: Fit complete.")
        
        return self
    
    def _fit_transfer_operator(self, X_source, A_source, Y_source, c_source):
        """
        Step B: Learn cross-arm transfer operator M from sources.
        
        Copied from PlaceboAnchoredDRLearner to keep SharedComponents self-contained.
        """
        sites = np.unique(c_source)
        sites = sites[sites > 0]
        p = self.n_features_
        
        if len(sites) < 2:
            warnings.warn("Less than 2 source sites; using M=I fallback")
            self.M_hat_ = np.eye(p)
            self.global_scaler_ = None
            self.transfer_diagnostics_ = {'n_sites_used': 0, 'fallback': True}
            return
        
        # Fit GLOBAL scaler
        self.global_scaler_ = StandardScaler()
        self.global_scaler_.fit(X_source)
        X_source_scaled = self.global_scaler_.transform(X_source)
        
        # Build site-specific corrections
        beta_0_by_site = {}
        beta_1_by_site = {}
        min_samples_per_arm = 10
        
        for site in sites:
            mask_site = (c_source == site)
            X_c_scaled = X_source_scaled[mask_site]
            X_c_unscaled = X_source[mask_site]
            A_c = A_source[mask_site]
            Y_c = Y_source[mask_site]
            
            # Placebo correction
            mask_placebo = (A_c == 0)
            if np.sum(mask_placebo) >= min_samples_per_arm:
                X_p_scaled = X_c_scaled[mask_placebo]
                X_p_unscaled = X_c_unscaled[mask_placebo]
                Y_p = Y_c[mask_placebo]
                
                mu0_proxy = self.proxy_models_[0].predict(X_p_unscaled)
                resid_p = Y_p - mu0_proxy
                
                lasso_0 = LassoCV(cv=5, fit_intercept=True, 
                                  random_state=self.random_state, n_jobs=-1)
                lasso_0.fit(X_p_scaled, resid_p)
                beta_0_by_site[site] = lasso_0.coef_
            
            # Treated correction
            mask_treated = (A_c == 1)
            if np.sum(mask_treated) >= min_samples_per_arm:
                X_t_scaled = X_c_scaled[mask_treated]
                X_t_unscaled = X_c_unscaled[mask_treated]
                Y_t = Y_c[mask_treated]
                
                mu1_proxy = self.proxy_models_[1].predict(X_t_unscaled)
                resid_t = Y_t - mu1_proxy
                
                lasso_1 = LassoCV(cv=5, fit_intercept=True,
                                  random_state=self.random_state, n_jobs=-1)
                lasso_1.fit(X_t_scaled, resid_t)
                beta_1_by_site[site] = lasso_1.coef_
        
        # Intersection: only sites with BOTH arms
        common_sites = sorted(set(beta_0_by_site.keys()) & set(beta_1_by_site.keys()))
        
        if len(common_sites) < 2:
            warnings.warn(f"Only {len(common_sites)} sites with both arms; using M=I")
            self.M_hat_ = np.eye(p)
            self.transfer_diagnostics_ = {'n_sites_used': len(common_sites), 'fallback': True}
            return
        
        # Stack aligned matrices
        B_0 = np.column_stack([beta_0_by_site[c] for c in common_sites])
        B_1 = np.column_stack([beta_1_by_site[c] for c in common_sites])
        C = len(common_sites)
        
        # Matrix ridge regression with CV for lambda
        sigma_scale = np.linalg.norm(B_0, 'fro') / np.sqrt(C * p) + 1e-6
        lambda_candidates = sigma_scale * np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        
        best_lambda = lambda_candidates[2]
        best_error = np.inf
        
        if C >= 4:
            for lam in lambda_candidates:
                cv_error = 0.0
                for held_out_site in common_sites:
                    train_sites = [s for s in common_sites if s != held_out_site]
                    B0_train = np.column_stack([beta_0_by_site[s] for s in train_sites])
                    B1_train = np.column_stack([beta_1_by_site[s] for s in train_sites])
                    
                    G = B0_train @ B0_train.T
                    try:
                        M_cv = (B1_train @ B0_train.T) @ np.linalg.inv(G + lam * np.eye(p))
                    except np.linalg.LinAlgError:
                        continue
                    
                    beta0_test = beta_0_by_site[held_out_site]
                    beta1_test = beta_1_by_site[held_out_site]
                    beta1_pred = M_cv @ beta0_test
                    cv_error += np.sum((beta1_test - beta1_pred)**2)
                
                if cv_error < best_error:
                    best_error = cv_error
                    best_lambda = lam
        
        # Final fit
        G = B_0 @ B_0.T
        try:
            M_hat = (B_1 @ B_0.T) @ np.linalg.inv(G + best_lambda * np.eye(p))
        except np.linalg.LinAlgError:
            warnings.warn("Matrix inversion failed; using M=I")
            self.M_hat_ = np.eye(p)
            self.transfer_diagnostics_ = {'n_sites_used': C, 'fallback': True}
            return
        
        self.M_hat_ = M_hat
        
        # Diagnostics
        svd_vals = np.linalg.svd(M_hat, compute_uv=False)
        self.transfer_diagnostics_ = {
            'n_sites_used': C,
            'sites_used': common_sites,
            'lambda_selected': best_lambda,
            'M_fro_norm': np.linalg.norm(M_hat, 'fro'),
            'M_spectral_norm': np.linalg.norm(M_hat, 2),
            'M_effective_rank': np.sum(svd_vals > 1e-6 * svd_vals[0]),
            'M_condition_number': svd_vals[0] / (svd_vals[-1] + 1e-10),
            'fallback': False
        }
        
        if self.verbose:
            print(f"  Step B: {C} sites, λ={best_lambda:.4f}, ||M||_F={self.transfer_diagnostics_['M_fro_norm']:.3f}")


# =============================================================================
# Ablation Runner: Efficient Multi-Variant Evaluation
# =============================================================================

def run_ablations(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    X_eval=None,
    propensity_target=None,
    variants=None,
    random_state=42,
    verbose=False
):
    """
    Run multiple ablation variants efficiently with shared components.
    
    Fits Stage 1 and Step B once, then runs each variant's Stage 2-3.
    
    Parameters
    ----------
    X_source, A_source, Y_source, c_source : arrays
        Source data
    X_target, A_target, Y_target : arrays
        Target data for estimation
    X_eval : array, optional
        Evaluation covariates (default: X_target)
    propensity_target : array, optional
        Target propensities (default: 0.5)
    variants : list of str, optional
        Variants to run. Default: all VALID_VARIANTS
    random_state : int
        Random seed
    verbose : bool
        Print progress
        
    Returns
    -------
    results : dict
        variant -> {
            'estimator': fitted PlaceboAnchoredDRLearner,
            'tau_pred': predictions on X_eval,
            'diagnostics': dict
        }
    shared : SharedComponents
        The fitted shared components (for inspection)
    """
    if variants is None:
        variants = VALID_VARIANTS
    
    if X_eval is None:
        X_eval = X_target
    
    # Step 1: Fit shared components ONCE
    if verbose:
        print("=" * 60)
        print("Fitting shared components (Stage 1 + Step B)...")
        print("=" * 60)
    
    shared = SharedComponents(random_state=random_state, verbose=verbose)
    shared.fit(X_source, A_source, Y_source, c_source)
    
    # Step 2: Run each variant using shared components
    results = {}
    
    for variant in variants:
        if verbose:
            print(f"\n--- Running variant: {variant} ---")
        
        est = PlaceboAnchoredDRLearner(
            variant=variant,
            random_state=random_state,
            verbose=verbose
        )
        
        # Use shared components (no refitting!)
        est.fit_with_shared(
            shared,
            X_target, A_target, Y_target,
            propensity_target
        )
        
        tau_pred = est.predict(X_eval)
        
        results[variant] = {
            'estimator': est,
            'tau_pred': tau_pred,
            'diagnostics': est.get_diagnostics()
        }
    
    if verbose:
        print("\n" + "=" * 60)
        print("Ablation run complete!")
        print("=" * 60)
    
    return results, shared
