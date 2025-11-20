"""Pentomino block definitions (18 different 5-block shapes for Crazy mode)."""

from dataclasses import dataclass
from typing import List, Tuple
from .tetromino import Block
from .constants import (
    COLOR_PINK, COLOR_TEAL, COLOR_LIME, COLOR_MAGENTA,
    COLOR_NAVY, COLOR_OLIVE, COLOR_MAROON, COLOR_AQUA,
    COLOR_FUCHSIA, COLOR_SILVER, COLOR_GOLD, COLOR_CORAL,
    COLOR_CYAN, COLOR_PURPLE, COLOR_GREEN, COLOR_RED,
    COLOR_BLUE, COLOR_ORANGE
)


# Pentomino shape definitions (5 blocks each)
# 18 different shapes: F, I, L, N, P, T, U, V, W, X, Y, Z + 6 mirrored variants

# F-pentomino
SHAPE_PENTO_F = [
    [
        [0, 1, 1],
        [1, 1, 0],
        [0, 1, 0],
    ],
    [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 1],
    ],
    [
        [0, 1, 0],
        [0, 1, 1],
        [1, 1, 0],
    ],
    [
        [1, 0, 0],
        [1, 1, 1],
        [0, 1, 0],
    ],
]

# F-pentomino mirrored
SHAPE_PENTO_F_MIRROR = [
    [
        [1, 1, 0],
        [0, 1, 1],
        [0, 1, 0],
    ],
    [
        [0, 0, 1],
        [1, 1, 1],
        [0, 1, 0],
    ],
    [
        [0, 1, 0],
        [1, 1, 0],
        [0, 1, 1],
    ],
    [
        [0, 1, 0],
        [1, 1, 1],
        [1, 0, 0],
    ],
]

# I-pentomino (5 in a line)
SHAPE_PENTO_I = [
    [
        [1, 1, 1, 1, 1],
    ],
    [
        [1],
        [1],
        [1],
        [1],
        [1],
    ],
]

# L-pentomino
SHAPE_PENTO_L = [
    [
        [1, 0],
        [1, 0],
        [1, 0],
        [1, 1],
    ],
    [
        [1, 1, 1, 1],
        [1, 0, 0, 0],
    ],
    [
        [1, 1],
        [0, 1],
        [0, 1],
        [0, 1],
    ],
    [
        [0, 0, 0, 1],
        [1, 1, 1, 1],
    ],
]

# L-pentomino mirrored
SHAPE_PENTO_L_MIRROR = [
    [
        [0, 1],
        [0, 1],
        [0, 1],
        [1, 1],
    ],
    [
        [1, 0, 0, 0],
        [1, 1, 1, 1],
    ],
    [
        [1, 1],
        [1, 0],
        [1, 0],
        [1, 0],
    ],
    [
        [1, 1, 1, 1],
        [0, 0, 0, 1],
    ],
]

# N-pentomino
SHAPE_PENTO_N = [
    [
        [0, 1],
        [1, 1],
        [1, 0],
        [1, 0],
    ],
    [
        [1, 1, 0, 0],
        [0, 1, 1, 1],
    ],
    [
        [0, 1],
        [0, 1],
        [1, 1],
        [1, 0],
    ],
    [
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ],
]

# N-pentomino mirrored
SHAPE_PENTO_N_MIRROR = [
    [
        [1, 0],
        [1, 1],
        [0, 1],
        [0, 1],
    ],
    [
        [0, 1, 1, 1],
        [1, 1, 0, 0],
    ],
    [
        [1, 0],
        [1, 0],
        [1, 1],
        [0, 1],
    ],
    [
        [0, 0, 1, 1],
        [1, 1, 1, 0],
    ],
]

# P-pentomino
SHAPE_PENTO_P = [
    [
        [1, 1],
        [1, 1],
        [1, 0],
    ],
    [
        [1, 1, 1],
        [0, 1, 1],
    ],
    [
        [0, 1],
        [1, 1],
        [1, 1],
    ],
    [
        [1, 1, 0],
        [1, 1, 1],
    ],
]

# P-pentomino mirrored
SHAPE_PENTO_P_MIRROR = [
    [
        [1, 1],
        [1, 1],
        [0, 1],
    ],
    [
        [0, 1, 1],
        [1, 1, 1],
    ],
    [
        [1, 0],
        [1, 1],
        [1, 1],
    ],
    [
        [1, 1, 1],
        [1, 1, 0],
    ],
]

# T-pentomino
SHAPE_PENTO_T = [
    [
        [1, 1, 1],
        [0, 1, 0],
        [0, 1, 0],
    ],
    [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
    ],
    [
        [0, 1, 0],
        [0, 1, 0],
        [1, 1, 1],
    ],
    [
        [1, 0, 0],
        [1, 1, 1],
        [1, 0, 0],
    ],
]

# U-pentomino
SHAPE_PENTO_U = [
    [
        [1, 0, 1],
        [1, 1, 1],
    ],
    [
        [1, 1],
        [1, 0],
        [1, 1],
    ],
    [
        [1, 1, 1],
        [1, 0, 1],
    ],
    [
        [1, 1],
        [0, 1],
        [1, 1],
    ],
]

