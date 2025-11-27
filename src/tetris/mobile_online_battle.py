"""
Mobile-friendly Online Battle Mode.

Uses single-player UI layout with opponent status bar at top.
Designed for touch controls on mobile web.
"""

import pygame
import asyncio
import time
import random
import logging

from .network_manager import NetworkManager
from .board import Board
from .tetromino import Block, create_tetromino
from .renderer import Renderer
from .touch_controls import TouchControlManager
from .constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, CELL_SIZE,
    GameState, COLOR_WHITE, COLOR_TEXT, COLOR_BLACK, COLOR_RED,
    INITIAL_FALL_SPEED, LOCK_DELAY, SPEED_INCREASE_PER_LEVEL,
    SCORE_SINGLE_LINE, SCORE_DOUBLE_LINE, SCORE_TRIPLE_LINE, SCORE_QUAD_LINE,
    SCORE_SOFT_DROP, SCORE_HARD_DROP, BATTLE_DURATION,
    BattlePowerUpType, BATTLE_POWERUP_SPAWN_RATE, BATTLE_POWERUP_DURATION
)

logger = logging.getLogger(__name__)


class MobileOnlineBattleGame:
    """Mobile-friendly online battle mode with touch controls."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Claire's Tetris - Online Battle")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Network
        self.network = NetworkManager()
        self.waiting_for_match = True
        self.local_role = 0
        self.connection_status = "Connecting..."
        self.opponent_disconnected = False
        self.game_result = None

        # Server block sequences
        self.my_block_sequence = []
        self.opponent_block_sequence = []
        self.my_block_index = 0
        self._use_server_blocks = False

        # Game state
        self.state = GameState.PLAYING
        self.board = Board(10, 20)  # Standard Tetris grid
        self.renderer = Renderer()
        self.touch_controls = TouchControlManager()

        # Player state
        self.current_block = None
        self.next_block = None
        self.held_block = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1

        # Opponent state (received from network)
        self.opponent_name = "Opponent"
        self.opponent_score = 0
        self.opponent_lines = 0
        self.opponent_debuffs = []  # List of active debuff names

        # Garbage and debuff system
        self.pending_garbage = 0
        self.active_debuffs = {}  # {debuff_type: end_time}
        self.powerups = []  # Inventory (max 2)

        # Timing
        self.fall_speed = INITIAL_FALL_SPEED
        self.fall_timer = 0
        self.lock_timer = 0
        self.is_on_ground = False
        self.game_start_time = 0
        self.time_remaining = BATTLE_DURATION
        self.server_time_remaining = BATTLE_DURATION

        # Input handling
        self.move_delay = 0.12
        self.last_move_time = {'left': 0, 'right': 0, 'down': 0}

        # Animation
        self.garbage_warning_flash = 0
        self._sync_counter = 0

    async def connect_and_wait(self, player_name: str = "Player"):
        """Connect to server and wait for match."""
        success = await self.network.connect()
        if not success:
            self.connection_status = "Connection Failed!"
            return False

        self.connection_status = "Joining matchmaking..."
        await self.network.join_matchmaking(player_name)

        while self.waiting_for_match:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False

            # Draw waiting screen
            self._draw_waiting_screen()
            self.clock.tick(30)

            # Check network events
            event = await self.network.get_event()
            if event:
                if event['type'] == 'MATCH_START':
                    self.local_role = event['role']
                    self.opponent_name = event.get('opponent_name', 'Opponent')
                    self.my_block_sequence = event.get('my_blocks', [])
                    self.my_block_index = 0
                    self._use_server_blocks = True
                    self.waiting_for_match = False
                    self._start_game()
                    return True
                elif event['type'] == 'WAITING':
                    self.connection_status = "Waiting for opponent..."

            if not self.network.connected:
                self.connection_status = "Connection Lost!"
                return False

            await asyncio.sleep(0.05)

        return True

    def _start_game(self):
        """Initialize game after match found."""
        self.state = GameState.PLAYING
        self.game_start_time = time.time()
        self._spawn_block()

    def _get_next_block_type(self) -> str:
        """Get next block from server sequence."""
        if not self._use_server_blocks:
            return random.choice(['I', 'O', 'T', 'S', 'Z', 'J', 'L'])

        if self.my_block_index < len(self.my_block_sequence):
            block_type = self.my_block_sequence[self.my_block_index]
            self.my_block_index += 1
            return block_type
        return random.choice(['I', 'O', 'T', 'S', 'Z', 'J', 'L'])

    def _spawn_block(self) -> bool:
        """Spawn a new block."""
        if self.next_block:
            self.current_block = self.next_block
        else:
            block_type = self._get_next_block_type()
            self.current_block = create_tetromino(block_type)

        # Maybe spawn powerup
        if random.random() < BATTLE_POWERUP_SPAWN_RATE and len(self.powerups) < 2:
            powerup = random.choice(list(BattlePowerUpType))
            self.powerups.append(powerup)

        # Next block
        next_type = self._get_next_block_type()
        self.next_block = create_tetromino(next_type)

        # Center the block
        current_shape = self.current_block.shape[self.current_block.rotation]
        block_width = len(current_shape[0]) if current_shape else 0
        self.current_block.x = (self.board.width - block_width) // 2
        self.current_block.y = 0
        self.current_block.rotation = 0

        # Check game over
        if not self.board.is_valid_position(self.current_block):
            return False

        self.fall_timer = 0
        self.lock_timer = 0
        self.is_on_ground = False
        self.can_hold = True
        return True

    async def run_async(self, player_name: str = "Player"):
        """Main async game loop."""
        connected = await self.connect_and_wait(player_name)

        if not connected:
            await self._show_error_screen()
            return

        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            # Process network events
            await self._process_network_events()

            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif not self._handle_event(event):
                    running = False

            # Handle continuous input
            if self.state == GameState.PLAYING:
                self._handle_continuous_input()
                self._update(dt)

            # Render
            self._render()

            # Sync state to server
            await self._sync_state()

            await asyncio.sleep(0)

        self.network.close()
        pygame.quit()

    async def _process_network_events(self):
        """Process incoming network events."""
        while True:
            event = await self.network.get_event()
            if not event:
                break

            event_type = event.get('type')

            if event_type == 'OPPONENT_STATE':
                self.opponent_score = event.get('score', self.opponent_score)
                self.opponent_lines = event.get('lines', self.opponent_lines)

            elif event_type == 'GARBAGE':
                lines = event.get('lines', 0)
                self.pending_garbage += lines
                self.garbage_warning_flash = time.time()

            elif event_type == 'TIME_SYNC':
                self.server_time_remaining = event.get('remaining', 0) / 1000.0
                self.time_remaining = self.server_time_remaining

            elif event_type == 'OPPONENT_DISCONNECTED':
                self.opponent_disconnected = True
                self.game_result = {'winner': self.local_role, 'reason': 'OPPONENT_DISCONNECTED'}
                self.state = GameState.GAME_OVER

            elif event_type == 'GAME_END':
                self.game_result = {
                    'winner': event.get('winner', 0),
                    'reason': event.get('reason', 'UNKNOWN')
                }
                self.state = GameState.GAME_OVER

            elif event_type == 'DEBUFF':
                debuff_type_str = event.get('debuff', '')
                duration = event.get('duration', 5.0)
                try:
                    debuff_enum = BattlePowerUpType(debuff_type_str)
                    current_time = time.time()
                    self.active_debuffs[debuff_enum] = current_time + duration
                    logger.info(f"Applied debuff {debuff_enum}")
                except ValueError:
                    pass

    def _handle_event(self, event) -> bool:
        """Handle pygame events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False

            if self.state == GameState.PLAYING:
                if event.key == pygame.K_SPACE:
                    self._hard_drop()
                elif event.key in (pygame.K_UP, pygame.K_x):
                    self._rotate(clockwise=True)
                elif event.key == pygame.K_z:
                    self._rotate(clockwise=False)
                elif event.key == pygame.K_c:
                    self._hold()
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self._use_powerup()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            action = self.touch_controls.handle_touch_down(*event.pos)
            if action:
                self._handle_touch_action(action)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.touch_controls.handle_touch_up(*event.pos)

        return True

    def _handle_touch_action(self, action: str):
        """Handle touch button actions."""
        if self.state != GameState.PLAYING:
            return

        if action == 'hard_drop':
            self._hard_drop()
        elif action == 'rotate':
            self._rotate(clockwise=True)
        elif action == 'powerup':
            self._use_powerup()
        elif action == 'hold':
            self._hold()
        elif action == 'pause':
            pass  # No pause in online mode

    def _handle_continuous_input(self):
        """Handle held keys and touch zones."""
        keys = pygame.key.get_pressed()
        current_time = time.time()

        # Keyboard
        if keys[pygame.K_LEFT] and current_time - self.last_move_time['left'] > self.move_delay:
            self._move(-1, 0)
            self.last_move_time['left'] = current_time
        if keys[pygame.K_RIGHT] and current_time - self.last_move_time['right'] > self.move_delay:
            self._move(1, 0)
            self.last_move_time['right'] = current_time
        if keys[pygame.K_DOWN] and current_time - self.last_move_time['down'] > self.move_delay:
            if self._move(0, 1):
                self.score += SCORE_SOFT_DROP
            self.last_move_time['down'] = current_time

        # Touch zones
        if self.touch_controls.is_left_held() and current_time - self.last_move_time['left'] > self.move_delay:
            self._move(-1, 0)
            self.last_move_time['left'] = current_time
        if self.touch_controls.is_right_held() and current_time - self.last_move_time['right'] > self.move_delay:
            self._move(1, 0)
            self.last_move_time['right'] = current_time

    def _update(self, dt: float):
        """Update game state."""
        if self.state != GameState.PLAYING:
            return

        # Update timer
        if self.server_time_remaining > 0:
            self.time_remaining = self.server_time_remaining
        else:
            elapsed = time.time() - self.game_start_time
            self.time_remaining = max(0, BATTLE_DURATION - elapsed)

        if self.time_remaining <= 0:
            self._end_game()
            return

        # Update debuffs
        current_time = time.time()
        expired = [d for d, end_time in self.active_debuffs.items() if current_time > end_time]
        for d in expired:
            del self.active_debuffs[d]

        # Apply pending garbage
        if self.pending_garbage > 0:
            self._add_garbage_lines(self.pending_garbage)
            self.pending_garbage = 0

        # Fall speed (considering debuffs)
        fall_speed = self._get_fall_speed()
        self.fall_timer += dt

        if self.fall_timer >= fall_speed:
            self.fall_timer = 0
            if not self._move(0, 1):
                self.is_on_ground = True

        # Lock delay
        if self.is_on_ground:
            self.lock_timer += dt
            if self.lock_timer >= LOCK_DELAY:
                self._lock_block()

    def _get_fall_speed(self) -> float:
        """Get current fall speed considering debuffs."""
        base_speed = INITIAL_FALL_SPEED * (SPEED_INCREASE_PER_LEVEL ** (self.level - 1))
        if BattlePowerUpType.SPEED_UP in self.active_debuffs:
            base_speed *= 0.5
        return base_speed

    def _move(self, dx: int, dy: int) -> bool:
        """Move current block."""
        if not self.current_block:
            return False

        # Handle reverse controls debuff
        if BattlePowerUpType.REVERSE in self.active_debuffs and dx != 0:
            dx = -dx

        self.current_block.x += dx
        self.current_block.y += dy

        if not self.board.is_valid_position(self.current_block):
            self.current_block.x -= dx
            self.current_block.y -= dy
            return False

        if dy > 0:
            self.is_on_ground = False
            self.lock_timer = 0

        return True

    def _rotate(self, clockwise: bool = True):
        """Rotate current block with wall kicks."""
        if not self.current_block:
            return

        old_rotation = self.current_block.rotation
        if clockwise:
            self.current_block.rotation = (self.current_block.rotation + 1) % len(self.current_block.shape)
        else:
            self.current_block.rotation = (self.current_block.rotation - 1) % len(self.current_block.shape)

        # Wall kick offsets
        kick_offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]

        for dx, dy in kick_offsets:
            self.current_block.x += dx
            self.current_block.y += dy
            if self.board.is_valid_position(self.current_block):
                return
            self.current_block.x -= dx
            self.current_block.y -= dy

        self.current_block.rotation = old_rotation

    def _hard_drop(self):
        """Hard drop current block."""
        if not self.current_block:
            return

        drop_distance = 0
        while self._move(0, 1):
            drop_distance += 1

        self.score += drop_distance * SCORE_HARD_DROP
        self._lock_block()

    def _hold(self):
        """Hold current block."""
        if not self.can_hold or not self.current_block:
            return

        if self.held_block:
            self.current_block, self.held_block = self.held_block, self.current_block
            self.current_block.x = (self.board.width - 4) // 2
            self.current_block.y = 0
            self.current_block.rotation = 0
        else:
            self.held_block = self.current_block
            self._spawn_block()

        self.can_hold = False

    def _use_powerup(self):
        """Use first powerup and send debuff to opponent."""
        if not self.powerups:
            return

        powerup = self.powerups.pop(0)
        duration = BATTLE_POWERUP_DURATION.get(powerup, 5.0)
        asyncio.create_task(self.network.send_debuff(powerup.value, duration))
        logger.info(f"Sent debuff {powerup.value} to opponent")

    def _lock_block(self):
        """Lock current block and check for line clears."""
        if not self.current_block:
            return

        # Place block on board
        for cell_x, cell_y in self.current_block.get_cells():
            if 0 <= cell_y < self.board.height and 0 <= cell_x < self.board.width:
                self.board.grid[cell_y][cell_x] = self.current_block.color

        # Clear lines
        lines_cleared = self.board.clear_lines()
        self.lines += lines_cleared

        # Score
        score_table = {1: SCORE_SINGLE_LINE, 2: SCORE_DOUBLE_LINE, 3: SCORE_TRIPLE_LINE, 4: SCORE_QUAD_LINE}
        self.score += score_table.get(lines_cleared, 0) * self.level

        # Level up
        self.level = self.lines // 10 + 1

        # Send garbage to opponent
        if lines_cleared >= 2:
            garbage_to_send = lines_cleared - 1
            asyncio.create_task(self.network.send_garbage(garbage_to_send))

        # Spawn next block
        if not self._spawn_block():
            asyncio.create_task(self.network.send_game_over())
            self._end_game()

    def _add_garbage_lines(self, count: int):
        """Add garbage lines from bottom."""
        for _ in range(count):
            # Move all rows up
            for y in range(1, self.board.height):
                self.board.grid[y - 1] = self.board.grid[y][:]

            # Create garbage line with random gap
            gap = random.randint(0, self.board.width - 1)
            garbage_row = [(128, 128, 128)] * self.board.width
            garbage_row[gap] = None
            self.board.grid[self.board.height - 1] = garbage_row

    def _end_game(self):
        """End the game."""
        self.state = GameState.GAME_OVER
        if not self.game_result:
            self.game_result = {'winner': 0, 'reason': 'TIMEOUT'}

    async def _sync_state(self):
        """Send state to server."""
        if self.state != GameState.PLAYING:
            return

        self._sync_counter += 1
        if self._sync_counter % 3 != 0:
            return

        await self.network.send_state(
            grid=self.board.grid,
            score=self.score,
            lines=self.lines,
            piece=self.current_block
        )

    def _render(self):
        """Render the game."""
        self.screen.fill(COLOR_WHITE)

        if self.waiting_for_match:
            self._draw_waiting_screen()
        elif self.state == GameState.PLAYING or self.state == GameState.GAME_OVER:
            self._draw_game()

        pygame.display.flip()

    def _draw_waiting_screen(self):
        """Draw waiting for opponent screen."""
        self.screen.fill(COLOR_WHITE)
        text = self.font_medium.render(self.connection_status, True, COLOR_TEXT)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(text, rect)

        hint = self.font_small.render("Press ESC to cancel", True, COLOR_TEXT)
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(hint, hint_rect)
        pygame.display.flip()

    def _draw_game(self):
        """Draw main game screen."""
        # 1. Draw opponent status bar at top (55px)
        self._draw_opponent_status_bar()

        # 2. Draw game board (offset down by 55px for status bar)
        board_offset_y = 55 + 50  # status bar + title area
        offset_x = 50

        # Set renderer screen to our screen and draw background
        self.renderer.screen = self.screen
        self.renderer.screen.blit(self.renderer.bg_surface, (0, 0))

        # Redraw status bar after background
        self._draw_opponent_status_bar()

        # Draw board and blocks
        self.renderer.draw_board(self.board, offset_x, board_offset_y)

        if self.current_block:
            self.renderer.draw_ghost_piece(self.current_block, self.board, offset_x, board_offset_y)
            self.renderer.draw_block(self.current_block, offset_x, board_offset_y)

        # Calculate board end position for UI placement
        board_end_x = offset_x + self.board.width * self.renderer.cell_size + 10

        # Draw UI elements
        self.renderer.draw_ui(
            score=self.score,
            level=self.level,
            lines=self.lines,
            high_score=0,
            board_end_x=board_end_x
        )

        # Draw next and hold blocks
        self.renderer.draw_next_block(self.next_block, board_end_x=board_end_x)
        self.renderer.draw_hold_block(self.held_block, board_end_x=board_end_x)

        # Draw powerup inventory if any
        if self.powerups:
            self._draw_powerups(board_end_x)

        # 3. Draw debuff effects on board
        self._draw_debuff_effects(board_offset_y)

        # 4. Draw touch controls
        self.touch_controls.draw(self.screen, self.font_small)

        # 5. Draw game over overlay
        if self.state == GameState.GAME_OVER:
            self._draw_game_over()

    def _draw_opponent_status_bar(self):
        """Draw opponent status bar at top of screen."""
        bar_height = 55
        bar_color = (50, 50, 60)

        # Background
        pygame.draw.rect(self.screen, bar_color, (0, 0, WINDOW_WIDTH, bar_height))

        # Timer (center)
        minutes = int(self.time_remaining) // 60
        seconds = int(self.time_remaining) % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"
        timer_surface = self.font_large.render(timer_text, True, COLOR_WHITE)
        timer_rect = timer_surface.get_rect(center=(WINDOW_WIDTH // 2, bar_height // 2))
        self.screen.blit(timer_surface, timer_rect)

        # Opponent info (left)
        vs_text = f"VS {self.opponent_name}"
        vs_surface = self.font_small.render(vs_text, True, COLOR_WHITE)
        self.screen.blit(vs_surface, (10, 8))

        score_text = f"{self.opponent_score} pts | {self.opponent_lines} lines"
        score_surface = self.font_small.render(score_text, True, (200, 200, 200))
        self.screen.blit(score_surface, (10, 32))

        # Garbage warning (right side, flashing)
        if self.pending_garbage > 0:
            flash = (time.time() - self.garbage_warning_flash) % 0.5 < 0.25
            warn_color = (255, 100, 100) if flash else (200, 50, 50)
            warn_text = f"+{self.pending_garbage}"
            warn_surface = self.font_medium.render(warn_text, True, warn_color)
            warn_rect = warn_surface.get_rect(right=WINDOW_WIDTH - 15, centery=bar_height // 2)
            self.screen.blit(warn_surface, warn_rect)

            # Warning icon
            pygame.draw.polygon(self.screen, warn_color, [
                (warn_rect.left - 25, bar_height // 2 - 12),
                (warn_rect.left - 5, bar_height // 2 - 12),
                (warn_rect.left - 15, bar_height // 2 + 12)
            ])

    def _draw_powerups(self, board_end_x: int):
        """Draw powerup inventory."""
        # Position below hold block
        panel_x = board_end_x + 15
        panel_y = 350
        panel_width = 120
        panel_height = 80

        # Panel background
        pygame.draw.rect(self.screen, (50, 50, 60), (panel_x, panel_y, panel_width, panel_height), border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 120), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=8)

        # Title
        title = self.font_small.render("POWER-UP", True, COLOR_WHITE)
        self.screen.blit(title, (panel_x + 10, panel_y + 5))

        # Powerup icons/names
        for i, powerup in enumerate(self.powerups[:2]):
            name = powerup.value[:3].upper()
            text = self.font_small.render(name, True, (255, 200, 100))
            self.screen.blit(text, (panel_x + 15 + i * 50, panel_y + 35))

        # Hint
        hint = self.font_small.render("[PWR]", True, (150, 150, 150))
        self.screen.blit(hint, (panel_x + 25, panel_y + 58))

    def _draw_debuff_effects(self, offset_y: int):
        """Draw visual debuff effects on the game board."""
        # Calculate board position
        board_width = self.board.width * CELL_SIZE
        board_height = self.board.height * CELL_SIZE
        offset_x = (WINDOW_WIDTH - board_width) // 2 - 80

        # Ink effect - dark overlay on bottom 2/3
        if BattlePowerUpType.INK in self.active_debuffs:
            ink_height = int(board_height * 0.67)
            ink_surface = pygame.Surface((board_width, ink_height))
            ink_surface.fill((5, 5, 10))
            ink_surface.set_alpha(240)
            self.screen.blit(ink_surface, (offset_x, offset_y + 50 + board_height - ink_height))

        # Draw active debuff icons
        if self.active_debuffs:
            debuff_y = offset_y + 60
            debuff_x = offset_x + board_width + 15
            label = self.font_small.render("DEBUFF", True, COLOR_RED)
            self.screen.blit(label, (debuff_x, debuff_y))
            for i, debuff in enumerate(self.active_debuffs.keys()):
                text = self.font_small.render(debuff.value[:3].upper(), True, COLOR_RED)
                self.screen.blit(text, (debuff_x, debuff_y + 20 + i * 18))

    def _draw_game_over(self):
        """Draw game over overlay."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        if not self.game_result:
            return

        winner = self.game_result.get('winner', 0)
        reason = self.game_result.get('reason', '')

        # Result text
        if winner == self.local_role:
            result_text = "YOU WIN!"
            color = (50, 200, 50)
        elif winner == 0:
            result_text = "DRAW"
            color = (200, 200, 50)
        else:
            result_text = "YOU LOSE"
            color = (200, 50, 50)

        text = self.font_large.render(result_text, True, color)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(text, rect)

        # Reason
        reason_texts = {
            'OPPONENT_DISCONNECTED': 'Opponent disconnected',
            'OPPONENT_TOPPED_OUT': 'Opponent topped out',
            'TIMEOUT': "Time's up!"
        }
        reason_str = reason_texts.get(reason, '')
        if reason_str:
            sub_text = self.font_medium.render(reason_str, True, COLOR_WHITE)
            sub_rect = sub_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
            self.screen.blit(sub_text, sub_rect)

        # Score
        score_text = f"Your Score: {self.score}"
        score_surface = self.font_small.render(score_text, True, COLOR_WHITE)
        score_rect = score_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        self.screen.blit(score_surface, score_rect)

        hint = self.font_small.render("Press ESC to return to menu", True, COLOR_WHITE)
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100))
        self.screen.blit(hint, hint_rect)

    async def _show_error_screen(self):
        """Show connection error screen."""
        error_start = time.time()
        while time.time() - error_start < 3:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return

            self.screen.fill(COLOR_WHITE)
            text = self.font_medium.render(self.connection_status, True, COLOR_TEXT)
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(text, rect)

            hint = self.font_small.render("Returning to menu...", True, COLOR_TEXT)
            hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
            self.screen.blit(hint, hint_rect)

            pygame.display.flip()
            await asyncio.sleep(0.1)
