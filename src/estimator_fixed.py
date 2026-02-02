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
"""

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV, RidgeCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted, check_array
import warnings


class _ZeroDelta:
    """Fallback predictor for folds with no samples."""
    def __init__(self, n_features):
        self.coef_ = np.zeros(n_features)
        self.intercept_ = 0.0
        self.n_features = n_features
    
    def predict(self, X):
        return np.zeros(len(X))


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
    n_folds : int, default=5
        Number of folds for cross-fitting in Stage 3
    random_state : int, default=42
    verbose : bool, default=False
    """
    
    def __init__(self, proxy_model=None, correction_model=None, cate_model=None,
                 option='A', n_folds=5, random_state=42, verbose=False):
        self.proxy_model = proxy_model
        self.correction_model = correction_model
        self.cate_model = cate_model
        self.option = option
        self.n_folds = n_folds
        self.random_state = random_state
        self.verbose = verbose
        
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
            # FIXED: Pipeline with StandardScaler + LassoCV
            self.correction_model = Pipeline([
                ("scaler", StandardScaler()),
                ("lasso", LassoCV(cv=5, fit_intercept=True, random_state=self.random_state, n_jobs=-1))
            ])
        if self.cate_model is None:
            self.cate_model = RandomForestRegressor(
                n_estimators=100, max_depth=5, random_state=self.random_state, n_jobs=-1
            )
        
        # ===================================================================
        # STAGE 1: Fit proxy models on source data
        # ===================================================================
        if self.verbose:
            print("Stage 1: Fitting proxy models on source data...")
        
        self._fit_proxy_models(X_source, A_source, Y_source)
        
        # ===================================================================
        # STAGE 2: Option B operator (if needed)
        # ===================================================================
        if self.option == 'B':
            if self.verbose:
                print("Stage 2: Learning cross-arm transfer operator M from sources...")
            self._fit_transfer_operator(X_source, A_source, Y_source, c_source)
        else:
            self.M_hat_ = None
        
        # ===================================================================
        # STAGE 2-3: Target-only corrections + DR with cross-fitting
        # ===================================================================
        if self.verbose:
            print(f"Stage 2-3: Target correction + DR with {self.n_folds}-fold cross-fitting (Option {self.option})...")
        
        self._fit_target_dr(X_target, A_target, Y_target, propensity_target)
        
        if self.verbose:
            print("Fitting complete.")
        
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
    
    def _fit_target_dr(self, X_target, A_target, Y_target, propensity_target):
        """
        Stage 2-3: Target corrections + DR with leak-proof cross-fitting.
        
        Key: Every nuisance estimate used for observation i is trained WITHOUT i.
        
        For Option B: Target corrections MUST use the same global scaler as Step B
        to ensure coefficients are in the same coordinate system.
        """
        n_target = len(X_target)
        
        # FIXED: StratifiedKFold to ensure both arms in each fold
        skf = StratifiedKFold(
            n_splits=self.n_folds, 
            shuffle=True, 
            random_state=self.random_state
        )
        
        pseudo_outcomes = np.zeros(n_target)
        self.fold_corrections_ = []  # For diagnostics
        
        # For Option B, check if we have the global scaler from Step B
        use_global_scaler = (self.option == 'B' and 
                            hasattr(self, 'global_scaler_') and 
                            self.global_scaler_ is not None)
        
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_target, A_target)):
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
            # Stage 2: Fit corrections on TRAINING fold only
            # -----------------------------------------------------------------
            
            # Placebo correction
            mask_placebo = (A_train == 0)
            n_placebo = np.sum(mask_placebo)
            
            if n_placebo >= 5:  # Minimum for stable LASSO
                X_p = X_train[mask_placebo]
                Y_p = Y_train[mask_placebo]
                mu0_p = self.proxy_models_[0].predict(X_p)
                resid_p = Y_p - mu0_p
                
                if use_global_scaler:
                    # OPTION B: Fit in global scaled space for M compatibility
                    X_p_scaled = self.global_scaler_.transform(X_p)
                    lasso = LassoCV(cv=5, fit_intercept=True,
                                   random_state=self.random_state, n_jobs=-1)
                    lasso.fit(X_p_scaled, resid_p)
                    
                    # Wrap in predictor that uses global scaler
                    class _ScaledDelta:
                        def __init__(self, coef, scaler):
                            self.coef_ = coef
                            self.scaler = scaler
                            self.intercept_ = 0.0
                        def predict(self, X):
                            return self.scaler.transform(X) @ self.coef_
                    
                    delta_0_fold = _ScaledDelta(lasso.coef_, self.global_scaler_)
                else:
                    # OPTION A: Use pipeline with local scaler
                    delta_0_fold = clone(self.correction_model)
                    delta_0_fold.fit(X_p, resid_p)
            else:
                # FIXED: Zero fallback (no leakage!)
                delta_0_fold = _ZeroDelta(self.n_features_)
                if self.verbose:
                    print(f"  Fold {fold_idx}: Only {n_placebo} placebo, using zero correction")
            
            # Treated correction
            if self.option == 'A':
                # Option A: Estimate from target treated data
                mask_treated = (A_train == 1)
                n_treated = np.sum(mask_treated)
                
                if n_treated >= 5:
                    X_t = X_train[mask_treated]
                    Y_t = Y_train[mask_treated]
                    mu1_t = self.proxy_models_[1].predict(X_t)
                    resid_t = Y_t - mu1_t
                    
                    delta_1_fold = clone(self.correction_model)
                    delta_1_fold.fit(X_t, resid_t)
                else:
                    # FIXED: If insufficient treated, use Option B transfer
                    if self.M_hat_ is not None:
                        delta_1_fold = self._apply_transfer_operator(delta_0_fold)
                    else:
                        delta_1_fold = _ZeroDelta(self.n_features_)
                    
                    if self.verbose:
                        print(f"  Fold {fold_idx}: Only {n_treated} treated, using operator transfer")
            
            elif self.option == 'B':
                # Option B: Apply learned transfer operator
                delta_1_fold = self._apply_transfer_operator(delta_0_fold)
            
            else:
                raise ValueError(f"Invalid option: {self.option}")
            
            # Store fold corrections for diagnostics
            self.fold_corrections_.append({
                'delta_0': delta_0_fold,
                'delta_1': delta_1_fold
            })
            
            # -----------------------------------------------------------------
            # Stage 3: Compute DR pseudo-outcomes on validation fold
            # -----------------------------------------------------------------
            
            # Anchored predictions
            mu0_val = self.proxy_models_[0].predict(X_val) + delta_0_fold.predict(X_val)
            mu1_val = self.proxy_models_[1].predict(X_val) + delta_1_fold.predict(X_val)
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
        self._fit_global_corrections(X_target, A_target, Y_target)
        
        return self
    
    def _apply_transfer_operator(self, delta_0_fold):
        """
        Apply learned operator M to placebo correction.
        
        Mathematical operation:
            β₁ = M̂ @ β₀
        
        IMPORTANT: β₀ must be in the GLOBAL scaled coordinate system.
        The returned predictor also operates in that system.
        
        Returns a predictor with .predict(X) method.
        """
        if isinstance(delta_0_fold, _ZeroDelta):
            return _ZeroDelta(self.n_features_)
        
        # Extract β₀ coefficients (should already be in global scaled space)
        if hasattr(delta_0_fold, 'coef_'):
            beta_0 = delta_0_fold.coef_
        else:
            beta_0 = np.zeros(self.n_features_)
        
        # Apply operator: β₁ = M @ β₀
        beta_1 = self.M_hat_ @ beta_0
        
        # Get the scaler used during Step B (or during target correction fitting)
        scaler = getattr(self, 'global_scaler_', None)
        
        # Create predictor that uses the same scaler
        class _TransferredDelta:
            def __init__(self, beta, scaler=None):
                self.coef_ = beta
                self.intercept_ = 0.0
                self.scaler = scaler
            
            def predict(self, X):
                if self.scaler is not None:
                    X_scaled = self.scaler.transform(X)
                    return X_scaled @ self.coef_
                return X @ self.coef_
        
        # Get scaler from delta_0_fold if it's a pipeline
        scaler = None
        if hasattr(delta_0_fold, 'named_steps'):
            scaler = delta_0_fold.named_steps['scaler']
        
        return _TransferredDelta(beta_1, scaler)
    
    def _fit_global_corrections(self, X_target, A_target, Y_target):
        """
        Fit global corrections on full target data.
        
        These are NOT used in Stage 3 (leak-proof!), only for:
        - predict_anchored() convenience method
        - Diagnostics and sparsity reporting
        """
        # Placebo
        mask_placebo = (A_target == 0)
        if np.sum(mask_placebo) >= 5:
            X_p = X_target[mask_placebo]
            Y_p = Y_target[mask_placebo]
            mu0_p = self.proxy_models_[0].predict(X_p)
            resid_p = Y_p - mu0_p
            
            self.delta_0_global_ = clone(self.correction_model)
            self.delta_0_global_.fit(X_p, resid_p)
        else:
            self.delta_0_global_ = _ZeroDelta(self.n_features_)
        
        # Treated
        if self.option == 'A':
            mask_treated = (A_target == 1)
            if np.sum(mask_treated) >= 5:
                X_t = X_target[mask_treated]
                Y_t = Y_target[mask_treated]
                mu1_t = self.proxy_models_[1].predict(X_t)
                resid_t = Y_t - mu1_t
                
                self.delta_1_global_ = clone(self.correction_model)
                self.delta_1_global_.fit(X_t, resid_t)
            else:
                if self.M_hat_ is not None:
                    self.delta_1_global_ = self._apply_transfer_operator(self.delta_0_global_)
                else:
                    self.delta_1_global_ = _ZeroDelta(self.n_features_)
        else:  # Option B
            self.delta_1_global_ = self._apply_transfer_operator(self.delta_0_global_)
        
        # Report sparsity
        if self.verbose:
            if hasattr(self.delta_0_global_, 'coef_'):
                s0 = np.sum(np.abs(self.delta_0_global_.coef_) > 1e-6)
            elif hasattr(self.delta_0_global_, 'named_steps'):
                s0 = np.sum(np.abs(self.delta_0_global_.named_steps['lasso'].coef_) > 1e-6)
            else:
                s0 = 0
            
            if hasattr(self.delta_1_global_, 'coef_'):
                s1 = np.sum(np.abs(self.delta_1_global_.coef_) > 1e-6)
            elif hasattr(self.delta_1_global_, 'named_steps'):
                s1 = np.sum(np.abs(self.delta_1_global_.named_steps['lasso'].coef_) > 1e-6)
            else:
                s1 = 0
            
            print(f"  Global corrections: δ₀ has {s0}/{self.n_features_} nonzero, δ₁ has {s1}/{self.n_features_} nonzero")
    
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
            'n_folds': self.n_folds,
            'option': self.option,
        }
        
        # Extract β₀ from global correction
        if hasattr(self.delta_0_global_, 'named_steps'):
            beta_0 = self.delta_0_global_.named_steps['lasso'].coef_
        elif hasattr(self.delta_0_global_, 'coef_'):
            beta_0 = self.delta_0_global_.coef_
        else:
            beta_0 = np.zeros(self.n_features_)
        
        # Extract β₁ from global correction (handle _TransferredDelta)
        if hasattr(self.delta_1_global_, 'named_steps'):
            beta_1 = self.delta_1_global_.named_steps['lasso'].coef_
        elif hasattr(self.delta_1_global_, 'coef_'):
            beta_1 = self.delta_1_global_.coef_
        else:
            beta_1 = np.zeros(self.n_features_)
        
        diagnostics['sparsity_0'] = int(np.sum(np.abs(beta_0) > 1e-6))
        diagnostics['sparsity_1'] = int(np.sum(np.abs(beta_1) > 1e-6))
        diagnostics['beta_0'] = beta_0
        diagnostics['beta_1'] = beta_1
        
        if hasattr(self, 'M_hat_') and self.M_hat_ is not None:
            diagnostics['M_norm'] = float(np.linalg.norm(self.M_hat_, 'fro'))
        
        return diagnostics
