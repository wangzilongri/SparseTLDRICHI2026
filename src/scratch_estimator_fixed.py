# =============================================================================
# FIXED: PlaceboAnchoredDRLearner
# - Handles disconnected (all-placebo) target correctly
# - Uses KFold when target has 1 arm
# - Skips DR pseudo-outcome noise injection in disconnected mode
# - Exposes plug-in CATE via predict_tau_plugin()
# - Makes clipping optional (default OFF)
# =============================================================================

import numpy as np
import warnings
from sklearn.base import clone, BaseEstimator, RegressorMixin
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.utils.validation import check_is_fitted, check_array

class PlaceboAnchoredDRLearner(BaseEstimator, RegressorMixin):
    """
    FIXED Three-stage doubly robust learner for transfer learning with placebo anchoring.
    
    Key fixes:
    - Detects disconnected target (placebo-only) and skips DR noise injection
    - Uses KFold instead of StratifiedKFold when target has single arm
    - Exposes plug-in tau prediction for comparison
    """
    def __init__(self, 
                 proxy_model=None,
                 cate_model=None,
                 option: str = 'B',
                 lasso_cv_folds: int = 5,
                 n_folds_dr: int = 5,
                 fit_intercept_correction: bool = False,
                 random_state: int = 42,
                 verbose: bool = False,
                 # NEW:
                 clip_pseudo_outcomes: bool = False,
                 pseudo_clip_sigma: float = 3.0):
        if proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=20, 
                random_state=random_state, n_jobs=-1
            )
        else:
            self.proxy_model = proxy_model

        if cate_model is None:
            self.cate_model = RandomForestRegressor(
                n_estimators=200, max_depth=5, min_samples_leaf=10,
                random_state=random_state, n_jobs=-1
            )
        else:
            self.cate_model = cate_model

        self.option = option
        self.lasso_cv_folds = lasso_cv_folds
        self.n_folds_dr = n_folds_dr
        self.fit_intercept_correction = fit_intercept_correction
        self.random_state = random_state
        self.verbose = verbose

        # NEW:
        self.clip_pseudo_outcomes = clip_pseudo_outcomes
        self.pseudo_clip_sigma = pseudo_clip_sigma

        # Fit attributes
        self.proxy_models_ = {}
        self.delta_placebo_ = None
        self.delta_treated_ = None
        self.intercept_placebo_ = 0.0
        self.intercept_treated_ = 0.0
        self.cate_model_ = None
        self.pseudo_outcomes_ = None
        self.fold_models_ = None
        self._is_disconnected_target_ = None

    def fit(self, X_source, A_source, Y_source,
            X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):

        X_s, A_s, Y_s = self._validate_data(X_source, A_source, Y_source, 'source')
        X_t, A_t, Y_t = self._validate_data(X_target, A_target, Y_target, 'target')

        if X_s.shape[1] != X_t.shape[1]:
            raise ValueError("Feature dimension mismatch between source and target")

        self.n_features_ = X_s.shape[1]

        if self.verbose:
            print("Stage 1: Fitting proxy models on source data...")
        self._fit_proxy(X_s, A_s, Y_s)

        if self.verbose:
            print(f"Stage 2-3: Gold anchoring ({self.option}) with {self.n_folds_dr}-fold cross-fitting...")
        self._fit_anchor_and_dr(X_t, A_t, Y_t, propensity_target)

        if self.verbose:
            print("Fitting complete.")
        return self

    def _validate_data(self, X, A, Y, name):
        X = check_array(X, ensure_2d=True, dtype=np.float64)
        A = np.asarray(A).ravel().astype(float)
        Y = np.asarray(Y).ravel().astype(float)
        if len(X) != len(A) or len(X) != len(Y):
            raise ValueError(f"Inconsistent lengths in {name} data")
        return X, A, Y

    def _fit_proxy(self, X, A, Y):
        self.proxy_models_ = {}
        for a in [0, 1]:
            mask = (A == a)
            n_a = int(np.sum(mask))
            if n_a == 0:
                raise ValueError(f"No observations in arm {a} in SOURCE")
            model = clone(self.proxy_model)
            model.fit(X[mask], Y[mask])
            self.proxy_models_[a] = model
            if self.verbose:
                print(f"  Proxy arm {a}: fitted on {n_a} samples")

    # --------------------------
    # NEW: helper to pick CV
    # --------------------------
    def _get_cv(self, X, A):
        unique = np.unique(A)
        if unique.size < 2:
            # Disconnected / single-arm target (all placebo)
            if self.verbose:
                print("  Target has single arm -> using KFold (not StratifiedKFold).")
            return KFold(n_splits=self.n_folds_dr, shuffle=True, random_state=self.random_state), None
        return StratifiedKFold(n_splits=self.n_folds_dr, shuffle=True, random_state=self.random_state), A

    # --------------------------
    # FIXED: Stage 2 + Stage 3
    # --------------------------
    def _fit_anchor_and_dr(self, X, A, Y, propensity):
        n = len(X)

        # Propensity
        if propensity is None:
            propensity = np.full(n, 0.5)
        else:
            propensity = np.asarray(propensity).ravel().astype(float)

        # Detect disconnected target
        self._is_disconnected_target_ = (np.unique(A).size < 2) or (np.sum(A == 1) == 0)
        if self._is_disconnected_target_ and self.verbose:
            print("  Disconnected target detected (no treated arm).")
            print("  -> Will SKIP DR noise injection and fit CATE model on plug-in tau only.")

        cv, strat_y = self._get_cv(X, A)
        splits = cv.split(X) if strat_y is None else cv.split(X, strat_y)

        pseudo_outcomes = np.zeros(n, dtype=float)
        fold_models = []

        for fold_idx, (train_idx, val_idx) in enumerate(splits):
            X_train, X_val = X[train_idx], X[val_idx]
            A_train, Y_train = A[train_idx], Y[train_idx]
            prop_val = propensity[val_idx]

            # --------------------------
            # Stage 2: placebo correction on TRAIN fold
            # --------------------------
            placebo_mask = (A_train == 0)
            n_placebo = int(np.sum(placebo_mask))

            if n_placebo < 10:
                warnings.warn(f"Fold {fold_idx}: Only {n_placebo} placebo samples; using zero correction.")
                delta_0 = np.zeros(self.n_features_)
                intercept_0 = 0.0
            else:
                X_p = X_train[placebo_mask]
                Y_p = Y_train[placebo_mask]
                mu0_proxy = self.proxy_models_[0].predict(X_p)
                resid_0 = Y_p - mu0_proxy

                lasso_0 = LassoCV(
                    cv=min(self.lasso_cv_folds, max(2, n_placebo // 5)),
                    fit_intercept=self.fit_intercept_correction,
                    random_state=self.random_state,
                    max_iter=4000
                )
                lasso_0.fit(X_p, resid_0)

                delta_0 = lasso_0.coef_.copy()
                intercept_0 = float(lasso_0.intercept_) if self.fit_intercept_correction else 0.0

            # --------------------------
            # Stage 2: treated correction
            # Option A if feasible else Option B
            # --------------------------
            treated_mask = (A_train == 1)
            n_treated = int(np.sum(treated_mask))

            if (self.option == 'A') and (n_treated >= 10):
                X_tr = X_train[treated_mask]
                Y_tr = Y_train[treated_mask]
                mu1_proxy = self.proxy_models_[1].predict(X_tr)
                resid_1 = Y_tr - mu1_proxy

                lasso_1 = LassoCV(
                    cv=min(self.lasso_cv_folds, max(2, n_treated // 5)),
                    fit_intercept=self.fit_intercept_correction,
                    random_state=self.random_state,
                    max_iter=4000
                )
                lasso_1.fit(X_tr, resid_1)

                delta_1 = lasso_1.coef_.copy()
                intercept_1 = float(lasso_1.intercept_) if self.fit_intercept_correction else 0.0
            else:
                # Option B: share bias
                delta_1 = delta_0.copy()
                intercept_1 = intercept_0

            fold_models.append({
                'delta_0': delta_0,
                'delta_1': delta_1,
                'intercept_0': intercept_0,
                'intercept_1': intercept_1
            })

            # Anchored predictions on VAL fold
            mu0_val = self.proxy_models_[0].predict(X_val) + X_val @ delta_0 + intercept_0
            mu1_val = self.proxy_models_[1].predict(X_val) + X_val @ delta_1 + intercept_1
            tau_val = mu1_val - mu0_val

            # --------------------------
            # Stage 3:
            # FIX: if disconnected target -> DO NOT add placebo residual noise
            # --------------------------
            if self._is_disconnected_target_:
                pseudo_outcomes[val_idx] = tau_val
            else:
                # Standard DR pseudo-outcome
                for j, idx in enumerate(val_idx):
                    a = A[idx]
                    y = Y[idx]
                    e = prop_val[j]
                    mu_a = mu1_val[j] if a == 1 else mu0_val[j]
                    if e * (1 - e) < 1e-8:
                        psi = tau_val[j]
                    else:
                        psi = tau_val[j] + ((a - e) / (e * (1 - e))) * (y - mu_a)
                    pseudo_outcomes[idx] = psi

        # Optional clipping (OFF by default)
        pseudo_used = pseudo_outcomes
        if self.clip_pseudo_outcomes:
            m = float(np.mean(pseudo_outcomes))
            s = float(np.std(pseudo_outcomes))
            lo, hi = m - self.pseudo_clip_sigma * s, m + self.pseudo_clip_sigma * s
            pseudo_used = np.clip(pseudo_outcomes, lo, hi)

        # Fit final CATE model on target X
        self.cate_model_ = clone(self.cate_model)
        if np.any(np.isnan(pseudo_used)):
            mask = ~np.isnan(pseudo_used)
            if np.sum(mask) == 0:
                warnings.warn("All pseudo outcomes are NaN; fitting zeros.")
                self.cate_model_.fit(X, np.zeros(n))
            else:
                self.cate_model_.fit(X[mask], pseudo_used[mask])
        else:
            self.cate_model_.fit(X, pseudo_used)

        self.pseudo_outcomes_ = pseudo_outcomes
        self.fold_models_ = fold_models

        # Average correction vectors for interpretability + plug-in prediction
        self.delta_placebo_ = np.mean([m['delta_0'] for m in fold_models], axis=0)
        self.delta_treated_ = np.mean([m['delta_1'] for m in fold_models], axis=0)
        self.intercept_placebo_ = float(np.mean([m['intercept_0'] for m in fold_models]))
        self.intercept_treated_ = float(np.mean([m['intercept_1'] for m in fold_models]))

        return self

    def predict(self, X):
        """Stage-3 DR prediction"""
        check_is_fitted(self, 'cate_model_')
        X = check_array(X)
        return self.cate_model_.predict(X)

    # --------------------------
    # NEW: plug-in tau prediction
    # --------------------------
    def predict_tau_plugin(self, X):
        """
        Plug-in CATE based on Stage 1 proxy + averaged Stage 2 corrections:
        tau_hat(x) = mu1_proxy(x)+delta1^T x - [mu0_proxy(x)+delta0^T x]
        
        In Option B (δ₁ = δ₀), this reduces to proxy-only: tau_proxy(x) = mu1_proxy(x) - mu0_proxy(x)
        """
        check_is_fitted(self, 'delta_placebo_')
        X = check_array(X)
        mu0 = self.proxy_models_[0].predict(X) + X @ self.delta_placebo_ + self.intercept_placebo_
        mu1 = self.proxy_models_[1].predict(X) + X @ self.delta_treated_ + self.intercept_treated_
        return mu1 - mu0

    def predict_proxy_only(self, X):
        """Pure proxy CATE (no corrections)"""
        check_is_fitted(self, 'proxy_models_')
        X = check_array(X)
        mu0 = self.proxy_models_[0].predict(X)
        mu1 = self.proxy_models_[1].predict(X)
        return mu1 - mu0

    def get_correction_vectors(self):
        """Inspect learned corrections"""
        check_is_fitted(self, 'delta_placebo_')
        return {
            'delta_placebo': self.delta_placebo_,
            'delta_treated': self.delta_treated_,
            'intercept_placebo': self.intercept_placebo_,
            'intercept_treated': self.intercept_treated_,
            'sparsity_placebo': int(np.sum(np.abs(self.delta_placebo_) > 1e-6)),
            'sparsity_treated': int(np.sum(np.abs(self.delta_treated_) > 1e-6)),
            'disconnected_target': bool(self._is_disconnected_target_)
        }
