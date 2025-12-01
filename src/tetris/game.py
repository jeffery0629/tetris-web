"""Enhanced game controller with power-ups and multiple modes."""

import pygame
import time
import random
import asyncio
import sys
from typing import Optional, Callable
from .board import Board

# Detect if running in Web/Pygbag environment
IS_WEB = sys.platform == "emscripten"
from .tetromino import Block, get_random_tetromino
from .pentomino import get_random_pentomino
from .renderer import Renderer
from .powerup import PowerUpManager, get_random_powerup, PowerUp
from .modes import GameMode, get_mode_config
from .touch_controls import TouchControlManager
from .text_input import TextInput
from .leaderboard_manager import GistLeaderboardManager, LeaderboardEntry
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

        # Exit flag for returning to menu
        self.should_exit_to_menu = False

        # Leaderboard system
        self.leaderboard_manager = GistLeaderboardManager()
        self.text_input = TextInput(
            x=300, y=400, width=200, height=40,
            font=self.renderer.font_small, max_length=12
        )
        self.leaderboard_entries = []  # Current leaderboard data
        self.current_player_id = ""  # Last entered player ID
        self._pending_submit_player_id = None  # For async submit

        # Mobile input button rects (for touch handling)
        self._submit_button_rect = None
        self._skip_button_rect = None
        self._input_box_rect = None  # For triggering browser prompt on mobile

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

        # Ghost mode allows moving through blocks but NOT out of bounds
        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            if self.board.is_within_bounds(self.current_block):
                # After horizontal move, check if block can fall further
                if dx != 0:
                    self._check_ground_after_move()
                return True
            else:
                # Still out of bounds, revert
                self.current_block.move(-dx, -dy)
                return False

        if self.board.is_valid_position(self.current_block):
            # After horizontal move, check if block can fall further
            if dx != 0:
                self._check_ground_after_move()
            return True
        else:
            # Revert move
            self.current_block.move(-dx, -dy)
            return False

    def _check_ground_after_move(self) -> None:
        """Check if block is still on ground after horizontal move.

        If block can fall further, reset is_on_ground and lock_timer.
        This prevents the floating block bug.
        """
        if not self.current_block or not self.is_on_ground:
            return

        # Test if block can move down
        self.current_block.move(0, 1)

        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            can_fall = self.board.is_within_bounds(self.current_block)
        else:
            can_fall = self.board.is_valid_position(self.current_block)

        # Revert test move
        self.current_block.move(0, -1)

        # If block can fall, it's no longer on ground
        if can_fall:
            self.is_on_ground = False
            self.lock_timer = 0

    def rotate_block(self, clockwise: bool = True) -> bool:
        """Rotate current block with wall kick support."""
        if not self.current_block:
            return False

        original_rotation = self.current_block.rotation

        if clockwise:
            self.current_block.rotate_cw()
        else:
            self.current_block.rotate_ccw()

        # Ghost mode ignores collisions but checks bounds
        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            if self.board.is_within_bounds(self.current_block):
                return True
            # Out of bounds, try wall kicks

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
                # Progressive speed increase: gentle at low levels, aggressive at high levels
                if self.level <= 5:
                    self.fall_speed *= SPEED_INCREASE_PER_LEVEL  # 0.9
                else:
                    self.fall_speed *= 0.85  # Faster acceleration after level 5

        # Check game over
        if self.board.is_game_over(spawn_y=1):
            # Show input screen if online, otherwise skip to game over
            if self.leaderboard_manager.online_mode:
                self.state = GameState.GAME_OVER_INPUT
                self.text_input.active = True  # Auto-activate input
            else:
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
            # Find and clear the most problematic mixed area (holes and blocks)
            center_x, center_y, score = self.board.find_most_problematic_area(radius=1)
            if score > 0:
                cleared = self.board.clear_area(center_x, center_y, radius=1)
                self.show_notification(f"BOOM! Cleared {cleared} blocks!")
            else:
                self.show_notification("No problematic areas to bomb!")

        elif powerup.type == PowerUpType.LINE_ERASER:
            self.board.clear_bottom_rows(2)

        elif powerup.type == PowerUpType.MAGNET:
            # Drop all floating blocks down (gravity compress)
            self.board.apply_gravity_compress()

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
        # Update text input cursor animation during input state
        if self.state == GameState.GAME_OVER_INPUT:
            self.text_input.update(dt)
            return

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

        # Ghost mode: check if at bottom boundary (can stop there)
        if self.powerup_manager.is_effect_active(PowerUpType.GHOST_MODE):
            # Can phase through blocks, but stops at bottom or if can't move down
            self.is_on_ground = not self.board.is_within_bounds(test_block)
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

    def _show_browser_prompt(self) -> Optional[str]:
        """Show browser prompt dialog for text input (Web only).

        Returns:
            User input string or None if cancelled
        """
        if not IS_WEB:
            return None

        try:
            from platform import window

            # Use browser's native prompt - this will show mobile keyboard
            js_code = '''
            (function() {
                var result = prompt("Enter your Player ID (max 12 chars):", "");
                if (result === null) return "";
                return result.slice(0, 12);
            })()
            '''
            result = window.eval(js_code)
            return result if result else None
        except Exception as e:
            print(f"Error showing prompt: {e}")
            return None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events (keyboard + touch)."""
        # Handle text input during game over input state
        if self.state == GameState.GAME_OVER_INPUT:
            # Mobile: Handle button clicks
            if IS_WEB and event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                # Check if tapped on input box - show browser prompt
                if self._input_box_rect and self._input_box_rect.collidepoint(pos):
                    player_id = self._show_browser_prompt()
                    if player_id:
                        self.text_input.set_text(player_id)
                    return

                # Check OK button
                if self._submit_button_rect and self._submit_button_rect.collidepoint(pos):
                    player_id = self.text_input.get_text()
                    if player_id:
                        self._pending_submit_player_id = player_id
                        self.state = GameState.SUBMITTING_SCORE
                    else:
                        # No name entered, show prompt first
                        player_id = self._show_browser_prompt()
                        if player_id:
                            self._pending_submit_player_id = player_id
                            self.state = GameState.SUBMITTING_SCORE
                        else:
                            self.state = GameState.GAME_OVER
                    return

                # Check SKIP button
                if self._skip_button_rect and self._skip_button_rect.collidepoint(pos):
                    self.state = GameState.GAME_OVER
                    return

            # Desktop: Handle keyboard input
            modified = self.text_input.handle_event(event)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # User pressed Enter - submit score
                player_id = self.text_input.get_text()
                if player_id:
                    # Mark that we need to submit (will be handled in async loop)
                    self._pending_submit_player_id = player_id
                    self.state = GameState.SUBMITTING_SCORE
                else:
                    # Skip if no ID entered
                    self.state = GameState.GAME_OVER
            return  # Don't process other events during input

        # Handle leaderboard screen
        if self.state == GameState.LEADERBOARD:
            if event.type == pygame.MOUSEBUTTONDOWN:
                action = self.renderer.get_leaderboard_button_clicked(event.pos)
                if action == "close":
                    self.state = GameState.GAME_OVER
            return

        # Handle touch/mouse events
        if self.enable_touch_controls:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Game Over screen buttons
                if self.state == GameState.GAME_OVER:
                    button_action = self.renderer.get_game_over_button_clicked(event.pos)
                    if button_action == "restart":
                        self.restart()
                        return
                    elif button_action == "quit":
                        # Set a flag to exit to menu
                        self.should_exit_to_menu = True
                        return

                # Touch controls
                action = self.touch_controls.handle_touch_down(event.pos[0], event.pos[1])

                # Pause/unpause is always allowed
                if action == "pause":
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    return

                # All other actions require PLAYING state
                if self.state != GameState.PLAYING:
                    return

                if action == "rotate":
                    self.rotate_block(clockwise=True)
                    if self.is_on_ground:
                        self.lock_timer = time.time()
                elif action == "hard_drop":
                    rows = self.hard_drop()
                    self.score += rows * SCORE_HARD_DROP
                elif action == "soft_drop":
                    if self.move_block(0, 1):
                        self.score += SCORE_SOFT_DROP
                elif action == "powerup":
                    self.use_powerup()
                elif action == "hold":
                    self.hold_current_block()
                elif action == "move_left":
                    self.move_block(-1, 0)
                elif action == "move_right":
                    self.move_block(1, 0)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.touch_controls.handle_touch_up(event.pos[0], event.pos[1])

            elif event.type == pygame.MOUSEMOTION:
                if self.state == GameState.PLAYING and event.buttons[0]:  # Left mouse button held
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

        # Calculate dynamic cell size based on board height
        # Maximum board height that fits: (750 - 50 offset - 80 button area) / cell_size
        # For Crazy mode (22 rows): need smaller cells
        from .constants import CELL_SIZE, WINDOW_HEIGHT
        max_board_height = WINDOW_HEIGHT - 130  # Leave space for title and buttons
        ideal_cell_size = max_board_height // self.board.height
        # Clamp between 24 and 30
        self.renderer.cell_size = min(30, max(24, ideal_cell_size))

        # Adjusted offsets for larger board
        offset_x = 40
        offset_y = 50

        # Calculate board end position for dynamic UI layout
        board_end_x = offset_x + self.board.width * self.renderer.cell_size + 10  # 10px padding

        # Draw board and blocks
        self.renderer.draw_board(self.board, offset_x, offset_y)

        if self.current_block:
            self.renderer.draw_ghost_piece(self.current_block, self.board, offset_x, offset_y)
            self.renderer.draw_block(self.current_block, offset_x, offset_y, is_powerup=self.is_powerup_block)

        # Draw UI with dynamic positioning based on board size
        self.renderer.draw_ui(
            score=self.score,
            level=self.level,
            lines=self.lines_cleared,
            high_score=self.high_score,
            mode=self.mode_config.display_name,
            board_end_x=board_end_x
        )

        # Draw next and hold blocks with dynamic positioning
        self.renderer.draw_next_block(self.next_block, board_end_x=board_end_x)
        self.renderer.draw_hold_block(self.held_block, board_end_x=board_end_x)

        # Draw power-up inventory and active effects
        if self.mode_config.power_ups_enabled:
            self.renderer.draw_powerup_inventory(
                inventory=self.powerup_manager.inventory,
                active_effects=self.powerup_manager.active_effects,
                board_end_x=board_end_x
            )

        # Draw notification if active
        if self.notification_text and time.time() - self.notification_time < self.notification_duration:
            self.renderer.draw_notification(self.notification_text)

        # Draw touch controls
        if self.enable_touch_controls:
            self.touch_controls.draw(self.renderer.screen, self.renderer.font_small)

        # Draw overlays
        if self.state == GameState.PAUSED:
            self.renderer.draw_pause_screen()

        elif self.state == GameState.GAME_OVER_INPUT:
            # Draw game over screen first
            self.renderer.draw_game_over_screen(
                self.score, self.lines_cleared, self.high_score
            )
            # Then draw input overlay on top
            self._draw_input_overlay()

        elif self.state == GameState.SUBMITTING_SCORE:
            # Show "Submitting..." screen
            self.renderer.draw_game_over_screen(
                self.score, self.lines_cleared, self.high_score
            )
            # Draw submitting overlay
            self._draw_submitting_overlay()

        elif self.state == GameState.LEADERBOARD:
            # Show leaderboard
            self.renderer.draw_leaderboard_screen(
                mode=self.mode.value,
                entries=self.leaderboard_entries,
                player_id=self.current_player_id
            )

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

        # Clear leaderboard state
        self.text_input.clear()
        self.leaderboard_entries = []
        # Keep current_player_id for next game

        self.state = GameState.PLAYING
        self.spawn_new_block()
        self.next_block = self.generate_block()

    async def _submit_score_to_leaderboard_async(self, player_id: str) -> None:
        """Submit score to leaderboard and show rankings (async version).

        Args:
            player_id: Player's chosen ID
        """
        self.current_player_id = player_id

        # Create entry
        entry = LeaderboardEntry(
            player_id=player_id,
            score=self.score,
            lines=self.lines_cleared,
            level=self.level,
            mode=self.mode.value  # "casual", "classic", or "crazy"
        )

        # Submit to cloud (async)
        success, message = await self.leaderboard_manager.submit_score_async(entry)

        if success:
            self.show_notification(message)
        else:
            self.show_notification(f"Upload failed: {message}")

        # Fetch and show leaderboard (even if upload failed) - async
        self.leaderboard_entries = await self.leaderboard_manager.get_leaderboard_async(
            mode=self.mode.value,
            limit=10
        )

        # Switch to leaderboard view
        self.state = GameState.LEADERBOARD

    def _submit_score_to_leaderboard(self, player_id: str) -> None:
        """Submit score to leaderboard (sync fallback for desktop).

        Args:
            player_id: Player's chosen ID
        """
        self.current_player_id = player_id

        # Create entry
        entry = LeaderboardEntry(
            player_id=player_id,
            score=self.score,
            lines=self.lines_cleared,
            level=self.level,
            mode=self.mode.value
        )

        # Submit to cloud
        success, message = self.leaderboard_manager.submit_score(entry)

        if success:
            self.show_notification(message)
        else:
            self.show_notification(f"Upload failed: {message}")

        # Fetch and show leaderboard
        self.leaderboard_entries = self.leaderboard_manager.get_leaderboard(
            mode=self.mode.value,
            limit=10
        )

        # Switch to leaderboard view
        self.state = GameState.LEADERBOARD

    def _draw_input_overlay(self) -> None:
        """Draw player ID input overlay on top of game over screen."""
        # Small overlay panel
        panel_width = 400
        panel_height = 250 if IS_WEB else 200
        panel_x = (800 - panel_width) // 2  # WINDOW_WIDTH = 800
        panel_y = 250

        # Semi-transparent background
        overlay = pygame.Surface((panel_width, panel_height))
        overlay.set_alpha(240)
        overlay.fill((255, 255, 255))
        self.renderer.screen.blit(overlay, (panel_x, panel_y))

        # Border
        pygame.draw.rect(
            self.renderer.screen,
            (100, 100, 100),
            pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            3,
            border_radius=15
        )

        # Prompt text
        self.renderer.draw_text(
            "Enter Your Player ID:",
            panel_x + panel_width // 2,
            panel_y + 40,
            self.renderer.font_small,
            (80, 70, 90),
            center=True
        )

        # Text input box (clickable on mobile to trigger prompt)
        self.text_input.rect.centerx = panel_x + panel_width // 2
        self.text_input.rect.y = panel_y + 80
        self._input_box_rect = self.text_input.rect.copy()
        self.text_input.draw(self.renderer.screen, placeholder="Tap to enter name" if IS_WEB else "Your Name")

        if IS_WEB:
            # Mobile: Show OK and SKIP buttons
            button_width = 120
            button_height = 50
            button_y = panel_y + 150
            gap = 20

            # OK button (green)
            ok_x = panel_x + panel_width // 2 - button_width - gap // 2
            self._submit_button_rect = pygame.Rect(ok_x, button_y, button_width, button_height)
            pygame.draw.rect(self.renderer.screen, (76, 175, 80), self._submit_button_rect, border_radius=10)
            pygame.draw.rect(self.renderer.screen, (56, 142, 60), self._submit_button_rect, 3, border_radius=10)
            self.renderer.draw_text(
                "OK",
                ok_x + button_width // 2,
                button_y + button_height // 2,
                self.renderer.font_small,
                (255, 255, 255),
                center=True
            )

            # SKIP button (gray)
            skip_x = panel_x + panel_width // 2 + gap // 2
            self._skip_button_rect = pygame.Rect(skip_x, button_y, button_width, button_height)
            pygame.draw.rect(self.renderer.screen, (158, 158, 158), self._skip_button_rect, border_radius=10)
            pygame.draw.rect(self.renderer.screen, (117, 117, 117), self._skip_button_rect, 3, border_radius=10)
            self.renderer.draw_text(
                "SKIP",
                skip_x + button_width // 2,
                button_y + button_height // 2,
                self.renderer.font_small,
                (255, 255, 255),
                center=True
            )
        else:
            # Desktop: Hint text
            self.renderer.draw_text(
                "Press ENTER to submit",
                panel_x + panel_width // 2,
                panel_y + 150,
                self.renderer.font_small,
                (150, 150, 150),
                center=True
            )

    def _draw_submitting_overlay(self) -> None:
        """Draw 'Submitting...' overlay during score upload."""
        # Small overlay panel
        panel_width = 300
        panel_height = 100
        panel_x = (800 - panel_width) // 2
        panel_y = 300

        # Semi-transparent background
        overlay = pygame.Surface((panel_width, panel_height))
        overlay.set_alpha(240)
        overlay.fill((255, 255, 255))
        self.renderer.screen.blit(overlay, (panel_x, panel_y))

        # Border
        pygame.draw.rect(
            self.renderer.screen,
            (100, 100, 100),
            pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            3,
            border_radius=15
        )

        # Submitting text
        self.renderer.draw_text(
            "Submitting score...",
            panel_x + panel_width // 2,
            panel_y + 50,
            self.renderer.font_small,
            (80, 70, 90),
            center=True
        )

    def run(self) -> None:
        """Main game loop (synchronous version for desktop)."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            # Check if should exit to menu
            if self.should_exit_to_menu:
                running = False
                break

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

            # Check if should exit to menu
            if self.should_exit_to_menu:
                running = False
                break

            # Handle async score submission
            if self.state == GameState.SUBMITTING_SCORE and self._pending_submit_player_id:
                player_id = self._pending_submit_player_id
                self._pending_submit_player_id = None
                await self._submit_score_to_leaderboard_async(player_id)

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
