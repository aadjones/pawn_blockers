"""TWIC (The Week in Chess) data source for chess games."""

import re
import tempfile
import zipfile
from pathlib import Path
from typing import Iterator, List, Optional
from urllib.parse import urljoin

import requests


class TWICClient:
    """Client for downloading games from The Week in Chess archive."""

    def __init__(self):
        self.base_url = "https://theweekinchess.com/zips/"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; Chess Analysis Bot)"})

    def get_latest_issue_number(self) -> Optional[int]:
        """Get the latest TWIC issue number by checking the main page."""
        try:
            response = self.session.get("https://theweekinchess.com/twic", timeout=10)
            response.raise_for_status()

            # Look for issue numbers in the HTML
            issue_pattern = r"twic(\d{4})g\.zip"
            matches = re.findall(issue_pattern, response.text)

            if matches:
                return max(int(match) for match in matches)

        except Exception as e:
            print(f"Failed to get latest issue: {e}")

        # Fallback - assume issue 1604 as a reasonable starting point
        return 1604

    def download_issue_games(self, issue_number: int) -> List[str]:
        """
        Download and extract games from a specific TWIC issue.

        Args:
            issue_number: TWIC issue number (e.g., 1604)

        Returns:
            List of PGN game strings
        """
        pgn_url = f"{self.base_url}twic{issue_number:04d}g.zip"

        try:
            print(f"   📥 Downloading TWIC {issue_number}...")
            response = self.session.get(pgn_url, timeout=30)
            response.raise_for_status()

            games = []
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(response.content)
                temp_file.flush()

                with zipfile.ZipFile(temp_file.name, "r") as zip_file:
                    for file_name in zip_file.namelist():
                        if file_name.endswith(".pgn"):
                            with zip_file.open(file_name) as pgn_file:
                                content = pgn_file.read().decode("utf-8", errors="ignore")
                                games.extend(self._split_pgn_content(content))

            print(f"   ✅ Extracted {len(games)} games from TWIC {issue_number}")
            return games

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed to download TWIC {issue_number}: {e}")
            return []
        except zipfile.BadZipFile as e:
            print(f"   ❌ Bad ZIP file for TWIC {issue_number}: {e}")
            return []
        except Exception as e:
            print(f"   ❌ Error processing TWIC {issue_number}: {e}")
            return []

    def download_recent_games(self, max_games: int = 1000, max_issues: int = 5) -> Iterator[str]:
        """
        Download recent games from latest TWIC issues.

        Args:
            max_games: Maximum number of games to collect
            max_issues: Maximum number of recent issues to check

        Yields:
            PGN game strings
        """
        latest_issue = self.get_latest_issue_number()
        if not latest_issue:
            print("   ❌ Could not determine latest TWIC issue")
            return

        games_collected = 0

        for issue_offset in range(max_issues):
            issue_number = latest_issue - issue_offset

            if issue_number < 1:
                break

            issue_games = self.download_issue_games(issue_number)

            for game in issue_games:
                if games_collected >= max_games:
                    return

                yield game
                games_collected += 1

        print(f"   📊 Total TWIC games collected: {games_collected}")

    def download_rating_filtered_games(
        self, min_rating: int = 2000, max_games: int = 1000, max_issues: int = 10
    ) -> Iterator[str]:
        """
        Download games filtered by minimum player rating.

        Args:
            min_rating: Minimum rating for either player
            max_games: Maximum number of games to collect
            max_issues: Maximum number of issues to check

        Yields:
            PGN game strings that meet rating criteria
        """
        games_yielded = 0

        for game in self.download_recent_games(max_games * 3, max_issues):  # Over-sample
            if games_yielded >= max_games:
                break

            # Extract ratings from PGN headers
            white_elo = self._extract_rating(game, "WhiteElo")
            black_elo = self._extract_rating(game, "BlackElo")

            # Check if either player meets minimum rating
            if (white_elo and white_elo >= min_rating) or (black_elo and black_elo >= min_rating):
                yield game
                games_yielded += 1

        print(f"   📊 Total rating-filtered games: {games_yielded}")

    def _split_pgn_content(self, content: str) -> List[str]:
        """Split PGN content into individual games."""
        games = []
        current_game = []

        for line in content.splitlines():
            line = line.strip()

            # Start of new game (Event header)
            if line.startswith("[Event "):
                if current_game:
                    games.append("\n".join(current_game))
                current_game = [line]
            elif current_game:
                current_game.append(line)

        # Don't forget the last game
        if current_game:
            games.append("\n".join(current_game))

        return games

    def _extract_rating(self, pgn: str, rating_tag: str) -> Optional[int]:
        """Extract rating from PGN headers."""
        pattern = rf'\[{rating_tag}\s+"(\d+)"\]'
        match = re.search(pattern, pgn)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
