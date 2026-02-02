#!/usr/bin/env python3
"""
Databricks-friendly wrapper for running core sweep benchmarks.

This script simply shells out to:
    python experiments/core_sweeps.py [args...]

Usage examples:
    python scripts/run_sweeps_databricks.py --sweep gold --n_rep 50 --n_jobs -1
    python scripts/run_sweeps_databricks.py --sweep all --n_rep 20 --parallel_sweeps
"""

import argparse
import os
import subprocess
import sys
from typing import List


def _repo_root() -> str:
    """Resolve repo root relative to this script."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _build_command(args: argparse.Namespace) -> List[str]:
    """Construct the core_sweeps.py command."""
    cmd = [
        sys.executable,
        os.path.join(_repo_root(), "experiments", "core_sweeps.py"),
        "--sweep",
        args.sweep,
        "--n_rep",
        str(args.n_rep),
        "--seed",
        str(args.seed),
        "--output",
        args.output,
        "--n_jobs",
        str(args.n_jobs),
    ]

    if args.methods:
        cmd.extend(["--methods"] + args.methods)
    if args.parallel_sweeps:
        cmd.append("--parallel_sweeps")
    if args.quiet:
        cmd.append("--quiet")

    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Databricks wrapper for core sweep benchmarks"
    )
    parser.add_argument(
        "--sweep",
        type=str,
        default="all",
        choices=["gold", "proxy", "imbalance", "all"],
        help="Sweep to run (default: all)",
    )
    parser.add_argument(
        "--n_rep",
        type=int,
        default=20,
        help="Number of Monte Carlo reps (default: 20)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Master seed (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/sweeps",
        help="Output directory (default: results/sweeps)",
    )
    parser.add_argument(
        "--methods",
        type=str,
        nargs="+",
        default=None,
        help="Methods to run (default: all standard methods)",
    )
    parser.add_argument(
        "--n_jobs",
        type=int,
        default=1,
        help="Parallel jobs: 1=sequential, -1=all cores, N=use N cores",
    )
    parser.add_argument(
        "--parallel_sweeps",
        action="store_true",
        help="Run sweeps in parallel (only when --sweep all)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    default_args = [
        "--sweep", "all",
        "--n_rep", "20",
        "--n_jobs", "-1",
    ]
    args = parser.parse_args(default_args if len(sys.argv) == 1 else None)
    cmd = _build_command(args)

    # Run from repo root so relative paths resolve in Databricks
    cwd = _repo_root()
    print("Running:", " ".join(cmd))
    print("Working dir:", cwd)

    completed = subprocess.run(cmd, cwd=cwd, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
