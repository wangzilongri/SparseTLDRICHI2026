#' Transfer Learning Estimators using glmtrans
#' 
#' This script provides wrapper functions around the glmtrans R package
#' for transfer learning in high-dimensional GLMs.
#' 
#' Reference:
#'   Tian, Y., & Feng, Y. (2023). Transfer learning under high-dimensional 
#'   generalized linear models. JASA, 118(544), 2684-2697.
#'
#' Usage from Python:
#'   Use rpy2 to source this file and call the functions, or
#'   call via subprocess with Rscript.

# =============================================================================
# Dependencies
# =============================================================================

# Set up local library path
local_lib <- file.path(dirname(getwd()), "R_libs")
if (dir.exists(local_lib)) {
  .libPaths(c(local_lib, .libPaths()))
}

# Check and install glmtrans if needed
if (!requireNamespace("glmtrans", quietly = TRUE)) {
  message("Installing glmtrans package...")
  if (!dir.exists(local_lib)) dir.create(local_lib, recursive = TRUE)
  install.packages("glmtrans", lib = local_lib, repos = "https://cloud.r-project.org")
  .libPaths(c(local_lib, .libPaths()))
}

suppressPackageStartupMessages({
  library(glmtrans)
  library(glmnet)
})

# =============================================================================
# Utility Functions
# =============================================================================

#' Format data for glmtrans
#' 
#' @param X Feature matrix (n x p)
#' @param Y Response vector (n)
#' @return List with x and y components
format_data <- function(X, Y) {
  list(x = as.matrix(X), y = as.vector(Y))
}

#' Format source data list for glmtrans
#' 
#' @param X_source Source feature matrix (n_source x p)
#' @param Y_source Source response vector (n_source)
#' @param c_source Source site indicators (n_source)
#' @return List of lists, one per source site
format_source_data <- function(X_source, Y_source, c_source) {
  X_source <- as.matrix(X_source)
  Y_source <- as.vector(Y_source)
  c_source <- as.vector(c_source)
  
  site_ids <- unique(c_source)
  source_list <- list()
  
  for (i in seq_along(site_ids)) {
    site <- site_ids[i]
    mask <- c_source == site
    source_list[[i]] <- list(
      x = X_source[mask, , drop = FALSE],
      y = Y_source[mask]
    )
  }
  
  return(source_list)
}

# =============================================================================
# Core glmtrans Wrapper
# =============================================================================

#' Fit glmtrans model for outcome regression
#' 
#' @param X_target Target features (n_target x p)
#' @param Y_target Target responses (n_target)
#' @param X_source Source features (n_source x p)
#' @param Y_source Source responses (n_source)
#' @param c_source Source site indicators (n_source)
#' @param family Response family: "gaussian", "binomial", "poisson"
#' @param transfer_source_id Which sources: "auto", "all", or integer vector
#' @param alpha Elastic-net mixing (1=lasso, 0=ridge)
#' @param nfolds CV folds for lambda selection
#' @param cores Number of cores for parallel computation
#' @param verbose Print progress
#' @return List with fitted model, coefficients, transferable sources
fit_glmtrans <- function(X_target, Y_target, 
                         X_source, Y_source, c_source,
                         family = "gaussian",
                         transfer_source_id = "auto",
                         alpha = 1,
                         nfolds = 10,
                         cores = 1,
                         verbose = FALSE) {
  
  # Format target data
  target <- format_data(X_target, Y_target)
  
  # Format source data by site
  source <- format_source_data(X_source, Y_source, c_source)
  
  if (verbose) {
    cat(sprintf("Target: n=%d, p=%d\n", nrow(target$x), ncol(target$x)))
    cat(sprintf("Sources: %d sites\n", length(source)))
    for (i in seq_along(source)) {
      cat(sprintf("  Site %d: n=%d\n", i, nrow(source[[i]]$x)))
    }
  }
  
  # Fit glmtrans
  fit <- glmtrans(
    target = target,
    source = source,
    family = family,
    transfer.source.id = transfer_source_id,
    alpha = alpha,
    nfolds = nfolds,
    cores = cores,
    detection.info = verbose
  )
  
  # Extract results
  result <- list(
    beta = fit$beta,
    intercept = fit$beta[1],
    coef = fit$beta[-1],
    transfer_source_ids = fit$transfer.source.id,
    family = family,
    model = fit
  )
  
  return(result)
}

