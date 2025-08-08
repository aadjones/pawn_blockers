"""Base classes for chess game metrics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd


@dataclass
class MetricResult:
    """Result of a metric comparison between cohorts."""

    metric_id: str
    metric_name: str
    cohort1_id: str
    cohort2_id: str
    cohort1_values: List[float]
    cohort2_values: List[float]
    summary_stats: Dict[str, Any]
    visualization_data: Dict[str, Any]
    raw_data: Dict[str, Any]


class AbstractMetric(ABC):
    """Base class for chess game metrics."""

    @property
    @abstractmethod
    def metric_id(self) -> str:
        """Unique identifier for this metric."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI display."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this metric measures."""
        pass

    @abstractmethod
    def calculate_for_cohort(self, cohort_df: pd.DataFrame) -> List[float]:
        """
        Calculate metric values for all games in a cohort.

        Args:
            cohort_df: DataFrame with analyzed games from a cohort

        Returns:
            List of metric values, one per game or position
        """
        pass

    @abstractmethod
    def compare_cohorts(
        self, cohort1_df: pd.DataFrame, cohort2_df: pd.DataFrame, cohort1_id: str, cohort2_id: str
    ) -> MetricResult:
        """
        Compare this metric between two cohorts.

        Args:
            cohort1_df: First cohort data
            cohort2_df: Second cohort data
            cohort1_id: First cohort identifier
            cohort2_id: Second cohort identifier

        Returns:
            MetricResult with comparison data and visualizations
        """
        pass

    def get_summary_for_cohort(self, cohort_df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for a single cohort."""
        values = self.calculate_for_cohort(cohort_df)
        if not values:
            return {"count": 0, "mean": 0, "median": 0}

        import numpy as np

        return {
            "count": len(values),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }
