"""PGN parsing utilities"""

from typing import Dict, Tuple


def parse_player_names(pgn_text: str) -> Tuple[str, str, Dict[str, str]]:
    """
    Extract player names and headers from PGN text.

    Returns:
        (white_player, black_player, all_headers)
    """
    headers = {}

    for line in pgn_text.splitlines():
        if line.startswith("["):
            # Parse header line: [Key "Value"]
            parts = line.split('"')
            if len(parts) >= 2:
                key = line.split()[0][1:]  # Remove opening bracket
                value = parts[1]  # Value between quotes
                headers[key] = value

    white_player = headers.get("White", "")
    black_player = headers.get("Black", "")

    return white_player, black_player, headers


def extract_game_metadata(headers: Dict[str, str]) -> Dict:
    """
    Extract useful metadata from PGN headers.

    Args:
        headers: Dictionary of PGN headers

    Returns:
        Dictionary with normalized metadata
    """
    # Extract game ID from Site header (works for Lichess)
    site = headers.get("Site", "")
    game_id = site.split("/")[-1] if "/" in site else headers.get("GameId", "")

    return {
        "game_id": game_id,
        "white": headers.get("White", ""),
        "black": headers.get("Black", ""),
        "result": headers.get("Result", ""),
        "date": headers.get("Date", ""),
        "time_control": headers.get("TimeControl", ""),
        "variant": headers.get("Variant", "Standard"),
        "starting_fen": headers.get("FEN") if headers.get("SetUp") == "1" else None,
        "white_elo": _safe_int(headers.get("WhiteElo")),
        "black_elo": _safe_int(headers.get("BlackElo")),
    }


def _safe_int(value: str) -> int:
    """Safely convert string to int, return None if invalid."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
