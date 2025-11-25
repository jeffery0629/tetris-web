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

# --- CUTE PASTEL COLOR PALETTE (UPDATED) ---

# Basic Colors
COLOR_BLACK = (60, 50, 60)  # Soft charcoal instead of pure black
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (180, 180, 190)
COLOR_DARK_GRAY = (100, 90, 100)
COLOR_LIGHT_GRAY = (220, 220, 230)

# Backgrounds (Gradient base colors)
COLOR_BG_TOP = (255, 240, 245)     # Very light pink
COLOR_BG_BOTTOM = (230, 230, 250)  # Lavender mist
COLOR_BACKGROUND = COLOR_BG_TOP    # Fallback solid color

COLOR_GRID_LINE = (200, 190, 210)  # Slightly darker for dots/fine lines
COLOR_BOARD_BG = (255, 255, 255, 200) # Semi-transparent white for board

# Text & UI
COLOR_TEXT = (80, 70, 90)          # Soft purple-grey text
COLOR_TEXT_SHADOW = (255, 255, 255) # White shadow/halo
COLOR_BUTTON_NORMAL = (255, 215, 225) # Pastel Pink Button
COLOR_BUTTON_HOVER = (255, 195, 205)
COLOR_BUTTON_LOCKED = (230, 230, 230)

# Macaron / Pastel Block Colors (Classic)
COLOR_CYAN = (130, 238, 253)       # I - Pastel Cyan
COLOR_YELLOW = (255, 245, 157)     # O - Pastel Yellow
COLOR_PURPLE = (209, 196, 233)     # T - Pastel Purple
COLOR_GREEN = (165, 214, 167)      # S - Pastel Green
COLOR_RED = (255, 171, 145)        # Z - Pastel Red/Salmon
COLOR_BLUE = (144, 202, 249)       # J - Pastel Blue
COLOR_ORANGE = (255, 204, 128)     # L - Pastel Orange

# Macaron Block Colors (Simple)
COLOR_LIGHT_BLUE = (179, 229, 252)  # I3 - Light Sky Blue
COLOR_LIGHT_ORANGE = (255, 224, 178) # L3 - Light Tangerine

# Macaron Block Colors (Crazy)
COLOR_PINK = (248, 187, 208)        # Pastel Pink
COLOR_TEAL = (178, 223, 219)        # Pastel Teal
COLOR_LIME = (220, 237, 200)        # Pastel Lime
COLOR_MAGENTA = (244, 143, 177)     # Pastel Magenta
COLOR_NAVY = (159, 168, 218)        # Pastel Indigo
COLOR_OLIVE = (230, 238, 156)       # Pastel Olive
COLOR_MAROON = (239, 154, 154)      # Pastel Red
COLOR_AQUA = (128, 222, 234)        # Pastel Aqua
COLOR_FUCHSIA = (240, 98, 146)      # Pastel Fuchsia (slightly darker for contrast)
COLOR_SILVER = (207, 216, 220)      # Pastel Blue Grey
COLOR_GOLD = (255, 229, 127)        # Pastel Gold
COLOR_CORAL = (255, 138, 101)       # Pastel Coral

# Power-up colors
COLOR_POWERUP_GLOW = (255, 255, 200)
COLOR_POWERUP_BORDER = (255, 255, 255)

class GameState(Enum):
    """Game state enumeration."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    GAME_OVER_INPUT = "game_over_input"  # Waiting for player ID input
    SUBMITTING_SCORE = "submitting_score"  # Async score submission in progress
    LEADERBOARD = "leaderboard"  # Showing leaderboard
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
