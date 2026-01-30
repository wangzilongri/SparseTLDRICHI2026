"""
Three-Stage Placebo-Anchored Doubly Robust Estimator
Based on: Transfer Learning for Meta-analysis Under Covariate Shift
"""

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold
from sklearn.utils.validation import check_is_fitted, check_array


class PlaceboAnchoredDRLearner(BaseEstimator, RegressorMixin):
    """
    Three-stage doubly robust learner with placebo anchoring.
    
    Stage 1: Fit proxy models on source trials
    Stage 2: Estimate sparse transport corrections using target placebo (gold)
    Stage 3: Doubly robust CATE estimation with cross-fitting
    
    Parameters
    ----------
    proxy_model : sklearn estimator, default=RandomForestRegressor
        Model for Stage 1 proxy fitting
    correction_model : sklearn estimator, default=LassoCV
        Sparse model for Stage 2 corrections
    cate_model : sklearn estimator, default=RandomForestRegressor
        Model for Stage 3 CATE regression
    option : str, 'A' or 'B', default='A'
        Option A: Estimate separate corrections when target has both arms
        Option B: Transfer placebo correction to treated arm
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
        Fit the three-stage estimator.
        
        Parameters
        ----------
        X_source : array-like, shape (n_source, p)
            Source covariates
        A_source : array-like, shape (n_source,)
            Source treatment assignments
        Y_source : array-like, shape (n_source,)
            Source outcomes
        c_source : array-like, shape (n_source,)
            Source site indicators
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
        
        n_source, self.n_features_ = X_source.shape
        n_target = len(X_target)
        
        # Default propensity for RCTs
        if propensity_target is None:
            propensity_target = np.full(n_target, 0.5)
        
        # Initialize models
        if self.proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=100, max_depth=8, random_state=self.random_state
            )
        if self.correction_model is None:
            self.correction_model = LassoCV(cv=5, random_state=self.random_state)
        if self.cate_model is None:
            self.cate_model = RandomForestRegressor(
                n_estimators=100, max_depth=5, random_state=self.random_state
            )
        
        # ===================================================================
        # STAGE 1: Fit proxy models on source data
        # ===================================================================
        if self.verbose:
            print("Stage 1: Fitting proxy models on source data...")
        
        self.proxy_models_ = {}
        for a in [0, 1]:
            mask = (A_source == a)
            if np.sum(mask) == 0:
                raise ValueError(f"No samples with A={a} in source data")
            
            from sklearn.base import clone
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.proxy_models_[a] = model
            
            if self.verbose:
                print(f"  Proxy model for A={a}: {np.sum(mask)} samples")
        
        # ===================================================================
        # STAGE 2: Gold correction on target placebo
        # ===================================================================
        if self.verbose:
            print(f"Stage 2: Gold correction (Option {self.option})...")
        
        # Placebo correction (always available)
        mask_target_placebo = (A_target == 0)
        if np.sum(mask_target_placebo) == 0:
            raise ValueError("No placebo samples in target data")
        
        X_gold_0 = X_target[mask_target_placebo]
        Y_gold_0 = Y_target[mask_target_placebo]
        
        # Residualize against proxy
        mu0_proxy = self.proxy_models_[0].predict(X_gold_0)
        residuals_0 = Y_gold_0 - mu0_proxy
        
        # Fit sparse correction
        from sklearn.base import clone
        correction_0 = clone(self.correction_model)
        correction_0.fit(X_gold_0, residuals_0)
        self.delta_0_ = correction_0
        
        if self.verbose:
            sparsity_0 = np.sum(np.abs(correction_0.coef_) > 1e-6)
            print(f"  Placebo correction: {sparsity_0}/{self.n_features_} nonzero")
        
        # Treated correction
        if self.option == 'A':
            # Option A: Estimate from target treated data
            mask_target_treated = (A_target == 1)
            
            if np.sum(mask_target_treated) >= 10:
                X_gold_1 = X_target[mask_target_treated]
                Y_gold_1 = Y_target[mask_target_treated]
                
                mu1_proxy = self.proxy_models_[1].predict(X_gold_1)
                residuals_1 = Y_gold_1 - mu1_proxy
                
                correction_1 = clone(self.correction_model)
                correction_1.fit(X_gold_1, residuals_1)
                self.delta_1_ = correction_1
                
                if self.verbose:
                    sparsity_1 = np.sum(np.abs(correction_1.coef_) > 1e-6)
                    print(f"  Treated correction: {sparsity_1}/{self.n_features_} nonzero")
            else:
                # Fallback to Option B if insufficient treated samples
                if self.verbose:
                    print(f"  Insufficient treated samples ({np.sum(mask_target_treated)}), using Option B")
                self.delta_1_ = self.delta_0_
        
        elif self.option == 'B':
            # Option B: Share placebo correction
            self.delta_1_ = self.delta_0_
            
            if self.verbose:
                print("  Treated correction: shared with placebo (Option B)")
        
        else:
            raise ValueError(f"Invalid option: {self.option}. Must be 'A' or 'B'")
        
        # ===================================================================
        # STAGE 3: Doubly robust CATE regression with cross-fitting
        # ===================================================================
        if self.verbose:
            print(f"Stage 3: DR CATE regression with {self.n_folds}-fold cross-fitting...")
        
        # Cross-fitting setup
        kf = KFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        pseudo_outcomes = np.zeros(n_target)
        
        for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X_target)):
            # Fit corrections on training fold
            X_train = X_target[train_idx]
            A_train = A_target[train_idx]
            Y_train = Y_target[train_idx]
            
            # Placebo correction
            mask_placebo = (A_train == 0)
            if np.sum(mask_placebo) > 0:
                X_p = X_train[mask_placebo]
                Y_p = Y_train[mask_placebo]
                mu0_p = self.proxy_models_[0].predict(X_p)
                resid_p = Y_p - mu0_p
                
                delta_0_fold = clone(self.correction_model)
                delta_0_fold.fit(X_p, resid_p)
            else:
                delta_0_fold = self.delta_0_
            
            # Treated correction
            if self.option == 'A':
                mask_treated = (A_train == 1)
                if np.sum(mask_treated) >= 5:
                    X_t = X_train[mask_treated]
                    Y_t = Y_train[mask_treated]
                    mu1_t = self.proxy_models_[1].predict(X_t)
                    resid_t = Y_t - mu1_t
                    
                    delta_1_fold = clone(self.correction_model)
                    delta_1_fold.fit(X_t, resid_t)
                else:
                    delta_1_fold = delta_0_fold
            else:
                delta_1_fold = delta_0_fold
            
            # Compute anchored predictions on validation fold
            X_val = X_target[val_idx]
            A_val = A_target[val_idx]
            Y_val = Y_target[val_idx]
            e_val = propensity_target[val_idx]
            
            mu0_val = self.proxy_models_[0].predict(X_val) + delta_0_fold.predict(X_val)
            mu1_val = self.proxy_models_[1].predict(X_val) + delta_1_fold.predict(X_val)
            tau_val = mu1_val - mu0_val
            
            # DR pseudo-outcome
            for i, idx in enumerate(val_idx):
                a = A_val[i]
                y = Y_val[i]
                e = e_val[i]
                mu_a = mu1_val[i] if a == 1 else mu0_val[i]
                
                # Avoid division by zero
                if e * (1 - e) > 1e-8:
                    psi = tau_val[i] + ((a - e) / (e * (1 - e))) * (y - mu_a)
                else:
                    psi = tau_val[i]
                
                pseudo_outcomes[idx] = psi
        
        # Fit final CATE model
        from sklearn.base import clone
        self.cate_model_ = clone(self.cate_model)
        self.cate_model_.fit(X_target, pseudo_outcomes)
        
        if self.verbose:
            print("Fitting complete.")
        
        return self
    
    def predict(self, X):
        """Predict CATE using Stage 3 DR model."""
        check_is_fitted(self, 'cate_model_')
        X = check_array(X)
        return self.cate_model_.predict(X)
    
    def predict_anchored(self, X):
        """Predict CATE using Stage 2 anchored models (plug-in)."""
        check_is_fitted(self, 'delta_0_')
        X = check_array(X)
        
        mu0 = self.proxy_models_[0].predict(X) + self.delta_0_.predict(X)
        mu1 = self.proxy_models_[1].predict(X) + self.delta_1_.predict(X)
        
        return mu1 - mu0
