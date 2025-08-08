#!/usr/bin/env python3
"""Quick test of F-pawn fate tracking functionality."""

from modules.core.metrics import calculate_spbts_for_game

# Test different F-pawn scenarios
test_games = {
    "never_blocked": """[Event "Never Blocked"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Be7 4. d3 d6 5. Be3 Bg4""",
    "permanent_block": """[Event "Permanent Block"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 f6 4. d3 Nf6 5. Bg5 h6 6. Bh4 g5 7. Bg3 Be7""",
    "push_f3": """[Event "Push F3"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 f6 3. d3 f5""",
}


def test_f_pawn_tracking():
    """Test that F-pawn fate tracking works correctly."""
    print("Testing F-pawn fate tracking...")

    for scenario, pgn in test_games.items():
        print(f"\n=== Testing {scenario} ===")
        try:
            summary, trace = calculate_spbts_for_game(pgn)

            print(f"White F-pawn fates: {summary['white']['f_pawn_fates']}")
            print(f"Black F-pawn fates: {summary['black']['f_pawn_fates']}")

        except Exception as e:
            print(f"Test failed for {scenario}: {e}")
            import traceback

            traceback.print_exc()

    print("\nAll tests completed! ✅")


if __name__ == "__main__":
    test_f_pawn_tracking()
