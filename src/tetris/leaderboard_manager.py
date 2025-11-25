"""Leaderboard manager using Cloudflare Worker proxy for secure API access."""

import json
import time
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Default Worker URL (can be overridden via environment variable)
DEFAULT_WORKER_URL = 'https://tetris-leaderboard.jefferysung860629.workers.dev'


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
    """Manages leaderboard using Cloudflare Worker proxy (no credentials needed)."""

    def __init__(self, worker_url: str = None):
        """Initialize leaderboard manager.

        Args:
            worker_url: Cloudflare Worker URL (uses default if None)
        """
        self.worker_url = worker_url or os.environ.get('WORKER_URL', DEFAULT_WORKER_URL)

        # Cache
        self._cache: Optional[Dict] = None
        self._cache_time: float = 0
        self._cache_duration: float = 30.0  # 30 seconds cache

        # Online mode (always True if worker URL is set)
        self.online_mode = bool(self.worker_url)

    def _fetch_leaderboard(self) -> Optional[Dict]:
        """Fetch leaderboard data from Worker API.

        Returns:
            Leaderboard data dict or None if failed
        """
        if not self.online_mode:
            return None

        # Check cache
        if self._cache and (time.time() - self._cache_time < self._cache_duration):
            return self._cache

        try:
            import requests
            url = f'{self.worker_url}/leaderboard'
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                self._cache = response.json()
                self._cache_time = time.time()
                return self._cache
            else:
                print(f"Failed to fetch leaderboard: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            return None

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

        data = self._fetch_leaderboard()
        if not data:
            return []

        entries = []
        for entry_dict in data.get(mode, []):
            entries.append(LeaderboardEntry.from_dict(entry_dict))

        # Already sorted by Worker, just apply limit
        return entries[:limit]

    def submit_score(self, entry: LeaderboardEntry) -> Tuple[bool, str]:
        """Submit a new score to the leaderboard via Worker API.

        Args:
            entry: LeaderboardEntry to submit

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.online_mode:
            return False, "Offline mode: No worker URL configured"

        try:
            import requests
            url = f'{self.worker_url}/submit'
            payload = {
                'player_id': entry.player_id,
                'score': entry.score,
                'lines': entry.lines,
                'level': entry.level,
                'mode': entry.mode
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                # Invalidate cache
                self._cache = None
                return True, result.get('message', 'Score submitted!')
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get('error', f'HTTP {response.status_code}')
                return False, f"Failed to submit: {error_msg}"

        except Exception as e:
            print(f"Error submitting score: {e}")
            return False, "Failed to submit score (network error)"

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