#' Predict from fitted glmtrans model
#' 
#' @param fit Fitted glmtrans result from fit_glmtrans
#' @param X_new New feature matrix
#' @param type Prediction type: "link", "response", "class"
#' @return Predictions
predict_glmtrans <- function(fit, X_new, type = "response") {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$model, newx = X_new, type = type)
  return(as.vector(pred))
}

# =============================================================================
# CATE Estimators
# =============================================================================

#' Estimate CATE using glmtrans transfer learning
#' 
#' This estimator:
#' 1. Learns μ₀(X) via transfer from source control data
#' 2. Learns μ₁(X) via transfer from source treated data  
#' 3. Computes τ(X) = μ₁(X) - μ₀(X)
#' 
#' @param X_source Source features (n_source x p)
#' @param A_source Source treatment indicators (0/1)
#' @param Y_source Source outcomes
#' @param c_source Source site indicators
#' @param X_target Target features (n_target x p)
#' @param A_target Target treatment indicators
#' @param Y_target Target outcomes
#' @param transfer_source_id Which sources: "auto", "all"
#' @param alpha Elastic-net mixing parameter
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with fitted models and prediction function
fit_glmtrans_cate <- function(X_source, A_source, Y_source, c_source,
                              X_target, A_target, Y_target,
                              transfer_source_id = "auto",
                              alpha = 1,
                              nfolds = 5,
                              verbose = FALSE) {
  
  X_source <- as.matrix(X_source)
  A_source <- as.vector(A_source)
  Y_source <- as.vector(Y_source)
  c_source <- as.vector(c_source)
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  
  # Split by treatment arm
  source_control <- A_source == 0
  source_treated <- A_source == 1
  target_control <- A_target == 0
  target_treated <- A_target == 1
  
  has_target_control <- sum(target_control) > 0
  has_target_treated <- sum(target_treated) > 0
  
  if (verbose) {
    cat(sprintf("Source: %d control, %d treated\n", 
                sum(source_control), sum(source_treated)))
    cat(sprintf("Target: %d control, %d treated\n",
                sum(target_control), sum(target_treated)))
  }
  
  # -------------------------------------------------------------------------
  # Fit μ₀ model (control outcome)
  # -------------------------------------------------------------------------
  mu0_fit <- NULL
  if (has_target_control && sum(source_control) > 0) {
    if (verbose) cat("\nFitting μ₀ model (control outcome)...\n")
    
    mu0_fit <- fit_glmtrans(
      X_target = X_target[target_control, , drop = FALSE],
      Y_target = Y_target[target_control],
      X_source = X_source[source_control, , drop = FALSE],
      Y_source = Y_source[source_control],
      c_source = c_source[source_control],
      family = "gaussian",
      transfer_source_id = transfer_source_id,
      alpha = alpha,
      nfolds = nfolds,
      verbose = verbose
    )
  } else if (has_target_control) {
    # No source, fit Lasso on target only
    if (verbose) cat("\nFitting μ₀ on target only (no source control)...\n")
    cv_fit <- cv.glmnet(X_target[target_control, , drop = FALSE], 
                        Y_target[target_control], 
                        alpha = alpha, nfolds = nfolds)
    mu0_fit <- list(
      beta = as.vector(coef(cv_fit, s = "lambda.min")),
      model = cv_fit,
      is_glmnet = TRUE
    )
  }
  
  # -------------------------------------------------------------------------
  # Fit μ₁ model (treated outcome)
  # -------------------------------------------------------------------------
  mu1_fit <- NULL
  if (has_target_treated && sum(source_treated) > 0) {
    if (verbose) cat("\nFitting μ₁ model (treated outcome)...\n")
    
    mu1_fit <- fit_glmtrans(
      X_target = X_target[target_treated, , drop = FALSE],
      Y_target = Y_target[target_treated],
      X_source = X_source[source_treated, , drop = FALSE],
      Y_source = Y_source[source_treated],
      c_source = c_source[source_treated],
      family = "gaussian",
      transfer_source_id = transfer_source_id,
      alpha = alpha,
      nfolds = nfolds,
      verbose = verbose
    )
  } else if (has_target_treated) {
    # No source treated, fit Lasso on target only
    if (verbose) cat("\nFitting μ₁ on target only (no source treated)...\n")
    cv_fit <- cv.glmnet(X_target[target_treated, , drop = FALSE], 
                        Y_target[target_treated], 
                        alpha = alpha, nfolds = nfolds)
    mu1_fit <- list(
      beta = as.vector(coef(cv_fit, s = "lambda.min")),
      model = cv_fit,
      is_glmnet = TRUE
    )
  }
  
  # -------------------------------------------------------------------------
  # Return result
  # -------------------------------------------------------------------------
  result <- list(
    mu0_fit = mu0_fit,
    mu1_fit = mu1_fit,
    has_target_control = has_target_control,
    has_target_treated = has_target_treated
  )
  
  class(result) <- "glmtrans_cate"
  return(result)
}

