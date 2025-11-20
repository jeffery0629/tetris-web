"""Mode selection menu."""

import pygame
from typing import Optional
from .constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    COLOR_BACKGROUND, COLOR_WHITE, COLOR_LIGHT_GRAY,
    COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER, COLOR_BUTTON_LOCKED,
    GameMode
)
from .save_manager import SaveManager


class ModeButton:
    """Clickable mode button."""

    def __init__(self, mode: GameMode, display_name: str, description: str,
                 x: int, y: int, width: int, height: int, unlocked: bool = True):
        """Initialize button."""
        self.mode = mode
        self.display_name = display_name
        self.description = description
        self.rect = pygame.Rect(x, y, width, height)
        self.unlocked = unlocked
        self.hovered = False

    def update(self, mouse_pos: tuple) -> None:
        """Update button state."""
        self.hovered = self.rect.collidepoint(mouse_pos) and self.unlocked

    def draw(self, screen: pygame.Surface, font_large: pygame.font.Font,
             font_small: pygame.font.Font) -> None:
        """Draw button."""
        # Background color
        if not self.unlocked:
            color = COLOR_BUTTON_LOCKED
        elif self.hovered:
            color = COLOR_BUTTON_HOVER
        else:
            color = COLOR_BUTTON_NORMAL

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, COLOR_WHITE, self.rect, 2)

        # Text
        text_color = COLOR_WHITE if self.unlocked else COLOR_LIGHT_GRAY

        # Mode name
        text = font_large.render(self.display_name, True, text_color)
        text_rect = text.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
        screen.blit(text, text_rect)

        # Description
        desc = font_small.render(self.description, True, text_color)
        desc_rect = desc.get_rect(center=(self.rect.centerx, self.rect.centery + 20))
        screen.blit(desc, desc_rect)

        # Lock icon
        if not self.unlocked:
            lock_text = font_small.render("[LOCKED]", True, text_color)
            lock_rect = lock_text.get_rect(center=(self.rect.centerx, self.rect.bottom - 20))
            screen.blit(lock_text, lock_rect)

    def is_clicked(self, mouse_pos: tuple) -> bool:
        """Check if button was clicked."""
        return self.rect.collidepoint(mouse_pos) and self.unlocked


class ModeSelectionMenu:
    """Mode selection screen."""

    def __init__(self, save_manager: SaveManager):
        """Initialize menu."""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Claire's Tetris - Select Mode")
        self.clock = pygame.time.Clock()
        self.save_manager = save_manager

        # Fonts
        self.font_title = pygame.font.Font(None, 72)
        self.font_large = pygame.font.Font(None, 42)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Create buttons - 3 modes
        button_width = 320
        button_height = 120
        button_spacing = 30
        start_y = 180

        self.buttons = [
            ModeButton(
                mode=GameMode.CASUAL,
                display_name="CASUAL [EASY]",
                description="7 pieces + helpful power-ups",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y,
                width=button_width,
                height=button_height,
                unlocked=True
            ),
            ModeButton(
                mode=GameMode.CLASSIC,
                display_name="CLASSIC [NORMAL]",
                description="Pure Tetris - no power-ups",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + button_height + button_spacing,
                width=button_width,
                height=button_height,
                unlocked=True
            ),
            ModeButton(
                mode=GameMode.CRAZY,
                display_name="CRAZY [HARD]",
                description="18 pentominoes + power-ups",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + (button_height + button_spacing) * 2,
                width=button_width,
                height=button_height,
                unlocked=save_manager.is_mode_unlocked("crazy")
            ),
        ]

        self.selected_mode: Optional[GameMode] = None

    def run(self) -> Optional[GameMode]:
        """Run menu and return selected mode."""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_1:
                        return GameMode.CASUAL
                    elif event.key == pygame.K_2:
                        return GameMode.CLASSIC
                    elif event.key == pygame.K_3:
                        if self.save_manager.is_mode_unlocked("crazy"):
                            return GameMode.CRAZY
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for button in self.buttons:
                        if button.is_clicked(mouse_pos):
                            return button.mode

            # Update
            for button in self.buttons:
                button.update(mouse_pos)

            # Draw
            self.screen.fill(COLOR_BACKGROUND)

            # Title
            title = self.font_title.render("CLAIRE'S TETRIS", True, COLOR_WHITE)
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 80))
            self.screen.blit(title, title_rect)

            # Subtitle
            subtitle = self.font_medium.render("Select Game Mode", True, COLOR_LIGHT_GRAY)
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 140))
            self.screen.blit(subtitle, subtitle_rect)

            # Buttons
            for button in self.buttons:
                button.draw(self.screen, self.font_large, self.font_small)

            # Instructions
            instructions = [
                "Click a mode or press 1-3",
                f"Total lines cleared: {self.save_manager.get_total_lines()}",
                "Unlock Crazy mode: Clear 50 lines in any mode",
            ]
            y = WINDOW_HEIGHT - 120
            for text in instructions:
                surf = self.font_small.render(text, True, COLOR_LIGHT_GRAY)
                rect = surf.get_rect(center=(WINDOW_WIDTH // 2, y))
                self.screen.blit(surf, rect)
                y += 30

            pygame.display.flip()
            self.clock.tick(FPS)

        return None

    def quit(self) -> None:
        """Quit menu."""
        pygame.quit()
