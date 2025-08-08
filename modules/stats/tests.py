"""Statistical test functions"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .corrections import holm_correction


def wilcoxon_test(
    group1_values: List[float], group2_values: List[float], alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test on paired data.

    Args:
        group1_values: First group values
        group2_values: Second group values (must be same length)
        alternative: "two-sided", "less", or "greater"

    Returns:
        (statistic, p_value)
    """
    if len(group1_values) != len(group2_values):
        raise ValueError("Groups must have same length for paired test")

    if len(group1_values) < 3:
        return np.nan, np.nan

    try:
        stat, p_value = wilcoxon(group1_values, group2_values, alternative=alternative)
        return float(stat), float(p_value)
    except ValueError:
        return np.nan, np.nan


def per_file_analysis(
    df: pd.DataFrame,
    group1_prefix: str = "leela",
    group2_prefix: str = "human",
    alternative: str = "two-sided",
    apply_correction: bool = True,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Analyze per-file blocking rates with statistical tests.

    Args:
        df: DataFrame with per-file columns (e.g., "leela_a", "human_a")
        group1_prefix: Prefix for first group columns
        group2_prefix: Prefix for second group columns
        alternative: Statistical test alternative
        apply_correction: Whether to apply multiple comparison correction
        alpha: Significance level

    Returns:
        DataFrame with per-file analysis results
    """
    files = "abcdefgh"
    results = []
    p_values = []

    for file_letter in files:
        col1 = f"{group1_prefix}_{file_letter}"
        col2 = f"{group2_prefix}_{file_letter}"

        if col1 not in df.columns or col2 not in df.columns:
            continue

        # Get paired data (both values non-null)
        mask = df[col1].notna() & df[col2].notna()
        pairs = mask.sum()

        if pairs < 10:  # Minimum sample size
            result = {
                "file": file_letter,
                "pairs": pairs,
                "group1_median": np.nan,
                "group2_median": np.nan,
                "difference": np.nan,
                "p_value": np.nan,
                "significant": False,
            }
        else:
            vals1 = df.loc[mask, col1]
            vals2 = df.loc[mask, col2]

            median1 = vals1.median()
            median2 = vals2.median()
            diff = median1 - median2

            stat, p_val = wilcoxon_test(vals1.tolist(), vals2.tolist(), alternative)
            p_values.append(p_val)

            result = {
                "file": file_letter,
                "pairs": pairs,
                "group1_median": round(median1, 3),
                "group2_median": round(median2, 3),
                "difference": round(diff, 3),
                "p_value": p_val,
                "significant": False,  # Will be set after correction
            }

        results.append(result)

    results_df = pd.DataFrame(results)

    # Apply multiple comparison correction
    if apply_correction and p_values:
        finite_p_values = [(i, p) for i, p in enumerate(p_values) if np.isfinite(p)]

        if finite_p_values:
            corrected = holm_correction([p for _, p in finite_p_values], alpha)

            for (original_idx, _), corrected_p, is_sig in zip(
                finite_p_values, corrected["adjusted_p"], corrected["significant"]
            ):
                results_df.at[original_idx, "p_adjusted"] = corrected_p
                results_df.at[original_idx, "significant"] = is_sig

    return results_df


def effect_size_analysis(group1_values: List[float], group2_values: List[float]) -> Dict[str, float]:
    """
    Calculate effect size measures for paired comparison.

    Args:
        group1_values: First group values
        group2_values: Second group values

    Returns:
        Dictionary with effect size metrics
    """
    if len(group1_values) != len(group2_values):
        raise ValueError("Groups must have same length")

    differences = np.array(group1_values) - np.array(group2_values)

    return {
        "mean_difference": float(np.mean(differences)),
        "median_difference": float(np.median(differences)),
        "std_difference": float(np.std(differences)),
        "cohen_d": float(np.mean(differences) / np.std(differences)) if np.std(differences) > 0 else 0.0,
        "effect_size_r": float(np.corrcoef(group1_values, group2_values)[0, 1]) if len(group1_values) > 1 else 0.0,
    }