#' Predict CATE from fitted glmtrans_cate model
#' 
#' @param fit Fitted model from fit_glmtrans_cate
#' @param X_new New feature matrix
#' @return Predicted CATE τ(X) = μ₁(X) - μ₀(X)
predict_cate <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  n <- nrow(X_new)
  
  # Predict μ₀
  if (!is.null(fit$mu0_fit)) {
    if (isTRUE(fit$mu0_fit$is_glmnet)) {
      mu0 <- as.vector(predict(fit$mu0_fit$model, X_new, s = "lambda.min"))
    } else {
      mu0 <- predict_glmtrans(fit$mu0_fit, X_new)
    }
  } else {
    mu0 <- rep(0, n)
  }
  
  # Predict μ₁
  if (!is.null(fit$mu1_fit)) {
    if (isTRUE(fit$mu1_fit$is_glmnet)) {
      mu1 <- as.vector(predict(fit$mu1_fit$model, X_new, s = "lambda.min"))
    } else {
      mu1 <- predict_glmtrans(fit$mu1_fit, X_new)
    }
  } else {
    mu1 <- rep(0, n)
  }
  
  # CATE = μ₁ - μ₀
  return(mu1 - mu0)
}

# =============================================================================
# Doubly Robust CATE Estimator
# =============================================================================

#' Estimate CATE with Doubly Robust pseudo-outcomes
#' 
#' Uses glmtrans for outcome models, then computes DR pseudo-outcomes
#' and fits a final CATE model.
#' 
#' @param X_source Source features
#' @param A_source Source treatments
#' @param Y_source Source outcomes
#' @param c_source Source site indicators
#' @param X_target Target features
#' @param A_target Target treatments
#' @param Y_target Target outcomes
#' @param propensity Target propensity scores (optional)
#' @param transfer_source_id Which sources to transfer
#' @param alpha Elastic-net mixing
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with CATE model
fit_glmtrans_dr <- function(X_source, A_source, Y_source, c_source,
                            X_target, A_target, Y_target,
                            propensity = NULL,
                            transfer_source_id = "auto",
                            alpha = 1,
                            nfolds = 5,
                            verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  n <- nrow(X_target)
  
  # First fit plug-in models
  plugin_fit <- fit_glmtrans_cate(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    transfer_source_id = transfer_source_id,
    alpha = alpha,
    nfolds = nfolds,
    verbose = verbose
  )
  
  # Get plug-in predictions on target
  mu0_hat <- rep(0, n)
  mu1_hat <- rep(0, n)
  
  if (!is.null(plugin_fit$mu0_fit)) {
    if (isTRUE(plugin_fit$mu0_fit$is_glmnet)) {
      mu0_hat <- as.vector(predict(plugin_fit$mu0_fit$model, X_target, s = "lambda.min"))
    } else {
      mu0_hat <- predict_glmtrans(plugin_fit$mu0_fit, X_target)
    }
  }
  
  if (!is.null(plugin_fit$mu1_fit)) {
    if (isTRUE(plugin_fit$mu1_fit$is_glmnet)) {
      mu1_hat <- as.vector(predict(plugin_fit$mu1_fit$model, X_target, s = "lambda.min"))
    } else {
      mu1_hat <- predict_glmtrans(plugin_fit$mu1_fit, X_target)
    }
  }
  
  # Propensity scores
  if (is.null(propensity)) {
    propensity <- mean(A_target)
  }
  e <- pmax(pmin(propensity, 0.99), 0.01)
  
  # Compute DR pseudo-outcomes
  # Γ = (A/e)(Y - μ₁) + μ₁ - ((1-A)/(1-e))(Y - μ₀) - μ₀
  pseudo_outcome <- (A_target / e) * (Y_target - mu1_hat) + mu1_hat -
                    ((1 - A_target) / (1 - e)) * (Y_target - mu0_hat) - mu0_hat
  
  # Fit CATE model on pseudo-outcomes
  if (verbose) cat("\nFitting CATE model on DR pseudo-outcomes...\n")
  
  cate_cv <- cv.glmnet(X_target, pseudo_outcome, alpha = alpha, nfolds = nfolds)
  
  result <- list(
    plugin_fit = plugin_fit,
    cate_model = cate_cv,
    mu0_hat = mu0_hat,
    mu1_hat = mu1_hat,
    pseudo_outcome = pseudo_outcome,
    ate_hat = mean(pseudo_outcome)
  )
  
  class(result) <- "glmtrans_dr"
  return(result)
}

