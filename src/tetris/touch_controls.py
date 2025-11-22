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

        # Button dimensions - redesigned layout for two-hand usage
        # Increased sizes by ~10-20%
        self.button_height = 78  # Base height +10%
        self.button_margin = 12
        
        # Bottom row Y position
        bottom_y = window_height - self.button_height - self.button_margin

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

        # --- LEFT SIDE BUTTONS (Left Hand) ---
        
        # Hard Drop (Bottom Left - Primary Action) - Increased size
        drop_width = 190  # +10%
        self.drop_button = TouchButton(
            x=self.button_margin,
            y=bottom_y,
            width=drop_width,
            height=self.button_height,
            label="Drop",
            icon="DROP",
            action="hard_drop",
            color=(220, 100, 100),   # Red
            hover_color=(240, 120, 120)
        )
        
        # Power-up (Left Inner - Secondary Action)
        pwr_width = 120  # +10%
        self.powerup_button = TouchButton(
            x=self.button_margin * 2 + drop_width,
            y=bottom_y,
            width=pwr_width,
            height=self.button_height,
            label="Power-up",
            icon="PWR",
            action="powerup",
            color=(200, 100, 200),   # Purple
            hover_color=(220, 120, 220)
        )

        # --- RIGHT SIDE BUTTONS (Right Hand) ---

        # Rotate (Bottom Right - Primary Action) - Extra Large (+20%)
        rot_width = 210  # +20%
        rot_height = 85  # Slightly taller
        rot_y = window_height - rot_height - self.button_margin
        
        self.rotate_button = TouchButton(
            x=window_width - rot_width - self.button_margin,
            y=rot_y,
            width=rot_width,
            height=rot_height,
            label="Rotate",
            icon="ROT",
            action="rotate",
            color=(100, 150, 200),   # Blue
            hover_color=(120, 170, 220)
        )

        # Hold (Right Inner - Secondary Action)
        hold_width = 120 # +10%
        self.hold_button = TouchButton(
            x=window_width - rot_width - hold_width - self.button_margin * 2,
            y=bottom_y,
            width=hold_width,
            height=self.button_height,
            label="Hold",
            icon="HOLD",
            action="hold",
            color=(200, 150, 100),   # Orange
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
        # Leave space below pause button
        pause_bottom = self.pause_button.y + self.pause_button.height
        self.game_area_top = pause_bottom + 10 
        
        # Bottom limit is above the buttons (use higher Y of the buttons)
        self.game_area_bottom = min(bottom_y, rot_y) - 10
        
        # Allow touch in entire screen width; buttons already capture presses with higher priority
        self.game_area_right = window_width
        # Center line is at half of total window width
        self.game_area_center = window_width // 2

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
        # Left zone: from left edge to center
        # Right zone: from center to screen edge (buttons already handled first)
        if y >= self.game_area_top and y <= self.game_area_bottom:
            # Left zone: entire left half of screen
            if x < self.game_area_center:
                self.left_pressed = True
                return "move_left"
            # Right zone: center to right edge (buttons handled before movement)
            elif x >= self.game_area_center and x <= self.game_area_right:
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
        # Only handle motion in game area (buttons were already processed on down)
        if self.game_area_top <= y <= self.game_area_bottom:
            # Left zone
            if x < self.game_area_center and not self.left_pressed:
                self.left_pressed = True
                self.right_pressed = False
                return "move_left"
            # Right zone (center to right edge)
            elif self.game_area_center <= x <= self.game_area_right and not self.right_pressed:
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
