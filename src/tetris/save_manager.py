"""Save/load game data using JSON."""

import json
from pathlib import Path
from typing import Dict, Any
from .constants import SAVE_FILE_PATH, SAVE_FILE_VERSION, GameMode


class SaveManager:
    """Manages game save data."""

    def __init__(self, save_path: str = SAVE_FILE_PATH):
        """Initialize save manager."""
        self.save_path = Path(save_path)
        self.data = self._load_or_create()

    def _get_default_data(self) -> Dict[str, Any]:
        """Get default save data structure."""
        return {
            "version": SAVE_FILE_VERSION,
            "high_scores": {
                "casual": 0,
                "classic": 0,
                "crazy": 0,
            },
            "total_lines": {
                "casual": 0,
                "classic": 0,
                "crazy": 0,
            },
            "total_playtime": {
                "casual": 0.0,
                "classic": 0.0,
                "crazy": 0.0,
            },
            "unlocked_modes": ["casual", "classic"],
            "settings": {
                "volume": 0.7,
                "show_ghost": True,
            }
        }

    def _load_or_create(self) -> Dict[str, Any]:
        """Load save data or create new if doesn't exist."""
        if not self.save_path.exists():
            return self._get_default_data()

        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate version
            if data.get("version") != SAVE_FILE_VERSION:
                return self._get_default_data()

            return data
        except (json.JSONDecodeError, IOError):
            return self._get_default_data()

    def save(self) -> bool:
        """Save current data to file."""
        try:
            # Create backup
            if self.save_path.exists():
                backup_path = self.save_path.with_suffix('.bak')
                self.save_path.replace(backup_path)

            # Write new data
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            return True
        except IOError:
            return False

    def get_high_score(self, mode: str) -> int:
        """Get high score for a mode."""
        return self.data["high_scores"].get(mode, 0)

    def update_high_score(self, mode: str, score: int) -> bool:
        """Update high score if new score is higher."""
        current = self.get_high_score(mode)
        if score > current:
            self.data["high_scores"][mode] = score
            self.save()
            return True
        return False

    def add_lines(self, mode: str, lines: int) -> None:
        """Add cleared lines to total."""
        if mode not in self.data["total_lines"]:
            self.data["total_lines"][mode] = 0
        self.data["total_lines"][mode] += lines
        self.save()

    def get_total_lines(self, mode: str = None) -> int:
        """Get total lines cleared."""
        if mode:
            return self.data["total_lines"].get(mode, 0)
        else:
            return sum(self.data["total_lines"].values())

    def is_mode_unlocked(self, mode: str) -> bool:
        """Check if a mode is unlocked."""
        return mode in self.data["unlocked_modes"]

    def unlock_mode(self, mode: str) -> None:
        """Unlock a mode."""
        if mode not in self.data["unlocked_modes"]:
            self.data["unlocked_modes"].append(mode)
            self.save()

    def check_and_unlock_modes(self) -> list[str]:
        """Check if any modes should be unlocked based on progress."""
        newly_unlocked = []
        total_lines = self.get_total_lines()

        # Unlock Crazy mode after 50 lines
        if total_lines >= 50 and not self.is_mode_unlocked("crazy"):
            self.unlock_mode("crazy")
            newly_unlocked.append("crazy")

        return newly_unlocked

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.data["settings"].get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.data["settings"][key] = value
        self.save()
