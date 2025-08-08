"""SPBTS (Self-Pawn Block To Start) metrics calculation"""

from collections import defaultdict
from io import StringIO
from typing import Dict, List, Tuple

import chess
import chess.pgn
import pandas as pd

from .board_analysis import FILES, get_blocking_info, is_pawn_exposed


def calculate_spbts_for_game(pgn_text: str, max_plies: int = 24) -> Tuple[Dict, pd.DataFrame]:
    """
    Calculate SPBTS metrics for a single game.

    Args:
        pgn_text: PGN string of the game
        max_plies: Maximum number of plies to analyze

    Returns:
        (summary_by_side, trace_df): Summary statistics and detailed trace
    """
    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        raise ValueError("Invalid PGN")

    # Handle custom starting positions (Chess960, etc.)
    if game.headers.get("SetUp") == "1" and "FEN" in game.headers:
        board = chess.Board(game.headers["FEN"])
    else:
        board = chess.Board()

    # Get all positions up to max_plies
    positions = [board.copy()]
    moves = list(game.mainline_moves())

    for i, move in enumerate(moves):
        if i >= max_plies - 1:
            break
        board.push(move)
        positions.append(board.copy())

    # Aggregate counters and detailed trace
    aggregates = {chess.WHITE: defaultdict(int), chess.BLACK: defaultdict(int)}
    per_file_exposure = {chess.WHITE: [0] * 8, chess.BLACK: [0] * 8}
    per_file_friendly_blocks = {chess.WHITE: [0] * 8, chess.BLACK: [0] * 8}
    trace_rows = []

    # Analyze each position
    for ply_idx, position in enumerate(positions):
        for color in (chess.WHITE, chess.BLACK):
            for file_idx in range(8):
                color_str = "white" if color == chess.WHITE else "black"

                if is_pawn_exposed(position, file_idx, color):
                    # Count exposure
                    aggregates[color]["exposure"] += 1
                    per_file_exposure[color][file_idx] += 1

                    # Get blocking info
                    friendly_np, enemy, any_block, piece_type = get_blocking_info(position, file_idx, color)

                    if friendly_np:
                        aggregates[color]["friendly_np"] += 1
                        per_file_friendly_blocks[color][file_idx] += 1
                    if enemy:
                        aggregates[color]["enemy"] += 1
                    if any_block:
                        aggregates[color]["any"] += 1

                    trace_rows.append(
                        {
                            "ply_index": ply_idx,
                            "color": color_str,
                            "file": FILES[file_idx],
                            "exposed": 1,
                            "friendly_np_block": int(friendly_np),
                            "enemy_block": int(enemy),
                            "any_block": int(any_block),
                            "blocker_piece": None if piece_type is None else chess.piece_symbol(piece_type),
                        }
                    )
                else:
                    # Not exposed
                    trace_rows.append(
                        {
                            "ply_index": ply_idx,
                            "color": color_str,
                            "file": FILES[file_idx],
                            "exposed": 0,
                            "friendly_np_block": 0,
                            "enemy_block": 0,
                            "any_block": 0,
                            "blocker_piece": None,
                        }
                    )

    trace_df = pd.DataFrame(trace_rows)

    def summarize_side(color: chess.Color) -> Dict:
        """Summarize SPBTS metrics for one side."""
        exposure = aggregates[color]["exposure"]
        if exposure == 0:
            return {
                "exposure": 0,
                "SPBTS_friendlyNP": None,
                "SPBTS_enemy": None,
                "SPBTS_any": None,
                "per_file_friendlyNP": None,
            }

        per_file_rates = {}
        for i in range(8):
            file_exposure = per_file_exposure[color][i]
            if file_exposure > 0:
                per_file_rates[FILES[i]] = per_file_friendly_blocks[color][i] / file_exposure
            else:
                per_file_rates[FILES[i]] = None

        return {
            "exposure": exposure,
            "SPBTS_friendlyNP": aggregates[color]["friendly_np"] / exposure,
            "SPBTS_enemy": aggregates[color]["enemy"] / exposure,
            "SPBTS_any": aggregates[color]["any"] / exposure,
            "per_file_friendlyNP": per_file_rates,
        }

    summary = {"white": summarize_side(chess.WHITE), "black": summarize_side(chess.BLACK)}

    return summary, trace_df
