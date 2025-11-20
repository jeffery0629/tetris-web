"""Game mode configurations and management."""

from dataclasses import dataclass
from typing import Callable
from .constants import (
    GameMode, CLASSIC_GRID, CRAZY_GRID,
    SCORE_MULTIPLIERS
)


@dataclass
class ModeConfig:
    """Configuration for a game mode."""
    name: str
    display_name: str
    grid_size: tuple  # (width, height)
    score_multiplier: float
    block_generator: Callable  # Function to generate random blocks
    power_ups_enabled: bool
    unlock_requirement: int  # Lines needed to unlock (0 = always unlocked)
    description: str


# Mode configurations
MODE_CONFIGS = {
    GameMode.CASUAL: ModeConfig(
        name="casual",
        display_name="Casual",
        grid_size=CLASSIC_GRID,
        score_multiplier=SCORE_MULTIPLIERS['casual'],
        block_generator=None,  # Will be set to get_random_tetromino
        power_ups_enabled=True,  # Power-ups enabled for fun
        unlock_requirement=0,
        description="7 classic pieces + helpful power-ups"
    ),
    GameMode.CLASSIC: ModeConfig(
        name="classic",
        display_name="Classic",
        grid_size=CLASSIC_GRID,
        score_multiplier=SCORE_MULTIPLIERS['classic'],
        block_generator=None,  # Will be set to get_random_tetromino
        power_ups_enabled=False,  # Pure Tetris, no power-ups
        unlock_requirement=0,
        description="Pure Tetris - 7 pieces, no power-ups"
    ),
    GameMode.CRAZY: ModeConfig(
        name="crazy",
        display_name="Crazy",
        grid_size=CRAZY_GRID,
        score_multiplier=SCORE_MULTIPLIERS['crazy'],
        block_generator=None,  # Will be set to get_random_pentomino
        power_ups_enabled=True,
        unlock_requirement=50,  # Unlock after 50 lines in any mode
        description="18 pentominoes + power-ups - extreme!"
    ),
}


def get_mode_config(mode: GameMode) -> ModeConfig:
    """Get configuration for a game mode.

    Args:
        mode: GameMode enum value

    Returns:
        ModeConfig instance
    """
    return MODE_CONFIGS[mode]


def is_mode_unlocked(mode: GameMode, total_lines_cleared: int) -> bool:
    """Check if a mode is unlocked.

    Args:
        mode: GameMode to check
        total_lines_cleared: Total lines cleared across all modes

    Returns:
        True if unlocked, False otherwise
    """
    config = get_mode_config(mode)
    return total_lines_cleared >= config.unlock_requirement
