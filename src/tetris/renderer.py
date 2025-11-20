"""Pygame rendering system for game graphics (Cute Style)."""

import pygame
from typing import Optional, Tuple
from .board import Board
from .tetromino import Block
from .constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, CELL_SIZE,
    COLOR_BACKGROUND, COLOR_GRID_LINE, COLOR_TEXT,
    COLOR_WHITE, COLOR_BLACK, COLOR_DARK_GRAY,
    COLOR_LIGHT_GRAY, COLOR_GRAY, COLOR_BOARD_BG, COLOR_BUTTON_NORMAL,
    COLOR_BUTTON_HOVER, COLOR_YELLOW, COLOR_GREEN,
    GameState
)


class Renderer:
    """Handles all game rendering using Pygame with a cute aesthetic."""

    def __init__(self):
        """Initialize Pygame and create window."""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Claire's Tetris 💖")

        # Try to load cute fonts, fallback to default
        # Priority: Arial Rounded MT Bold (common cute font), Comic Sans MS (actually good for cute UI), Microsoft JhengHei
        self.font_name = pygame.font.match_font('arialroundedmtbold') 
        if not self.font_name:
             self.font_name = pygame.font.match_font('comicsansms')
        if not self.font_name:
             self.font_name = pygame.font.match_font('microsoftjhenghei')

        self.font_large = pygame.font.Font(self.font_name, 72)
        self.font_medium = pygame.font.Font(self.font_name, 48)
        self.font_small = pygame.font.Font(self.font_name, 28)  # Slightly larger for readability
        self.font_tiny = pygame.font.Font(self.font_name, 20)

        # Load cat icon for title display
        try:
            cat_img = pygame.image.load("images/cat.jpg")
            self.cat_icon = pygame.transform.scale(cat_img, (40, 40))
        except (pygame.error, FileNotFoundError):
            self.cat_icon = None

    def draw_rounded_rect(self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], radius: int = 10, width: int = 0) -> None:
        """Helper to draw rounded rectangles."""
        pygame.draw.rect(surface, color, rect, width, border_radius=radius)

    def draw_cell(self, x: int, y: int, color: Tuple[int, int, int],
                  offset_x: int = 0, offset_y: int = 0, alpha: int = 255) -> None:
        """Draw a single cell (block) with classic Tetris style."""

        # Pixel coordinates
        px = offset_x + x * CELL_SIZE
        py = offset_y + y * CELL_SIZE

        # Main block body
        rect = pygame.Rect(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2)

        if alpha < 255:
            # Ghost piece with transparency
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color, alpha), (1, 1, CELL_SIZE - 2, CELL_SIZE - 2))
            pygame.draw.rect(s, (0, 0, 0, alpha), (1, 1, CELL_SIZE - 2, CELL_SIZE - 2), 2)
            self.screen.blit(s, (px, py))
        else:
            # Solid block with classic 3D effect
            # Fill main color
            pygame.draw.rect(self.screen, color, rect)

            # Light edges (top and left) - classic 3D highlight
            lighter = (min(255, color[0] + 80), min(255, color[1] + 80), min(255, color[2] + 80))
            pygame.draw.line(self.screen, lighter, (px + 1, py + 1), (px + CELL_SIZE - 2, py + 1), 3)  # Top
            pygame.draw.line(self.screen, lighter, (px + 1, py + 1), (px + 1, py + CELL_SIZE - 2), 3)  # Left

            # Dark edges (bottom and right) - classic 3D shadow
            darker = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
            pygame.draw.line(self.screen, darker, (px + 1, py + CELL_SIZE - 2), (px + CELL_SIZE - 2, py + CELL_SIZE - 2), 3)  # Bottom
            pygame.draw.line(self.screen, darker, (px + CELL_SIZE - 2, py + 1), (px + CELL_SIZE - 2, py + CELL_SIZE - 2), 3)  # Right

            # Black outer border
            pygame.draw.rect(self.screen, (0, 0, 0), (px, py, CELL_SIZE, CELL_SIZE), 1)

    def draw_board(self, board: Board, offset_x: int = 50, offset_y: int = 50) -> None:
        """Draw the game board grid and placed blocks."""
        
        # Draw Board Background (Container)
        board_rect = pygame.Rect(
            offset_x - 5, 
            offset_y - 5, 
            board.width * CELL_SIZE + 10, 
            board.height * CELL_SIZE + 10
        )
        self.draw_rounded_rect(self.screen, board_rect, COLOR_WHITE, radius=10)
        pygame.draw.rect(self.screen, COLOR_GRID_LINE, board_rect, 3, border_radius=10)

        # Draw soft grid lines (dots or very light lines)
        for y in range(board.height + 1):
            start_pos = (offset_x, offset_y + y * CELL_SIZE)
            end_pos = (offset_x + board.width * CELL_SIZE, offset_y + y * CELL_SIZE)
            pygame.draw.line(self.screen, COLOR_GRID_LINE, start_pos, end_pos, 1)
            
        for x in range(board.width + 1):
            start_pos = (offset_x + x * CELL_SIZE, offset_y)
            end_pos = (offset_x + x * CELL_SIZE, offset_y + board.height * CELL_SIZE)
            pygame.draw.line(self.screen, COLOR_GRID_LINE, start_pos, end_pos, 1)

        # Draw placed blocks
        for y in range(board.height):
            for x in range(board.width):
                color = board.get_cell(x, y)
                if color:
                    self.draw_cell(x, y, color, offset_x, offset_y)

    def draw_block(self, block: Block, offset_x: int = 50, offset_y: int = 50,
                   alpha: int = 255, is_powerup: bool = False) -> None:
        """Draw a falling block."""
        cells = block.get_cells()
        for x, y in cells:
            if y >= 0:  # Only draw visible cells
                self.draw_cell(x, y, block.color, offset_x, offset_y, alpha)

                # Draw star/icon indicator for power-up blocks
                if is_powerup:
                    cell_x = offset_x + x * CELL_SIZE + CELL_SIZE // 2
                    cell_y = offset_y + y * CELL_SIZE + CELL_SIZE // 2
                    
                    # Draw a cute heart or star
                    pygame.draw.circle(self.screen, (255, 255, 255), (cell_x, cell_y), 8)
                    pygame.draw.circle(self.screen, COLOR_YELLOW, (cell_x, cell_y), 5)

    def draw_ghost_piece(self, block: Block, board: Board,
                         offset_x: int = 50, offset_y: int = 50) -> None:
        """Draw ghost piece."""
        ghost = block.copy()
        ghost.y = board.get_drop_position(block)
        
        cells = ghost.get_cells()
        for x, y in cells:
            if y >= 0:
                px = offset_x + x * CELL_SIZE
                py = offset_y + y * CELL_SIZE
                rect = pygame.Rect(px + 2, py + 2, CELL_SIZE - 4, CELL_SIZE - 4)
                pygame.draw.rect(self.screen, (ghost.color[0], ghost.color[1], ghost.color[2]), rect, 2, border_radius=6)

    def draw_text(self, text: str, x: int, y: int, font: pygame.font.Font = None,
                  color: Tuple[int, int, int] = COLOR_TEXT, center: bool = False,
                  shadow: bool = False) -> None:
        """Draw text on screen with optional shadow."""
        if font is None:
            font = self.font_small

        if shadow:
            shadow_surface = font.render(text, True, COLOR_WHITE)
            if center:
                shadow_rect = shadow_surface.get_rect(center=(x + 2, y + 2))
                self.screen.blit(shadow_surface, shadow_rect)
            else:
                self.screen.blit(shadow_surface, (x + 2, y + 2))

        surface = font.render(text, True, color)
        if center:
            rect = surface.get_rect(center=(x, y))
            self.screen.blit(surface, rect)
        else:
            self.screen.blit(surface, (x, y))

    def draw_panel(self, x: int, y: int, width: int, height: int, title: str = None) -> None:
        """Draw a cute UI panel/card."""
        rect = pygame.Rect(x, y, width, height)
        
        # Shadow
        shadow_rect = pygame.Rect(x + 4, y + 4, width, height)
        self.draw_rounded_rect(self.screen, shadow_rect, (230, 220, 230), radius=15)
        
        # Main Card
        self.draw_rounded_rect(self.screen, rect, COLOR_WHITE, radius=15)
        # Border
        pygame.draw.rect(self.screen, COLOR_BUTTON_NORMAL, rect, 2, border_radius=15)
        
        if title:
            self.draw_text(title, x + 15, y + 10, self.font_tiny, COLOR_TEXT, shadow=True)

    def draw_ui(self, score: int, level: int, lines: int, high_score: int = 0,
                mode: str = "Classic") -> None:
        """Draw UI elements."""
        ui_x = 420
        
        # Title with cat icon
        self.draw_text("CLAIRE'S TETRIS", WINDOW_WIDTH // 2 - 30, 30,
                      self.font_medium, COLOR_TEXT, center=True, shadow=True)

        # Draw cat icon next to title
        if self.cat_icon:
            cat_x = WINDOW_WIDTH // 2 + 180
            cat_y = 10
            self.screen.blit(self.cat_icon, (cat_x, cat_y))

        # Info Panel
        self.draw_panel(ui_x, 70, 250, 180, "STATS")
        
        start_y = 110
        gap = 35
        
        self.draw_text(f"Mode: {mode}", ui_x + 20, start_y, self.font_tiny)
        self.draw_text(f"Score: {score}", ui_x + 20, start_y + gap, self.font_small)
        self.draw_text(f"High: {high_score}", ui_x + 20, start_y + gap*2, self.font_tiny, COLOR_GRAY)
        self.draw_text(f"Level: {level}", ui_x + 20, start_y + gap*3, self.font_small)
        self.draw_text(f"Lines: {lines}", ui_x + 140, start_y + gap*3, self.font_small)

    def draw_next_block(self, block: Optional[Block], x: int = 420, y: int = 270) -> None:
        """Draw next block preview."""
        self.draw_panel(x, y, 120, 120, "NEXT")

        if block:
            preview_block = block.copy()
            preview_block.x = 0
            preview_block.y = 0
            
            # Center in panel
            preview_offset_x = x + 30
            preview_offset_y = y + 45
            
            self.draw_block(preview_block, preview_offset_x, preview_offset_y)

    def draw_hold_block(self, block: Optional[Block], x: int = 560, y: int = 270) -> None:
        """Draw held block."""
        self.draw_panel(x, y, 110, 120, "HOLD")

        if block:
            preview_block = block.copy()
            preview_block.x = 0
            preview_block.y = 0
            
            self.draw_block(preview_block, x + 25, y + 45)

    def draw_powerup_inventory(self, inventory: list, active_effects: list,
                               x: int = 420, y: int = 410) -> None:
        """Draw power-up inventory (compact version)."""
        self.draw_panel(x, y, 250, 120, "POWER-UPS")

        # Draw inventory slots (compact, side by side)
        slot_y = y + 40
        for i in range(2):
            slot_x = x + 15 + i * 110
            slot_rect = pygame.Rect(slot_x, slot_y, 100, 50)
            
            self.draw_rounded_rect(self.screen, slot_rect, (245, 245, 255), radius=10)

            if i < len(inventory):
                powerup = inventory[i]
                pygame.draw.rect(self.screen, COLOR_BUTTON_NORMAL, slot_rect, 2, border_radius=10)

                # Simplified text labels (no emoji for web compatibility)
                name_map = {
                    "bomb": "BOMB",
                    "rainbow": "RAIN",
                    "time_freeze": "FRZE",
                    "gravity_reverse": "GRAV",
                    "line_eraser": "ERAS",
                    "ghost_mode": "GHST"
                }
                name = name_map.get(powerup.type.value, powerup.type.value[:4].upper())
                self.draw_text(name, slot_x + 25, slot_y + 15,
                             self.font_tiny, COLOR_TEXT)
            else:
                pygame.draw.rect(self.screen, COLOR_LIGHT_GRAY, slot_rect, 1, border_radius=10)
                self.draw_text("---", slot_x + 35, slot_y + 15,
                             self.font_tiny, COLOR_LIGHT_GRAY)

    def draw_game_over_screen(self, score: int, lines: int, high_score: int) -> None:
        """Draw cute game over overlay."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLOR_BACKGROUND) # Soft overlay
        self.screen.blit(overlay, (0, 0))

        # Modal Box
        box_width, box_height = 450, 380
        box_x = (WINDOW_WIDTH - box_width) // 2
        box_y = (WINDOW_HEIGHT - box_height) // 2

        self.draw_panel(box_x, box_y, box_width, box_height)

        self.draw_text("GAME OVER", WINDOW_WIDTH // 2, box_y + 40,
                      self.font_medium, COLOR_TEXT, center=True, shadow=True)

        self.draw_text(f"Score: {score}", WINDOW_WIDTH // 2, box_y + 100,
                      self.font_small, COLOR_TEXT, center=True)

        if score >= high_score and score > 0:
            self.draw_text("NEW HIGH SCORE!", WINDOW_WIDTH // 2, box_y + 140,
                          self.font_small, COLOR_ORANGE, center=True)

        # Touch-friendly buttons
        button_width = 180
        button_height = 60
        button_y = box_y + 220

        # Restart button
        restart_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - button_width - 10,
            button_y,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (100, 200, 100), restart_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), restart_rect, 3, border_radius=10)
        self.draw_text("RESTART", restart_rect.centerx, restart_rect.centery,
                      self.font_small, COLOR_WHITE, center=True)

        # Quit button
        quit_rect = pygame.Rect(
            WINDOW_WIDTH // 2 + 10,
            button_y,
            button_width,
            button_height
        )
        pygame.draw.rect(self.screen, (200, 100, 100), quit_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), quit_rect, 3, border_radius=10)
        self.draw_text("MENU", quit_rect.centerx, quit_rect.centery,
                      self.font_small, COLOR_WHITE, center=True)

    def get_game_over_button_clicked(self, mouse_pos: tuple) -> Optional[str]:
        """Check if game over buttons were clicked. Returns 'restart' or 'quit'."""
        box_width, box_height = 450, 380
        box_x = (WINDOW_WIDTH - box_width) // 2
        box_y = (WINDOW_HEIGHT - box_height) // 2

        button_width = 180
        button_height = 60
        button_y = box_y + 220

        # Restart button
        restart_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - button_width - 10,
            button_y,
            button_width,
            button_height
        )
        if restart_rect.collidepoint(mouse_pos):
            return "restart"

        # Quit button
        quit_rect = pygame.Rect(
            WINDOW_WIDTH // 2 + 10,
            button_y,
            button_width,
            button_height
        )
        if quit_rect.collidepoint(mouse_pos):
            return "quit"

        return None

    def draw_notification(self, text: str, y: int = 350) -> None:
        """Draw a bubble notification."""
        text_surface = self.font_small.render(text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect()
        
        # Bubble dimensions
        bubble_width = text_rect.width + 40
        bubble_height = text_rect.height + 30
        bubble_x = (WINDOW_WIDTH - bubble_width) // 2
        
        bubble_rect = pygame.Rect(bubble_x, y - bubble_height//2, bubble_width, bubble_height)
        
        self.draw_rounded_rect(self.screen, bubble_rect, COLOR_WHITE, radius=20)
        pygame.draw.rect(self.screen, COLOR_YELLOW, bubble_rect, 3, border_radius=20)
        
        self.screen.blit(text_surface, (bubble_x + 20, y - bubble_height//2 + 15))

    def draw_pause_screen(self) -> None:
        """Draw pause overlay."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(COLOR_BACKGROUND)
        self.screen.blit(overlay, (0, 0))

        self.draw_text("PAUSED ⏸️", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
                      self.font_medium, COLOR_TEXT, center=True, shadow=True)

    def clear_screen(self) -> None:
        """Clear screen."""
        self.screen.fill(COLOR_BACKGROUND)

    def update_display(self) -> None:
        """Update the display."""
        pygame.display.flip()

    def quit(self) -> None:
        """Quit Pygame."""
        pygame.quit()
