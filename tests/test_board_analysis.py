"""Tests for core board analysis functions"""

import chess
import pytest

from modules.core.board_analysis import (
    get_blocking_info,
    get_file_index,
    get_pawn_start_and_ahead_squares,
    is_pawn_exposed,
)


class TestBoardAnalysis:
    """Test board analysis functions."""

    def test_get_file_index(self):
        """Test file letter to index conversion."""
        assert get_file_index("a") == 0
        assert get_file_index("d") == 3
        assert get_file_index("h") == 7

        with pytest.raises(ValueError):
            get_file_index("i")

    def test_get_pawn_start_and_ahead_squares(self):
        """Test getting pawn start and ahead squares."""
        # White f-pawn
        start, ahead = get_pawn_start_and_ahead_squares(5, chess.WHITE)  # f-file = index 5
        assert start == chess.F2
        assert ahead == chess.F3

        # Black f-pawn
        start, ahead = get_pawn_start_and_ahead_squares(5, chess.BLACK)
        assert start == chess.F7
        assert ahead == chess.F6

    def test_is_pawn_exposed_starting_position(self):
        """Test pawn exposure detection in starting position."""
        board = chess.Board()

        # All pawns should be exposed initially
        for file_idx in range(8):
            assert is_pawn_exposed(board, file_idx, chess.WHITE)
            assert is_pawn_exposed(board, file_idx, chess.BLACK)

    def test_is_pawn_exposed_after_moves(self):
        """Test pawn exposure after some moves."""
        board = chess.Board()

        # Move e2-e4
        board.push_san("e4")

        # e-pawn (index 4) should no longer be exposed for white
        assert not is_pawn_exposed(board, 4, chess.WHITE)
        # Other white pawns should still be exposed
        assert is_pawn_exposed(board, 3, chess.WHITE)  # d-pawn
        assert is_pawn_exposed(board, 5, chess.WHITE)  # f-pawn

        # All black pawns should still be exposed
        for file_idx in range(8):
            assert is_pawn_exposed(board, file_idx, chess.BLACK)

    def test_get_blocking_info_no_blocker(self):
        """Test blocking info when square is empty."""
        board = chess.Board()

        # f3 is empty in starting position
        friendly_np, enemy, any_block, piece_type = get_blocking_info(board, 5, chess.WHITE)

        assert not friendly_np
        assert not enemy
        assert not any_block
        assert piece_type is None

    def test_get_blocking_info_friendly_piece(self):
        """Test blocking info with friendly piece."""
        board = chess.Board()

        # Place white knight on f3
        board.set_piece_at(chess.F3, chess.Piece(chess.KNIGHT, chess.WHITE))

        friendly_np, enemy, any_block, piece_type = get_blocking_info(board, 5, chess.WHITE)

        assert friendly_np  # Knight is friendly non-pawn
        assert not enemy
        assert any_block
        assert piece_type == chess.KNIGHT

    def test_get_blocking_info_friendly_pawn(self):
        """Test blocking info with friendly pawn (should not count as friendly_np)."""
        board = chess.Board()

        # Place white pawn on f3
        board.set_piece_at(chess.F3, chess.Piece(chess.PAWN, chess.WHITE))

        friendly_np, enemy, any_block, piece_type = get_blocking_info(board, 5, chess.WHITE)

        assert not friendly_np  # Pawn doesn't count as non-pawn blocker
        assert not enemy
        assert any_block
        assert piece_type == chess.PAWN

    def test_get_blocking_info_enemy_piece(self):
        """Test blocking info with enemy piece."""
        board = chess.Board()

        # Place black knight on f3
        board.set_piece_at(chess.F3, chess.Piece(chess.KNIGHT, chess.BLACK))

        friendly_np, enemy, any_block, piece_type = get_blocking_info(board, 5, chess.WHITE)

        assert not friendly_np
        assert enemy
        assert any_block
        assert piece_type == chess.KNIGHT
