"""Core board position analysis functions"""

from typing import Optional, Tuple

import chess

FILES = "abcdefgh"


def get_pawn_start_and_ahead_squares(file_idx: int, color: chess.Color) -> Tuple[int, int]:
    """Get the starting square and square directly ahead for a pawn on given file."""
    if color == chess.WHITE:
        return chess.square(file_idx, 1), chess.square(file_idx, 2)  # e.g., f2, f3
    else:
        return chess.square(file_idx, 6), chess.square(file_idx, 5)  # e.g., f7, f6


def is_pawn_exposed(board: chess.Board, file_idx: int, color: chess.Color) -> bool:
    """Check if a pawn is still on its starting square (exposed)."""
    start_sq, _ = get_pawn_start_and_ahead_squares(file_idx, color)
    piece = board.piece_at(start_sq)
    return piece is not None and piece.piece_type == chess.PAWN and piece.color == color


def get_blocking_info(board: chess.Board, file_idx: int, color: chess.Color) -> Tuple[bool, bool, bool, Optional[int]]:
    """
    Get blocking information for a pawn file.

    Returns:
        (friendly_non_pawn_block, enemy_block, any_block, blocker_piece_type)
    """
    _, ahead_sq = get_pawn_start_and_ahead_squares(file_idx, color)
    piece = board.piece_at(ahead_sq)

    if piece is None:
        return False, False, False, None

    any_block = True
    if piece.color == color:
        friendly_non_pawn_block = piece.piece_type != chess.PAWN
        return friendly_non_pawn_block, False, any_block, piece.piece_type
    else:
        return False, True, any_block, piece.piece_type


def get_file_index(file_letter: str) -> int:
    """Convert file letter to index (a=0, b=1, ..., h=7)."""
    return FILES.index(file_letter)
