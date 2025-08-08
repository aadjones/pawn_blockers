"""Multiple comparison corrections"""

from typing import Dict, List

import numpy as np


def holm_correction(p_values: List[float], alpha: float = 0.05) -> Dict:
    """
    Apply Holm step-down correction for multiple comparisons.

    Args:
        p_values: List of p-values to correct
        alpha: Family-wise error rate

    Returns:
        Dictionary with corrected p-values and significance flags
    """
    p_values = np.array(p_values)
    n = len(p_values)

    if n == 0:
        return {"adjusted_p": [], "significant": []}

    # Sort p-values and track original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Apply Holm correction (step-down)
    adjusted_p = np.zeros_like(sorted_p)
    running_max = 0.0

    for i, p in enumerate(sorted_p):
        # Holm adjustment: multiply by (m - i) where m is total tests
        holm_adjusted = min(1.0, (n - i) * p)
        # Ensure monotonicity (adjusted p-values don't decrease)
        running_max = max(running_max, holm_adjusted)
        adjusted_p[i] = running_max

    # Map back to original order
    final_adjusted = np.zeros_like(p_values)
    final_adjusted[sorted_indices] = adjusted_p

    # Determine significance
    significant = final_adjusted < alpha

    return {
        "adjusted_p": final_adjusted.tolist(),
        "significant": significant.tolist(),
        "alpha": alpha,
        "method": "holm",
    }


def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> Dict:
    """
    Apply Benjamini-Hochberg (FDR) correction.

    Args:
        p_values: List of p-values to correct
        alpha: False discovery rate

    Returns:
        Dictionary with corrected p-values and significance flags
    """
    p_values = np.array(p_values)
    n = len(p_values)

    if n == 0:
        return {"adjusted_p": [], "significant": []}

    # Sort p-values and track original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Apply BH correction
    adjusted_p = np.zeros_like(sorted_p)
    for i, p in enumerate(sorted_p):
        adjusted_p[i] = min(1.0, p * n / (i + 1))

    # Ensure monotonicity (step-up procedure)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])

    # Map back to original order
    final_adjusted = np.zeros_like(p_values)
    final_adjusted[sorted_indices] = adjusted_p

    # Determine significance
    significant = final_adjusted < alpha

    return {
        "adjusted_p": final_adjusted.tolist(),
        "significant": significant.tolist(),
        "alpha": alpha,
        "method": "benjamini_hochberg",
    }
