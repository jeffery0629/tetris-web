"""Touch control system for mobile web version."""

import pygame
from dataclasses import dataclass
from typing import Optional, Tuple
from .constants import WINDOW_WIDTH, WINDOW_HEIGHT


@dataclass
class TouchButton:
    """Represents a touch button on screen."""
    x: int
    y: int
    width: int
    height: int
    label: str
    icon: str
    action: str
    color: Tuple[int, int, int]
    hover_color: Tuple[int, int, int]
    is_pressed: bool = False

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is inside button bounds."""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw button on screen."""
        color = self.hover_color if self.is_pressed else self.color

        # Draw button background with rounded corners
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=10)

        # Draw icon/label
        text_surface = font.render(self.icon, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2,
                                                    self.y + self.height // 2))
        screen.blit(text_surface, text_rect)


class TouchControlManager:
    """Manages touch controls for mobile gameplay."""

    def __init__(self, window_width: int = WINDOW_WIDTH, window_height: int = WINDOW_HEIGHT):
        """Initialize touch control manager."""
        self.window_width = window_width
        self.window_height = window_height

        # Button dimensions - redesigned layout
        self.button_height = 70
        self.button_margin = 10

        # Pause button (top-left corner)
        self.pause_button = TouchButton(
            x=10,
            y=10,
            width=60,
            height=50,
            label="Pause",
            icon="||",
            action="pause",
            color=(100, 100, 100),
            hover_color=(150, 150, 150)
        )

        # Right-side buttons (stacked vertically in bottom-right)
        right_button_width = 180
        right_button_height = 95

        # Hard drop button (bottom-right, upper position)
        self.drop_button = TouchButton(
            x=window_width - right_button_width - self.button_margin,
            y=window_height - right_button_height * 2 - self.button_margin * 2,
            width=right_button_width,
            height=right_button_height,
            label="Drop",
            icon="DROP",
            action="hard_drop",
            color=(220, 100, 100),
            hover_color=(240, 120, 120)
        )

        # Rotate button (bottom-right, lower position)
        self.rotate_button = TouchButton(
            x=window_width - right_button_width - self.button_margin,
            y=window_height - right_button_height - self.button_margin,
            width=right_button_width,
            height=right_button_height,
            label="Rotate",
            icon="ROT",
            action="rotate",
            color=(100, 150, 200),
            hover_color=(120, 170, 220)
        )

        # Bottom buttons (PWR and HLD side by side)
        bottom_button_width = (window_width - right_button_width - self.button_margin * 3) // 2
        button_y = window_height - self.button_height - self.button_margin

        # Power-up button (bottom-left)
        self.powerup_button = TouchButton(
            x=self.button_margin,
            y=button_y,
            width=bottom_button_width,
            height=self.button_height,
            label="Power-up",
            icon="PWR",
            action="powerup",
            color=(200, 100, 200),
            hover_color=(220, 120, 220)
        )

        # Hold button (bottom-center)
        self.hold_button = TouchButton(
            x=self.button_margin * 2 + bottom_button_width,
            y=button_y,
            width=bottom_button_width,
            height=self.button_height,
            label="Hold",
            icon="HLD",
            action="hold",
            color=(200, 150, 100),
            hover_color=(220, 170, 120)
        )

        self.buttons = [
            self.pause_button,
            self.drop_button,
            self.rotate_button,
            self.powerup_button,
            self.hold_button
        ]

        # Touch state
        self.left_pressed = False
        self.right_pressed = False

        # Expanded game area bounds for easier touch control
        # Leave space below pause button (pause button: y=10, height=50, so bottom is at 60)
        pause_bottom = self.pause_button.y + self.pause_button.height
        self.game_area_top = pause_bottom + 10  # 10px gap below pause button
        self.game_area_bottom = window_height - self.button_height - self.button_margin  # Just above bottom buttons (expanded)
        self.game_area_right = window_width - right_button_width - self.button_margin  # Left of right buttons (no extra margin)
        self.game_area_center = self.game_area_right // 2

    def handle_touch_down(self, x: int, y: int) -> Optional[str]:
        """Handle touch/mouse down event.

        Args:
            x, y: Touch position

        Returns:
            Action string if button pressed, None otherwise
        """
        # Check buttons first (except pause - allow movement overlap)
        for button in self.buttons:
            if button == self.pause_button:
                continue  # Skip pause for now, check later
            if button.contains_point(x, y):
                button.is_pressed = True
                return button.action

        # Expanded left/right touch zones (entire left and right areas)
        # Left zone: from left edge to center (except right buttons)
        # Right zone: from center to right buttons
        if y >= self.game_area_top and y <= self.game_area_bottom:
            if x <= self.game_area_right:
                if x < self.game_area_center:
                    self.left_pressed = True
                    return "move_left"
                else:
                    self.right_pressed = True
                    return "move_right"

        # Finally check pause button (lowest priority)
        if self.pause_button.contains_point(x, y):
            self.pause_button.is_pressed = True
            return self.pause_button.action

        return None

    def handle_touch_up(self, x: int, y: int) -> None:
        """Handle touch/mouse up event."""
        # Release all buttons
        for button in self.buttons:
            button.is_pressed = False

        # Release movement
        self.left_pressed = False
        self.right_pressed = False

    def handle_touch_motion(self, x: int, y: int) -> Optional[str]:
        """Handle touch/mouse motion (for drag operations).

        Args:
            x, y: Touch position

        Returns:
            Action string if in movement area
        """
        # Only handle motion in game area (avoid rotate button)
        if (self.game_area_top <= y <= self.game_area_bottom and
            x <= self.game_area_right):
            if x < self.game_area_center and not self.left_pressed:
                self.left_pressed = True
                self.right_pressed = False
                return "move_left"
            elif x >= self.game_area_center and not self.right_pressed:
                self.right_pressed = True
                self.left_pressed = False
                return "move_right"

        return None

    def is_left_held(self) -> bool:
        """Check if left side is being held."""
        return self.left_pressed

    def is_right_held(self) -> bool:
        """Check if right side is being held."""
        return self.right_pressed

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw all touch controls."""
        # Draw visual hint for left/right areas (semi-transparent)
        hint_surface = pygame.Surface((self.window_width // 2,
                                       self.game_area_bottom - self.game_area_top))
        hint_surface.set_alpha(30)

        if self.left_pressed:
            hint_surface.fill((100, 150, 255))
            screen.blit(hint_surface, (0, self.game_area_top))

        if self.right_pressed:
            hint_surface.fill((255, 150, 100))
            screen.blit(hint_surface, (self.window_width // 2, self.game_area_top))

        # Draw buttons
        for button in self.buttons:
            button.draw(screen, font)
