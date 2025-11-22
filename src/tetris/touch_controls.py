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

        # Button dimensions
        self.button_height = 78
        self.button_margin = 12
        
        # Bottom row Y position
        bottom_y = window_height - self.button_height - self.button_margin

        # Pause button (top-left corner)
        # Positioned higher to avoid overlap with game board (offset_y=50)
        self.pause_button = TouchButton(
            x=10,
            y=5,
            width=70,
            height=40,
            label="Pause",
            icon="||",
            action="pause",
            color=(100, 100, 100),
            hover_color=(150, 150, 150)
        )

        # --- BOTTOM ROW BUTTONS ---
        
        # 1. Hard Drop (Bottom Left)
        # Wide button
        drop_width = 200
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
        
        # 2. Power-up (Next to Drop)
        # Wide button (similar to Drop/Rot)
        pwr_width = 200
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

        # 3. Rotate (Bottom Right)
        # Extra Large
        rot_width = 210
        rot_height = 85
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

        # --- FLOATING ACTION BUTTON ---

        # 4. Hold (Below Power-up Panel, Right Side)
        # Placed in the gap between Power-ups panel and bottom buttons
        # Power-ups panel is at y=410, height=120 -> ends at 530
        # Bottom buttons start at ~660
        # Center vertically in that gap ~595
        hold_width = 300 # Wide button to fill the right area space
        hold_x = 430 # Aligned with right UI column
        hold_y = 555
        
        self.hold_button = TouchButton(
            x=hold_x,
            y=hold_y,
            width=hold_width,
            height=70,
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
        
        # Bottom limit is above the HOLD button (since it's higher up now)
        self.game_area_bottom = hold_y - 10
        
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

        # Expanded left/right touch zones
        if y >= self.game_area_top and y <= self.game_area_bottom:
            # Left zone
            if x < self.game_area_center:
                self.left_pressed = True
                return "move_left"
            # Right zone
            elif x >= self.game_area_center:
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