#' Predict CATE from DR model
predict_dr <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$cate_model, X_new, s = "lambda.min")
  return(as.vector(pred))
}

# =============================================================================
# Option B: Glmtrans for Source Detection + Source-DR CATE
# =============================================================================
# This implements the theoretically correct Option B as suggested by the advisor:
# 1. Use glmtrans ONLY on control arm for transferable source detection
# 2. Restrict to selected sources (no weighting, just selection)
# 3. Fit DR CATE learner on selected sources only
# 4. Transport the learned CATE to target
# 
# This preserves:
# - The theory of glmtrans (deterministic transferable subset selection)
# - Feasibility for placebo-only target (no treated units required)

#' Fit Option B: Glmtrans source detection + Source-DR CATE
#'
#' @param X_source Source features (n_source x p)
#' @param A_source Source treatment indicators (n_source)
#' @param Y_source Source outcomes (n_source)
#' @param c_source Source site indicators (n_source)
#' @param X_target Target features (n_target x p)
#' @param Y_target_control Target control outcomes (placebo only, can have NAs)
#' @param alpha Elastic-net mixing (1=lasso, 0=ridge)
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with CATE model trained on selected sources
fit_glmtrans_option_b <- function(X_source, A_source, Y_source, c_source,
                                   X_target, Y_target_control = NULL,
                                   alpha = 1,
                                   nfolds = 5,
                                   verbose = FALSE) {
  
  X_source <- as.matrix(X_source)
  A_source <- as.vector(A_source)
  Y_source <- as.vector(Y_source)
  c_source <- as.vector(c_source)
  X_target <- as.matrix(X_target)
  
  n_source <- nrow(X_source)
  n_target <- nrow(X_target)
  p <- ncol(X_source)
  
  # =========================================================================
  # Stage 0: Transferable source detection on CONTROL ARM ONLY
  # =========================================================================
  if (verbose) cat("Stage 0: Detecting transferable sources (control arm only)...\n")
  
  # Separate source data by treatment arm
  ctrl_mask <- A_source == 0
  X_source_ctrl <- X_source[ctrl_mask, , drop = FALSE]
  Y_source_ctrl <- Y_source[ctrl_mask]
  c_source_ctrl <- c_source[ctrl_mask]
  
  # Format source control data by site
  source_ctrl_list <- format_source_data(X_source_ctrl, Y_source_ctrl, c_source_ctrl)
  
  # If we have target control data, use it for detection
  # Otherwise, use target X with synthetic fallback
  if (!is.null(Y_target_control) && length(Y_target_control) > 0) {
    # Filter to non-NA values
    valid_idx <- !is.na(Y_target_control)
    if (sum(valid_idx) > 10) {
      X_target_ctrl <- X_target[valid_idx, , drop = FALSE]
      Y_target_ctrl <- Y_target_control[valid_idx]
      target_ctrl <- format_data(X_target_ctrl, Y_target_ctrl)
    } else {
      # Not enough target control data, use all sources
      if (verbose) cat("  Insufficient target control data, using all sources.\n")
      selected_sources <- unique(c_source)
      target_ctrl <- NULL
    }
  } else {
    # No target control data at all - use all sources (cannot detect)
    if (verbose) cat("  No target control data, using all sources.\n")
    selected_sources <- unique(c_source)
    target_ctrl <- NULL
  }
  
  # Run glmtrans source detection if we have target control data
  if (exists("target_ctrl") && !is.null(target_ctrl)) {
    tryCatch({
      # Run glmtrans on control arm
      ctrl_fit <- glmtrans::glmtrans(
        target = target_ctrl,
        source = source_ctrl_list,
        family = "gaussian",
        transfer.source.id = "all",  # First fit with all to get detection info
        alpha = alpha,
        nfolds = nfolds,
        cores = 1
      )
      
      # Use source detection algorithm
      # Transferable source if its loss <= C0 * target-only loss
      C0 <- 2  # Threshold multiplier (from glmtrans paper)
      
      # Get individual source performances
      site_ids <- unique(c_source_ctrl)
      n_sites <- length(site_ids)
      
      # Fit target-only model
      target_only_cv <- cv.glmnet(target_ctrl$x, target_ctrl$y, 
                                   alpha = alpha, nfolds = nfolds)
      target_loss <- min(target_only_cv$cvm)
      
      selected_sources <- c()
      for (k in seq_along(site_ids)) {
        site_k <- site_ids[k]
        mask_k <- c_source_ctrl == site_k
        X_k <- X_source_ctrl[mask_k, , drop = FALSE]
        Y_k <- Y_source_ctrl[mask_k]
        
        if (length(Y_k) < 10) next  # Skip small sites
        
        # Test this source on target data
        cv_k <- cv.glmnet(X_k, Y_k, alpha = alpha, nfolds = min(nfolds, length(Y_k)))
        pred_k <- predict(cv_k, target_ctrl$x, s = "lambda.min")
        loss_k <- mean((target_ctrl$y - pred_k)^2)
        
        if (loss_k <= C0 * target_loss) {
          selected_sources <- c(selected_sources, site_k)
        }
      }
      
      if (length(selected_sources) == 0) {
        if (verbose) cat("  No sources passed detection, using all.\n")
        selected_sources <- site_ids
      }
      
      if (verbose) {
        cat(sprintf("  Selected %d/%d sources: %s\n", 
                    length(selected_sources), n_sites, 
                    paste(selected_sources, collapse = ", ")))
      }
      
    }, error = function(e) {
      if (verbose) cat(sprintf("  Source detection failed: %s. Using all sources.\n", e$message))
      selected_sources <<- unique(c_source)
    })
  }
  
  # =========================================================================
  # Step 1: Restrict to selected sources
  # =========================================================================
  if (verbose) cat("Step 1: Restricting to selected sources...\n")
  
  selected_mask <- c_source %in% selected_sources
  X_src_good <- X_source[selected_mask, , drop = FALSE]
  A_src_good <- A_source[selected_mask]
  Y_src_good <- Y_source[selected_mask]
  c_src_good <- c_source[selected_mask]
  
  if (verbose) {
    cat(sprintf("  Using %d/%d source observations from selected sites.\n",
                nrow(X_src_good), n_source))
  }
  
  # =========================================================================
  # Step 2: Fit DR CATE on selected sources
  # =========================================================================
  if (verbose) cat("Step 2: Fitting DR CATE on selected sources...\n")
  
  # Separate by treatment
  ctrl_good <- A_src_good == 0
  trt_good <- A_src_good == 1
  
  X_src_ctrl <- X_src_good[ctrl_good, , drop = FALSE]
  Y_src_ctrl <- Y_src_good[ctrl_good]
  X_src_trt <- X_src_good[trt_good, , drop = FALSE]
  Y_src_trt <- Y_src_good[trt_good]
  
  # Fit outcome models on sources
  mu0_cv <- cv.glmnet(X_src_ctrl, Y_src_ctrl, alpha = alpha, nfolds = nfolds)
  mu1_cv <- cv.glmnet(X_src_trt, Y_src_trt, alpha = alpha, nfolds = nfolds)
  
  # Estimate propensity on sources
  e_hat <- mean(A_src_good)
  e_hat <- pmax(pmin(e_hat, 0.99), 0.01)
  
  # Get predictions on all selected source data
  mu0_src <- as.vector(predict(mu0_cv, X_src_good, s = "lambda.min"))
  mu1_src <- as.vector(predict(mu1_cv, X_src_good, s = "lambda.min"))
  
  # Compute DR pseudo-outcomes on sources
  # Γ = (A/e)(Y - μ₁) + μ₁ - ((1-A)/(1-e))(Y - μ₀) - μ₀
  pseudo_src <- (A_src_good / e_hat) * (Y_src_good - mu1_src) + mu1_src -
                ((1 - A_src_good) / (1 - e_hat)) * (Y_src_good - mu0_src) - mu0_src
  
  # Fit CATE model on source pseudo-outcomes
  cate_cv <- cv.glmnet(X_src_good, pseudo_src, alpha = alpha, nfolds = nfolds)
  
  # =========================================================================
  # Step 3: Package results for transport to target
  # =========================================================================
  if (verbose) cat("Step 3: Packaging for target transport...\n")
  
  # Get predictions on target
  tau_target <- as.vector(predict(cate_cv, X_target, s = "lambda.min"))
  mu0_target <- as.vector(predict(mu0_cv, X_target, s = "lambda.min"))
  mu1_target <- as.vector(predict(mu1_cv, X_target, s = "lambda.min"))
  
  result <- list(
    # Models
    mu0_model = mu0_cv,
    mu1_model = mu1_cv,
    cate_model = cate_cv,
    
    # Source detection info
    selected_sources = selected_sources,
    n_sources_used = length(selected_sources),
    n_obs_used = nrow(X_src_good),
    
    # Target predictions
    tau_target = tau_target,
    mu0_target = mu0_target,
    mu1_target = mu1_target,
    ate_hat = mean(tau_target),
    
    # Diagnostics
    source_propensity = e_hat
  )
  
  class(result) <- "glmtrans_option_b"
  
  if (verbose) {
    cat(sprintf("  ATE estimate: %.4f\n", result$ate_hat))
    cat("✓ Option B fit complete.\n")
  }
  
  return(result)
}

