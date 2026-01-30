"""
Baseline Methods for Comparison

Implements:
1. No-Transfer: Target placebo only
2. Proxy-Only: Pooled sources without anchoring
3. Anchor-Only: Anchoring without DR correction
"""

import numpy as np
from sklearn.base import clone, BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor


class NoTransferBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Use only target placebo data, cannot extrapolate to treated.
    Returns constant CATE (cannot predict heterogeneity).
    """
    
    def __init__(self):
        self.mu0_mean_ = None
    
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        # Only use target placebo
        mask_placebo = (A_target == 0)
        if np.sum(mask_placebo) > 0:
            self.mu0_mean_ = np.mean(Y_target[mask_placebo])
        else:
            self.mu0_mean_ = 0.0
        return self
    
    def predict(self, X):
        # Cannot predict heterogeneity, return zeros
        return np.zeros(len(X))
    
    def predict_counterfactuals(self, X):
        mu_0 = np.full(len(X), self.mu0_mean_)
        mu_1 = np.full(len(X), self.mu0_mean_)  # Unknown, assume same
        return mu_0, mu_1


class ProxyOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Use pooled source data without anchoring to target.
    This is the Stage 1 model without Stage 2 correction.
    """
    
    def __init__(self, proxy_model=None):
        if proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=20,
                random_state=42, n_jobs=-1
            )
        else:
            self.proxy_model = proxy_model
        self.models_ = None
    
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        # Fit separate models for each arm on source data only
        self.models_ = {}
        
        for arm in [0, 1]:
            mask = (A_source == arm)
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.models_[arm] = model
        
        return self
    
    def predict(self, X):
        mu_0 = self.models_[0].predict(X)
        mu_1 = self.models_[1].predict(X)
        return mu_1 - mu_0
    
    def predict_counterfactuals(self, X):
        mu_0 = self.models_[0].predict(X)
        mu_1 = self.models_[1].predict(X)
        return mu_0, mu_1


class AnchorOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Anchoring (Stage 1 + Stage 2) but no DR correction (no Stage 3).
    Returns anchored CATE directly without orthogonalization.
    """
    
    def __init__(self, proxy_model=None):
        from sklearn.linear_model import LassoCV
        
        if proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=20,
                random_state=42, n_jobs=-1
            )
        else:
            self.proxy_model = proxy_model
        self.models_ = None
        self.delta_0_ = None
        self.delta_1_ = None
        self.intercept_0_ = 0.0
        self.intercept_1_ = 0.0
    
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        from sklearn.linear_model import LassoCV
        
        # Stage 1: Proxy models
        self.models_ = {}
        for arm in [0, 1]:
            mask = (A_source == arm)
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.models_[arm] = model
        
        # Stage 2: Placebo correction
        mask_placebo = (A_target == 0)
        if np.sum(mask_placebo) >= 10:
            X_gold_0 = X_target[mask_placebo]
            Y_gold_0 = Y_target[mask_placebo]
            Y_resid = Y_gold_0 - self.models_[0].predict(X_gold_0)
            
            lasso = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=42)
            lasso.fit(X_gold_0, Y_resid)
            self.delta_0_ = lasso.coef_
            self.intercept_0_ = lasso.intercept_
        else:
            self.delta_0_ = np.zeros(X_target.shape[1])
        
        # Try to estimate delta_1 if treated data available (Option A)
        mask_treated = (A_target == 1)
        if np.sum(mask_treated) >= 10:
            # Option A: Estimate delta_1 separately from treated data
            X_gold_1 = X_target[mask_treated]
            Y_gold_1 = Y_target[mask_treated]
            Y_resid_1 = Y_gold_1 - self.models_[1].predict(X_gold_1)
            
            lasso_1 = LassoCV(cv=5, fit_intercept=True, max_iter=5000, random_state=42)
            lasso_1.fit(X_gold_1, Y_resid_1)
            self.delta_1_ = lasso_1.coef_
            self.intercept_1_ = lasso_1.intercept_
        else:
            # Option B: shared bias assumption
            self.delta_1_ = self.delta_0_
            self.intercept_1_ = self.intercept_0_
        
        return self
    
    def predict(self, X):
        # Direct anchored CATE (no DR)
        mu_0 = self.models_[0].predict(X) + X @ self.delta_0_ + self.intercept_0_
        mu_1 = self.models_[1].predict(X) + X @ self.delta_1_ + self.intercept_1_
        return mu_1 - mu_0
    
    def predict_counterfactuals(self, X):
        mu_0 = self.models_[0].predict(X) + X @ self.delta_0_ + self.intercept_0_
        mu_1 = self.models_[1].predict(X) + X @ self.delta_1_ + self.intercept_1_
        return mu_0, mu_1
