"""
Online Battle Mode - 2-player networked Tetris battle.

Inherits from BattleGame and adds network synchronization.
"""

import pygame
import asyncio
import time
import logging
from .battle_game import BattleGame, BattlePlayer
from .network_manager import NetworkManager

logger = logging.getLogger(__name__)
from .constants import (
    GameState, CELL_SIZE, COLOR_WHITE, COLOR_TEXT, COLOR_BLACK,
    SCORE_SOFT_DROP, SCORE_HARD_DROP, BATTLE_DURATION, LOCK_DELAY,
    BattlePowerUpType, BATTLE_POWERUP_SPAWN_RATE, BATTLE_POWERUP_DURATION
)
from .board import Board
from .tetromino import create_tetromino, get_random_tetromino
import random


class OnlineBattleGame(BattleGame):
    """Online battle mode with network synchronization."""

    def __init__(self):
        # Initialize block sequences BEFORE super().__init__()
        # because parent's __init__ calls _spawn_block which uses these
        self.my_block_sequence = []  # Blocks for local player
        self.opponent_block_sequence = []  # Blocks for remote player
        self.my_block_index = 0
        self.opponent_block_index = 0
        self._use_server_blocks = False  # Flag to use random blocks during init

        super().__init__()

        self.network = NetworkManager()
        self.waiting_for_match = True
        self.local_role = 0  # 1 or 2, assigned by server
        self.connection_status = "Connecting..."
        self.opponent_disconnected = False
        self.game_result = None  # {winner, reason}

        # Sync counter for throttling state updates
        self._sync_counter = 0

        # Server time tracking
        self.server_time_remaining = BATTLE_DURATION

    async def connect_and_wait(self, player_name: str = "Player"):
        """Connect to server and wait for match."""
        success = await self.network.connect()
        if not success:
            self.connection_status = "Connection Failed!"
            return False

        self.connection_status = "Joining matchmaking..."

        # Join matchmaking queue
        await self.network.join_matchmaking(player_name)

        # Wait for MATCH_START or WAITING while keeping pygame responsive
        while self.waiting_for_match:
            # Process pygame events to prevent "not responding"
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False

            # Draw waiting screen
            self.screen.fill(COLOR_WHITE)
            text = self.font_medium.render(self.connection_status, True, COLOR_TEXT)
            rect = text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2))
            self.screen.blit(text, rect)

            hint = self.font_small.render("Press ESC to cancel", True, COLOR_TEXT)
            hint_rect = hint.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 50))
            self.screen.blit(hint, hint_rect)

            pygame.display.flip()
            self.clock.tick(30)

            # Check for network events
            event = await self.network.get_event()
            if event:
                if event['type'] == 'MATCH_START':
                    self.local_role = event['role']
                    self.network.role = event['role']
                    self.network.game_id = event.get('game_id')
                    self.network.opponent_name = event.get('opponent_name', 'Opponent')

                    # Get server-assigned block sequences
                    self.my_block_sequence = event.get('my_blocks', [])
                    self.opponent_block_sequence = event.get('opponent_blocks', [])
                    self.my_block_index = 0
                    self.opponent_block_index = 0

                    self.waiting_for_match = False
                    self.connection_status = "Match Starting!"
                    self._setup_online_game()
                    return True
                elif event['type'] == 'WAITING':
                    self.connection_status = "Waiting for opponent..."

            # Check if still connected
            if not self.network.connected:
                self.connection_status = "Connection Lost!"
                return False

            await asyncio.sleep(0.05)

        return True

    def _setup_online_game(self):
        """Configure players based on assigned role."""
        # Set local/remote flags
        self.player1.is_local = (self.local_role == 1)
        self.player2.is_local = (self.local_role == 2)

        # Set opponent name
        if self.local_role == 1:
            self.player2.name = self.network.opponent_name
        else:
            self.player1.name = self.network.opponent_name

        # Reset block indices and enable server blocks
        self.my_block_index = 0
        self.opponent_block_index = 0
        self._use_server_blocks = True  # Now use server sequence

        # Spawn initial blocks using server sequence
        # Clear existing blocks (from __init__) and spawn fresh ones
        self.player1.current_block = None
        self.player1.next_block = None
        self.player2.current_block = None
        self.player2.next_block = None

        # The overridden _spawn_block will use server sequences based on is_local
        self._spawn_block(self.player1)
        self._spawn_block(self.player2)

        # Start game
        self.state = GameState.PLAYING
        self.game_start_time = time.time()

    def _get_next_block_type(self, is_local: bool) -> str:
        """Get next block type from the server sequence.

        Args:
            is_local: True for local player's sequence, False for opponent's
        """
        # During __init__, sequences are empty - use random blocks
        # These will be replaced when game actually starts with server sequence
        if not self._use_server_blocks:
            return random.choice(['I', 'O', 'T', 'S', 'Z', 'J', 'L'])

        if is_local:
            if self.my_block_index < len(self.my_block_sequence):
                block_type = self.my_block_sequence[self.my_block_index]
                self.my_block_index += 1
                return block_type
            else:
                # Fallback if we run out of blocks (shouldn't happen in 10min game)
                return random.choice(['I', 'O', 'T', 'S', 'Z', 'J', 'L'])
        else:
            if self.opponent_block_index < len(self.opponent_block_sequence):
                block_type = self.opponent_block_sequence[self.opponent_block_index]
                self.opponent_block_index += 1
                return block_type
            else:
                return random.choice(['I', 'O', 'T', 'S', 'Z', 'J', 'L'])

    def _spawn_block(self, player: BattlePlayer) -> bool:
        """Override parent's spawn_block to use server-assigned sequence.

        Args:
            player: The player to spawn a block for

        Returns:
            True if spawned successfully, False if game over
        """
        # Determine if this is the local player based on role
        is_local = player.is_local

        if player.next_block:
            player.current_block = player.next_block
        else:
            # Get first block from sequence
            block_type = self._get_next_block_type(is_local)
            player.current_block = create_tetromino(block_type)

        # Spawn power-ups for local player only (opponent won't see them, but that's OK)
        if is_local and random.random() < BATTLE_POWERUP_SPAWN_RATE:
            powerup = random.choice(list(BattlePowerUpType))
            player.add_powerup(powerup)

        # Get next block from sequence
        next_block_type = self._get_next_block_type(is_local)
        player.next_block = create_tetromino(next_block_type)

        # Center the block
        current_shape = player.current_block.shape[player.current_block.rotation]
        block_width = len(current_shape[0]) if current_shape else 0
        player.current_block.x = (player.board.width - block_width) // 2
        player.current_block.y = 0
        player.current_block.rotation = 0

        # Check if spawn position is valid
        if not player.board.is_valid_position(player.current_block):
            player.is_dead = True
            return False

        player.fall_timer = 0
        player.lock_timer = 0
        player.is_on_ground = False
        player.can_hold = True

        return True

    async def run_async(self, player_name: str = "Player"):
        """Main async game loop."""
        # Initial connection
        connected = await self.connect_and_wait(player_name)

        if not connected:
            # Show error for 2 seconds then return
            error_start = time.time()
            while time.time() - error_start < 3:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return

                self.screen.fill(COLOR_WHITE)
                text = self.font_medium.render(self.connection_status, True, COLOR_TEXT)
                rect = text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2))
                self.screen.blit(text, rect)

                hint = self.font_small.render("Returning to menu...", True, COLOR_TEXT)
                hint_rect = hint.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 50))
                self.screen.blit(hint, hint_rect)

                pygame.display.flip()
                await asyncio.sleep(0.1)
            return

        running = True

        while running:
            dt = self.clock.tick(60) / 1000.0

            # 1. Process network events
            await self._process_network_events()

            # 2. Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif not self._handle_event_online(event):
                    running = False

            # 3. Handle continuous input (only for local player)
            self._handle_input_online()

            # 4. Update game state (only for local player)
            self._update_online(dt)

            # 5. Render
            self._render_online()

            # 6. Send state to server
            await self._sync_state()

            # Yield to event loop
            await asyncio.sleep(0)

        self.network.close()
        pygame.quit()

    async def _process_network_events(self):
        """Process all pending network events."""
        while True:
            event = await self.network.get_event()
            if not event:
                break

            event_type = event.get('type')

            if event_type == 'OPPONENT_STATE':
                self._handle_opponent_state(event)

            elif event_type == 'GARBAGE':
                # Receive garbage from opponent
                lines = event.get('lines', 0)
                local_player = self.player1 if self.local_role == 1 else self.player2
                local_player.pending_garbage += lines

            elif event_type == 'TIME_SYNC':
                # Server time sync
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
                # Receive debuff from opponent - apply to local player
                debuff_type_str = event.get('debuff', '')
                duration = event.get('duration', 5.0)
                logger.info(f"Received DEBUFF: {debuff_type_str} for {duration}s")
                local_player = self.player1 if self.local_role == 1 else self.player2
                # Convert string to BattlePowerUpType enum
                try:
                    debuff_enum = BattlePowerUpType(debuff_type_str)
                    # apply_debuff expects current_time, not duration!
                    current_time = time.time()
                    local_player.apply_debuff(debuff_enum, current_time)
                    logger.info(f"Applied debuff {debuff_enum} to local player (ends at {current_time + duration})")
                except ValueError:
                    logger.warning(f"Unknown debuff type: {debuff_type_str}")

    def _handle_opponent_state(self, data):
        """Update remote player's state from network data."""
        remote_player = self.player2 if self.local_role == 1 else self.player1

        # Update grid
        if 'grid' in data:
            for y, row in enumerate(data['grid']):
                for x, cell in enumerate(row):
                    if cell == 0:
                        remote_player.board.grid[y][x] = None
                    else:
                        remote_player.board.grid[y][x] = tuple(cell)

        # Update stats
        remote_player.score = data.get('score', remote_player.score)
        remote_player.lines = data.get('lines', remote_player.lines)

        # Update current piece for display
        # Create a visual-only Block from the received piece data
        if 'piece' in data:
            piece_data = data['piece']
            if piece_data and 'shape' in piece_data:
                from .tetromino import Block
                # Create a block with the received shape and position
                shape = piece_data.get('shape', [])
                color = tuple(piece_data.get('color', [128, 128, 128]))
                x = piece_data.get('x', 0)
                y = piece_data.get('y', 0)

                # Create a minimal Block for rendering
                # Shape needs to be in the format: [rotation0, rotation1, ...]
                # Since we receive the current rotation's shape, wrap it
                visual_block = Block(
                    shape=[shape],  # Single rotation shape
                    color=color,
                    x=x,
                    y=y,
                    rotation=0
                )
                remote_player.current_block = visual_block

    def _handle_event_online(self, event) -> bool:
        """Handle pygame events for online mode.

        Uses unified single-player controls (same as solo modes):
        - Arrow keys: Move left/right, soft drop
        - Space: Hard drop
        - Up / X: Rotate clockwise
        - Z: Rotate counter-clockwise
        - C: Hold
        - Shift: Use power-up
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False

            if self.state == GameState.PLAYING:
                local_player = self.player1 if self.local_role == 1 else self.player2
                opponent = self.player2 if self.local_role == 1 else self.player1

                if not local_player.is_dead:
                    # Unified controls (same as single-player mode)
                    if event.key == pygame.K_SPACE:
                        self._hard_drop(local_player, opponent)
                    elif event.key in (pygame.K_UP, pygame.K_x):
                        self._rotate_block(local_player, clockwise=True)
                    elif event.key == pygame.K_z:
                        self._rotate_block(local_player, clockwise=False)
                    elif event.key == pygame.K_c:
                        self._hold_block(local_player)
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self._use_powerup(local_player, opponent)

            elif self.state == GameState.GAME_OVER:
                if event.key == pygame.K_ESCAPE:
                    return False

        return True

    def _handle_input_online(self):
        """Handle continuous keyboard input for local player only.

        Uses unified single-player controls (arrow keys).
        """
        if self.state != GameState.PLAYING:
            return

        keys = pygame.key.get_pressed()
        current_time = time.time()

        local_player = self.player1 if self.local_role == 1 else self.player2
        inputs = self.last_input_time[local_player.player_id]

        if local_player.is_dead:
            return

        # Unified controls: Arrow keys for movement
        if keys[pygame.K_LEFT] and current_time - inputs.get('left', 0) > self.input_delay:
            self._move_block(local_player, -1, 0)
            inputs['left'] = current_time
        if keys[pygame.K_RIGHT] and current_time - inputs.get('right', 0) > self.input_delay:
            self._move_block(local_player, 1, 0)
            inputs['right'] = current_time
        if keys[pygame.K_DOWN] and current_time - inputs.get('down', 0) > self.input_delay:
            if self._move_block(local_player, 0, 1):
                local_player.score += SCORE_SOFT_DROP
            inputs['down'] = current_time

    def _update_online(self, dt: float):
        """Update game state for local player only."""
        if self.state != GameState.PLAYING:
            return

        # Update timer (prefer server time if available)
        if self.server_time_remaining > 0:
            self.time_remaining = self.server_time_remaining
        else:
            elapsed = time.time() - self.game_start_time
            self.time_remaining = max(0, BATTLE_DURATION - elapsed)

        if self.time_remaining <= 0:
            self._end_game_online()
            return

        # Update debuffs (clear expired effects)
        current_time = time.time()
        self.player1.update_debuffs(current_time)
        self.player2.update_debuffs(current_time)

        # Only update local player physics
        local_player = self.player1 if self.local_role == 1 else self.player2
        opponent = self.player2 if self.local_role == 1 else self.player1

        if local_player.is_dead:
            return

        # Apply pending garbage
        if local_player.pending_garbage > 0:
            self._add_garbage_lines(local_player, local_player.pending_garbage)
            local_player.pending_garbage = 0

        # Fall timer
        local_player.fall_timer += dt
        fall_speed = local_player.get_fall_speed()

        if local_player.fall_timer >= fall_speed:
            local_player.fall_timer = 0
            if not self._move_block(local_player, 0, 1):
                local_player.is_on_ground = True

        # Lock delay
        if local_player.is_on_ground:
            local_player.lock_timer += dt
            if local_player.lock_timer >= LOCK_DELAY:
                self._lock_block_online(local_player, opponent)

        # Check death
        if local_player.is_dead:
            asyncio.create_task(self.network.send_game_over())
            self._end_game_online()

    def _use_powerup(self, player, opponent):
        """Override to send powerup effect via network instead of locally."""
        powerup = player.use_powerup()
        if powerup:
            # Get duration for this powerup type
            duration = BATTLE_POWERUP_DURATION.get(powerup, 5.0)
            # Send debuff to remote opponent via network
            logger.info(f"Sending DEBUFF: {powerup.value} for {duration}s")
            asyncio.create_task(self.network.send_debuff(powerup.value, duration))

    def _lock_block_online(self, player, opponent):
        """Lock block and handle garbage sending via network."""
        # Use parent's lock logic
        lines_before = player.lines
        self._lock_block(player, opponent)
        lines_cleared = player.lines - lines_before

        # Send garbage via network instead of directly adding to opponent
        if lines_cleared >= 2:
            garbage_to_send = lines_cleared - 1
            # Reset opponent's pending_garbage (parent added it locally)
            opponent.pending_garbage = max(0, opponent.pending_garbage - garbage_to_send)
            # Send via network
            asyncio.create_task(self.network.send_garbage(garbage_to_send))

    def _end_game_online(self):
        """End the game and determine winner."""
        self.state = GameState.GAME_OVER

        local_player = self.player1 if self.local_role == 1 else self.player2
        remote_player = self.player2 if self.local_role == 1 else self.player1

        if local_player.is_dead:
            # I lost
            winner = 2 if self.local_role == 1 else 1
        elif remote_player.is_dead:
            # Opponent lost
            winner = self.local_role
        else:
            # Time's up - compare scores
            if local_player.score > remote_player.score:
                winner = self.local_role
            elif local_player.score < remote_player.score:
                winner = 2 if self.local_role == 1 else 1
            else:
                winner = 0  # Draw

        self.game_result = {'winner': winner, 'reason': 'TIMEOUT'}

    async def _sync_state(self):
        """Send local state to opponent periodically."""
        if self.state != GameState.PLAYING:
            return

        # Throttle: send every 3 frames (~20 FPS)
        self._sync_counter += 1
        if self._sync_counter % 3 != 0:
            return

        local_player = self.player1 if self.local_role == 1 else self.player2

        await self.network.send_state(
            grid=local_player.board.grid,
            score=local_player.score,
            lines=local_player.lines,
            piece=local_player.current_block
        )

    def _render_online(self):
        """Render the online battle game."""
        if self.waiting_for_match:
            self.screen.fill(COLOR_WHITE)
            text = self.font_medium.render(self.connection_status, True, COLOR_TEXT)
            rect = text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2))
            self.screen.blit(text, rect)
            pygame.display.flip()
            return

        # Use parent's render
        super().render()

        # Overlay game result if game over
        if self.state == GameState.GAME_OVER and self.game_result:
            self._draw_game_over_overlay()

        pygame.display.flip()

    def _draw_game_over_overlay(self):
        """Draw game over overlay with result."""
        # Dark overlay
        overlay = pygame.Surface((self.BATTLE_WINDOW_WIDTH, self.BATTLE_WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # Result text
        winner = self.game_result.get('winner', 0)
        reason = self.game_result.get('reason', '')

        if winner == self.local_role:
            result_text = "YOU WIN!"
            color = (50, 200, 50)  # Green
        elif winner == 0:
            result_text = "DRAW"
            color = (200, 200, 50)  # Yellow
        else:
            result_text = "YOU LOSE"
            color = (200, 50, 50)  # Red

        text = self.font_large.render(result_text, True, color)
        rect = text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(text, rect)

        # Reason
        if reason == 'OPPONENT_DISCONNECTED':
            reason_text = "Opponent disconnected"
        elif reason == 'OPPONENT_TOPPED_OUT':
            reason_text = "Opponent topped out"
        elif reason == 'TIMEOUT':
            reason_text = "Time's up!"
        else:
            reason_text = ""

        if reason_text:
            sub_text = self.font_medium.render(reason_text, True, COLOR_WHITE)
            sub_rect = sub_text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 20))
            self.screen.blit(sub_text, sub_rect)

        # Instructions
        hint = self.font_small.render("Press ESC to return to menu", True, COLOR_WHITE)
        hint_rect = hint.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 80))
        self.screen.blit(hint, hint_rect)