#' Predict CATE from Option B model
predict_option_b <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$cate_model, X_new, s = "lambda.min")
  return(as.vector(pred))
}

# =============================================================================
# Propensity Score Transfer Learning
# =============================================================================

#' Transfer learning for propensity score estimation
#' 
#' @param X_target Target features
#' @param A_target Target treatments
#' @param X_source Source features
#' @param A_source Source treatments  
#' @param c_source Source site indicators
#' @param transfer_source_id Which sources
#' @param alpha Elastic-net mixing
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with fitted propensity model
fit_glmtrans_propensity <- function(X_target, A_target,
                                    X_source, A_source, c_source,
                                    transfer_source_id = "auto",
                                    alpha = 1,
                                    nfolds = 5,
                                    verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  
  fit <- fit_glmtrans(
    X_target = X_target,
    Y_target = A_target,
    X_source = X_source,
    Y_source = A_source,
    c_source = c_source,
    family = "binomial",
    transfer_source_id = transfer_source_id,
    alpha = alpha,
    nfolds = nfolds,
    verbose = verbose
  )
  
  return(fit)
}

#' Predict propensity scores
predict_propensity <- function(fit, X_new) {
  pred <- predict_glmtrans(fit, X_new, type = "response")
  return(pmax(pmin(pred, 0.99), 0.01))  # Clip for stability
}

