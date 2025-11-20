"""Tetromino block definitions (7 standard 4-block shapes for Classic mode)."""

from dataclasses import dataclass
from typing import List, Tuple
from .constants import (
    COLOR_CYAN, COLOR_YELLOW, COLOR_PURPLE, COLOR_GREEN,
    COLOR_RED, COLOR_BLUE, COLOR_ORANGE
)


@dataclass
class Block:
    """Base block class representing a game piece."""
    shape: List[List[int]]  # Rotation states as 2D matrices
    color: Tuple[int, int, int]
    x: int = 0  # Grid position X (column)
    y: int = 0  # Grid position Y (row)
    rotation: int = 0  # Current rotation index

    def get_cells(self) -> List[Tuple[int, int]]:
        """Get list of (x, y) coordinates of filled cells in current rotation."""
        cells = []
        current_shape = self.shape[self.rotation]
        for row_idx, row in enumerate(current_shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    cells.append((self.x + col_idx, self.y + row_idx))
        return cells

    def rotate_cw(self) -> None:
        """Rotate clockwise."""
        self.rotation = (self.rotation + 1) % len(self.shape)

    def rotate_ccw(self) -> None:
        """Rotate counter-clockwise."""
        self.rotation = (self.rotation - 1) % len(self.shape)

    def move(self, dx: int, dy: int) -> None:
        """Move block by offset."""
        self.x += dx
        self.y += dy

    def copy(self) -> 'Block':
        """Create a deep copy of this block."""
        return Block(
            shape=self.shape,
            color=self.color,
            x=self.x,
            y=self.y,
            rotation=self.rotation
        )


# Tetromino shape definitions using Super Rotation System (SRS)
# Each shape is a list of rotation states (0°, 90°, 180°, 270°)
# 1 = filled cell, 0 = empty cell

# I-piece (Cyan) - 4 blocks in a line
SHAPE_I = [
    # Rotation 0: Horizontal
    [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    # Rotation 90: Vertical
    [
        [0, 0, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 0],
    ],
    # Rotation 180: Horizontal (same as 0)
    [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
    ],
    # Rotation 270: Vertical (same as 90)
    [
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 0, 0],
    ],
]

# O-piece (Yellow) - 2x2 square
SHAPE_O = [
    # Only one rotation state (square is symmetric)
    [
        [1, 1],
        [1, 1],
    ],
]

# T-piece (Purple) - T-shape
SHAPE_T = [
    # Rotation 0: T pointing up
    [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
    ],
    # Rotation 90: T pointing right
    [
        [0, 1, 0],
        [0, 1, 1],
        [0, 1, 0],
    ],
    # Rotation 180: T pointing down
    [
        [0, 0, 0],
        [1, 1, 1],
        [0, 1, 0],
    ],
    # Rotation 270: T pointing left
    [
        [0, 1, 0],
        [1, 1, 0],
        [0, 1, 0],
    ],
]

# S-piece (Green) - S-shape
SHAPE_S = [
    # Rotation 0: Horizontal S
    [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0],
    ],
    # Rotation 90: Vertical S
    [
        [0, 1, 0],
        [0, 1, 1],
        [0, 0, 1],
    ],
    # Rotation 180: Horizontal S (same as 0)
    [
        [0, 0, 0],
        [0, 1, 1],
        [1, 1, 0],
    ],
    # Rotation 270: Vertical S (same as 90)
    [
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ],
]

# Z-piece (Red) - Z-shape
SHAPE_Z = [
    # Rotation 0: Horizontal Z
    [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0],
    ],
    # Rotation 90: Vertical Z
    [
        [0, 0, 1],
        [0, 1, 1],
        [0, 1, 0],
    ],
    # Rotation 180: Horizontal Z (same as 0)
    [
        [0, 0, 0],
        [1, 1, 0],
        [0, 1, 1],
    ],
    # Rotation 270: Vertical Z (same as 90)
    [
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
    ],
]

# J-piece (Blue) - J-shape
SHAPE_J = [
    # Rotation 0: J pointing up
    [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ],
    # Rotation 90: J pointing right
    [
        [0, 1, 1],
        [0, 1, 0],
        [0, 1, 0],
    ],
    # Rotation 180: J pointing down
    [
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 1],
    ],
    # Rotation 270: J pointing left
    [
        [0, 1, 0],
        [0, 1, 0],
        [1, 1, 0],
    ],
]

# L-piece (Orange) - L-shape
SHAPE_L = [
    # Rotation 0: L pointing up
    [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0],
    ],
    # Rotation 90: L pointing right
    [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 1],
    ],
    # Rotation 180: L pointing down
    [
        [0, 0, 0],
        [1, 1, 1],
        [1, 0, 0],
    ],
    # Rotation 270: L pointing left
    [
        [1, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ],
]


# Tetromino definitions
TETROMINOES = {
    'I': {'shape': SHAPE_I, 'color': COLOR_CYAN},
    'O': {'shape': SHAPE_O, 'color': COLOR_YELLOW},
    'T': {'shape': SHAPE_T, 'color': COLOR_PURPLE},
    'S': {'shape': SHAPE_S, 'color': COLOR_GREEN},
    'Z': {'shape': SHAPE_Z, 'color': COLOR_RED},
    'J': {'shape': SHAPE_J, 'color': COLOR_BLUE},
    'L': {'shape': SHAPE_L, 'color': COLOR_ORANGE},
}


def create_tetromino(piece_type: str) -> Block:
    """Create a new tetromino block of the specified type.

    Args:
        piece_type: One of 'I', 'O', 'T', 'S', 'Z', 'J', 'L'

    Returns:
        Block instance
    """
    if piece_type not in TETROMINOES:
        raise ValueError(f"Invalid tetromino type: {piece_type}")

    config = TETROMINOES[piece_type]
    return Block(
        shape=config['shape'],
        color=config['color'],
        x=0,  # Will be set by game logic to spawn position
        y=0,
        rotation=0
    )


def get_random_tetromino() -> Block:
    """Get a random tetromino."""
    import random
    piece_type = random.choice(list(TETROMINOES.keys()))
    return create_tetromino(piece_type)
