"""Tests for player classification and grouping"""

import pytest

from modules.analysis.grouping import (
    GameFilter,
    GameInfo,
    PlayerClassifier,
    create_leela_vs_human_classifier,
)


class TestPlayerClassifier:
    """Test player classification system."""

    def test_add_engine_rule(self):
        """Test engine detection rule."""
        classifier = PlayerClassifier().add_engine_rule()

        # Test engine detection
        engine_game = GameInfo(
            white_player="Stockfish",
            black_player="Human",
            white_elo=3000,
            black_elo=1500,
            time_control="180+2",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(engine_game)
        assert "engine" in groups

        # Test human vs human
        human_game = GameInfo(
            white_player="Alice",
            black_player="Bob",
            white_elo=1600,
            black_elo=1550,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(human_game)
        assert "engine" not in groups

    def test_add_rating_rule(self):
        """Test rating-based classification."""
        classifier = PlayerClassifier().add_rating_rule("strong", 2000, 3000).add_rating_rule("weak", 0, 1200)

        strong_game = GameInfo(
            white_player="Expert",
            black_player="Master",
            white_elo=2200,
            black_elo=2100,
            time_control="900+10",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(strong_game)
        assert "strong" in groups
        assert "weak" not in groups

        weak_game = GameInfo(
            white_player="Beginner1",
            black_player="Beginner2",
            white_elo=1000,
            black_elo=1100,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(weak_game)
        assert "weak" in groups
        assert "strong" not in groups

    def test_add_player_name_rule(self):
        """Test player name matching."""
        classifier = PlayerClassifier().add_player_name_rule("leela", ["LeelaChessZero", "LeelaRookOdds", "LazyBot"])

        leela_game = GameInfo(
            white_player="LeelaRookOdds",
            black_player="Human123",
            white_elo=None,
            black_elo=1800,
            time_control="180+0",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(leela_game)
        assert "leela" in groups

        human_game = GameInfo(
            white_player="RandomHuman",
            black_player="AnotherHuman",
            white_elo=1500,
            black_elo=1600,
            time_control="300+3",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(human_game)
        assert "leela" not in groups

    def test_multiple_rules(self):
        """Test game matching multiple classification rules."""
        classifier = (
            PlayerClassifier()
            .add_engine_rule("engine")
            .add_rating_rule("strong", 2500)
            .add_player_name_rule("leela", ["LeelaChessZero"])
        )

        game = GameInfo(
            white_player="LeelaChessZero",
            black_player="Human",
            white_elo=3200,
            black_elo=2000,
            time_control="60+1",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(game)
        assert "engine" in groups
        assert "strong" in groups
        assert "leela" in groups

        assert len(groups) == 3


class TestGameFilter:
    """Test game filtering system."""

    def test_variant_filter(self):
        """Test filtering by chess variant."""
        game_filter = GameFilter().add_variant_filter(["Standard", "Blitz"])

        standard_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=1500,
            black_elo=1600,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )
        assert game_filter.passes(standard_game)

        chess960_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=1500,
            black_elo=1600,
            time_control="600+0",
            variant="Chess960",
            metadata={},
        )
        assert not game_filter.passes(chess960_game)

    def test_time_control_filter(self):
        """Test filtering by time control."""
        game_filter = GameFilter().add_time_control_filter(["180", "300"])

        blitz_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=1500,
            black_elo=1600,
            time_control="180+2",
            variant="Standard",
            metadata={},
        )
        assert game_filter.passes(blitz_game)

        rapid_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=1500,
            black_elo=1600,
            time_control="900+10",
            variant="Standard",
            metadata={},
        )
        assert not game_filter.passes(rapid_game)

    def test_rating_filter(self):
        """Test filtering by rating range."""
        game_filter = GameFilter().add_rating_filter(min_rating=1500, max_rating=2000)

        # Game within range
        good_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=1600,
            black_elo=1800,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )
        assert game_filter.passes(good_game)

        # Game too low
        low_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=1200,
            black_elo=1300,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )
        assert not game_filter.passes(low_game)

        # Game too high
        high_game = GameInfo(
            white_player="A",
            black_player="B",
            white_elo=2200,
            black_elo=2300,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )
        assert not game_filter.passes(high_game)


class TestPredefinedClassifiers:
    """Test predefined classifier functions."""

    def test_create_leela_vs_human_classifier(self):
        """Test Leela vs human classifier creation."""
        classifier = create_leela_vs_human_classifier()

        # Test Leela rook odds
        leela_game = GameInfo(
            white_player="LeelaRookOdds",
            black_player="Human123",
            white_elo=None,
            black_elo=1800,
            time_control="180+0",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(leela_game)
        assert "leela_rook" in groups
        assert "engine" in groups

        # Test human vs human
        human_game = GameInfo(
            white_player="Alice",
            black_player="Bob",
            white_elo=1600,
            black_elo=1550,
            time_control="600+0",
            variant="Standard",
            metadata={},
        )

        groups = classifier.classify_game(human_game)
        assert len([g for g in groups if g.startswith("leela_")]) == 0
