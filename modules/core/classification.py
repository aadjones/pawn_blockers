"""F-file bucket classification and other pattern analysis"""

from io import StringIO
from typing import Dict, List, Optional

import chess
import chess.pgn

from .board_analysis import get_file_index, get_pawn_start_and_ahead_squares


def classify_f_bucket_for_color(positions: List[chess.Board], color: chess.Color, max_plies: int = 24) -> str:
    """
    Classify f-file pawn behavior into buckets (A1, A2, A3, B4, B5, other).

    Args:
        positions: List of board positions from ply 0 to K
        color: Which side's f-pawn to analyze
        max_plies: Maximum plies to consider

    Returns:
        Bucket classification string
    """
    file_idx = get_file_index("f")

    # Track exposure and friendly blocking per ply
    exposed = []
    friendly_blocks = []

    for position in positions:
        start_sq, ahead_sq = get_pawn_start_and_ahead_squares(file_idx, color)

        # Check if f-pawn is exposed (on starting square)
        pawn = position.piece_at(start_sq)
        is_exposed = pawn is not None and pawn.piece_type == chess.PAWN and pawn.color == color
        exposed.append(is_exposed)

        # Check for friendly non-pawn block if exposed
        if is_exposed:
            blocker = position.piece_at(ahead_sq)
            has_friendly_block = blocker is not None and blocker.color == color and blocker.piece_type != chess.PAWN
            friendly_blocks.append(has_friendly_block)
        else:
            friendly_blocks.append(False)

    # Find when pawn first moves off starting square
    move_off_ply = None
    for t in range(1, len(positions)):
        if exposed[t - 1] and not exposed[t]:
            move_off_ply = t
            break

    # Check if there was any friendly blocking while exposed
    any_friendly_block = any(friendly_blocks)

    # Classification logic
    if move_off_ply is None and not any_friendly_block:
        return "A1"  # Never moved, never blocked

    # If moved with no prior friendly block, check destination
    if move_off_ply is not None and not any(friendly_blocks[:move_off_ply]):
        position = positions[move_off_ply]

        # Check if pawn landed on f3/f6 (one square) or f4/f5 (two squares)
        f3_or_f6 = chess.square(file_idx, 2 if color == chess.WHITE else 5)
        f4_or_f5 = chess.square(file_idx, 3 if color == chess.WHITE else 4)

        pawn_on_f3 = position.piece_at(f3_or_f6)
        pawn_on_f4 = position.piece_at(f4_or_f5)

        if pawn_on_f3 and pawn_on_f3.piece_type == chess.PAWN and pawn_on_f3.color == color:
            return "A2"  # Moved one square
        elif pawn_on_f4 and pawn_on_f4.piece_type == chess.PAWN and pawn_on_f4.color == color:
            return "A3"  # Moved two squares
        else:
            return "other"  # Moved by capture or other

    # Had friendly blocking: compute first episode duration
    block_start = None
    for t in range(len(positions)):
        if friendly_blocks[t]:
            block_start = t
            break

    if block_start is None:
        return "other"

    # Find when blocking episode ends
    block_end = len(positions)  # Default: censored at window end
    for t in range(block_start + 1, len(positions)):
        if not exposed[t]:  # Pawn moved
            block_end = t
            break
        if exposed[t] and not friendly_blocks[t]:  # Blocker left
            block_end = t
            break

    duration = block_end - block_start
    return "B4" if duration <= 2 else "B5"


def classify_f_buckets_from_pgn(pgn_text: str, max_plies: int = 24) -> Optional[Dict[str, str]]:
    """
    Classify f-file buckets for both sides from a PGN string.

    Returns:
        Dictionary with 'white' and 'black' bucket classifications, or None if invalid PGN
    """
    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        return None

    # Handle custom starting positions
    if game.headers.get("SetUp") == "1" and "FEN" in game.headers:
        board = chess.Board(game.headers["FEN"])
    else:
        board = chess.Board()

    # Build position list
    positions = [board.copy()]
    moves = list(game.mainline_moves())

    for i, move in enumerate(moves):
        if i >= max_plies - 1:
            break
        board.push(move)
        positions.append(board.copy())

    return {
        "white": classify_f_bucket_for_color(positions, chess.WHITE, max_plies),
        "black": classify_f_bucket_for_color(positions, chess.BLACK, max_plies),
    }