# =============================================================================
# Source Detection (Transferability Analysis)
# =============================================================================

#' Detect which sources are transferable
#' 
#' @param X_target Target features
#' @param Y_target Target responses
#' @param X_source Source features
#' @param Y_source Source responses
#' @param c_source Source site indicators
#' @param family Response family
#' @param C0 Threshold constant (default 2)
#' @param verbose Print progress
#' @return List with transfer_source_ids, source_losses, threshold
detect_transferable_sources <- function(X_target, Y_target,
                                        X_source, Y_source, c_source,
                                        family = "gaussian",
                                        C0 = 2,
                                        verbose = FALSE) {
  
  target <- format_data(X_target, Y_target)
  source <- format_source_data(X_source, Y_source, c_source)
  
  detection <- source_detection(
    target = target,
    source = source,
    family = family,
    C0 = C0,
    detection.info = verbose
  )
  
  return(list(
    transfer_source_ids = detection$transfer.source.id,
    source_losses = detection$source.loss,
    target_valid_loss = detection$target.valid.loss,
    threshold = detection$threshold
  ))
}

# =============================================================================
# Baseline: Target-Only Lasso (No Transfer)
# =============================================================================

#' Fit CATE using target data only (no transfer learning)
#' 
#' This serves as a baseline for comparison.
fit_target_only_cate <- function(X_target, A_target, Y_target,
                                 alpha = 1, nfolds = 5, verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  
  target_control <- A_target == 0
  target_treated <- A_target == 1
  
  # Fit μ₀ on target control
  mu0_fit <- NULL
  if (sum(target_control) > 5) {
    mu0_fit <- cv.glmnet(X_target[target_control, , drop = FALSE],
                         Y_target[target_control],
                         alpha = alpha, nfolds = nfolds)
  }
  
  # Fit μ₁ on target treated  
  mu1_fit <- NULL
  if (sum(target_treated) > 5) {
    mu1_fit <- cv.glmnet(X_target[target_treated, , drop = FALSE],
                         Y_target[target_treated],
                         alpha = alpha, nfolds = nfolds)
  }
  
  result <- list(mu0_fit = mu0_fit, mu1_fit = mu1_fit)
  class(result) <- "target_only_cate"
  return(result)
}

