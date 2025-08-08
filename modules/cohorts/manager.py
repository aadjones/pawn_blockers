"""Cohort management and coordination."""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .config import CohortConfig, CohortConfigManager, create_example_configs
from .pipeline import CohortPipeline


class CohortManager:
    """High-level manager for cohort-based analysis."""

    def __init__(
        self, config_dir: str = "config/cohorts", data_dir: str = "data/cohorts", lichess_token: Optional[str] = None
    ):
        self.config_manager = CohortConfigManager(config_dir)
        self.pipeline = CohortPipeline(data_dir, lichess_token)

        # Create example configs if none exist
        if not self.config_manager.list_cohorts():
            self._create_default_configs()

        # Load existing results from disk
        self._load_existing_results()

    def _create_default_configs(self):
        """Create default cohort configurations."""
        print("🏗️  Creating default cohort configurations...")

        example_configs = create_example_configs()
        for config in example_configs:
            self.config_manager.save_cohort(config)

        print(f"   ✅ Created {len(example_configs)} default cohorts")

    def _load_existing_results(self):
        """Load existing results from disk for all configured cohorts."""
        cohorts = self.config_manager.list_cohorts()
        for cohort in cohorts:
            df = self.pipeline.load_cohort_results(cohort.id)
            if df is not None:
                self.pipeline.results[cohort.id] = df

    def list_available_cohorts(self) -> List[CohortConfig]:
        """List all available cohort configurations."""
        return self.config_manager.list_cohorts()

    def get_cohort_by_id(self, cohort_id: str) -> Optional[CohortConfig]:
        """Get a specific cohort configuration."""
        return self.config_manager.get_cohort(cohort_id)

    def process_cohort(self, cohort_id: str, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """Process a single cohort and return results."""
        cohort = self.config_manager.get_cohort(cohort_id)
        if not cohort:
            print(f"❌ Cohort '{cohort_id}' not found")
            return None

        self.pipeline.process_cohorts([cohort], force_refresh)
        return self.pipeline.results.get(cohort_id)

    def process_cohorts_by_tag(self, tag: str, force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        """Process all cohorts with a specific tag."""
        cohorts = self.config_manager.get_cohorts_by_tag(tag)
        if not cohorts:
            print(f"❌ No cohorts found with tag '{tag}'")
            return {}

        self.pipeline.process_cohorts(cohorts, force_refresh)
        return {c.id: self.pipeline.results.get(c.id) for c in cohorts if c.id in self.pipeline.results}

    def process_all_cohorts(self, force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        """Process all available cohorts."""
        cohorts = self.config_manager.list_cohorts()
        if not cohorts:
            print("❌ No cohorts configured")
            return {}

        self.pipeline.process_cohorts(cohorts, force_refresh)
        return self.pipeline.get_results()

    def compare_cohorts(self, cohort_id1: str, cohort_id2: str) -> Dict:
        """Compare two cohorts."""
        return self.pipeline.compare_cohorts(cohort_id1, cohort_id2)

    def get_cohort_summary(self, cohort_id: str) -> Dict:
        """Get summary statistics for a cohort."""
        results = self.pipeline.results.get(cohort_id)
        if results is None or results.empty:
            return {"error": f"No results found for cohort '{cohort_id}'"}

        df = results
        return {
            "cohort_id": cohort_id,
            "total_games": len(df),
            "unique_players": len(set(df["white_player"]) | set(df["black_player"])),
            "avg_plies_analyzed": df["plies_analyzed"].mean(),
            "spbts_stats": {
                "white_median": df["white_spbts"].median(),
                "black_median": df["black_spbts"].median(),
                "white_mean": df["white_spbts"].mean(),
                "black_mean": df["black_spbts"].mean(),
                "f_file_mean": df.get("white_f", pd.Series()).mean() if "white_f" in df.columns else None,
            },
            "date_range": {
                "earliest": df["date"].min() if "date" in df.columns else None,
                "latest": df["date"].max() if "date" in df.columns else None,
            },
        }

    def create_cohort(self, config: CohortConfig):
        """Create and save a new cohort configuration."""
        self.config_manager.save_cohort(config)

    def update_cohort(self, cohort_id: str, **updates):
        """Update an existing cohort configuration."""
        cohort = self.config_manager.get_cohort(cohort_id)
        if not cohort:
            raise ValueError(f"Cohort '{cohort_id}' not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(cohort, key):
                setattr(cohort, key, value)

        self.config_manager.save_cohort(cohort)

    def delete_cohort_data(self, cohort_id: str):
        """Delete cached data for a cohort."""
        data_dir = Path(self.pipeline.output_dir)

        json_file = data_dir / f"{cohort_id}.json"
        csv_file = data_dir / f"{cohort_id}.csv"

        deleted = []
        for file_path in [json_file, csv_file]:
            if file_path.exists():
                file_path.unlink()
                deleted.append(str(file_path))

        # Remove from memory
        if cohort_id in self.pipeline.results:
            del self.pipeline.results[cohort_id]

        return deleted

    def get_status(self) -> Dict:
        """Get overall status of cohort system."""
        cohorts = self.config_manager.list_cohorts()
        results = self.pipeline.get_results()

        cohort_status = []
        for cohort in cohorts:
            df = results.get(cohort.id)
            status = {
                "id": cohort.id,
                "name": cohort.name,
                "target_games": cohort.target_games,
                "collected_games": len(df) if df is not None else 0,
                "progress": (len(df) / cohort.target_games * 100) if df is not None and cohort.target_games > 0 else 0,
                "tags": cohort.tags,
                "priority": cohort.priority,
            }
            cohort_status.append(status)

        return {
            "total_cohorts": len(cohorts),
            "active_cohorts": len(results),
            "total_games": sum(len(df) for df in results.values()),
            "cohorts": cohort_status,
        }
