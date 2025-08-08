"""Multi-cohort data collection pipeline."""

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from ..analysis import AnalysisPipeline
from ..analysis.grouping import GameFilter, PlayerClassifier
from ..data.sources.lichess import LichessClient
from ..data.sources.twic import TWICClient
from .config import CohortConfig, CohortType


class CohortPipeline:
    """Pipeline for collecting and analyzing data from multiple cohorts."""

    def __init__(self, output_dir: str = "data/cohorts", lichess_token: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lichess_token = lichess_token
        self.results = {}

    def collect_cohort_data(self, cohort: CohortConfig) -> pd.DataFrame:
        """Collect data for a single cohort."""
        print(f"🎯 Collecting data for cohort: {cohort.name}")

        # Set up classifier based on cohort configuration
        classifier = self._create_classifier(cohort)

        # Set up game filter
        game_filter = self._create_game_filter(cohort)

        # Create analysis pipeline
        pipeline = AnalysisPipeline()
        pipeline.set_classifier(classifier)
        pipeline.set_game_filter(game_filter)
        pipeline.set_analysis_params(cohort.max_plies, cohort.min_exposure)

        # Add games from data sources
        games_collected = 0
        for source in cohort.data_sources:
            if games_collected >= cohort.target_games:
                break

            remaining_games = cohort.target_games - games_collected
            source_games = self._collect_from_source(source, remaining_games)

            if source_games:
                pipeline.games.extend(source_games)
                games_collected += len(source_games)
                print(f"   ✅ Collected {len(source_games)} games from {source.get('type', 'unknown')}")

        if games_collected == 0:
            print(f"   ⚠️  No games collected for {cohort.id}")
            return pd.DataFrame()

        # Run analysis
        print(f"   🔍 Analyzing {games_collected} games...")
        try:
            pipeline.run_analysis()
            df = pipeline.get_results()

            # Add cohort metadata
            df["cohort_id"] = cohort.id
            df["cohort_name"] = cohort.name
            df["cohort_tags"] = [cohort.tags] * len(df)

            print(f"   ✅ Analysis complete: {len(df)} valid games")
            return df

        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            return pd.DataFrame()

    def _create_classifier(self, cohort: CohortConfig) -> PlayerClassifier:
        """Create player classifier based on cohort config."""
        classifier = PlayerClassifier()

        # Add engine detection if requested
        if cohort.engine_detection:
            classifier.add_engine_rule("engine")

        # Add player pattern matching
        if cohort.player_patterns:
            classifier.add_player_name_rule("target_players", cohort.player_patterns)

        # Add rating-based classification if specified
        if cohort.min_rating or cohort.max_rating:
            min_r = cohort.min_rating or 0
            max_r = cohort.max_rating or 9999
            classifier.add_rating_rule(f"rating_{min_r}_{max_r}", min_r, max_r)

        # Add cohort-specific classification
        classifier.add_rule("cohort_member", lambda game: True)  # All games in cohort

        return classifier

    def _create_game_filter(self, cohort: CohortConfig) -> GameFilter:
        """Create game filter based on cohort config."""
        game_filter = GameFilter()

        # Rating filter
        if cohort.min_rating or cohort.max_rating:
            game_filter.add_rating_filter(cohort.min_rating, cohort.max_rating)

        # Variant filter
        if cohort.variants:
            game_filter.add_variant_filter(cohort.variants)

        # Time control filter
        if cohort.time_controls:
            game_filter.add_time_control_filter(cohort.time_controls)

        return game_filter

    def _collect_from_source(self, source: Dict, max_games: int) -> List[str]:
        """Collect games from a single data source."""
        source_type = source.get("type")

        if source_type == "lichess_user":
            return self._collect_lichess_user(source, max_games)
        elif source_type == "lichess_human_sample":
            return self._collect_lichess_human_sample(source, max_games)
        elif source_type == "twic":
            return self._collect_twic(source, max_games)
        elif source_type == "lichess_query":
            return self._collect_lichess_query(source, max_games)
        elif source_type == "pgn_files":
            return self._collect_pgn_files(source, max_games)
        else:
            print(f"   ⚠️  Unknown source type: {source_type}")
            return []

    def _collect_twic(self, source: Dict, max_games: int) -> List[str]:
        """Collect games from TWIC archive."""
        min_rating = source.get("min_rating", 2000)
        max_issues = source.get("max_issues", 10)

        try:
            client = TWICClient()

            if min_rating > 0:
                games = list(
                    client.download_rating_filtered_games(
                        min_rating=min_rating, max_games=max_games, max_issues=max_issues
                    )
                )
            else:
                games = list(client.download_recent_games(max_games=max_games, max_issues=max_issues))

            return games

        except Exception as e:
            print(f"   ❌ Failed to collect from TWIC: {e}")
            return []

    def _collect_lichess_human_sample(self, source: Dict, max_games: int) -> List[str]:
        """Collect games from a sample of human players."""
        rating_min = source.get("rating_min", 1800)
        rating_max = source.get("rating_max", 2200)
        variant = source.get("variant", "standard")
        players_count = source.get("players_count", 15)
        games_per_player = max(5, max_games // players_count)

        try:
            client = LichessClient(self.lichess_token)
            human_players = client.get_random_human_players(rating_min, rating_max, variant, players_count)

            if not human_players:
                print(f"   ⚠️  No human players found in rating range {rating_min}-{rating_max}")
                return []

            all_games = []
            for username in human_players:
                try:
                    user_games = list(client.stream_user_games(username, games_per_player))
                    all_games.extend(user_games)
                    print(f"   ✅ Collected {len(user_games)} games from {username}")

                    if len(all_games) >= max_games:
                        break

                except Exception as e:
                    print(f"   ⚠️  Failed to collect from {username}: {e}")
                    continue

            return all_games[:max_games]

        except Exception as e:
            print(f"   ❌ Failed to collect human sample: {e}")
            return []

    def _collect_lichess_user(self, source: Dict, max_games: int) -> List[str]:
        """Collect games from a Lichess user."""
        username = source.get("username")
        if not username:
            return []

        try:
            client = LichessClient(self.lichess_token)
            games = list(client.stream_user_games(username, max_games))
            return games
        except Exception as e:
            print(f"   ❌ Failed to collect from {username}: {e}")
            return []

    def _collect_lichess_query(self, source: Dict, max_games: int) -> List[str]:
        """Collect games from Lichess query (placeholder - would need API extension)."""
        print(f"   ⚠️  Lichess query collection not implemented yet")
        # TODO: Implement Lichess database query functionality
        # This would require extending the LichessClient to support:
        # - Rating range queries
        # - Time control queries
        # - Variant-specific queries
        return []

    def _collect_pgn_files(self, source: Dict, max_games: int) -> List[str]:
        """Collect games from PGN files."""
        file_paths = source.get("paths", [])
        games = []

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    with open(path, "r") as f:
                        content = f.read()
                        # Split PGN file into individual games
                        pgn_games = content.split("\n\n[Event ")
                        pgn_games = ["[Event " + game if i > 0 else game for i, game in enumerate(pgn_games)]
                        games.extend(pgn_games[: max_games - len(games)])

                        if len(games) >= max_games:
                            break

            except Exception as e:
                print(f"   ❌ Failed to read {file_path}: {e}")

        return games[:max_games]

    def save_cohort_results(self, cohort_id: str, df: pd.DataFrame):
        """Save cohort results to disk."""
        if df.empty:
            return

        # Save as JSON for the web app
        json_path = self.output_dir / f"{cohort_id}.json"
        with open(json_path, "w") as f:
            json.dump(df.to_dict("records"), f, indent=2, default=str)

        # Save as CSV for analysis
        csv_path = self.output_dir / f"{cohort_id}.csv"
        df.to_csv(csv_path, index=False)

        print(f"   💾 Saved to {json_path} and {csv_path}")

    def load_cohort_results(self, cohort_id: str) -> Optional[pd.DataFrame]:
        """Load existing cohort results from disk."""
        json_path = self.output_dir / f"{cohort_id}.json"

        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                return pd.DataFrame(data)
            except Exception as e:
                print(f"Failed to load {json_path}: {e}")

        return None

    def process_cohorts(self, cohorts: List[CohortConfig], force_refresh: bool = False):
        """Process multiple cohorts, optionally refreshing cached data."""
        # Sort by priority (higher first)
        sorted_cohorts = sorted(cohorts, key=lambda c: c.priority, reverse=True)

        for cohort in sorted_cohorts:
            print(f"\n{'='*60}")
            print(f"Processing cohort: {cohort.name}")
            print(f"{'='*60}")

            # Check if we already have results
            if not force_refresh:
                existing_df = self.load_cohort_results(cohort.id)
                if existing_df is not None and len(existing_df) >= cohort.target_games * 0.8:
                    print(f"   ✅ Using cached results ({len(existing_df)} games)")
                    self.results[cohort.id] = existing_df
                    continue

            # Collect and analyze new data
            df = self.collect_cohort_data(cohort)

            if not df.empty:
                self.save_cohort_results(cohort.id, df)
                self.results[cohort.id] = df
            else:
                print(f"   ❌ No data collected for {cohort.id}")

    def get_results(self) -> Dict[str, pd.DataFrame]:
        """Get all cohort results."""
        return self.results.copy()

    def compare_cohorts(self, cohort_id1: str, cohort_id2: str) -> Dict:
        """Compare two cohorts using existing analysis tools."""
        if cohort_id1 not in self.results or cohort_id2 not in self.results:
            return {"error": "One or both cohorts not found in results"}

        # Combine dataframes and use existing comparison logic
        df1 = self.results[cohort_id1].copy()
        df2 = self.results[cohort_id2].copy()

        # Add cohort identifiers for grouping
        df1["comparison_group"] = cohort_id1
        df2["comparison_group"] = cohort_id2

        combined_df = pd.concat([df1, df2], ignore_index=True)

        from ..analysis.comparisons import compare_groups

        return compare_groups(combined_df, cohort_id1, cohort_id2, group_col="comparison_group")
