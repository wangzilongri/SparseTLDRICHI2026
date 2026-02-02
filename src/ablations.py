"""
Ablation baselines for the placebo-anchored DR estimator.

Based on Table in paper:
- No-Transfer: Only target placebo, cannot extrapolate treated
- Proxy-Only: Source trials without anchoring
- Anchor-Only: Placebo anchoring without DR correction
- Proposed: Full method (implemented in estimator.py)
"""

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.utils.validation import check_is_fitted, check_array


class NoTransferBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Only use target placebo data.
    Cannot extrapolate to treated outcomes.
    Returns constant CATE = 0 (no heterogeneity).
    
    Source of benefit tested: Proxy information from source trials
    """
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target, Y_target, propensity_target=None):
        """Fit using only target placebo data."""
        X_target = check_array(X_target)
        A_target = np.asarray(A_target).ravel()
        Y_target = np.asarray(Y_target).ravel()
        
        # Only use target placebo
        mask_placebo = (A_target == 0)
        if np.sum(mask_placebo) == 0:
            raise ValueError("No placebo samples in target")
        
        # Constant CATE prediction
        self.constant_cate_ = 0.0
        
        return self
    
    def predict(self, X):
        """Return constant CATE = 0."""
        check_is_fitted(self, 'constant_cate_')
        X = check_array(X)
        return np.full(len(X), self.constant_cate_)


class ProxyOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Use pooled source trials without target anchoring.
    
    Source of benefit tested: Placebo anchoring
    """
    
    def __init__(self, proxy_model=None, random_state=42):
        self.proxy_model = proxy_model
        self.random_state = random_state
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target, Y_target, propensity_target=None):
        """Fit proxy models on source data only."""
        X_source = check_array(X_source)
        A_source = np.asarray(A_source).ravel()
        Y_source = np.asarray(Y_source).ravel()
        
        # Initialize model
        if self.proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=100, max_depth=8, random_state=self.random_state
            )
        
        # Fit separate models for each arm on source data
        self.proxy_models_ = {}
        for a in [0, 1]:
            mask = (A_source == a)
            if np.sum(mask) == 0:
                raise ValueError(f"No samples with A={a} in source")
            
            from sklearn.base import clone
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.proxy_models_[a] = model
        
        return self
    
    def predict(self, X):
        """Predict CATE as difference of proxy models."""
        check_is_fitted(self, 'proxy_models_')
        X = check_array(X)
        
        mu0 = self.proxy_models_[0].predict(X)
        mu1 = self.proxy_models_[1].predict(X)
        
        return mu1 - mu0


class AnchorOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Proxy + placebo anchoring, but no DR correction (no Stage 3).
    
    Source of benefit tested: Doubly robust orthogonalization
    """
    
    def __init__(self, proxy_model=None, correction_model=None, 
                 option='A', random_state=42, verbose=False):
        self.proxy_model = proxy_model
        self.correction_model = correction_model
        self.option = option
        self.random_state = random_state
        self.verbose = verbose
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target, Y_target, propensity_target=None):
        """Fit proxy models + corrections, skip Stage 3."""
        # Validate
        X_source = check_array(X_source)
        X_target = check_array(X_target)
        A_source = np.asarray(A_source).ravel()
        A_target = np.asarray(A_target).ravel()
        Y_source = np.asarray(Y_source).ravel()
        Y_target = np.asarray(Y_target).ravel()
        
        self.n_features_ = X_source.shape[1]
        
        # Initialize models
        if self.proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=100, max_depth=8, random_state=self.random_state
            )
        if self.correction_model is None:
            self.correction_model = LassoCV(cv=5, max_iter=10000, tol=1e-3, random_state=self.random_state)
        
        # Stage 1: Proxy models
        if self.verbose:
            print("Stage 1: Fitting proxy models...")
        
        self.proxy_models_ = {}
        for a in [0, 1]:
            mask = (A_source == a)
            from sklearn.base import clone
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.proxy_models_[a] = model
        
        # Stage 2: Corrections
        if self.verbose:
            print(f"Stage 2: Gold correction (Option {self.option})...")
        
        # Placebo correction
        mask_placebo = (A_target == 0)
        if np.sum(mask_placebo) == 0:
            raise ValueError("No placebo samples in target")
        
        X_gold_0 = X_target[mask_placebo]
        Y_gold_0 = Y_target[mask_placebo]
        mu0_proxy = self.proxy_models_[0].predict(X_gold_0)
        residuals_0 = Y_gold_0 - mu0_proxy
        
        from sklearn.base import clone
        self.delta_0_ = clone(self.correction_model)
        self.delta_0_.fit(X_gold_0, residuals_0)
        
        # Treated correction
        if self.option == 'A':
            mask_treated = (A_target == 1)
            if np.sum(mask_treated) >= 10:
                X_gold_1 = X_target[mask_treated]
                Y_gold_1 = Y_target[mask_treated]
                mu1_proxy = self.proxy_models_[1].predict(X_gold_1)
                residuals_1 = Y_gold_1 - mu1_proxy
                
                self.delta_1_ = clone(self.correction_model)
                self.delta_1_.fit(X_gold_1, residuals_1)
            else:
                self.delta_1_ = self.delta_0_
        else:  # Option B
            self.delta_1_ = self.delta_0_
        
        # No Stage 3 (this is the ablation!)
        if self.verbose:
            print("Stage 3: Skipped (Anchor-Only baseline)")
        
        return self
    
    def predict(self, X):
        """Predict CATE using anchored models (plug-in, no DR)."""
        check_is_fitted(self, 'delta_0_')
        X = check_array(X)
        
        mu0 = self.proxy_models_[0].predict(X) + self.delta_0_.predict(X)
        mu1 = self.proxy_models_[1].predict(X) + self.delta_1_.predict(X)
        
        return mu1 - mu0