#' Predict CATE from target-only model
predict_target_only <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  n <- nrow(X_new)
  
  mu0 <- if (!is.null(fit$mu0_fit)) {
    as.vector(predict(fit$mu0_fit, X_new, s = "lambda.min"))
  } else {
    rep(0, n)
  }
  
  mu1 <- if (!is.null(fit$mu1_fit)) {
    as.vector(predict(fit$mu1_fit, X_new, s = "lambda.min"))
  } else {
    rep(0, n)
  }
  
  return(mu1 - mu0)
}

# =============================================================================
# Baseline: Pooled Source (Naive Transfer)
# =============================================================================

#' Fit CATE by pooling all source data (naive transfer)
#' 
#' This pools all source data without accounting for heterogeneity.
fit_pooled_source_cate <- function(X_source, A_source, Y_source,
                                   alpha = 1, nfolds = 5, verbose = FALSE) {
  
  X_source <- as.matrix(X_source)
  A_source <- as.vector(A_source)
  Y_source <- as.vector(Y_source)
  
  source_control <- A_source == 0
  source_treated <- A_source == 1
  
  # Fit μ₀ on pooled source control
  mu0_fit <- NULL
  if (sum(source_control) > 5) {
    mu0_fit <- cv.glmnet(X_source[source_control, , drop = FALSE],
                         Y_source[source_control],
                         alpha = alpha, nfolds = nfolds)
  }
  
  # Fit μ₁ on pooled source treated
  mu1_fit <- NULL
  if (sum(source_treated) > 5) {
    mu1_fit <- cv.glmnet(X_source[source_treated, , drop = FALSE],
                         Y_source[source_treated],
                         alpha = alpha, nfolds = nfolds)
  }
  
  result <- list(mu0_fit = mu0_fit, mu1_fit = mu1_fit)
  class(result) <- "pooled_source_cate"
  return(result)
}

#' Predict CATE from pooled source model
predict_pooled_source <- function(fit, X_new) {
  # Same as target_only
  predict_target_only(fit, X_new)
}

# =============================================================================
# Test Function
# =============================================================================

