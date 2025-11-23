"""GitHub Gist-based leaderboard manager for cross-player score sharing."""

import json
import time
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

# Load environment variables from .env file when available
if load_dotenv:
    load_dotenv()

# Try to import web config (for deployed Web version)
try:
    from . import web_config
    WEB_CONFIG_AVAILABLE = True
except ImportError:
    WEB_CONFIG_AVAILABLE = False


class LeaderboardEntry:
    """Single leaderboard entry."""

    def __init__(self, player_id: str, score: int, lines: int, level: int,
                 mode: str, timestamp: float = None):
        """Initialize leaderboard entry.

        Args:
            player_id: Player's chosen ID
            score: Final score
            lines: Lines cleared
            level: Final level reached
            mode: Game mode (casual/classic/crazy)
            timestamp: Unix timestamp (auto-generated if None)
        """
        self.player_id = player_id
        self.score = score
        self.lines = lines
        self.level = level
        self.mode = mode
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'player_id': self.player_id,
            'score': self.score,
            'lines': self.lines,
            'level': self.level,
            'mode': self.mode,
            'timestamp': self.timestamp,
            'date': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M')
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LeaderboardEntry':
        """Create entry from dictionary."""
        return cls(
            player_id=data['player_id'],
            score=data['score'],
            lines=data['lines'],
            level=data.get('level', 1),
            mode=data['mode'],
            timestamp=data['timestamp']
        )


class GistLeaderboardManager:
    """Manages leaderboard using GitHub Gist as backend."""

    def __init__(self, gist_id: str = None, github_token: str = None):
        """Initialize Gist leaderboard manager.

        Args:
            gist_id: GitHub Gist ID (from env var if None)
            github_token: GitHub Personal Access Token (from env var if None)
        """
        # Priority: parameter > web_config > environment variable
        if WEB_CONFIG_AVAILABLE:
            self.gist_id = gist_id or web_config.GIST_ID
            self.github_token = github_token or web_config.GITHUB_TOKEN
        else:
            self.gist_id = gist_id or os.environ.get('GIST_ID', '')
            self.github_token = github_token or os.environ.get('GITHUB_TOKEN', '')
        self.filename = 'tetris_leaderboard.json'
        self.api_base = 'https://api.github.com'

        # Cache
        self._cache: Optional[Dict] = None
        self._cache_time: float = 0
        self._cache_duration: float = 30.0  # 30 seconds cache

        # Fallback mode (if no credentials)
        self.online_mode = bool(self.gist_id and self.github_token)

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitHub API."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        return headers

    def _fetch_gist(self) -> Optional[Dict]:
        """Fetch current gist data from GitHub.

        Returns:
            Gist data dict or None if failed
        """
        if not self.online_mode:
            return None

        # Check cache
        if self._cache and (time.time() - self._cache_time < self._cache_duration):
            return self._cache

        try:
            import requests
            url = f'{self.api_base}/gists/{self.gist_id}'
            response = requests.get(url, headers=self._get_headers(), timeout=5)

            if response.status_code == 200:
                self._cache = response.json()
                self._cache_time = time.time()
                return self._cache
            else:
                print(f"Failed to fetch gist: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching gist: {e}")
            return None

    def _update_gist(self, content: str, max_retries: int = 3) -> bool:
        """Update gist with new content (with retry on conflict).

        Args:
            content: JSON string content
            max_retries: Maximum retry attempts

        Returns:
            True if successful
        """
        if not self.online_mode:
            return False

        for attempt in range(max_retries):
            try:
                import requests
                url = f'{self.api_base}/gists/{self.gist_id}'
                payload = {
                    'files': {
                        self.filename: {
                            'content': content
                        }
                    }
                }

                response = requests.patch(
                    url,
                    headers=self._get_headers(),
                    data=json.dumps(payload),
                    timeout=10
                )

                if response.status_code == 200:
                    # Invalidate cache
                    self._cache = None
                    return True
                elif response.status_code == 409:  # Conflict
                    print(f"Conflict detected, retry {attempt + 1}/{max_retries}")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"Failed to update gist: {response.status_code}")
                    return False

            except Exception as e:
                print(f"Error updating gist (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))

        return False

    def _parse_leaderboard_data(self, gist_data: Dict) -> Dict[str, List[LeaderboardEntry]]:
        """Parse leaderboard data from gist.

        Returns:
            Dict mapping mode -> list of entries
        """
        try:
            content = gist_data['files'][self.filename]['content']
            data = json.loads(content)

            leaderboards = {}
            for mode in ['casual', 'classic', 'crazy']:
                entries = []
                for entry_dict in data.get(mode, []):
                    entries.append(LeaderboardEntry.from_dict(entry_dict))
                leaderboards[mode] = entries

            return leaderboards
        except Exception as e:
            print(f"Error parsing leaderboard data: {e}")
            return {'casual': [], 'classic': [], 'crazy': []}

    def get_leaderboard(self, mode: str, limit: int = 10) -> List[LeaderboardEntry]:
        """Get top scores for a mode.

        Args:
            mode: Game mode (casual/classic/crazy)
            limit: Maximum number of entries to return

        Returns:
            List of LeaderboardEntry, sorted by score descending
        """
        if not self.online_mode:
            return []

        gist_data = self._fetch_gist()
        if not gist_data:
            return []

        leaderboards = self._parse_leaderboard_data(gist_data)
        entries = leaderboards.get(mode, [])

        # Sort by score descending
        entries.sort(key=lambda x: x.score, reverse=True)
        return entries[:limit]

    def submit_score(self, entry: LeaderboardEntry) -> Tuple[bool, str]:
        """Submit a new score to the leaderboard.

        Args:
            entry: LeaderboardEntry to submit

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.online_mode:
            return False, "Offline mode: No GIST_ID or GITHUB_TOKEN"

        # Fetch current data
        gist_data = self._fetch_gist()
        if not gist_data:
            return False, "Failed to fetch leaderboard"

        # Parse and add new entry
        leaderboards = self._parse_leaderboard_data(gist_data)
        mode_entries = leaderboards.get(entry.mode, [])
        mode_entries.append(entry)

        # Sort and keep top 100 per mode (prevent unlimited growth)
        mode_entries.sort(key=lambda x: x.score, reverse=True)
        mode_entries = mode_entries[:100]

        # Update all modes
        leaderboards[entry.mode] = mode_entries

        # Convert to JSON
        output = {}
        for mode, entries in leaderboards.items():
            output[mode] = [e.to_dict() for e in entries]

        content = json.dumps(output, indent=2, ensure_ascii=False)

        # Update gist
        success = self._update_gist(content)

        if success:
            # Check rank
            rank = next((i + 1 for i, e in enumerate(mode_entries)
                        if e.timestamp == entry.timestamp), None)
            return True, f"Score submitted! Rank: #{rank}" if rank else "Score submitted!"
        else:
            return False, "Failed to submit score (please retry)"

    def get_player_rank(self, mode: str, score: int) -> Optional[int]:
        """Get rank for a given score in a mode.

        Args:
            mode: Game mode
            score: Score to check

        Returns:
            Rank (1-indexed) or None if failed
        """
        entries = self.get_leaderboard(mode, limit=100)
        if not entries:
            return 1  # First player

        rank = 1
        for entry in entries:
            if score > entry.score:
                return rank
            rank += 1

        return rank  # Lower than all existing scores
