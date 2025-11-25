"""Leaderboard manager using Cloudflare Worker proxy for secure API access."""

import json
import time
import os
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Default Worker URL (can be overridden via environment variable)
DEFAULT_WORKER_URL = 'https://tetris-leaderboard.jefferysung860629.workers.dev'

# Detect if running in Web/Pygbag environment
IS_WEB = sys.platform == "emscripten"


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

        # Async operation results (for Web version)
        self._last_fetch_result: Optional[Dict] = None
        self._last_submit_result: Optional[Tuple[bool, str]] = None
        self._operation_pending: bool = False

    def _fetch_leaderboard_sync(self) -> Optional[Dict]:
        """Fetch leaderboard using synchronous requests (desktop only)."""
        try:
            import requests
            url = f'{self.worker_url}/leaderboard'
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch leaderboard: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            return None

    async def _fetch_leaderboard_web_async(self) -> Optional[Dict]:
        """Fetch leaderboard using pygbag async fetch (Web only)."""
        try:
            from pygbag.support.cross.aio.fetch import RequestHandler
            handler = RequestHandler()
            url = f'{self.worker_url}/leaderboard'

            response = await handler.get(url)
            if response:
                return json.loads(response)
            else:
                print("Failed to fetch leaderboard: empty response")
                return None
        except ImportError:
            # Fallback: try using JavaScript directly
            try:
                import platform
                url = f'{self.worker_url}/leaderboard'
                # Use JavaScript fetch with async/await pattern
                js_result = platform.window.fetch(url)
                if js_result:
                    response = await js_result
                    text = await response.text()
                    return json.loads(text)
            except Exception as e:
                print(f"Error fetching leaderboard (js fallback): {e}")
            return None
        except Exception as e:
            print(f"Error fetching leaderboard (web): {e}")
            return None

    def _fetch_leaderboard(self) -> Optional[Dict]:
        """Fetch leaderboard data from Worker API (sync version for compatibility).

        Returns:
            Leaderboard data dict or None if failed
        """
        if not self.online_mode:
            return None

        # Check cache
        if self._cache and (time.time() - self._cache_time < self._cache_duration):
            return self._cache

        # For Web, return cached result if available (async fetch happens separately)
        if IS_WEB:
            return self._last_fetch_result

        # Desktop: use sync request
        data = self._fetch_leaderboard_sync()
        if data:
            self._cache = data
            self._cache_time = time.time()

        return data

    async def fetch_leaderboard_async(self) -> Optional[Dict]:
        """Fetch leaderboard data asynchronously (for Web version).

        Call this method from your async game loop to fetch data.
        Results are stored in _last_fetch_result for sync access.
        """
        if not self.online_mode:
            return None

        # Check cache
        if self._cache and (time.time() - self._cache_time < self._cache_duration):
            return self._cache

        if IS_WEB:
            data = await self._fetch_leaderboard_web_async()
        else:
            data = self._fetch_leaderboard_sync()

        if data:
            self._cache = data
            self._cache_time = time.time()
            self._last_fetch_result = data

        return data

    def _submit_score_sync(self, payload: Dict) -> Tuple[bool, str]:
        """Submit score using synchronous requests (desktop only)."""
        try:
            import requests
            url = f'{self.worker_url}/submit'
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return True, result.get('message', 'Score submitted!')
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'HTTP {response.status_code}')
                except Exception:
                    error_msg = f'HTTP {response.status_code}'
                return False, f"Failed to submit: {error_msg}"
        except Exception as e:
            print(f"Error submitting score: {e}")
            return False, "Failed to submit score (network error)"

    async def _submit_score_web_async(self, payload: Dict) -> Tuple[bool, str]:
        """Submit score using pygbag async fetch (Web only)."""
        try:
            from pygbag.support.cross.aio.fetch import RequestHandler
            handler = RequestHandler()
            url = f'{self.worker_url}/submit'

            # Convert payload to JSON string for POST
            response = await handler.post(url, data=json.dumps(payload))

            if response:
                result = json.loads(response)
                if result.get('success'):
                    return True, result.get('message', 'Score submitted!')
                else:
                    return False, result.get('error', 'Unknown error')
            else:
                return False, "Failed to submit: empty response"
        except ImportError:
            # Fallback: try using JavaScript directly
            try:
                import platform
                url = f'{self.worker_url}/submit'
                options = {
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(payload)
                }
                js_result = platform.window.fetch(url, options)
                if js_result:
                    response = await js_result
                    text = await response.text()
                    result = json.loads(text)
                    if result.get('success'):
                        return True, result.get('message', 'Score submitted!')
                    else:
                        return False, result.get('error', 'Unknown error')
            except Exception as e:
                print(f"Error submitting score (js fallback): {e}")
            return False, "Failed to submit score (network error)"
        except Exception as e:
            print(f"Error submitting score (web): {e}")
            return False, f"Failed to submit score: {e}"

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

    async def get_leaderboard_async(self, mode: str, limit: int = 10) -> List[LeaderboardEntry]:
        """Get top scores for a mode asynchronously.

        Args:
            mode: Game mode (casual/classic/crazy)
            limit: Maximum number of entries to return

        Returns:
            List of LeaderboardEntry, sorted by score descending
        """
        if not self.online_mode:
            return []

        data = await self.fetch_leaderboard_async()
        if not data:
            return []

        entries = []
        for entry_dict in data.get(mode, []):
            entries.append(LeaderboardEntry.from_dict(entry_dict))

        return entries[:limit]

    def submit_score(self, entry: LeaderboardEntry) -> Tuple[bool, str]:
        """Submit a new score to the leaderboard via Worker API (sync).

        For Web version, this returns the last async result.
        Call submit_score_async() first from your async game loop.

        Args:
            entry: LeaderboardEntry to submit

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.online_mode:
            return False, "Offline mode: No worker URL configured"

        # For Web, return cached async result
        if IS_WEB:
            if self._last_submit_result:
                result = self._last_submit_result
                self._last_submit_result = None  # Clear after reading
                return result
            return False, "Submitting..."

        # Desktop: use sync request
        payload = {
            'player_id': entry.player_id,
            'score': entry.score,
            'lines': entry.lines,
            'level': entry.level,
            'mode': entry.mode
        }

        # Invalidate cache
        self._cache = None

        return self._submit_score_sync(payload)

    async def submit_score_async(self, entry: LeaderboardEntry) -> Tuple[bool, str]:
        """Submit a new score to the leaderboard asynchronously.

        Args:
            entry: LeaderboardEntry to submit

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.online_mode:
            return False, "Offline mode: No worker URL configured"

        payload = {
            'player_id': entry.player_id,
            'score': entry.score,
            'lines': entry.lines,
            'level': entry.level,
            'mode': entry.mode
        }

        # Invalidate cache
        self._cache = None

        if IS_WEB:
            result = await self._submit_score_web_async(payload)
            self._last_submit_result = result
            return result
        else:
            return self._submit_score_sync(payload)

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
