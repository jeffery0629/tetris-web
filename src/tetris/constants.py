"""Game constants and configuration."""

from enum import Enum
from typing import Tuple

# Window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 750
FPS = 60

# Cell size for rendering (in pixels)
CELL_SIZE = 27

# Grid dimensions for different modes
SIMPLE_GRID = (8, 16)    # (cols, rows)
CLASSIC_GRID = (10, 20)
CRAZY_GRID = (12, 22)

# Game timing
INITIAL_FALL_SPEED = 1.0  # seconds per row fall
LOCK_DELAY = 0.5          # seconds before block locks
SPEED_INCREASE_PER_LEVEL = 0.9  # multiply fall speed by this each level

# Scoring
SCORE_SINGLE_LINE = 100
SCORE_DOUBLE_LINE = 300
SCORE_TRIPLE_LINE = 500
SCORE_QUAD_LINE = 800
SCORE_SOFT_DROP = 1
SCORE_HARD_DROP = 2

# Mode multipliers
SCORE_MULTIPLIERS = {
    'casual': 0.8,
    'classic': 1.0,
    'crazy': 2.0,
}

# Level progression
LINES_PER_LEVEL = 10

# Power-up settings
POWERUP_SPAWN_RATE = 0.20
MAX_POWERUP_INVENTORY = 2

# --- CUTE PASTEL COLOR PALETTE ---

# Basic Colors
COLOR_BLACK = (60, 50, 60)  # Soft charcoal instead of pure black
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (180, 180, 190)
COLOR_DARK_GRAY = (100, 90, 100)
COLOR_LIGHT_GRAY = (220, 220, 230)

# Backgrounds
COLOR_BACKGROUND = (255, 248, 250)  # Creamy Pink / White
COLOR_GRID_LINE = (240, 220, 230)   # Very faint pink grid
COLOR_BOARD_BG = (255, 255, 255)    # Pure white board background

# Text & UI
COLOR_TEXT = (90, 80, 100)          # Soft purple-grey text
COLOR_TEXT_SHADOW = (255, 255, 255) # White shadow/halo
COLOR_BUTTON_NORMAL = (255, 200, 210) # Pastel Pink Button
COLOR_BUTTON_HOVER = (255, 180, 195)
COLOR_BUTTON_LOCKED = (230, 230, 230)

# Pastel Block Colors (Classic)
COLOR_CYAN = (150, 230, 240)        # I - Soft Cyan
COLOR_YELLOW = (255, 245, 150)      # O - Butter Yellow
COLOR_PURPLE = (220, 180, 240)      # T - Lavender
COLOR_GREEN = (160, 235, 160)       # S - Mint
COLOR_RED = (255, 160, 160)         # Z - Salmon Pink
COLOR_BLUE = (160, 190, 255)        # J - Periwinkle
COLOR_ORANGE = (255, 200, 150)      # L - Peach

# Pastel Block Colors (Simple)
COLOR_LIGHT_BLUE = (180, 220, 255)  # I3
COLOR_LIGHT_ORANGE = (255, 220, 180) # L3

# Pastel Block Colors (Crazy) - Expanded Macaron Palette
COLOR_PINK = (255, 192, 203)
COLOR_TEAL = (140, 210, 210)
COLOR_LIME = (210, 255, 160)
COLOR_MAGENTA = (240, 160, 240)
COLOR_NAVY = (140, 140, 200)
COLOR_OLIVE = (200, 200, 140)
COLOR_MAROON = (200, 140, 140)
COLOR_AQUA = (160, 240, 240)
COLOR_FUCHSIA = (240, 140, 240)
COLOR_SILVER = (210, 210, 220)
COLOR_GOLD = (255, 230, 140)
COLOR_CORAL = (255, 180, 160)

# Power-up colors
COLOR_POWERUP_GLOW = (255, 255, 200)
COLOR_POWERUP_BORDER = (255, 255, 255)

class GameState(Enum):
    """Game state enumeration."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    MODE_UNLOCKED = "mode_unlocked"


class GameMode(Enum):
    """Game mode enumeration."""
    CASUAL = "casual"
    CLASSIC = "classic"
    CRAZY = "crazy"


class PowerUpType(Enum):
    """Power-up type enumeration."""
    BOMB = "bomb"              # Clears 3x3 area
    RAINBOW = "rainbow"        # Wildcard block
    TIME_FREEZE = "time_freeze"  # Pause falling
    GRAVITY_REVERSE = "gravity_reverse"  # Blocks fall upward
    LINE_ERASER = "line_eraser"  # Clear bottom 2 rows
    GHOST_MODE = "ghost_mode"    # Next 3 blocks can overlap


# Unlock requirements
UNLOCK_REQUIREMENTS = {
    GameMode.CASUAL: 0,      # Always unlocked
    GameMode.CLASSIC: 0,     # Always unlocked
    GameMode.CRAZY: 50,      # Unlock after 50 lines cleared in any mode
}

# Save file
SAVE_FILE_PATH = "tetris_save.json"
SAVE_FILE_VERSION = "1.0"
