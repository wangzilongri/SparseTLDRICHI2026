"""
Improved Baseline Estimators with Linear Models

All baselines updated to use linear regression for consistency with improved estimator.

Author: Updated January 29, 2026
"""

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge, RidgeCV, ElasticNetCV, LassoCV
from sklearn.utils.validation import check_is_fitted, check_array


class ImprovedProxyOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Proxy-Only baseline with linear regression (Stage 1 only).
    
    Trains Ridge regression models on source data, predicts directly on target.
    No transport bias correction.
    
    Parameters:
    -----------
    alpha : float or 'cv', default='cv'
        Ridge regularization parameter. If 'cv', uses RidgeCV
    alphas : array-like, default=None
        Alpha grid for RidgeCV
    """
    
    def __init__(self, alpha='cv', alphas=None):
        self.alpha = alpha
        self.alphas = alphas
        self.models_ = {}
    
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target):
        """Fit proxy models on source data"""
        
        if self.alphas is None:
            alphas = np.logspace(-2, 2, 20)
        else:
            alphas = self.alphas
        
        # Fit separate models per arm
        for arm in [0, 1]:
            mask = (A_source == arm)
            X_arm = X_source[mask]
            Y_arm = Y_source[mask]
            
            if self.alpha == 'cv':
                model = RidgeCV(alphas=alphas, cv=5, scoring='neg_mean_squared_error')
            else:
                model = Ridge(alpha=self.alpha)
            
            model.fit(X_arm, Y_arm)
            self.models_[arm] = model
        
        return self
    
    def predict(self, X):
        """Predict CATE: τ(x) = μ₁(x) - μ₀(x)"""
        check_is_fitted(self, 'models_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        mu0 = self.models_[0].predict(X)
        mu1 = self.models_[1].predict(X)
        return mu1 - mu0
    
    def predict_counterfactuals(self, X):
        """Predict μ₀(x) and μ₁(x)"""
        check_is_fitted(self, 'models_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        mu0 = self.models_[0].predict(X)
        mu1 = self.models_[1].predict(X)
        return mu0, mu1


class ImprovedAnchorOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Anchor-Only baseline with linear models (Stages 1+2, no DR).
    
    Stage 1: Ridge regression on source data
    Stage 2: Elastic Net sparse corrections on target data
    
    Parameters:
    -----------
    stage1_alpha : float or 'cv', default='cv'
        Ridge parameter for Stage 1
    stage1_alphas : array-like, default=None
        Alpha grid for RidgeCV
    stage2_model : {'elasticnet', 'lasso'}, default='elasticnet'
        Correction model type
    stage2_l1_ratios : array-like, default=None
        L1 ratios for ElasticNetCV
    stage2_cv_folds : int, default=5
        CV folds for Stage 2
    """
    
    def __init__(self,
                 stage1_alpha='cv',
                 stage1_alphas=None,
                 stage2_model='elasticnet',
                 stage2_l1_ratios=None,
                 stage2_cv_folds=5):
        
        self.stage1_alpha = stage1_alpha
        self.stage1_alphas = stage1_alphas
        self.stage2_model = stage2_model
        self.stage2_l1_ratios = stage2_l1_ratios
        self.stage2_cv_folds = stage2_cv_folds
        
        self.models_ = {}
        self.delta_0_ = None
        self.delta_1_ = None
        self.intercept_0_ = None
        self.intercept_1_ = None
    
    def fit(self, X_source, A_source, Y_source, 
            X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        """Fit proxy models + sparse corrections"""
        
        if self.stage1_alphas is None:
            alphas = np.logspace(-2, 2, 20)
        else:
            alphas = self.stage1_alphas
        
        # Stage 1: Fit proxy models
        for arm in [0, 1]:
            mask = (A_source == arm)
            X_arm = X_source[mask]
            Y_arm = Y_source[mask]
            
            if self.stage1_alpha == 'cv':
                model = RidgeCV(alphas=alphas, cv=5, scoring='neg_mean_squared_error')
            else:
                model = Ridge(alpha=self.stage1_alpha)
            
            model.fit(X_arm, Y_arm)
            self.models_[arm] = model
        
        # Stage 2: Fit corrections on target
        # Control arm
        mask_control = (A_target == 0)
        if np.sum(mask_control) >= 10:
            X_control = X_target[mask_control]
            Y_control = Y_target[mask_control]
            mu0_proxy = self.models_[0].predict(X_control)
            resid_0 = Y_control - mu0_proxy
            
            if self.stage2_model == 'elasticnet':
                if self.stage2_l1_ratios is None:
                    l1_ratios = [.1, .5, .7, .9, .95, .99, 1]
                else:
                    l1_ratios = self.stage2_l1_ratios
                
                correction_0 = ElasticNetCV(
                    l1_ratio=l1_ratios,
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=42
                )
            else:  # lasso
                correction_0 = LassoCV(
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=42
                )
            
            correction_0.fit(X_control, resid_0)
            self.delta_0_ = correction_0.coef_
            self.intercept_0_ = correction_0.intercept_
        else:
            self.delta_0_ = np.zeros(X_target.shape[1])
            self.intercept_0_ = 0.0
        
        # Treated arm
        mask_treated = (A_target == 1)
        if np.sum(mask_treated) >= 10:
            X_treated = X_target[mask_treated]
            Y_treated = Y_target[mask_treated]
            mu1_proxy = self.models_[1].predict(X_treated)
            resid_1 = Y_treated - mu1_proxy
            
            if self.stage2_model == 'elasticnet':
                if self.stage2_l1_ratios is None:
                    l1_ratios = [.1, .5, .7, .9, .95, .99, 1]
                else:
                    l1_ratios = self.stage2_l1_ratios
                
                correction_1 = ElasticNetCV(
                    l1_ratio=l1_ratios,
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=42
                )
            else:  # lasso
                correction_1 = LassoCV(
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=42
                )
            
            correction_1.fit(X_treated, resid_1)
            self.delta_1_ = correction_1.coef_
            self.intercept_1_ = correction_1.intercept_
        else:
            # Shared bias assumption
            self.delta_1_ = self.delta_0_
            self.intercept_1_ = self.intercept_0_
        
        return self
    
    def predict(self, X):
        """Predict CATE with corrections"""
        check_is_fitted(self, 'models_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        mu0 = self.models_[0].predict(X) + X @ self.delta_0_ + self.intercept_0_
        mu1 = self.models_[1].predict(X) + X @ self.delta_1_ + self.intercept_1_
        return mu1 - mu0
    
    def predict_counterfactuals(self, X):
        """Predict μ₀(x) and μ₁(x)"""
        check_is_fitted(self, 'models_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        mu0 = self.models_[0].predict(X) + X @ self.delta_0_ + self.intercept_0_
        mu1 = self.models_[1].predict(X) + X @ self.delta_1_ + self.intercept_1_
        return mu0, mu1


class NoTransferBaseline(BaseEstimator, RegressorMixin):
    """
    No-Transfer baseline: Only uses target data (ignores source).
    
    Useful for measuring value of transfer learning.
    """
    
    def __init__(self):
        self.models_ = {}
    
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target):
        """Fit only on target data"""
        
        for arm in [0, 1]:
            mask = (A_target == arm)
            if np.sum(mask) >= 5:
                X_arm = X_target[mask]
                Y_arm = Y_target[mask]
                
                # Simple Ridge with small regularization
                model = Ridge(alpha=1.0)
                model.fit(X_arm, Y_arm)
                self.models_[arm] = model
            else:
                # Not enough data, use zero prediction
                self.models_[arm] = None
        
        return self
    
    def predict(self, X):
        """Predict CATE"""
        check_is_fitted(self, 'models_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        if self.models_[0] is None or self.models_[1] is None:
            return np.zeros(len(X))
        
        mu0 = self.models_[0].predict(X)
        mu1 = self.models_[1].predict(X)
        return mu1 - mu0
    
    def predict_counterfactuals(self, X):
        """Predict μ₀(x) and μ₁(x)"""
        check_is_fitted(self, 'models_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        if self.models_[0] is None or self.models_[1] is None:
            return np.zeros(len(X)), np.zeros(len(X))
        
        mu0 = self.models_[0].predict(X)
        mu1 = self.models_[1].predict(X)
        return mu0, mu1
