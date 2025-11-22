"""Game constants and configuration."""

from enum import Enum
from typing import Tuple

# Window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 750
FPS = 60

# Cell size for rendering (in pixels)
# Increased from 27 to 30 (+11%) to make game board larger
CELL_SIZE = 30

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

# Vibrant Block Colors with 3D effect (Classic)
COLOR_CYAN = (0, 240, 255)          # I - Bright Cyan
COLOR_YELLOW = (255, 220, 0)        # O - Golden Yellow
COLOR_PURPLE = (180, 0, 255)        # T - Vibrant Purple
COLOR_GREEN = (0, 255, 100)         # S - Bright Green
COLOR_RED = (255, 50, 50)           # Z - Bright Red
COLOR_BLUE = (0, 100, 255)          # J - Deep Blue
COLOR_ORANGE = (255, 140, 0)        # L - Vibrant Orange

# Vibrant Block Colors (Simple)
COLOR_LIGHT_BLUE = (100, 200, 255)  # I3 - Sky Blue
COLOR_LIGHT_ORANGE = (255, 160, 80) # L3 - Tangerine

# Vibrant Block Colors (Crazy) - Saturated Palette
COLOR_PINK = (255, 105, 180)        # Hot Pink
COLOR_TEAL = (0, 200, 200)          # Turquoise
COLOR_LIME = (180, 255, 0)          # Neon Lime
COLOR_MAGENTA = (255, 0, 255)       # Magenta
COLOR_NAVY = (70, 70, 200)          # Navy Blue
COLOR_OLIVE = (180, 180, 0)         # Olive
COLOR_MAROON = (180, 0, 0)          # Maroon
COLOR_AQUA = (0, 255, 255)          # Aqua
COLOR_FUCHSIA = (255, 0, 200)       # Fuchsia
COLOR_SILVER = (192, 192, 192)      # Silver
COLOR_GOLD = (255, 215, 0)          # Gold
COLOR_CORAL = (255, 127, 80)        # Coral

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
    MAGNET = "magnet"          # Gravity compress - drop all floating blocks
    TIME_FREEZE = "time_freeze"  # Pause falling
    GRAVITY_REVERSE = "gravity_reverse"  # Blocks fall upward
    LINE_ERASER = "line_eraser"  # Clear bottom 2 rows
    GHOST_MODE = "ghost_mode"    # Next 3 blocks can overlap


# Unlock requirements
UNLOCK_REQUIREMENTS = {
    GameMode.CASUAL: 0,      # Always unlocked
    GameMode.CLASSIC: 0,     # Always unlocked
    GameMode.CRAZY: 0,       # Always unlocked (was 50 lines)
}

# Save file
SAVE_FILE_PATH = "tetris_save.json"
SAVE_FILE_VERSION = "1.0"
