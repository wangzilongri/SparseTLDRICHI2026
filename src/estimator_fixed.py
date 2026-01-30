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
        
        For each source site c:
        1. Fit corrections β₀,c and β₁,c
        2. Stack into matrices B₀ = [β₀,₁ ... β₀,C], B₁ = [β₁,₁ ... β₁,C]
        3. Learn M via ridge regression: β₁,c ≈ M·β₀,c
        """
        sites = np.unique(c_source)
        sites = sites[sites > 0]  # Exclude target (c=0)
        
        if len(sites) < 2:
            warnings.warn("Less than 2 source sites; using M=I fallback")
            self.M_hat_ = np.eye(self.n_features_)
            return
        
        beta_0_list = []
        beta_1_list = []
        
        for c in sites:
            mask_site = (c_source == c)
            X_c = X_source[mask_site]
            A_c = A_source[mask_site]
            Y_c = Y_source[mask_site]
            
            # Fit corrections for this site
            for a, beta_list in [(0, beta_0_list), (1, beta_1_list)]:
                mask_arm = (A_c == a)
                if np.sum(mask_arm) < 10:
                    continue
                
                X_a = X_c[mask_arm]
                Y_a = Y_c[mask_arm]
                
                # Residualize against proxy
                mu_proxy = self.proxy_models_[a].predict(X_a)
                resid = Y_a - mu_proxy
                
                # Fit correction
                correction = clone(self.correction_model)
                correction.fit(X_a, resid)
                
                # Extract coefficients (handle pipeline)
                if hasattr(correction, 'named_steps'):
                    beta = correction.named_steps['lasso'].coef_
                else:
                    beta = correction.coef_
                
                beta_list.append(beta)
        
        if len(beta_0_list) < 2 or len(beta_1_list) < 2:
            warnings.warn("Insufficient sites for M estimation; using M=I")
            self.M_hat_ = np.eye(self.n_features_)
            return
        
        # Stack into matrices
        B_0 = np.column_stack(beta_0_list)  # p × C
        B_1 = np.column_stack(beta_1_list)  # p × C
        
        # Learn M via ridge regression in coefficient space
        # For each feature dimension, regress β₁[j,:] on β₀[j,:]
        M_hat = np.zeros((self.n_features_, self.n_features_))
        
        for j in range(self.n_features_):
            # Ridge regression for jth row of M
            ridge = RidgeCV(alphas=np.logspace(-3, 3, 20))
            ridge.fit(B_0.T, B_1[j, :])  # Fit: β₁[j,:] ~ M[j,:]·B₀
            M_hat[j, :] = ridge.coef_
        
        self.M_hat_ = M_hat
        
        if self.verbose:
            print(f"  Learned M from {len(sites)} source sites")
            print(f"  ||M||_F = {np.linalg.norm(M_hat, 'fro'):.3f}")
    
    def _fit_target_dr(self, X_target, A_target, Y_target, propensity_target):
        """
        Stage 2-3: Target corrections + DR with leak-proof cross-fitting.
        
        Key: Every nuisance estimate used for observation i is trained WITHOUT i.
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
        
        Returns a predictor with .predict(X) method.
        """
        if isinstance(delta_0_fold, _ZeroDelta):
            return _ZeroDelta(self.n_features_)
        
        # Extract β₀ coefficients
        if hasattr(delta_0_fold, 'named_steps'):
            beta_0 = delta_0_fold.named_steps['lasso'].coef_
        else:
            beta_0 = delta_0_fold.coef_
        
        # Apply operator: β₁ = M·β₀
        beta_1 = self.M_hat_ @ beta_0
        
        # Create predictor
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
