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

        # Pending async results (for Web version)
        self._pending_fetch_result: Optional[Dict] = None
        self._pending_submit_result: Optional[Tuple[bool, str]] = None

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

    def _fetch_leaderboard_web(self) -> Optional[Dict]:
        """Fetch leaderboard using browser fetch API (Web/Pygbag)."""
        try:
            import platform
            if platform.window:
                # Use JavaScript fetch via Pygbag
                url = f'{self.worker_url}/leaderboard'
                # Use synchronous XMLHttpRequest for simplicity
                js_code = f"""
                (function() {{
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', '{url}', false);  // false = synchronous
                    xhr.send(null);
                    if (xhr.status === 200) {{
                        return xhr.responseText;
                    }}
                    return null;
                }})()
                """
                result = platform.window.eval(js_code)
                if result:
                    return json.loads(result)
        except Exception as e:
            print(f"Error fetching leaderboard (web): {e}")
        return None

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

        # Use appropriate method based on platform
        if IS_WEB:
            data = self._fetch_leaderboard_web()
        else:
            data = self._fetch_leaderboard_sync()

        if data:
            self._cache = data
            self._cache_time = time.time()

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

    def _submit_score_web(self, payload: Dict) -> Tuple[bool, str]:
        """Submit score using browser fetch API (Web/Pygbag)."""
        try:
            import platform
            if platform.window:
                url = f'{self.worker_url}/submit'
                payload_json = json.dumps(payload)
                # Use synchronous XMLHttpRequest
                js_code = f"""
                (function() {{
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', '{url}', false);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.send('{payload_json}');
                    return JSON.stringify({{status: xhr.status, text: xhr.responseText}});
                }})()
                """
                result_str = platform.window.eval(js_code)
                if result_str:
                    result = json.loads(result_str)
                    if result['status'] == 200:
                        data = json.loads(result['text'])
                        return True, data.get('message', 'Score submitted!')
                    else:
                        try:
                            error_data = json.loads(result['text'])
                            error_msg = error_data.get('error', f"HTTP {result['status']}")
                        except Exception:
                            error_msg = f"HTTP {result['status']}"
                        return False, f"Failed to submit: {error_msg}"
        except Exception as e:
            print(f"Error submitting score (web): {e}")
        return False, "Failed to submit score (network error)"

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

        payload = {
            'player_id': entry.player_id,
            'score': entry.score,
            'lines': entry.lines,
            'level': entry.level,
            'mode': entry.mode
        }

        # Invalidate cache before submit
        self._cache = None

        # Use appropriate method based on platform
        if IS_WEB:
            return self._submit_score_web(payload)
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
