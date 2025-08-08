"""End-to-end analysis pipeline"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..data.sources.lichess import LichessClient
from .comparisons import analyze_game_collection, compare_groups
from .grouping import GameFilter, PlayerClassifier


class AnalysisPipeline:
    """Flexible pipeline for chess game analysis."""

    def __init__(self):
        self.games = []
        self.classifier = PlayerClassifier()
        self.game_filter = GameFilter()
        self.results_df = None
        self.max_plies = 24
        self.min_exposure = 64

    def add_games_from_lichess(
        self, username: str, max_games: int = 200, token: Optional[str] = None
    ) -> "AnalysisPipeline":
        """Add games from Lichess user."""
        client = LichessClient(token)
        user_games = list(client.stream_user_games(username, max_games))
        self.games.extend(user_games)
        return self

    def add_games_from_pgn_list(self, pgn_games: List[str]) -> "AnalysisPipeline":
        """Add games from list of PGN strings."""
        self.games.extend(pgn_games)
        return self

    def set_classifier(self, classifier: PlayerClassifier) -> "AnalysisPipeline":
        """Set the player classifier."""
        self.classifier = classifier
        return self

    def set_game_filter(self, game_filter: GameFilter) -> "AnalysisPipeline":
        """Set the game filter."""
        self.game_filter = game_filter
        return self

    def set_analysis_params(self, max_plies: int = 24, min_exposure: int = 64) -> "AnalysisPipeline":
        """Set analysis parameters."""
        self.max_plies = max_plies
        self.min_exposure = min_exposure
        return self

    def run_analysis(self) -> "AnalysisPipeline":
        """Run the analysis on collected games."""
        self.results_df = analyze_game_collection(
            self.games, self.classifier, self.game_filter, self.max_plies, self.min_exposure
        )
        return self

    def get_results(self) -> pd.DataFrame:
        """Get analysis results DataFrame."""
        if self.results_df is None:
            raise ValueError("Must run analysis first")
        return self.results_df

    def compare_groups(self, group1: str, group2: str) -> Dict[str, Any]:
        """Compare two groups from the analysis."""
        if self.results_df is None:
            raise ValueError("Must run analysis first")
        return compare_groups(self.results_df, group1, group2)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the analysis."""
        if self.results_df is None:
            raise ValueError("Must run analysis first")

        df = self.results_df
        return {
            "total_games": len(df),
            "unique_players": len(set(df["white_player"]) | set(df["black_player"])),
            "avg_plies_analyzed": df["plies_analyzed"].mean(),
            "group_distribution": self._get_group_distribution(),
            "spbts_overall": {
                "white_median": df["white_spbts"].median(),
                "black_median": df["black_spbts"].median(),
                "white_mean": df["white_spbts"].mean(),
                "black_mean": df["black_spbts"].mean(),
            },
        }

    def _get_group_distribution(self) -> Dict[str, int]:
        """Count games per group."""
        from collections import Counter

        all_groups = []
        for groups_list in self.results_df["all_groups"]:
            all_groups.extend(groups_list)
        return dict(Counter(all_groups))
