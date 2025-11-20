"""Game board logic: grid, collision detection, line clearing."""

from typing import List, Tuple, Optional
from .tetromino import Block
from .constants import CLASSIC_GRID


class Board:
    """Game board that manages the grid and placed blocks."""

    def __init__(self, width: int = CLASSIC_GRID[0], height: int = CLASSIC_GRID[1]):
        """Initialize board with specified dimensions.

        Args:
            width: Number of columns
            height: Number of rows
        """
        self.width = width
        self.height = height
        # Grid stores color tuples for placed blocks, None for empty cells
        self.grid: List[List[Optional[Tuple[int, int, int]]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

    def is_valid_position(self, block: Block) -> bool:
        """Check if block position is valid (no collision).

        Args:
            block: Block to check

        Returns:
            True if position is valid, False otherwise
        """
        cells = block.get_cells()
        for x, y in cells:
            # Check boundaries
            if x < 0 or x >= self.width or y >= self.height:
                return False
            # Allow blocks above the visible area (y < 0) during spawn
            if y >= 0:
                # Check collision with placed blocks
                if self.grid[y][x] is not None:
                    return False
        return True

    def place_block(self, block: Block) -> None:
        """Place block on the board permanently.

        Args:
            block: Block to place
        """
        cells = block.get_cells()
        for x, y in cells:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = block.color

    def clear_lines(self) -> int:
        """Clear completed lines and return number of lines cleared.

        Returns:
            Number of lines cleared
        """
        lines_cleared = 0
        # Check from bottom to top
        y = self.height - 1
        while y >= 0:
            if all(cell is not None for cell in self.grid[y]):
                # Line is full, remove it
                del self.grid[y]
                # Add empty line at top
                self.grid.insert(0, [None for _ in range(self.width)])
                lines_cleared += 1
                # Don't decrement y, check same row again
            else:
                y -= 1
        return lines_cleared

    def is_game_over(self, spawn_y: int = 0) -> bool:
        """Check if game is over (blocks stacked to spawn position).

        Args:
            spawn_y: Y position where new blocks spawn

        Returns:
            True if game over, False otherwise
        """
        # Check if spawn row has any blocks
        if spawn_y < 0 or spawn_y >= self.height:
            return False
        return any(cell is not None for cell in self.grid[spawn_y])

    def get_cell(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """Get color of cell at position.

        Args:
            x: Column
            y: Row

        Returns:
            Color tuple or None if empty/out of bounds
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def clear(self) -> None:
        """Clear the entire board."""
        self.grid = [
            [None for _ in range(self.width)] for _ in range(self.height)
        ]

    def get_drop_position(self, block: Block) -> int:
        """Get the Y position where block would land if hard dropped.

        Args:
            block: Block to check

        Returns:
            Y position where block would land
        """
        test_block = block.copy()
        while self.is_valid_position(test_block):
            test_block.y += 1
        return test_block.y - 1

    def clear_area(self, center_x: int, center_y: int, radius: int = 1) -> int:
        """Clear blocks in an area (for bomb power-up).

        Args:
            center_x: Center column
            center_y: Center row
            radius: Radius of area to clear (1 = 3x3, 2 = 5x5)

        Returns:
            Number of cells cleared
        """
        cleared = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    if self.grid[y][x] is not None:
                        self.grid[y][x] = None
                        cleared += 1
        return cleared

    def find_most_problematic_area(self, radius: int = 1) -> tuple:
        """Find the area with most mixed empty/filled cells (problematic holes).

        Args:
            radius: Radius of area (1 = 3x3, 2 = 5x5)

        Returns:
            Tuple of (center_x, center_y, problem_score)
        """
        best_x, best_y, max_score = 0, 0, 0

        # Search entire board for most problematic area
        for y in range(radius, self.height - radius):
            for x in range(radius, self.width - radius):
                # Count filled and empty cells
                filled = 0
                empty = 0
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        if self.grid[y + dy][x + dx] is not None:
                            filled += 1
                        else:
                            empty += 1

                # Problem score: areas with both filled and empty are problematic
                # Maximum score when 50/50 mix (most chaotic)
                # Score = filled * empty (highest when both are non-zero)
                problem_score = filled * empty

                if problem_score > max_score:
                    max_score = problem_score
                    best_x = x
                    best_y = y

        return (best_x, best_y, max_score)

    def clear_bottom_rows(self, num_rows: int = 2) -> int:
        """Clear bottom N rows (for line eraser power-up).

        Args:
            num_rows: Number of rows to clear from bottom

        Returns:
            Number of cells cleared
        """
        cleared = 0
        for _ in range(min(num_rows, self.height)):
            # Remove bottom row
            bottom_row = self.grid.pop()
            cleared += sum(1 for cell in bottom_row if cell is not None)
            # Add empty row at top
            self.grid.insert(0, [None for _ in range(self.width)])
        return cleared
