"""Lichess API client for game data collection"""

import json
from typing import Iterator, Optional

import requests


class LichessClient:
    """Client for fetching games from Lichess API."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize Lichess client.

        Args:
            token: Optional Lichess API token for higher rate limits
        """
        self.token = token
        self.base_url = "https://lichess.org/api"

    def _get_headers(self) -> dict:
        """Get HTTP headers for API requests."""
        headers = {"Accept": "application/x-ndjson"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def stream_user_games(
        self, username: str, max_games: int = 200, include_moves: bool = True, timeout: int = 60
    ) -> Iterator[str]:
        """
        Stream games for a specific user.

        Args:
            username: Lichess username
            max_games: Maximum number of games to fetch
            include_moves: Whether to include game moves in PGN
            timeout: Request timeout in seconds

        Yields:
            PGN strings of games
        """
        url = f"{self.base_url}/games/user/{username}"
        params = {"max": max_games, "moves": str(include_moves).lower(), "pgnInJson": "true"}
        headers = self._get_headers()

        with requests.get(url, params=params, headers=headers, stream=True, timeout=timeout) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    game_data = json.loads(line.decode("utf-8"))
                    pgn = game_data.get("pgn", "")
                    if pgn:
                        yield pgn
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Skip malformed lines
                    continue

    def get_random_human_players(
        self, rating_min: int = 1800, rating_max: int = 2200, variant: str = "standard", count: int = 20
    ) -> list:
        """
        Get a list of human players in rating range by sampling from leaderboards.

        Args:
            rating_min: Minimum rating to look for
            rating_max: Maximum rating to look for
            variant: Game variant (standard, blitz, rapid, etc)
            count: Number of players to find

        Returns:
            List of usernames that are likely human players
        """
        # Use public leaderboard endpoint to find players in rating range
        url = f"{self.base_url}/player"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            # Get online players (more likely to be active humans)
            response = requests.get(f"{url}/online", headers=headers, timeout=10)
            response.raise_for_status()

            online_players = response.json().get("users", [])

            # Filter for players in our rating range (approximate)
            candidates = []
            for player in online_players:
                perfs = player.get("perfs", {})
                if variant in perfs:
                    rating = perfs[variant].get("rating", 0)
                    if rating_min <= rating <= rating_max:
                        # Simple bot detection - exclude obvious bot names
                        username = player.get("id", "")
                        if not self._looks_like_bot(username):
                            candidates.append(username)
                            if len(candidates) >= count:
                                break

            return candidates[:count]

        except Exception:
            # Fallback: return some known human players in different rating ranges
            fallback_players = [
                "DrNykterstein",
                "Hikaru",
                "GMWSO",
                "penguingim1",
                "MagnusCarlsen",
                "FairChess_on_YouTube",
                "Zhigalko_Sergei",
                "Polish_fighter3000",
                "GMHikaruOnTwitch",
                "FIDE_World_Championship",
            ]
            return fallback_players[:count]

    def _looks_like_bot(self, username: str) -> bool:
        """Simple heuristic to detect bot/engine usernames."""
        bot_patterns = ["bot", "engine", "stockfish", "leela", "lc0", "komodo", "fire", "dragon", "computer", "maia"]
        username_lower = username.lower()
        return any(pattern in username_lower for pattern in bot_patterns)

    def get_user_info(self, username: str) -> dict:
        """
        Get user information.

        Args:
            username: Lichess username

        Returns:
            Dictionary with user information
        """
        url = f"{self.base_url}/user/{username}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
