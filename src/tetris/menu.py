"""Mode selection menu."""

import pygame
import asyncio
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
                 x: int, y: int, width: int, height: int, unlocked: bool = True, icon: pygame.Surface = None):
        """Initialize button."""
        self.mode = mode
        self.display_name = display_name
        self.description = description
        self.rect = pygame.Rect(x, y, width, height)
        self.unlocked = unlocked
        self.hovered = False
        self.icon = icon

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

        # Text color - use dark text on light background for better contrast
        from .constants import COLOR_TEXT
        text_color = COLOR_TEXT if self.unlocked else (140, 140, 140)

        # Mode name
        text = font_large.render(self.display_name, True, text_color)
        text_rect = text.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
        screen.blit(text, text_rect)

        # Description
        desc = font_small.render(self.description, True, text_color)
        desc_rect = desc.get_rect(center=(self.rect.centerx, self.rect.centery + 20))
        screen.blit(desc, desc_rect)

        # Cat icon on the right side
        if self.icon:
            icon_x = self.rect.right - 70
            icon_y = self.rect.centery - 30
            screen.blit(self.icon, (icon_x, icon_y))

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

        # Fonts - use English only for web compatibility
        # Chinese characters don't render well in Pygbag web environment
        self.font_title = pygame.font.Font(None, 72)
        self.font_large = pygame.font.Font(None, 42)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Load cat icon with smooth scaling for better quality
        try:
            cat_img = pygame.image.load("images/cat.jpg")
            self.cat_icon = pygame.transform.smoothscale(cat_img, (50, 50))
        except (pygame.error, FileNotFoundError):
            self.cat_icon = None

        # Load mode icons (cat1, cat2, cat3)
        self.mode_icons = {}
        icon_size = (60, 60)
        try:
            cat1_img = pygame.image.load("images/cat1.jpg")
            self.mode_icons['casual'] = pygame.transform.smoothscale(cat1_img, icon_size)
        except (pygame.error, FileNotFoundError):
            self.mode_icons['casual'] = None

        try:
            cat2_img = pygame.image.load("images/cat2.jpg")
            self.mode_icons['classic'] = pygame.transform.smoothscale(cat2_img, icon_size)
        except (pygame.error, FileNotFoundError):
            self.mode_icons['classic'] = None

        try:
            cat3_img = pygame.image.load("images/cat3.jpg")
            self.mode_icons['crazy'] = pygame.transform.smoothscale(cat3_img, icon_size)
        except (pygame.error, FileNotFoundError):
            self.mode_icons['crazy'] = None

        # Create buttons - 6 modes (smaller buttons to fit all)
        button_width = 420
        button_height = 75
        button_spacing = 8
        start_y = 140

        self.buttons = [
            ModeButton(
                mode=GameMode.CASUAL,
                display_name="CASUAL [EASY]",
                description="7 pieces + helpful power-ups",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y,
                width=button_width,
                height=button_height,
                unlocked=True,
                icon=self.mode_icons.get('casual')
            ),
            ModeButton(
                mode=GameMode.CLASSIC,
                display_name="CLASSIC [NORMAL]",
                description="Pure Tetris - no power-ups",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + button_height + button_spacing,
                width=button_width,
                height=button_height,
                unlocked=True,
                icon=self.mode_icons.get('classic')
            ),
            ModeButton(
                mode=GameMode.CRAZY,
                display_name="CRAZY [HARD]",
                description="18 pentominoes + power-ups",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + (button_height + button_spacing) * 2,
                width=button_width,
                height=button_height,
                unlocked=save_manager.is_mode_unlocked("crazy"),
                icon=self.mode_icons.get('crazy')
            ),
            ModeButton(
                mode=GameMode.BATTLE,
                display_name="BATTLE [2P LOCAL]",
                description="Local 2-player battle",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + (button_height + button_spacing) * 3,
                width=button_width,
                height=button_height,
                unlocked=True,
                icon=None
            ),
            ModeButton(
                mode=GameMode.ONLINE_BATTLE,
                display_name="ONLINE [PC]",
                description="Desktop online battle - dual boards",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + (button_height + button_spacing) * 4,
                width=button_width,
                height=button_height,
                unlocked=True,
                icon=None
            ),
            ModeButton(
                mode=GameMode.MOBILE_ONLINE,
                display_name="ONLINE [MOBILE]",
                description="Mobile online battle - single board",
                x=WINDOW_WIDTH // 2 - button_width // 2,
                y=start_y + (button_height + button_spacing) * 5,
                width=button_width,
                height=button_height,
                unlocked=True,
                icon=None
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
                    elif event.key == pygame.K_4:
                        return GameMode.BATTLE
                    elif event.key == pygame.K_5:
                        return GameMode.ONLINE_BATTLE
                    elif event.key == pygame.K_6:
                        return GameMode.MOBILE_ONLINE
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
            from .constants import COLOR_TEXT
            title = self.font_title.render("CLAIRE'S TETRIS", True, COLOR_TEXT)
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 60))
            self.screen.blit(title, title_rect)

            # Subtitle with cat icon
            subtitle = self.font_medium.render("Select Game Mode", True, COLOR_TEXT)
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 120))
            self.screen.blit(subtitle, subtitle_rect)

            # Cat icon next to subtitle
            if self.cat_icon:
                cat_x = subtitle_rect.right + 10
                cat_y = subtitle_rect.centery - 25
                self.screen.blit(self.cat_icon, (cat_x, cat_y))

            # Buttons
            for button in self.buttons:
                button.draw(self.screen, self.font_large, self.font_small)

            pygame.display.flip()
            self.clock.tick(FPS)

        return None

    async def run_async(self) -> Optional[GameMode]:
        """Run menu and return selected mode (async version for web)."""
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
                    elif event.key == pygame.K_4:
                        return GameMode.BATTLE
                    elif event.key == pygame.K_5:
                        return GameMode.ONLINE_BATTLE
                    elif event.key == pygame.K_6:
                        return GameMode.MOBILE_ONLINE
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
            from .constants import COLOR_TEXT
            title = self.font_title.render("CLAIRE'S TETRIS", True, COLOR_TEXT)
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 60))
            self.screen.blit(title, title_rect)

            # Subtitle with cat icon
            subtitle = self.font_medium.render("Select Game Mode", True, COLOR_TEXT)
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 120))
            self.screen.blit(subtitle, subtitle_rect)

            # Cat icon next to subtitle
            if self.cat_icon:
                cat_x = subtitle_rect.right + 10
                cat_y = subtitle_rect.centery - 25
                self.screen.blit(self.cat_icon, (cat_x, cat_y))

            # Buttons
            for button in self.buttons:
                button.draw(self.screen, self.font_large, self.font_small)

            pygame.display.flip()
            self.clock.tick(FPS)

            # Yield control to event loop
            await asyncio.sleep(0)

        return None

    def quit(self) -> None:
        """Quit menu."""
        pygame.quit()
