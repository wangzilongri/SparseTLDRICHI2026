"""
IHDP Multi-Site Generator

Constructs multi-site structure from IHDP data by clustering covariates,
enabling evaluation of transfer learning methods with real covariates
and known ground-truth treatment effects.

The key idea: partition IHDP subjects into "sites" via k-means clustering
on covariates, which naturally induces covariate shift between sites.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import warnings

try:
    from .ihdp_data import IHDPDataLoader, IHDPRealization
except ImportError:
    from ihdp_data import IHDPDataLoader, IHDPRealization


@dataclass
class IHDPMultiSiteData:
    """Container for multi-site IHDP data matching benchmark interface."""
    # Source data (all sites except target)
    X_source: np.ndarray      # (n_source, p)
    A_source: np.ndarray      # (n_source,) treatment indicator
    Y_source: np.ndarray      # (n_source,) observed outcome
    c_source: np.ndarray      # (n_source,) site indicator (1, 2, ..., C)
    
    # Target data
    X_target: np.ndarray      # (n_target, p)
    A_target: np.ndarray      # (n_target,) treatment indicator
    Y_target: np.ndarray      # (n_target,) observed outcome
    
    # Ground truth for evaluation
    tau_true_target: np.ndarray  # (n_target,) true CATE on target
    mu0_true_target: np.ndarray  # (n_target,) true mu_0 on target
    mu1_true_target: np.ndarray  # (n_target,) true mu_1 on target
    ate_true_target: float       # True ATE on target
    
    # Full ground truth (for diagnostics)
    tau_true_source: np.ndarray  # (n_source,) true CATE on sources
    
    # Metadata
    n_sites: int
    site_sizes: Dict[int, int]
    realization_id: int
    
    @property
    def propensity_target(self) -> np.ndarray:
        """Return known propensity (treatment is randomized in IHDP benchmark)."""
        # IHDP uses ~18% treatment rate, but for benchmarking we treat as 0.5
        # Actually, compute empirical propensity from source data
        return np.full(len(self.A_target), 0.5)
    
    @property
    def n_target(self) -> int:
        return len(self.X_target)
    
    @property
    def m0(self) -> int:
        """Number of target placebo samples."""
        return int(np.sum(self.A_target == 0))
    
    @property
    def m1(self) -> int:
        """Number of target treated samples."""
        return int(np.sum(self.A_target == 1))


class IHDPMultiSiteGenerator:
    """
    Constructs multi-site structure from IHDP data via k-means clustering.
    
    This enables:
    1. Testing transfer learning with real covariate distributions
    2. Known ground-truth for CATE evaluation
    3. Controllable covariate shift (via clustering)
    4. Both connected (Option A) and disconnected (Option B) regimes
    """
    
    def __init__(
        self,
        n_sites: int = 6,
        target_site_idx: Optional[int] = None,
        data_dir: Optional[str] = None,
        random_state: int = 42,
        standardize_for_clustering: bool = True,
        min_treated_per_site: int = 5,
    ):
        """
        Initialize multi-site generator.
        
        Args:
            n_sites: Total number of sites (1 target + n_sites-1 sources)
            target_site_idx: Which cluster becomes target. If None, automatically
                           select the cluster with most treated units.
            data_dir: Path to IHDP data directory
            random_state: Random seed for reproducibility
            standardize_for_clustering: Whether to standardize X before k-means
            min_treated_per_site: Minimum treated units required per site
        """
        self.n_sites = n_sites
        self.target_site_idx = target_site_idx
        self.random_state = random_state
        self.standardize_for_clustering = standardize_for_clustering
        self.min_treated_per_site = min_treated_per_site
        
        self.loader = IHDPDataLoader(data_dir)
        self._cluster_cache: Dict[int, np.ndarray] = {}
    
    def _get_site_assignments(
        self, 
        X: np.ndarray, 
        realization_id: int
    ) -> np.ndarray:
        """
        Assign subjects to sites via k-means clustering.
        
        Returns:
            site_ids: (n,) array with values 0, 1, ..., n_sites-1
        """
        cache_key = (realization_id, self.n_sites, self.random_state)
        
        # Use cached assignments if available
        if cache_key in self._cluster_cache:
            return self._cluster_cache[cache_key]
        
        # Standardize features for clustering
        if self.standardize_for_clustering:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # K-means clustering
        kmeans = KMeans(
            n_clusters=self.n_sites,
            random_state=self.random_state,
            n_init=10
        )
        site_ids = kmeans.fit_predict(X_scaled)
        
        self._cluster_cache[cache_key] = site_ids
        return site_ids
    
    def _select_target_site(
        self, 
        site_ids: np.ndarray, 
        treatment: np.ndarray,
        m1_requested: Optional[int]
    ) -> int:
        """
        Select best cluster to use as target site.
        
        If m1_requested == 0 (disconnected), select cluster with most control units.
        Otherwise, select cluster with most treated units to enable Option A.
        """
        if self.target_site_idx is not None:
            return self.target_site_idx
        
        unique_sites = np.unique(site_ids)
        
        if m1_requested == 0:
            # Disconnected regime: prioritize control units
            best_site = max(
                unique_sites,
                key=lambda s: np.sum((site_ids == s) & (treatment == 0))
            )
        else:
            # Connected regime: need both arms, prioritize treated (scarcer)
            best_site = max(
                unique_sites,
                key=lambda s: np.sum((site_ids == s) & (treatment == 1))
            )
        
        return best_site
    
    def generate(
        self,
        realization_id: int = 1,
        m0: Optional[int] = None,
        m1: Optional[int] = None,
        balance_treatment: bool = True,
    ) -> IHDPMultiSiteData:
        """
        Generate multi-site data from one IHDP realization.
        
        Args:
            realization_id: Which IHDP realization to use (1-50)
            m0: Target placebo sample size (None = use all available)
            m1: Target treated sample size (0 = disconnected regime, None = all)
            balance_treatment: Whether to balance treatment in subsampling
            
        Returns:
            IHDPMultiSiteData matching benchmark interface
        """
        rng = np.random.RandomState(self.random_state + realization_id)
        
        # Load IHDP realization
        ihdp = self.loader.load_realization(realization_id)
        
        # Assign to sites via clustering
        site_ids = self._get_site_assignments(ihdp.X, realization_id)
        
        # Select target site (auto-select if not specified)
        target_site = self._select_target_site(site_ids, ihdp.t, m1)
        
        # Separate target and source
        target_mask = (site_ids == target_site)
        source_mask = ~target_mask
        
        # Source data (all non-target sites)
        X_source = ihdp.X[source_mask]
        A_source = ihdp.t[source_mask]
        Y_source = ihdp.y[source_mask]
        tau_source = ihdp.tau_true[source_mask]
        
        # Remap source site IDs to 1, 2, ..., n_sites-1
        source_site_ids = site_ids[source_mask]
        unique_source_sites = np.unique(source_site_ids)
        site_mapping = {old: new + 1 for new, old in enumerate(unique_source_sites)}
        c_source = np.array([site_mapping[s] for s in source_site_ids])
        
        # Target data
        target_indices = np.where(target_mask)[0]
        X_target_full = ihdp.X[target_mask]
        A_target_full = ihdp.t[target_mask]
        Y_target_full = ihdp.y[target_mask]
        tau_target_full = ihdp.tau_true[target_mask]
        mu0_target_full = ihdp.mu_0[target_mask]
        mu1_target_full = ihdp.mu_1[target_mask]
        
        # Subsample target if requested
        if m0 is not None or m1 is not None:
            X_target, A_target, Y_target, tau_target, mu0_target, mu1_target = \
                self._subsample_target(
                    X_target_full, A_target_full, Y_target_full,
                    tau_target_full, mu0_target_full, mu1_target_full,
                    m0, m1, rng, balance_treatment
                )
        else:
            X_target = X_target_full
            A_target = A_target_full
            Y_target = Y_target_full
            tau_target = tau_target_full
            mu0_target = mu0_target_full
            mu1_target = mu1_target_full
        
        # Compute site sizes
        site_sizes = {0: len(X_target)}
        for site_id in np.unique(c_source):
            site_sizes[site_id] = int(np.sum(c_source == site_id))
        
        return IHDPMultiSiteData(
            X_source=X_source,
            A_source=A_source,
            Y_source=Y_source,
            c_source=c_source,
            X_target=X_target,
            A_target=A_target,
            Y_target=Y_target,
            tau_true_target=tau_target,
            mu0_true_target=mu0_target,
            mu1_true_target=mu1_target,
            ate_true_target=float(np.mean(tau_target)),
            tau_true_source=tau_source,
            n_sites=self.n_sites,
            site_sizes=site_sizes,
            realization_id=realization_id,
        )
    
    def _subsample_target(
        self,
        X: np.ndarray,
        A: np.ndarray,
        Y: np.ndarray,
        tau: np.ndarray,
        mu0: np.ndarray,
        mu1: np.ndarray,
        m0: Optional[int],
        m1: Optional[int],
        rng: np.random.RandomState,
        balance_treatment: bool,
    ) -> Tuple[np.ndarray, ...]:
        """Subsample target to specified (m0, m1) budget."""
        
        control_idx = np.where(A == 0)[0]
        treated_idx = np.where(A == 1)[0]
        
        n_control = len(control_idx)
        n_treated = len(treated_idx)
        
        # Determine actual sample sizes
        if m0 is None:
            m0_actual = n_control
        else:
            m0_actual = min(m0, n_control)
            if m0 > n_control:
                warnings.warn(f"Requested m0={m0} but only {n_control} controls available")
        
        if m1 is None:
            m1_actual = n_treated
        elif m1 == 0:
            m1_actual = 0  # Disconnected regime
        else:
            m1_actual = min(m1, n_treated)
            if m1 > n_treated:
                warnings.warn(f"Requested m1={m1} but only {n_treated} treated available")
        
        # Subsample
        if m0_actual < n_control:
            selected_control = rng.choice(control_idx, size=m0_actual, replace=False)
        else:
            selected_control = control_idx
        
        if m1_actual == 0:
            selected_treated = np.array([], dtype=int)
        elif m1_actual < n_treated:
            selected_treated = rng.choice(treated_idx, size=m1_actual, replace=False)
        else:
            selected_treated = treated_idx
        
        # Combine and sort
        selected = np.concatenate([selected_control, selected_treated])
        selected = np.sort(selected)
        
        return (
            X[selected],
            A[selected],
            Y[selected],
            tau[selected],
            mu0[selected],
            mu1[selected],
        )
    
    def compute_covariate_shift_auc(self, data: IHDPMultiSiteData) -> float:
        """
        Compute AUC of classifier predicting target vs source.
        Higher AUC = stronger covariate shift.
        """
        from sklearn.linear_model import LogisticRegression
        
        X_all = np.vstack([data.X_source, data.X_target])
        y_site = np.concatenate([
            np.zeros(len(data.X_source)),
            np.ones(len(data.X_target))
        ])
        
        clf = LogisticRegression(max_iter=1000, random_state=self.random_state)
        clf.fit(X_all, y_site)
        probs = clf.predict_proba(X_all)[:, 1]
        
        return roc_auc_score(y_site, probs)
    
    def summarize(self, data: IHDPMultiSiteData) -> str:
        """Generate summary of multi-site data."""
        lines = [
            f"IHDP Multi-Site Data Summary",
            f"=" * 40,
            f"Realization: {data.realization_id}",
            f"Total sites: {data.n_sites}",
            f"",
            f"Source data:",
            f"  - Samples: {len(data.X_source)}",
            f"  - Sites: {len(np.unique(data.c_source))}",
            f"  - Treatment rate: {data.A_source.mean():.3f}",
            f"",
            f"Target data:",
            f"  - Samples: {data.n_target}",
            f"  - m0 (placebo): {data.m0}",
            f"  - m1 (treated): {data.m1}",
            f"  - True ATE: {data.ate_true_target:.3f}",
            f"",
            f"Site sizes: {data.site_sizes}",
        ]
        
        try:
            auc = self.compute_covariate_shift_auc(data)
            lines.append(f"Covariate shift AUC: {auc:.3f}")
        except Exception:
            pass
        
        return "\n".join(lines)


def generate_ihdp_multisite(
    realization_id: int = 1,
    n_sites: int = 6,
    m0: Optional[int] = None,
    m1: Optional[int] = None,
    random_state: int = 42,
    data_dir: Optional[str] = None,
) -> IHDPMultiSiteData:
    """
    Convenience function to generate multi-site IHDP data.
    
    Args:
        realization_id: IHDP realization (1-50)
        n_sites: Number of sites (1 target + sources)
        m0: Target placebo budget (None = all)
        m1: Target treated budget (0 = disconnected, None = all)
        random_state: Random seed
        data_dir: Path to IHDP data
        
    Returns:
        IHDPMultiSiteData object
    """
    generator = IHDPMultiSiteGenerator(
        n_sites=n_sites,
        random_state=random_state,
        data_dir=data_dir,
    )
    return generator.generate(
        realization_id=realization_id,
        m0=m0,
        m1=m1,
    )


if __name__ == "__main__":
    # Test multi-site generation
    generator = IHDPMultiSiteGenerator(n_sites=6)
    
    # Connected regime
    print("=" * 50)
    print("Connected regime (m0=50, m1=50)")
    print("=" * 50)
    data_connected = generator.generate(realization_id=1, m0=50, m1=50)
    print(generator.summarize(data_connected))
    
    print()
    
    # Disconnected regime
    print("=" * 50)
    print("Disconnected regime (m0=50, m1=0)")
    print("=" * 50)
    data_disconnected = generator.generate(realization_id=1, m0=50, m1=0)
    print(generator.summarize(data_disconnected))
