"""
IHDP Data Loader

Loads and processes IHDP (Infant Health and Development Program) semi-synthetic data
for causal inference benchmarking.

Data format (from NPCI benchmark):
- Column 0: Treatment indicator t (0/1)
- Column 1: Observed outcome y
- Column 2: Counterfactual outcome y_cf
- Column 3: True mu_0 (potential outcome under control)
- Column 4: True mu_1 (potential outcome under treatment)
- Columns 5+: 25 covariates (19 binary, 6 continuous)

Ground-truth CATE: tau(x) = mu_1 - mu_0
"""

import numpy as np
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict


@dataclass
class IHDPRealization:
    """Container for one IHDP realization."""
    X: np.ndarray          # (n, p) covariates
    t: np.ndarray          # (n,) treatment indicator
    y: np.ndarray          # (n,) observed outcome
    y_cf: np.ndarray       # (n,) counterfactual outcome
    mu_0: np.ndarray       # (n,) true E[Y(0)|X]
    mu_1: np.ndarray       # (n,) true E[Y(1)|X]
    tau_true: np.ndarray   # (n,) true CATE = mu_1 - mu_0
    realization_id: int    # Which realization (1-50)
    
    @property
    def n_samples(self) -> int:
        return self.X.shape[0]
    
    @property
    def n_features(self) -> int:
        return self.X.shape[1]
    
    @property
    def ate_true(self) -> float:
        """True average treatment effect."""
        return float(np.mean(self.tau_true))
    
    def get_observed_outcomes(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get Y(0) and Y(1) for each unit based on treatment assignment."""
        Y0 = np.where(self.t == 0, self.y, self.y_cf)
        Y1 = np.where(self.t == 1, self.y, self.y_cf)
        return Y0, Y1


class IHDPDataLoader:
    """
    Loader for IHDP semi-synthetic benchmark data.
    
    IHDP contains 50 realizations of semi-synthetic data with:
    - Real covariates from the Infant Health and Development Program
    - Simulated potential outcomes with known ground truth
    
    This enables exact evaluation of CATE estimation methods.
    """
    
    # Default path relative to project root
    DEFAULT_DATA_DIR = "L1-TCL/dat/ihdp/csv"
    
    # Covariate indices
    BINARY_FEATURES = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    CONTINUOUS_FEATURES = [0, 1, 2, 3, 4, 5]
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize IHDP data loader.
        
        Args:
            data_dir: Path to directory containing ihdp_npci_*.csv files.
                     If None, uses default path relative to project root.
        """
        if data_dir is None:
            # Find project root (parent of src/)
            src_dir = Path(__file__).parent
            project_root = src_dir.parent
            self.data_dir = project_root / self.DEFAULT_DATA_DIR
        else:
            self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"IHDP data directory not found: {self.data_dir}\n"
                f"Expected CSV files at: {self.data_dir}/ihdp_npci_*.csv"
            )
    
    def _get_file_path(self, realization_id: int) -> Path:
        """Get path to specific realization file."""
        if not 1 <= realization_id <= 50:
            raise ValueError(f"realization_id must be 1-50, got {realization_id}")
        return self.data_dir / f"ihdp_npci_{realization_id}.csv"
    
    def load_realization(self, realization_id: int) -> IHDPRealization:
        """
        Load one IHDP realization.
        
        Args:
            realization_id: Realization number (1-50)
            
        Returns:
            IHDPRealization containing all data and ground truth
        """
        file_path = self._get_file_path(realization_id)
        
        if not file_path.exists():
            raise FileNotFoundError(f"IHDP file not found: {file_path}")
        
        # Load raw data
        data = np.loadtxt(file_path, delimiter=',')
        
        # Parse columns
        t = data[:, 0].astype(int)
        y = data[:, 1]
        y_cf = data[:, 2]
        mu_0 = data[:, 3]
        mu_1 = data[:, 4]
        X = data[:, 5:]
        
        # Compute ground-truth CATE
        tau_true = mu_1 - mu_0
        
        # Reorder features: binary first, then continuous (standard IHDP convention)
        perm = self.BINARY_FEATURES + self.CONTINUOUS_FEATURES
        # But the raw X already has 25 features indexed 0-24 after column 5
        # The perm indices are relative to original columns 5+
        # So we need to adjust: columns 5-29 in original become 0-24 in X
        # perm values 6-24 refer to original columns 11-29, which are X columns 6-24
        # perm values 0-5 refer to original columns 5-10, which are X columns 0-5
        # So perm should be applied to X directly
        X_reordered = X[:, [i for i in range(25)]]  # Keep original order for now
        
        return IHDPRealization(
            X=X_reordered,
            t=t,
            y=y,
            y_cf=y_cf,
            mu_0=mu_0,
            mu_1=mu_1,
            tau_true=tau_true,
            realization_id=realization_id
        )
    
    def load_all_realizations(self) -> Dict[int, IHDPRealization]:
        """Load all 50 realizations."""
        return {i: self.load_realization(i) for i in range(1, 51)}
    
    def get_available_realizations(self) -> list:
        """Get list of available realization IDs."""
        available = []
        for i in range(1, 51):
            if self._get_file_path(i).exists():
                available.append(i)
        return available
    
    def summarize(self) -> str:
        """Print summary of available data."""
        available = self.get_available_realizations()
        
        if not available:
            return f"No IHDP data found in {self.data_dir}"
        
        # Load first realization for stats
        first = self.load_realization(available[0])
        
        lines = [
            f"IHDP Data Summary",
            f"=" * 40,
            f"Data directory: {self.data_dir}",
            f"Available realizations: {len(available)} (IDs: {min(available)}-{max(available)})",
            f"Samples per realization: {first.n_samples}",
            f"Features: {first.n_features} (19 binary, 6 continuous)",
            f"",
            f"First realization stats:",
            f"  - Treatment rate: {first.t.mean():.3f}",
            f"  - True ATE: {first.ate_true:.3f}",
            f"  - CATE range: [{first.tau_true.min():.3f}, {first.tau_true.max():.3f}]",
        ]
        
        return "\n".join(lines)


def load_ihdp(realization_id: int = 1, data_dir: Optional[str] = None) -> IHDPRealization:
    """
    Convenience function to load one IHDP realization.
    
    Args:
        realization_id: Realization number (1-50)
        data_dir: Optional path to data directory
        
    Returns:
        IHDPRealization object
    """
    loader = IHDPDataLoader(data_dir)
    return loader.load_realization(realization_id)


if __name__ == "__main__":
    # Test loading
    loader = IHDPDataLoader()
    print(loader.summarize())
    print()
    
    # Load and inspect first realization
    real1 = loader.load_realization(1)
    print(f"Realization 1:")
    print(f"  X shape: {real1.X.shape}")
    print(f"  Treatment counts: {np.bincount(real1.t)}")
    print(f"  Y range: [{real1.y.min():.2f}, {real1.y.max():.2f}]")
    print(f"  True ATE: {real1.ate_true:.3f}")
