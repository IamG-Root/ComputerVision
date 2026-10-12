"""Gated assignment with explicit unmatched choices (no zero padding)."""
import numpy as np
from munkres import Munkres


def assign(costs, limit):
    costs = np.asarray(costs, dtype=float)
    if costs.ndim != 2 or not all(costs.shape):
        return []
    n, m = costs.shape
    # Each row has its own dummy; real matches are cheaper than unmatched.
    matrix = np.full((n + m, n + m), 1e9)
    matrix[:n, :m] = np.where(np.isfinite(costs) & (costs <= limit), costs, 1e9)
    matrix[:n, m:] = limit + 1
    matrix[n:, :m] = limit + 1
    matrix[n:, m:] = 0
    return [(i, j) for i, j in Munkres().compute(matrix.tolist())
            if i < n and j < m and matrix[i, j] <= limit]
