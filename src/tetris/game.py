"""Enhanced game controller with power-ups and multiple modes."""

import pygame
import time
import random
import asyncio
from typing import Optional, Callable
from .board import Board
from .tetromino import Block, get_random_tetromino
from .pentomino import get_random_pentomino
from .renderer import Renderer
from .powerup import PowerUpManager, get_random_powerup, PowerUp
from .modes import GameMode, get_mode_config
from .touch_controls import TouchControlManager
from .constants import (
    FPS, INITIAL_FALL_SPEED, LOCK_DELAY,
    SPEED_INCREASE_PER_LEVEL, LINES_PER_LEVEL,
    SCORE_SINGLE_LINE, SCORE_DOUBLE_LINE, SCORE_TRIPLE_LINE, SCORE_QUAD_LINE,
    SCORE_SOFT_DROP, SCORE_HARD_DROP, POWERUP_SPAWN_RATE,
    GameState, PowerUpType
)


class GameEnhanced:
    """Enhanced game controller with power-ups and multiple modes."""

    def __init__(self, mode: GameMode = GameMode.CLASSIC):
        """Initialize game.

        Args:
            mode: GameMode enum value
        """
        self.mode = mode
        self.mode_config = get_mode_config(mode)

        # Set up board
        self.board = Board(
            self.mode_config.grid_size[0],
            self.mode_config.grid_size[1]
        )

        self.renderer = Renderer()
        self.clock = pygame.time.Clock()

        # Touch controls for mobile
        self.touch_controls = TouchControlManager()
        self.enable_touch_controls = True  # Can be toggled for desktop

        # Game state
        self.state = GameState.PLAYING
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.lines_cleared = 0

        # Block generator based on mode
        if mode == GameMode.CLASSIC:
            self.block_generator = get_random_tetromino
        elif mode == GameMode.CRAZY:
            self.block_generator = get_random_pentomino
        else:
            self.block_generator = get_random_tetromino

        # Current and next blocks
        self.current_block: Optional[Block] = None
        self.next_block: Optional[Block] = None
        self.held_block: Optional[Block] = None
        self.can_hold = True
        self.is_powerup_block = False  # Is current block a power-up?

        # Power-up system
        self.powerup_manager = PowerUpManager()

        # Timing
        self.fall_speed = INITIAL_FALL_SPEED
        self.last_fall_time = time.time()
        self.lock_timer = 0
        self.is_on_ground = False

        # Input handling
        self.move_delay = 0.15
        self.last_left_move = 0
        self.last_right_move = 0
        self.last_down_move = 0

        # Notification system
        self.notification_text = ""
        self.notification_time = 0
        self.notification_duration = 2.0  # seconds

        # Spawn first blocks
        self.spawn_new_block()
        self.next_block = self.generate_block()

    def generate_block(self) -> Block:
        """Generate a new block, possibly a power-up.

        Returns:
            Block instance
        """
        # Check if should spawn power-up (only in modes that support it)
        if self.mode_config.power_ups_enabled and random.random() < POWERUP_SPAWN_RATE:
            # TODO: Mark this block visually as power-up
            block = self.block_generator()
            # Store power-up type for when block is placed
            return block
        else:
            return self.block_generator()

    def spawn_new_block(self) -> None:
        """Spawn a new block at the top of the board."""
        if self.next_block:
            self.current_block = self.next_block
            self.next_block = self.generate_block()
        else:
            self.current_block = self.generate_block()

        # Determine if next block is power-up
        self.is_powerup_block = (
            self.mode_config.power_ups_enabled and
            random.random() < POWERUP_SPAWN_RATE
        )

        # Set spawn position (centered at top)
        self.current_block.x = self.board.width // 2 - 2
        self.current_block.y = 0

        # Check if spawn position is valid (game over if not)
        # Ghost mode allows overlapping
        if not self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            if not self.board.is_valid_position(self.current_block):
                self.state = GameState.GAME_OVER

        self.can_hold = True
        self.is_on_ground = False
        self.lock_timer = 0

    def move_block(self, dx: int, dy: int) -> bool:
        """Move current block by offset.

        Args:
            dx: Horizontal offset
            dy: Vertical offset

        Returns:
            True if move was successful
        """
        if not self.current_block:
            return False

        self.current_block.move(dx, dy)

        # Ghost mode allows moving through blocks
        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            return True

        if self.board.is_valid_position(self.current_block):
            return True
        else:
            # Revert move
            self.current_block.move(-dx, -dy)
            return False

    def rotate_block(self, clockwise: bool = True) -> bool:
        """Rotate current block with wall kick support."""
        if not self.current_block:
            return False

        original_rotation = self.current_block.rotation

        if clockwise:
            self.current_block.rotate_cw()
        else:
            self.current_block.rotate_ccw()

        # Ghost mode ignores collisions
        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            return True

        if self.board.is_valid_position(self.current_block):
            return True

        # Try wall kicks
        wall_kicks = [(1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]
        for dx, dy in wall_kicks:
            self.current_block.move(dx, dy)
            if self.board.is_valid_position(self.current_block):
                return True
            self.current_block.move(-dx, -dy)

        # Rotation failed, revert
        self.current_block.rotation = original_rotation
        return False

    def hard_drop(self) -> int:
        """Drop block instantly to bottom."""
        if not self.current_block:
            return 0

        rows_dropped = 0
        while self.move_block(0, 1):
            rows_dropped += 1

        self.lock_block()
        return rows_dropped

    def soft_drop(self) -> bool:
        """Move block down one row."""
        return self.move_block(0, 1)

    def lock_block(self) -> None:
        """Lock current block to board and spawn new one."""
        if not self.current_block:
            return

        # Collect power-up if this was a power-up block
        if self.is_powerup_block:
            powerup_type = get_random_powerup()
            success = self.powerup_manager.add_powerup(powerup_type)
            if success:
                name_map = {
                    "bomb": "BOMB", "rainbow": "RAINBOW", "time_freeze": "FREEZE",
                    "gravity_reverse": "REVERSE", "line_eraser": "ERASER", "ghost_mode": "GHOST"
                }
                name = name_map.get(powerup_type.value, powerup_type.value.upper())
                self.show_notification(f"Got {name}!")
            else:
                self.show_notification("Inventory Full!")
            self.is_powerup_block = False

        # Decrement ghost mode counter if active
        self.powerup_manager.decrement_ghost_mode()

        self.board.place_block(self.current_block)
        lines = self.board.clear_lines()

        # Update score
        if lines > 0:
            self.lines_cleared += lines
            line_score = [0, SCORE_SINGLE_LINE, SCORE_DOUBLE_LINE,
                         SCORE_TRIPLE_LINE, SCORE_QUAD_LINE][min(lines, 4)]
            multiplier = self.mode_config.score_multiplier
            self.score += int(line_score * self.level * multiplier)

            # Level up
            new_level = (self.lines_cleared // LINES_PER_LEVEL) + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_speed *= SPEED_INCREASE_PER_LEVEL

        # Check game over
        if self.board.is_game_over(spawn_y=1):
            self.state = GameState.GAME_OVER
            if self.score > self.high_score:
                self.high_score = self.score
        else:
            self.spawn_new_block()

    def show_notification(self, text: str) -> None:
        """Show a notification message.

        Args:
            text: Message to display
        """
        self.notification_text = text
        self.notification_time = time.time()

    def use_powerup(self) -> None:
        """Activate a power-up from inventory."""
        powerup = self.powerup_manager.use_powerup()
        if not powerup:
            return

        # Show activation message
        name_map = {
            "bomb": "BOMB Activated!", "rainbow": "RAINBOW Activated!",
            "time_freeze": "TIME FREEZE!", "gravity_reverse": "GRAVITY REVERSED!",
            "line_eraser": "LINES CLEARED!", "ghost_mode": "GHOST MODE!"
        }
        msg = name_map.get(powerup.type.value, "Power-up activated!")
        self.show_notification(msg)

        # Apply instant effects
        if powerup.type == PowerUpType.BOMB:
            if self.current_block:
                # Get block center position
                cells = self.current_block.get_cells()
                if cells:
                    center_x = sum(x for x, y in cells) // len(cells)
                    center_y = sum(y for x, y in cells) // len(cells)
                    self.board.clear_area(center_x, center_y, radius=1)

        elif powerup.type == PowerUpType.LINE_ERASER:
            self.board.clear_bottom_rows(2)

        elif powerup.type == PowerUpType.RAINBOW:
            # Rainbow effect handled in board logic
            pass

    def hold_current_block(self) -> None:
        """Hold current block and swap with held block."""
        if not self.can_hold or not self.current_block:
            return

        if self.held_block:
            self.current_block, self.held_block = self.held_block, self.current_block
        else:
            self.held_block = self.current_block
            self.current_block = self.next_block
            self.next_block = self.generate_block()

        # Reset position
        self.current_block.x = self.board.width // 2 - 2
        self.current_block.y = 0
        self.current_block.rotation = 0

        self.can_hold = False

    def update(self, dt: float) -> None:
        """Update game state."""
        if self.state != GameState.PLAYING:
            return

        if not self.current_block:
            return

        # Update power-ups
        self.powerup_manager.update(dt)

        current_time = time.time()

        # Check if block is on ground
        test_block = self.current_block.copy()
        test_block.y += 1

        # Ghost mode allows floating
        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            self.is_on_ground = False
        else:
            self.is_on_ground = not self.board.is_valid_position(test_block)

        # Time freeze stops falling
        if self.powerup_manager.is_effect_active(PowerUpType.TIME_FREEZE):
            return

        # Gravity (automatic fall)
        # Reverse gravity makes blocks fall upward
        if self.powerup_manager.is_effect_active(PowerUpType.GRAVITY_REVERSE):
            dy = -1
        else:
            dy = 1

        if current_time - self.last_fall_time >= self.fall_speed:
            if not self.move_block(0, dy):
                if not self.is_on_ground:
                    self.is_on_ground = True
                    self.lock_timer = current_time
            else:
                self.is_on_ground = False

            self.last_fall_time = current_time

        # Lock delay
        if self.is_on_ground:
            if self.lock_timer == 0:
                self.lock_timer = current_time
            elif current_time - self.lock_timer >= LOCK_DELAY:
                self.lock_block()

    def handle_input(self) -> None:
        """Handle keyboard input."""
        if self.state != GameState.PLAYING:
            return

        current_time = time.time()
        keys = pygame.key.get_pressed()

        # Left movement
        if keys[pygame.K_LEFT]:
            if current_time - self.last_left_move >= self.move_delay:
                if self.move_block(-1, 0):
                    self.last_left_move = current_time
                    if self.is_on_ground:
                        self.lock_timer = current_time

        # Right movement
        if keys[pygame.K_RIGHT]:
            if current_time - self.last_right_move >= self.move_delay:
                if self.move_block(1, 0):
                    self.last_right_move = current_time
                    if self.is_on_ground:
                        self.lock_timer = current_time

        # Soft drop
        if keys[pygame.K_DOWN]:
            if current_time - self.last_down_move >= 0.05:
                if self.soft_drop():
                    self.score += SCORE_SOFT_DROP
                    self.last_down_move = current_time

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events (keyboard + touch)."""
        # Handle touch/mouse events
        if self.enable_touch_controls:
            if event.type == pygame.MOUSEBUTTONDOWN:
                action = self.touch_controls.handle_touch_down(event.pos[0], event.pos[1])
                if action == "rotate":
                    self.rotate_block(clockwise=True)
                    if self.is_on_ground:
                        self.lock_timer = time.time()
                elif action == "powerup":
                    self.use_powerup()
                elif action == "hold":
                    self.hold_current_block()
                elif action == "pause":
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                elif action == "move_left":
                    self.move_block(-1, 0)
                elif action == "move_right":
                    self.move_block(1, 0)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.touch_controls.handle_touch_up(event.pos[0], event.pos[1])

            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:  # Left mouse button held
                    action = self.touch_controls.handle_touch_motion(event.pos[0], event.pos[1])
                    if action == "move_left":
                        self.move_block(-1, 0)
                    elif action == "move_right":
                        self.move_block(1, 0)

        # Handle keyboard events (keep for desktop compatibility)
        if event.type == pygame.KEYDOWN:
            if self.state == GameState.PLAYING:
                if event.key == pygame.K_UP:
                    self.rotate_block(clockwise=True)
                    if self.is_on_ground:
                        self.lock_timer = time.time()
                elif event.key == pygame.K_z:
                    self.rotate_block(clockwise=False)
                    if self.is_on_ground:
                        self.lock_timer = time.time()
                elif event.key == pygame.K_SPACE:
                    rows = self.hard_drop()
                    self.score += rows * SCORE_HARD_DROP
                elif event.key == pygame.K_c:
                    self.hold_current_block()
                elif event.key == pygame.K_e:
                    self.use_powerup()
                elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.state = GameState.PAUSED

            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_p:
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    return

            elif self.state == GameState.GAME_OVER:
                if event.key == pygame.K_r:
                    self.restart()

    def render(self) -> None:
        """Render current game state."""
        self.renderer.clear_screen()

        offset_x = 50
        offset_y = 80

        # Draw board and blocks
        self.renderer.draw_board(self.board, offset_x, offset_y)

        if self.current_block:
            self.renderer.draw_ghost_piece(self.current_block, self.board, offset_x, offset_y)
            self.renderer.draw_block(self.current_block, offset_x, offset_y, is_powerup=self.is_powerup_block)

        # Draw UI
        self.renderer.draw_ui(
            score=self.score,
            level=self.level,
            lines=self.lines_cleared,
            high_score=self.high_score,
            mode=self.mode_config.display_name
        )

        # Draw next and hold blocks
        self.renderer.draw_next_block(self.next_block)
        self.renderer.draw_hold_block(self.held_block)

        # Draw power-up inventory and active effects
        if self.mode_config.power_ups_enabled:
            self.renderer.draw_powerup_inventory(
                inventory=self.powerup_manager.inventory,
                active_effects=self.powerup_manager.active_effects
            )

        # Draw notification if active
        if self.notification_text and time.time() - self.notification_time < self.notification_duration:
            self.renderer.draw_notification(self.notification_text)

        # Draw touch controls
        if self.enable_touch_controls:
            self.touch_controls.draw(self.renderer.screen, self.renderer.font)

        # Draw overlays
        if self.state == GameState.PAUSED:
            self.renderer.draw_pause_screen()
        elif self.state == GameState.GAME_OVER:
            self.renderer.draw_game_over_screen(
                self.score, self.lines_cleared, self.high_score
            )

        self.renderer.update_display()

    def restart(self) -> None:
        """Restart the game."""
        self.board.clear()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = INITIAL_FALL_SPEED
        self.current_block = None
        self.next_block = None
        self.held_block = None
        self.can_hold = True
        self.is_powerup_block = False
        self.powerup_manager.clear()
        self.state = GameState.PLAYING
        self.spawn_new_block()
        self.next_block = self.generate_block()

    def run(self) -> None:
        """Main game loop (synchronous version for desktop)."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.state == GameState.GAME_OVER:
                        running = False
                    else:
                        self.handle_event(event)
                else:
                    self.handle_event(event)

            self.handle_input()
            self.update(dt)
            self.render()

        self.renderer.quit()

    async def run_async(self) -> None:
        """Main game loop (async version for web/Pygbag)."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.state == GameState.GAME_OVER:
                        running = False
                    else:
                        self.handle_event(event)
                else:
                    self.handle_event(event)

            self.handle_input()
            self.update(dt)
            self.render()

            # Yield control to event loop (critical for Pygbag)
            await asyncio.sleep(0)

        self.renderer.quit()