# V-pentomino
SHAPE_PENTO_V = [
    [
        [1, 0, 0],
        [1, 0, 0],
        [1, 1, 1],
    ],
    [
        [1, 1, 1],
        [1, 0, 0],
        [1, 0, 0],
    ],
    [
        [1, 1, 1],
        [0, 0, 1],
        [0, 0, 1],
    ],
    [
        [0, 0, 1],
        [0, 0, 1],
        [1, 1, 1],
    ],
]

# W-pentomino
SHAPE_PENTO_W = [
    [
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 1],
    ],
    [
        [0, 1, 1],
        [1, 1, 0],
        [1, 0, 0],
    ],
    [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 1],
    ],
    [
        [0, 0, 1],
        [0, 1, 1],
        [1, 1, 0],
    ],
]

# X-pentomino (plus sign)
SHAPE_PENTO_X = [
    [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
    ],
]

# Y-pentomino
SHAPE_PENTO_Y = [
    [
        [0, 1],
        [1, 1],
        [0, 1],
        [0, 1],
    ],
    [
        [0, 0, 1, 0],
        [1, 1, 1, 1],
    ],
    [
        [1, 0],
        [1, 0],
        [1, 1],
        [1, 0],
    ],
    [
        [1, 1, 1, 1],
        [0, 1, 0, 0],
    ],
]

# Y-pentomino mirrored
SHAPE_PENTO_Y_MIRROR = [
    [
        [1, 0],
        [1, 1],
        [1, 0],
        [1, 0],
    ],
    [
        [1, 1, 1, 1],
        [0, 0, 1, 0],
    ],
    [
        [0, 1],
        [0, 1],
        [1, 1],
        [0, 1],
    ],
    [
        [0, 1, 0, 0],
        [1, 1, 1, 1],
    ],
]

# Z-pentomino
SHAPE_PENTO_Z = [
    [
        [1, 1, 0],
        [0, 1, 0],
        [0, 1, 1],
    ],
    [
        [0, 0, 1],
        [1, 1, 1],
        [1, 0, 0],
    ],
    [
        [1, 1, 0],
        [0, 1, 0],
        [0, 1, 1],
    ],
    [
        [0, 0, 1],
        [1, 1, 1],
        [1, 0, 0],
    ],
]

# Z-pentomino mirrored
SHAPE_PENTO_Z_MIRROR = [
    [
        [0, 1, 1],
        [0, 1, 0],
        [1, 1, 0],
    ],
    [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 1],
    ],
    [
        [0, 1, 1],
        [0, 1, 0],
        [1, 1, 0],
    ],
    [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 1],
    ],
]


# Pentomino definitions
PENTOMINOES = {
    'F': {'shape': SHAPE_PENTO_F, 'color': COLOR_PINK},
    'F_MIRROR': {'shape': SHAPE_PENTO_F_MIRROR, 'color': COLOR_TEAL},
    'I': {'shape': SHAPE_PENTO_I, 'color': COLOR_CYAN},
    'L': {'shape': SHAPE_PENTO_L, 'color': COLOR_LIME},
    'L_MIRROR': {'shape': SHAPE_PENTO_L_MIRROR, 'color': COLOR_MAGENTA},
    'N': {'shape': SHAPE_PENTO_N, 'color': COLOR_NAVY},
    'N_MIRROR': {'shape': SHAPE_PENTO_N_MIRROR, 'color': COLOR_OLIVE},
    'P': {'shape': SHAPE_PENTO_P, 'color': COLOR_MAROON},
    'P_MIRROR': {'shape': SHAPE_PENTO_P_MIRROR, 'color': COLOR_AQUA},
    'T': {'shape': SHAPE_PENTO_T, 'color': COLOR_PURPLE},
    'U': {'shape': SHAPE_PENTO_U, 'color': COLOR_FUCHSIA},
    'V': {'shape': SHAPE_PENTO_V, 'color': COLOR_SILVER},
    'W': {'shape': SHAPE_PENTO_W, 'color': COLOR_GOLD},
    'X': {'shape': SHAPE_PENTO_X, 'color': COLOR_CORAL},
    'Y': {'shape': SHAPE_PENTO_Y, 'color': COLOR_GREEN},
    'Y_MIRROR': {'shape': SHAPE_PENTO_Y_MIRROR, 'color': COLOR_RED},
    'Z': {'shape': SHAPE_PENTO_Z, 'color': COLOR_BLUE},
    'Z_MIRROR': {'shape': SHAPE_PENTO_Z_MIRROR, 'color': COLOR_ORANGE},
}


def create_pentomino(piece_type: str) -> Block:
    """Create a new pentomino block of the specified type.

    Args:
        piece_type: One of the 18 pentomino types

    Returns:
        Block instance
    """
    if piece_type not in PENTOMINOES:
        raise ValueError(f"Invalid pentomino type: {piece_type}")

    config = PENTOMINOES[piece_type]
    return Block(
        shape=config['shape'],
        color=config['color'],
        x=0,
        y=0,
        rotation=0
    )


def get_random_pentomino() -> Block:
    """Get a random pentomino."""
    import random
    piece_type = random.choice(list(PENTOMINOES.keys()))
    return create_pentomino(piece_type)
