"""Pawn blocking (SPBTS) metric implementation."""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .base import AbstractMetric, MetricResult


class PawnBlockingMetric(AbstractMetric):
    """Measures Self-Pawn Block To Start (SPBTS) rates."""

    @property
    def metric_id(self) -> str:
        return "pawn_blocking"

    @property
    def display_name(self) -> str:
        return "Pawn Blocking (SPBTS)"

    @property
    def description(self) -> str:
        return "Rate at which pawns on starting squares get blocked by friendly non-pawn pieces"

    def calculate_for_cohort(self, cohort_df: pd.DataFrame) -> List[float]:
        """Extract all SPBTS values from both white and black sides."""
        values = []

        # Collect white SPBTS values
        if "white_spbts" in cohort_df.columns:
            white_values = cohort_df["white_spbts"].dropna().tolist()
            values.extend(white_values)

        # Collect black SPBTS values
        if "black_spbts" in cohort_df.columns:
            black_values = cohort_df["black_spbts"].dropna().tolist()
            values.extend(black_values)

        return values

    def compare_cohorts(
        self, cohort1_df: pd.DataFrame, cohort2_df: pd.DataFrame, cohort1_id: str, cohort2_id: str
    ) -> MetricResult:
        """Compare pawn blocking rates between two cohorts."""

        cohort1_values = self.calculate_for_cohort(cohort1_df)
        cohort2_values = self.calculate_for_cohort(cohort2_df)

        # Calculate summary statistics
        summary_stats = self._calculate_comparison_stats(cohort1_values, cohort2_values)

        # Prepare visualization data
        viz_data = self._prepare_visualization_data(cohort1_df, cohort2_df, cohort1_id, cohort2_id)

        # Raw data for exports
        raw_data = {
            "cohort1_games": len(cohort1_df),
            "cohort2_games": len(cohort2_df),
            "cohort1_players": len(set(cohort1_df["white_player"]) | set(cohort1_df["black_player"])),
            "cohort2_players": len(set(cohort2_df["white_player"]) | set(cohort2_df["black_player"])),
        }

        return MetricResult(
            metric_id=self.metric_id,
            metric_name=self.display_name,
            cohort1_id=cohort1_id,
            cohort2_id=cohort2_id,
            cohort1_values=cohort1_values,
            cohort2_values=cohort2_values,
            summary_stats=summary_stats,
            visualization_data=viz_data,
            raw_data=raw_data,
        )

    def _calculate_comparison_stats(self, values1: List[float], values2: List[float]) -> Dict[str, Any]:
        """Calculate statistical comparison between two sets of values."""
        if not values1 or not values2:
            return {"error": "Insufficient data for comparison"}

        arr1 = np.array(values1)
        arr2 = np.array(values2)

        return {
            "cohort1_median": float(np.median(arr1)),
            "cohort2_median": float(np.median(arr2)),
            "cohort1_mean": float(np.mean(arr1)),
            "cohort2_mean": float(np.mean(arr2)),
            "median_difference": float(np.median(arr1) - np.median(arr2)),
            "mean_difference": float(np.mean(arr1) - np.mean(arr2)),
            "cohort1_std": float(np.std(arr1)),
            "cohort2_std": float(np.std(arr2)),
            "effect_size": self._calculate_cohens_d(arr1, arr2),
        }

    def _calculate_cohens_d(self, arr1: np.ndarray, arr2: np.ndarray) -> float:
        """Calculate Cohen's d effect size."""
        try:
            pooled_std = np.sqrt(
                ((len(arr1) - 1) * np.var(arr1) + (len(arr2) - 1) * np.var(arr2)) / (len(arr1) + len(arr2) - 2)
            )
            return float((np.mean(arr1) - np.mean(arr2)) / pooled_std)
        except (ZeroDivisionError, ValueError):
            return 0.0

    def _prepare_visualization_data(
        self, cohort1_df: pd.DataFrame, cohort2_df: pd.DataFrame, cohort1_id: str, cohort2_id: str
    ) -> Dict[str, Any]:
        """Prepare data needed for visualizations."""
        viz_data = {"cohort_names": {cohort1_id: cohort1_id, cohort2_id: cohort2_id}, "per_file_data": {}}

        # Extract per-file blocking rates for heatmaps
        for cohort_df, cohort_id in [(cohort1_df, cohort1_id), (cohort2_df, cohort2_id)]:
            file_data = {}
            for file_letter in "abcdefgh":
                white_col = f"white_{file_letter}"
                black_col = f"black_{file_letter}"

                values = []
                if white_col in cohort_df.columns:
                    values.extend(cohort_df[white_col].dropna().tolist())
                if black_col in cohort_df.columns:
                    values.extend(cohort_df[black_col].dropna().tolist())

                if values:
                    file_data[file_letter] = np.mean(values)
                else:
                    file_data[file_letter] = 0.0

            viz_data["per_file_data"][cohort_id] = file_data

        # Aggregate F-pawn fates
        viz_data["f_pawn_fates"] = {}
        for cohort_df, cohort_id in [(cohort1_df, cohort1_id), (cohort2_df, cohort2_id)]:
            aggregated_fates = {
                "never_blocked": 0,
                "push_f3": 0,
                "push_f4": 0,
                "capture_e3": 0,
                "capture_g3": 0,
                "temporary_block": 0,
                "permanent_block": 0,
            }

            # Combine fates from both white and black columns
            for color_prefix in ["white", "black"]:
                fate_col = f"{color_prefix}_f_pawn_fates"
                if fate_col in cohort_df.columns:
                    for row_idx, row in cohort_df.iterrows():
                        fates = row[fate_col]
                        if fates:
                            # Handle both dict and string representations
                            if isinstance(fates, str):
                                try:
                                    import ast

                                    fates = ast.literal_eval(fates)
                                except (ValueError, SyntaxError):
                                    print(f"DEBUG: Parse error on row {row_idx}: {fates}")
                                    continue
                            elif not isinstance(fates, dict):
                                print(f"DEBUG: Row {row_idx} has unexpected type {type(fates)}: {fates}")
                                continue

                            # Check if all expected keys are present
                            missing_keys = set(aggregated_fates.keys()) - set(fates.keys())
                            if missing_keys:
                                print(f"DEBUG: Row {row_idx} missing keys: {missing_keys}")
                                print(f"DEBUG: Row {row_idx} has keys: {list(fates.keys())}")
                                # Add missing keys with 0 count
                                for key in missing_keys:
                                    fates[key] = 0

                            # Now we have a dict with all keys
                            for fate, count in fates.items():
                                if fate in aggregated_fates:
                                    aggregated_fates[fate] += count

            viz_data["f_pawn_fates"][cohort_id] = aggregated_fates

        return viz_data
