"""SPBTS (Self-Pawn Block To Start) metrics calculation"""

from collections import defaultdict
from io import StringIO
from typing import Dict, List, Tuple

import chess
import chess.pgn
import pandas as pd

from .board_analysis import FILES, get_blocking_info, is_pawn_exposed


def track_f_pawn_fate(positions: List[chess.Board], color: chess.Color) -> Dict[str, int]:
    """
    Track complete F-pawn fate over the course of a game.

    Returns counts for each fate category:
    - never_blocked: F-pawn stays on f2, never gets blocked
    - push_f3: Pawn advances one square
    - push_f4: Pawn advances two squares
    - capture_e3: Pawn captures on e3
    - capture_g3: Pawn captures on g3
    - temporary_block: Blocked for ≥1 ply, then freed (blocker moves away)
    - permanent_block: Blocked and remains blocked through analysis end
    """
    f_file_idx = 5  # F-file
    fates = {
        "never_blocked": 0,
        "push_f3": 0,
        "push_f4": 0,
        "capture_e3": 0,
        "capture_g3": 0,
        "temporary_block": 0,
        "permanent_block": 0,
    }

    # Track F-pawn blocking events and position changes
    pawn_present_plies = []
    blocked_plies = []

    for ply_idx, position in enumerate(positions):
        if is_pawn_exposed(position, f_file_idx, color):
            pawn_present_plies.append(ply_idx)
            friendly_np, _, _, _ = get_blocking_info(position, f_file_idx, color)
            if friendly_np:
                blocked_plies.append(ply_idx)

    # If F-pawn never appeared on starting square, skip
    if not pawn_present_plies:
        return fates

    # Check if pawn ever moved
    pawn_moved = False
    pawn_movement_fate = None

    for ply_idx in range(len(positions) - 1):
        if pawn_present_plies and ply_idx in pawn_present_plies:
            # Pawn is present at this ply, check if it moves next ply
            if ply_idx + 1 < len(positions):
                next_position = positions[ply_idx + 1]
                if not is_pawn_exposed(next_position, f_file_idx, color):
                    # Pawn moved! Determine where
                    pawn_movement_fate = _determine_pawn_movement(positions[ply_idx], next_position, f_file_idx, color)
                    pawn_moved = True
                    break

    if pawn_moved and pawn_movement_fate:
        fates[pawn_movement_fate] += 1
        return fates

    # Pawn never moved - classify based on blocking behavior
    if not blocked_plies:
        # Never blocked at all
        fates["never_blocked"] += 1
    else:
        # Was blocked - check if it got freed
        first_block_ply = blocked_plies[0]
        pawn_freed = False

        for ply_idx in range(first_block_ply + 1, len(positions)):
            if ply_idx in pawn_present_plies:
                position = positions[ply_idx]
                friendly_np, _, _, _ = get_blocking_info(position, f_file_idx, color)
                if not friendly_np:  # No longer blocked
                    pawn_freed = True
                    break

        if pawn_freed:
            fates["temporary_block"] += 1
        else:
            fates["permanent_block"] += 1

    return fates


def _determine_pawn_movement(before_pos: chess.Board, after_pos: chess.Board, file_idx: int, color: chess.Color) -> str:
    """Determine how the F-pawn moved by comparing positions."""
    if color == chess.WHITE:
        f2, f3, f4 = chess.F2, chess.F3, chess.F4
        e3, g3 = chess.E3, chess.G3
    else:
        f2, f3, f4 = chess.F7, chess.F6, chess.F5
        e3, g3 = chess.E6, chess.G6

    # Check if pawn moved to f3/f6
    piece_f3 = after_pos.piece_at(f3)
    if piece_f3 and piece_f3.piece_type == chess.PAWN and piece_f3.color == color:
        return "push_f3"

    # Check if pawn moved to f4/f5
    piece_f4 = after_pos.piece_at(f4)
    if piece_f4 and piece_f4.piece_type == chess.PAWN and piece_f4.color == color:
        return "push_f4"

    # Check if pawn captured on e3/e6
    piece_e3 = after_pos.piece_at(e3)
    if piece_e3 and piece_e3.piece_type == chess.PAWN and piece_e3.color == color:
        return "capture_e3"

    # Check if pawn captured on g3/g6
    piece_g3 = after_pos.piece_at(g3)
    if piece_g3 and piece_g3.piece_type == chess.PAWN and piece_g3.color == color:
        return "capture_g3"

    return None


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
                "f_pawn_fates": None,
            }

        per_file_rates = {}
        for i in range(8):
            file_exposure = per_file_exposure[color][i]
            if file_exposure > 0:
                per_file_rates[FILES[i]] = per_file_friendly_blocks[color][i] / file_exposure
            else:
                per_file_rates[FILES[i]] = None

        # Calculate F-pawn fates
        f_pawn_fates = track_f_pawn_fate(positions, color)

        return {
            "exposure": exposure,
            "SPBTS_friendlyNP": aggregates[color]["friendly_np"] / exposure,
            "SPBTS_enemy": aggregates[color]["enemy"] / exposure,
            "SPBTS_any": aggregates[color]["any"] / exposure,
            "per_file_friendlyNP": per_file_rates,
            "f_pawn_fates": f_pawn_fates,
        }

    summary = {"white": summarize_side(chess.WHITE), "black": summarize_side(chess.BLACK)}

    return summary, trace_df
