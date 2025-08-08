"""Statistical comparisons between groups"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.metrics import calculate_spbts_for_game
from ..data.game_parser import extract_game_metadata, parse_player_names
from .grouping import GameFilter, GameInfo, PlayerClassifier


def analyze_game_collection(
    pgn_games: List[str],
    classifier: PlayerClassifier,
    game_filter: Optional[GameFilter] = None,
    max_plies: int = 24,
    min_exposure: int = 64,
) -> pd.DataFrame:
    """
    Analyze a collection of PGN games and classify them.

    Args:
        pgn_games: List of PGN strings
        classifier: PlayerClassifier to group games
        game_filter: Optional GameFilter to exclude games
        max_plies: Maximum plies to analyze per game
        min_exposure: Minimum exposure required for inclusion

    Returns:
        DataFrame with game analysis results and classifications
    """
    results = []

    for pgn in pgn_games:
        try:
            # Parse game metadata
            white, black, headers = parse_player_names(pgn)
            metadata = extract_game_metadata(headers)

            game_info = GameInfo(
                white_player=white,
                black_player=black,
                white_elo=metadata.get("white_elo"),
                black_elo=metadata.get("black_elo"),
                time_control=metadata.get("time_control"),
                variant=metadata.get("variant", "Standard"),
                metadata=metadata,
            )

            # Apply filters
            if game_filter and not game_filter.passes(game_info):
                continue

            # Calculate SPBTS metrics
            summary, trace = calculate_spbts_for_game(pgn, max_plies)

            # Skip games with insufficient exposure
            white_exp = summary["white"]["exposure"]
            black_exp = summary["black"]["exposure"]
            if white_exp < min_exposure or black_exp < min_exposure:
                continue

            # Classify game
            groups = classifier.classify_game(game_info)

            # Determine which side is which group (for paired analysis)
            white_groups = []
            black_groups = []

            for group in groups:
                # Simple heuristic: if group name appears in player name, assign to that side
                if any(term in white.lower() for term in group.split("_")):
                    white_groups.append(group)
                elif any(term in black.lower() for term in group.split("_")):
                    black_groups.append(group)

            # Build result record
            plies_analyzed = int(trace["ply_index"].max()) if not trace.empty else 0

            # Extract per-file rates
            white_per_file = summary["white"].get("per_file_friendlyNP", {})
            black_per_file = summary["black"].get("per_file_friendlyNP", {})

            result = {
                "game_id": metadata["game_id"],
                "white_player": white,
                "black_player": black,
                "white_groups": white_groups,
                "black_groups": black_groups,
                "all_groups": groups,
                "white_spbts": summary["white"]["SPBTS_friendlyNP"],
                "black_spbts": summary["black"]["SPBTS_friendlyNP"],
                "white_exposure": white_exp,
                "black_exposure": black_exp,
                "plies_analyzed": plies_analyzed,
                **metadata,
            }

            # Add per-file rates
            for file_letter in "abcdefgh":
                result[f"white_{file_letter}"] = white_per_file.get(file_letter)
                result[f"black_{file_letter}"] = black_per_file.get(file_letter)

            results.append(result)

        except Exception:
            # Skip problematic games
            continue

    return pd.DataFrame(results)


def compare_groups(
    df: pd.DataFrame,
    group1_name: str,
    group2_name: str,
    metrics: Optional[List[str]] = None,
    group_col: str = "all_groups",
) -> Dict:
    """
    Compare SPBTS metrics between two groups.

    Args:
        df: DataFrame from analyze_game_collection
        group1_name: First group to compare
        group2_name: Second group to compare
        metrics: List of metrics to compare (default: SPBTS rates)
        group_col: Column to use for group identification (default: "all_groups")

    Returns:
        Dictionary with comparison results
    """
    if metrics is None:
        metrics = ["spbts"] + [f"file_{f}" for f in "abcdefgh"]

    # Handle cohort comparison (simple group assignment)
    if group_col == "comparison_group":
        group1_df = df[df[group_col] == group1_name]
        group2_df = df[df[group_col] == group2_name]

        if group1_df.empty or group2_df.empty:
            return {"error": f"Insufficient data for comparison between {group1_name} and {group2_name}"}

        # For cohort comparison, use all SPBTS values from each cohort
        group1_values = pd.concat([group1_df["white_spbts"], group1_df["black_spbts"]]).dropna().tolist()
        group2_values = pd.concat([group2_df["white_spbts"], group2_df["black_spbts"]]).dropna().tolist()

        results = {
            "group1": group1_name,
            "group2": group2_name,
            "n_games": len(group1_df) + len(group2_df),
            "group1_games": len(group1_df),
            "group2_games": len(group2_df),
            "metrics": {},
        }

    else:
        # Original paired comparison logic for within-game groups
        mask = df[group_col].apply(lambda x: group1_name in x and group2_name in x)
        comparison_df = df[mask].copy()

        if comparison_df.empty:
            return {"error": f"No games found with both {group1_name} and {group2_name}"}

        results = {"group1": group1_name, "group2": group2_name, "n_games": len(comparison_df), "metrics": {}}

        # For each game, determine which side is which group
        group1_values = []
        group2_values = []

        for _, row in comparison_df.iterrows():
            # Determine side assignment based on groups
            if group1_name in row["white_groups"]:
                group1_side, group2_side = "white", "black"
            else:
                group1_side, group2_side = "black", "white"

            group1_spbts = row[f"{group1_side}_spbts"]
            group2_spbts = row[f"{group2_side}_spbts"]

            if group1_spbts is not None and group2_spbts is not None:
                group1_values.append(group1_spbts)
                group2_values.append(group2_spbts)

    # Calculate comparison statistics
    if group1_values and group2_values:
        group1_arr = np.array(group1_values)
        group2_arr = np.array(group2_values)

        results["metrics"]["spbts"] = {
            "group1_median": float(np.median(group1_arr)),
            "group2_median": float(np.median(group2_arr)),
            "group1_mean": float(np.mean(group1_arr)),
            "group2_mean": float(np.mean(group2_arr)),
            "difference": float(np.median(group1_arr) - np.median(group2_arr)),
            "group1_values": group1_values,
            "group2_values": group2_values,
        }

    return results
