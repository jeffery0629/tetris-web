"""Text input widget for player ID entry."""

import pygame
from typing import Optional
from .constants import COLOR_TEXT, COLOR_WHITE, COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER


class TextInput:
    """Simple text input widget for Pygame."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 font: pygame.font.Font, max_length: int = 12):
        """Initialize text input.

        Args:
            x: X position
            y: Y position
            width: Input box width
            height: Input box height
            font: Pygame font to use
            max_length: Maximum characters allowed
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.max_length = max_length

        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_speed = 0.5  # seconds

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event.

        Args:
            event: Pygame event

        Returns:
            True if input was modified
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if clicked inside input box
            if self.rect.collidepoint(event.pos):
                self.active = True
                return True
            else:
                self.active = False
                return False

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                return False
            else:
                # Add character if under max length
                if len(self.text) < self.max_length:
                    char = event.unicode
                    # Allow alphanumeric and some special chars
                    if char.isprintable() and char not in ['/', '\\', '|', '<', '>', ':', '"', '*', '?']:
                        self.text += char
                        return True

        return False

    def update(self, dt: float) -> None:
        """Update cursor blink animation.

        Args:
            dt: Delta time in seconds
        """
        if self.active:
            self.cursor_timer += dt
            if self.cursor_timer >= self.cursor_blink_speed:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0

    def draw(self, surface: pygame.Surface, placeholder: str = "Enter ID") -> None:
        """Draw text input box.

        Args:
            surface: Pygame surface to draw on
            placeholder: Placeholder text when empty
        """
        # Border color based on active state
        border_color = COLOR_TEXT if self.active else (180, 180, 180)
        bg_color = COLOR_WHITE if self.active else (245, 245, 245)

        # Draw background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw text or placeholder
        if self.text:
            text_surface = self.font.render(self.text, True, COLOR_TEXT)
        else:
            text_surface = self.font.render(placeholder, True, (150, 150, 150))

        # Center text vertically
        text_rect = text_surface.get_rect()
        text_rect.midleft = (self.rect.x + 10, self.rect.centery)
        surface.blit(text_surface, text_rect)

        # Draw cursor if active
        if self.active and self.cursor_visible and len(self.text) < self.max_length:
            cursor_x = text_rect.right + 2
            cursor_y = self.rect.y + 5
            cursor_height = self.rect.height - 10
            pygame.draw.line(surface, COLOR_TEXT,
                           (cursor_x, cursor_y),
                           (cursor_x, cursor_y + cursor_height), 2)

    def get_text(self) -> str:
        """Get current input text (trimmed)."""
        return self.text.strip()

    def set_text(self, text: str) -> None:
        """Set input text."""
        self.text = text[:self.max_length]

    def clear(self) -> None:
        """Clear input text."""
        self.text = ""
        self.active = False
