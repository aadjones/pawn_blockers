"""Flexible player and game classification system"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import pandas as pd


@dataclass
class GameInfo:
    """Container for game information used in classification."""

    white_player: str
    black_player: str
    white_elo: Optional[int]
    black_elo: Optional[int]
    time_control: Optional[str]
    variant: str
    metadata: Dict[str, Any]


class PlayerClassifier:
    """Flexible system for classifying players into groups."""

    def __init__(self):
        self.rules = []
        self.engine_patterns = [
            "leela",
            "stockfish",
            "komodo",
            "houdini",
            "fire",
            "dragon",
            "lc0",
            "sf",
            "bot",
            "engine",
            "computer",
        ]

    def add_rule(self, name: str, classifier_func: Callable[[GameInfo], bool]) -> "PlayerClassifier":
        """
        Add a classification rule.

        Args:
            name: Name of the classification group
            classifier_func: Function that takes GameInfo and returns True if match

        Returns:
            Self for method chaining
        """
        self.rules.append((name, classifier_func))
        return self

    def add_engine_rule(self, name: str = "engine") -> "PlayerClassifier":
        """Add rule to identify chess engines."""

        def is_engine(game: GameInfo) -> bool:
            white_lower = game.white_player.lower()
            black_lower = game.black_player.lower()
            return any(pattern in white_lower or pattern in black_lower for pattern in self.engine_patterns)

        return self.add_rule(name, is_engine)

    def add_rating_rule(self, name: str, min_rating: int, max_rating: int = 9999) -> "PlayerClassifier":
        """Add rule based on rating range."""

        def rating_match(game: GameInfo) -> bool:
            ratings = [r for r in [game.white_elo, game.black_elo] if r is not None]
            if not ratings:
                return False
            max_rating_in_game = max(ratings)
            return min_rating <= max_rating_in_game <= max_rating

        return self.add_rule(name, rating_match)

    def add_player_name_rule(self, name: str, player_names: List[str]) -> "PlayerClassifier":
        """Add rule for specific player names."""
        player_set = {p.lower() for p in player_names}

        def name_match(game: GameInfo) -> bool:
            return game.white_player.lower() in player_set or game.black_player.lower() in player_set

        return self.add_rule(name, name_match)

    def classify_game(self, game: GameInfo) -> List[str]:
        """
        Classify a game according to all rules.

        Returns:
            List of group names that match this game
        """
        matches = []
        for name, rule_func in self.rules:
            if rule_func(game):
                matches.append(name)
        return matches


class GameFilter:
    """Filter games based on various criteria."""

    def __init__(self):
        self.filters = []

    def add_variant_filter(self, variants: List[str]) -> "GameFilter":
        """Filter by chess variant."""
        variant_set = {v.lower() for v in variants}

        def variant_match(game: GameInfo) -> bool:
            return game.variant.lower() in variant_set

        self.filters.append(variant_match)
        return self

    def add_time_control_filter(self, time_controls: List[str]) -> "GameFilter":
        """Filter by time control patterns."""

        def time_match(game: GameInfo) -> bool:
            if game.time_control is None:
                return False
            return any(tc in game.time_control for tc in time_controls)

        self.filters.append(time_match)
        return self

    def add_rating_filter(self, min_rating: Optional[int] = None, max_rating: Optional[int] = None) -> "GameFilter":
        """Filter by rating range."""

        def rating_filter(game: GameInfo) -> bool:
            ratings = [r for r in [game.white_elo, game.black_elo] if r is not None]
            if not ratings:
                return min_rating is None  # Accept games without ratings only if no min specified

            max_game_rating = max(ratings)
            if min_rating is not None and max_game_rating < min_rating:
                return False
            if max_rating is not None and max_game_rating > max_rating:
                return False
            return True

        self.filters.append(rating_filter)
        return self

    def passes(self, game: GameInfo) -> bool:
        """Check if game passes all filters."""
        return all(filter_func(game) for filter_func in self.filters)


# Predefined classifiers for common use cases
def create_leela_vs_human_classifier() -> PlayerClassifier:
    """Create classifier for Leela vs Human analysis."""
    return (
        PlayerClassifier()
        .add_player_name_rule("leela_rook", ["LeelaRookOdds"])
        .add_player_name_rule("leela_knight", ["LeelaKnightOdds"])
        .add_player_name_rule("leela_queen", ["LeelaQueenOdds"])
        .add_player_name_rule("leela_std", ["LazyBot"])
        .add_engine_rule("engine")
    )


def create_rating_classifier() -> PlayerClassifier:
    """Create classifier by rating brackets."""
    return (
        PlayerClassifier()
        .add_rating_rule("beginner", 0, 1200)
        .add_rating_rule("intermediate", 1200, 1800)
        .add_rating_rule("advanced", 1800, 2200)
        .add_rating_rule("expert", 2200, 9999)
    )