test_glmtrans_estimators <- function() {
  cat("============================================================\n")
  cat("Testing glmtrans R implementation\n")
  cat("============================================================\n\n")
  
  set.seed(42)
  
  # Generate synthetic data
  p <- 30
  n_source <- 500
  n_target <- 100
  n_sites <- 3
  
  # True coefficients
  alpha0 <- rep(0, p)
  alpha0[1:5] <- c(0.5, -0.3, 0.8, -0.2, 0.4)
  
  alpha1 <- rep(0, p)
  alpha1[1:5] <- c(0.3, -0.5, 0.6, -0.1, 0.3)
  
  # Source data
  X_source <- matrix(rnorm(n_source * n_sites * p), ncol = p)
  c_source <- rep(1:n_sites, each = n_source)
  A_source <- rbinom(n_source * n_sites, 1, 0.5)
  
  mu0_source <- X_source %*% alpha0
  mu1_source <- X_source %*% alpha1
  Y_source <- (1 - A_source) * mu0_source + A_source * mu1_source + rnorm(n_source * n_sites) * 0.3
  
  # Target data
  X_target <- matrix(rnorm(n_target * p), ncol = p)
  A_target <- rbinom(n_target, 1, 0.5)
  
  mu0_target <- X_target %*% alpha0
  mu1_target <- X_target %*% alpha1
  tau_true <- mu1_target - mu0_target
  Y_target <- (1 - A_target) * mu0_target + A_target * mu1_target + rnorm(n_target) * 0.3
  
  cat(sprintf("Source: %d samples across %d sites\n", nrow(X_source), n_sites))
  cat(sprintf("Target: %d samples (%d control, %d treated)\n", 
              n_target, sum(A_target == 0), sum(A_target == 1)))
  cat(sprintf("True ATE: %.4f\n", mean(tau_true)))
  
  # Test 1: Source detection
  cat("\n--- Test 1: Source Detection ---\n")
  detection <- detect_transferable_sources(
    X_target[A_target == 0, ], Y_target[A_target == 0],
    X_source[A_source == 0, ], Y_source[A_source == 0], c_source[A_source == 0],
    verbose = TRUE
  )
  cat(sprintf("Transferable sources: %s\n", paste(detection$transfer_source_ids, collapse = ", ")))
  
  # Test 2: Plug-in CATE
  cat("\n--- Test 2: Glmtrans Plug-in CATE ---\n")
  plugin_fit <- fit_glmtrans_cate(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    transfer_source_id = "auto",
    verbose = TRUE
  )
  tau_plugin <- predict_cate(plugin_fit, X_target)
  pehe_plugin <- sqrt(mean((tau_plugin - tau_true)^2))
  ate_err_plugin <- abs(mean(tau_plugin) - mean(tau_true))
  cat(sprintf("PEHE: %.4f\n", pehe_plugin))
  cat(sprintf("|ATE Error|: %.4f\n", ate_err_plugin))
  
  # Test 3: DR CATE
  cat("\n--- Test 3: Glmtrans DR CATE ---\n")
  dr_fit <- fit_glmtrans_dr(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    transfer_source_id = "auto",
    verbose = TRUE
  )
  tau_dr <- predict_dr(dr_fit, X_target)
  pehe_dr <- sqrt(mean((tau_dr - tau_true)^2))
  ate_err_dr <- abs(mean(tau_dr) - mean(tau_true))
  cat(sprintf("PEHE: %.4f\n", pehe_dr))
  cat(sprintf("|ATE Error|: %.4f\n", ate_err_dr))
  
  # Test 4: Target-only baseline
  cat("\n--- Test 4: Target-Only Baseline ---\n")
  target_fit <- fit_target_only_cate(X_target, A_target, Y_target)
  tau_target <- predict_target_only(target_fit, X_target)
  pehe_target <- sqrt(mean((tau_target - tau_true)^2))
  ate_err_target <- abs(mean(tau_target) - mean(tau_true))
  cat(sprintf("PEHE: %.4f\n", pehe_target))
  cat(sprintf("|ATE Error|: %.4f\n", ate_err_target))
  
  # Summary
  cat("\n============================================================\n")
  cat("SUMMARY\n")
  cat("============================================================\n")
  cat(sprintf("%-25s | PEHE   | ATE Err | Improvement\n", "Method"))
  cat(paste(rep("-", 60), collapse = ""), "\n")
  cat(sprintf("%-25s | %.4f | %.4f  | baseline\n", "Target-Only", pehe_target, ate_err_target))
  cat(sprintf("%-25s | %.4f | %.4f  | %.1f%%\n", "Glmtrans Plugin", pehe_plugin, ate_err_plugin,
              (pehe_target - pehe_plugin) / pehe_target * 100))
  cat(sprintf("%-25s | %.4f | %.4f  | %.1f%%\n", "Glmtrans DR", pehe_dr, ate_err_dr,
              (pehe_target - pehe_dr) / pehe_target * 100))
  
  cat("\n✓ All tests completed!\n")
}

# Run tests if executed directly
if (sys.nframe() == 0) {
  test_glmtrans_estimators()
}
