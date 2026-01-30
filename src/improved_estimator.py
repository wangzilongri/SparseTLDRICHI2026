"""
Improved Placebo-Anchored DR-Learner with Linear Stages and Hyperparameter Optimization

Key Changes from Original:
1. Stage 1: Linear Regression (Ridge) instead of Random Forest
2. Stage 2: Elastic Net with CV for alpha and l1_ratio
3. Stage 3: Multiple model options with hyperparameter CV
4. All hyperparameters optimized via cross-validation

Author: Updated January 29, 2026
"""

import numpy as np
import warnings
from sklearn.base import clone, BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge, ElasticNetCV, LassoCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.utils.validation import check_is_fitted, check_array


class ImprovedPlaceboAnchoredDRLearner(BaseEstimator, RegressorMixin):
    """
    Three-stage estimator with LINEAR stages and hyperparameter optimization.
    
    Stage 1: Ridge Regression on source data (linear, regularized)
    Stage 2: Elastic Net CV for sparse corrections (auto-tuned alpha + l1_ratio)
    Stage 3: Flexible CATE model with CV hyperparameter tuning
    
    Parameters:
    -----------
    stage1_model : {'ridge', 'linear'}, default='ridge'
        Model type for Stage 1 proxy estimation
    stage1_alpha : float or 'cv', default='cv'
        Ridge regularization. If 'cv', uses RidgeCV with automatic selection
    stage1_alphas : array-like, default=None
        Alpha grid for RidgeCV. If None, uses [0.1, 1.0, 10.0, 100.0]
    
    stage2_model : {'elasticnet', 'lasso'}, default='elasticnet'
        Model type for Stage 2 sparse corrections
    stage2_l1_ratios : array-like, default=None
        L1 ratios for ElasticNetCV. If None, uses [.1, .5, .7, .9, .95, .99, 1]
    stage2_cv_folds : int, default=5
        CV folds for Stage 2 regularization parameter selection
    
    stage3_model : {'rf', 'gbm', 'ridge'}, default='rf'
        Model type for Stage 3 CATE estimation
    stage3_tune : bool, default=True
        Whether to tune Stage 3 hyperparameters via CV
    stage3_cv_folds : int, default=3
        CV folds for Stage 3 hyperparameter tuning (expensive!)
    stage3_param_grid : dict, default=None
        Parameter grid for Stage 3. If None, uses defaults for each model type
    
    option : {'A', 'B'}, default='A'
        'A' = separate corrections (requires treated data in target)
        'B' = shared bias assumption
    
    n_folds_dr : int, default=3
        Number of folds for cross-fitting in DR step
    
    random_state : int, default=42
        Random seed
    
    verbose : bool, default=False
        Print progress messages
    """
    
    def __init__(self,
                 # Stage 1 parameters
                 stage1_model='ridge',
                 stage1_alpha='cv',
                 stage1_alphas=None,
                 # Stage 2 parameters
                 stage2_model='elasticnet',
                 stage2_l1_ratios=None,
                 stage2_cv_folds=5,
                 # Stage 3 parameters
                 stage3_model='rf',
                 stage3_tune=True,
                 stage3_cv_folds=3,
                 stage3_param_grid=None,
                 # General parameters
                 option='A',
                 n_folds_dr=3,
                 random_state=42,
                 verbose=False):
        
        self.stage1_model = stage1_model
        self.stage1_alpha = stage1_alpha
        self.stage1_alphas = stage1_alphas
        
        self.stage2_model = stage2_model
        self.stage2_l1_ratios = stage2_l1_ratios
        self.stage2_cv_folds = stage2_cv_folds
        
        self.stage3_model = stage3_model
        self.stage3_tune = stage3_tune
        self.stage3_cv_folds = stage3_cv_folds
        self.stage3_param_grid = stage3_param_grid
        
        self.option = option
        self.n_folds_dr = n_folds_dr
        self.random_state = random_state
        self.verbose = verbose
        
        # Set during fit
        self.proxy_models_ = {}
        self.delta_0_ = None
        self.delta_1_ = None
        self.intercept_0_ = None
        self.intercept_1_ = None
        self.cate_model_ = None
        self.fold_models_ = []
        self.pseudo_outcomes_ = None
    
    def fit(self, X_source, A_source, Y_source,
            X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        """
        Fit the three-stage estimator.
        
        Parameters:
        -----------
        X_source : array-like, shape (n_source, n_features)
            Source covariates
        A_source : array-like, shape (n_source,)
            Source treatment assignments
        Y_source : array-like, shape (n_source,)
            Source outcomes
        X_target : array-like, shape (n_target, n_features)
            Target covariates
        A_target : array-like, shape (n_target,)
            Target treatment assignments
        Y_target : array-like, shape (n_target,)
            Target outcomes
        propensity_source : array-like, shape (n_source,), optional
            Source propensity scores (defaults to 0.5)
        propensity_target : array-like, shape (n_target,), optional
            Target propensity scores (defaults to 0.5)
        
        Returns:
        --------
        self : object
        """
        # Validate
        X_source = check_array(X_source, ensure_2d=True, dtype=np.float64)
        X_target = check_array(X_target, ensure_2d=True, dtype=np.float64)
        A_source = np.asarray(A_source).ravel()
        A_target = np.asarray(A_target).ravel()
        Y_source = np.asarray(Y_source).ravel()
        Y_target = np.asarray(Y_target).ravel()
        
        if X_source.shape[1] != X_target.shape[1]:
            raise ValueError("Feature dimension mismatch")
        
        self.n_features_ = X_source.shape[1]
        
        if propensity_target is None:
            propensity_target = np.full(len(X_target), 0.5)
        
        # Stage 1: Fit proxy models
        if self.verbose:
            print(f"Stage 1: Fitting {self.stage1_model} proxy models...")
        self._fit_stage1(X_source, A_source, Y_source)
        
        # Stages 2 & 3: Anchoring + DR
        if self.verbose:
            print(f"Stages 2-3: Sparse anchoring ({self.option}) + DR with cross-fitting...")
        self._fit_stages2_and_3(X_target, A_target, Y_target, propensity_target)
        
        if self.verbose:
            print("Fitting complete.")
        
        return self
    
    def _fit_stage1(self, X, A, Y):
        """Stage 1: Fit linear proxy models for each arm"""
        
        if self.stage1_alphas is None:
            alphas = np.logspace(-2, 2, 20)  # [0.01, 0.1, ..., 100]
        else:
            alphas = self.stage1_alphas
        
        for arm in [0, 1]:
            mask = (A == arm)
            X_arm = X[mask]
            Y_arm = Y[mask]
            
            if self.stage1_model == 'ridge':
                if self.stage1_alpha == 'cv':
                    # Automatic CV selection of alpha
                    from sklearn.linear_model import RidgeCV
                    model = RidgeCV(alphas=alphas, cv=5, scoring='neg_mean_squared_error')
                else:
                    model = Ridge(alpha=self.stage1_alpha)
            elif self.stage1_model == 'linear':
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
            else:
                raise ValueError(f"Unknown stage1_model: {self.stage1_model}")
            
            model.fit(X_arm, Y_arm)
            self.proxy_models_[arm] = model
            
            if self.verbose and self.stage1_model == 'ridge' and self.stage1_alpha == 'cv':
                selected_alpha = model.alpha_
                print(f"  Arm {arm}: Selected alpha = {selected_alpha:.4f}")
    
    def _fit_stages2_and_3(self, X, A, Y, propensity):
        """Stages 2 & 3: Sparse correction + DR with cross-fitting"""
        
        n = len(X)
        pseudo_outcomes = np.zeros(n)
        fold_models = []
        
        # Cross-fitting
        kfold = KFold(n_splits=self.n_folds_dr, shuffle=True, random_state=self.random_state)
        
        for fold_idx, (train_idx, val_idx) in enumerate(kfold.split(X)):
            if self.verbose:
                print(f"  Fold {fold_idx + 1}/{self.n_folds_dr}...")
            
            X_train, X_val = X[train_idx], X[val_idx]
            A_train, A_val = A[train_idx], A[val_idx]
            Y_train, Y_val = Y[train_idx], Y[val_idx]
            prop_val = propensity[val_idx]
            
            # Stage 2: Fit sparse corrections on training fold
            delta_0, intercept_0, delta_1, intercept_1 = self._fit_stage2(
                X_train, A_train, Y_train, fold_idx
            )
            
            fold_models.append({
                'delta_0': delta_0,
                'delta_1': delta_1,
                'intercept_0': intercept_0,
                'intercept_1': intercept_1
            })
            
            # Compute corrected predictions for validation fold
            mu0_val = self.proxy_models_[0].predict(X_val) + X_val @ delta_0 + intercept_0
            mu1_val = self.proxy_models_[1].predict(X_val) + X_val @ delta_1 + intercept_1
            tau_val = mu1_val - mu0_val
            
            # Stage 3: Compute pseudo-outcomes (DR formula)
            for i, idx in enumerate(val_idx):
                a = A_val[i]
                y = Y[idx]
                e = prop_val[i]
                mu_a = mu1_val[i] if a == 1 else mu0_val[i]
                
                # Doubly robust pseudo-outcome
                if e * (1 - e) < 1e-6:
                    psi = tau_val[i]
                else:
                    psi = tau_val[i] + ((a - e) / (e * (1 - e))) * (y - mu_a)
                
                pseudo_outcomes[idx] = psi
        
        # Clip outliers
        mean_psi = np.mean(pseudo_outcomes)
        std_psi = np.std(pseudo_outcomes)
        pseudo_outcomes_clipped = np.clip(pseudo_outcomes,
                                          mean_psi - 3*std_psi,
                                          mean_psi + 3*std_psi)
        
        # Stage 3: Fit final CATE model with hyperparameter tuning
        if self.verbose:
            print(f"  Stage 3: Fitting {self.stage3_model} CATE model...")
        self.cate_model_ = self._fit_stage3(X, pseudo_outcomes_clipped)
        
        self.pseudo_outcomes_ = pseudo_outcomes
        self.fold_models_ = fold_models
        
        # Store average corrections
        self.delta_0_ = np.mean([m['delta_0'] for m in fold_models], axis=0)
        self.delta_1_ = np.mean([m['delta_1'] for m in fold_models], axis=0)
        self.intercept_0_ = np.mean([m['intercept_0'] for m in fold_models])
        self.intercept_1_ = np.mean([m['intercept_1'] for m in fold_models])
    
    def _fit_stage2(self, X, A, Y, fold_idx):
        """Stage 2: Fit sparse corrections using Elastic Net"""
        
        # Control arm correction
        mask_control = (A == 0)
        if np.sum(mask_control) >= 10:
            X_control = X[mask_control]
            Y_control = Y[mask_control]
            mu0_proxy = self.proxy_models_[0].predict(X_control)
            resid_0 = Y_control - mu0_proxy
            
            if self.stage2_model == 'elasticnet':
                if self.stage2_l1_ratios is None:
                    l1_ratios = [.1, .5, .7, .9, .95, .99, 1]
                else:
                    l1_ratios = self.stage2_l1_ratios
                
                correction_model_0 = ElasticNetCV(
                    l1_ratio=l1_ratios,
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=self.random_state
                )
            elif self.stage2_model == 'lasso':
                correction_model_0 = LassoCV(
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=self.random_state
                )
            else:
                raise ValueError(f"Unknown stage2_model: {self.stage2_model}")
            
            correction_model_0.fit(X_control, resid_0)
            delta_0 = correction_model_0.coef_
            intercept_0 = correction_model_0.intercept_
            
            if self.verbose and hasattr(correction_model_0, 'alpha_'):
                print(f"    Fold {fold_idx}: Control alpha = {correction_model_0.alpha_:.4f}")
        else:
            delta_0 = np.zeros(X.shape[1])
            intercept_0 = 0.0
        
        # Treated arm correction
        mask_treated = (A == 1)
        if self.option == 'A' and np.sum(mask_treated) >= 10:
            X_treated = X[mask_treated]
            Y_treated = Y[mask_treated]
            mu1_proxy = self.proxy_models_[1].predict(X_treated)
            resid_1 = Y_treated - mu1_proxy
            
            if self.stage2_model == 'elasticnet':
                if self.stage2_l1_ratios is None:
                    l1_ratios = [.1, .5, .7, .9, .95, .99, 1]
                else:
                    l1_ratios = self.stage2_l1_ratios
                
                correction_model_1 = ElasticNetCV(
                    l1_ratio=l1_ratios,
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=self.random_state
                )
            elif self.stage2_model == 'lasso':
                correction_model_1 = LassoCV(
                    cv=self.stage2_cv_folds,
                    fit_intercept=True,
                    max_iter=5000,
                    random_state=self.random_state
                )
            else:
                raise ValueError(f"Unknown stage2_model: {self.stage2_model}")
            
            correction_model_1.fit(X_treated, resid_1)
            delta_1 = correction_model_1.coef_
            intercept_1 = correction_model_1.intercept_
            
            if self.verbose and hasattr(correction_model_1, 'alpha_'):
                print(f"    Fold {fold_idx}: Treated alpha = {correction_model_1.alpha_:.4f}")
        else:
            # Option B or insufficient treated data
            delta_1 = delta_0
            intercept_1 = intercept_0
        
        return delta_0, intercept_0, delta_1, intercept_1
    
    def _fit_stage3(self, X, pseudo_outcomes):
        """Stage 3: Fit CATE model with optional hyperparameter tuning"""
        
        # Remove NaN values
        mask = ~np.isnan(pseudo_outcomes)
        if not np.any(mask):
            warnings.warn("All pseudo-outcomes are NaN, using zeros")
            X_fit = X
            y_fit = np.zeros(len(X))
        else:
            X_fit = X[mask]
            y_fit = pseudo_outcomes[mask]
        
        # Get base model and param grid
        if self.stage3_model == 'rf':
            base_model = RandomForestRegressor(random_state=self.random_state, n_jobs=-1)
            if self.stage3_param_grid is None:
                param_grid = {
                    'n_estimators': [100, 200],
                    'max_depth': [3, 5, 7],
                    'min_samples_leaf': [10, 20, 30]
                }
            else:
                param_grid = self.stage3_param_grid
        
        elif self.stage3_model == 'gbm':
            base_model = GradientBoostingRegressor(random_state=self.random_state)
            if self.stage3_param_grid is None:
                param_grid = {
                    'n_estimators': [100, 200],
                    'max_depth': [3, 5],
                    'learning_rate': [0.01, 0.1],
                    'min_samples_leaf': [10, 20]
                }
            else:
                param_grid = self.stage3_param_grid
        
        elif self.stage3_model == 'ridge':
            base_model = Ridge()
            if self.stage3_param_grid is None:
                param_grid = {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                }
            else:
                param_grid = self.stage3_param_grid
        
        else:
            raise ValueError(f"Unknown stage3_model: {self.stage3_model}")
        
        # Fit with or without hyperparameter tuning
        if self.stage3_tune and len(y_fit) >= 30:  # Need enough data for CV
            grid_search = GridSearchCV(
                base_model,
                param_grid,
                cv=min(self.stage3_cv_folds, len(y_fit) // 10),  # Adaptive CV folds
                scoring='neg_mean_squared_error',
                n_jobs=1,  # Sequential to avoid nested parallelism issues
                verbose=0
            )
            grid_search.fit(X_fit, y_fit)
            model = grid_search.best_estimator_
            
            if self.verbose:
                print(f"    Best Stage 3 params: {grid_search.best_params_}")
        else:
            # Use defaults
            if self.stage3_model == 'rf':
                model = RandomForestRegressor(
                    n_estimators=200, max_depth=5, min_samples_leaf=10,
                    random_state=self.random_state, n_jobs=-1
                )
            elif self.stage3_model == 'gbm':
                model = GradientBoostingRegressor(
                    n_estimators=100, max_depth=3, learning_rate=0.1,
                    random_state=self.random_state
                )
            elif self.stage3_model == 'ridge':
                model = Ridge(alpha=1.0)
            
            model.fit(X_fit, y_fit)
        
        return model
    
    def predict(self, X):
        """
        Predict CATE τ(x) for new patients.
        
        Parameters:
        -----------
        X : array-like, shape (n_samples, n_features)
            Covariate matrix
        
        Returns:
        --------
        tau : array, shape (n_samples,)
            Predicted CATE values
        """
        check_is_fitted(self, 'cate_model_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        return self.cate_model_.predict(X)
    
    def predict_counterfactuals(self, X):
        """
        Predict counterfactual outcomes μ₀(x) and μ₁(x).
        
        Parameters:
        -----------
        X : array-like, shape (n_samples, n_features)
            Covariate matrix
        
        Returns:
        --------
        mu0 : array, shape (n_samples,)
            Predicted control outcomes
        mu1 : array, shape (n_samples,)
            Predicted treated outcomes
        """
        check_is_fitted(self, 'cate_model_')
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        
        # Use proxy + average corrections
        mu0 = self.proxy_models_[0].predict(X) + X @ self.delta_0_ + self.intercept_0_
        mu1 = self.proxy_models_[1].predict(X) + X @ self.delta_1_ + self.intercept_1_
        
        return mu0, mu1
