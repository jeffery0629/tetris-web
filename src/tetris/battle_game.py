"""Battle mode game controller for 2-player local multiplayer."""

import pygame
import time
import random
from typing import Optional, List, Tuple
from .board import Board
from .tetromino import Block, get_random_tetromino
from .constants import (
    FPS, INITIAL_FALL_SPEED, LOCK_DELAY,
    SPEED_INCREASE_PER_LEVEL, LINES_PER_LEVEL,
    SCORE_SINGLE_LINE, SCORE_DOUBLE_LINE, SCORE_TRIPLE_LINE, SCORE_QUAD_LINE,
    SCORE_SOFT_DROP, SCORE_HARD_DROP,
    GameState, BattlePowerUpType,
    BATTLE_DURATION, BATTLE_GRID, GARBAGE_LINES,
    BATTLE_POWERUP_DURATION, BATTLE_POWERUP_SPAWN_RATE,
    WINDOW_WIDTH, WINDOW_HEIGHT, CELL_SIZE,
    COLOR_WHITE, COLOR_BLACK, COLOR_TEXT, COLOR_GRAY,
    COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW,
)


class BattlePlayer:
    """Represents one player in battle mode."""

    def __init__(self, player_id: int, board: Board):
        """Initialize battle player.

        Args:
            player_id: 1 or 2
            board: Player's game board
        """
        self.player_id = player_id
        self.board = board
        self.score = 0
        self.lines = 0
        self.level = 1

        # Current and next blocks
        self.current_block: Optional[Block] = None
        self.next_block: Optional[Block] = None
        self.hold_block: Optional[Block] = None
        self.can_hold = True

        # Timing
        self.fall_timer = 0
        self.lock_timer = 0
        self.is_on_ground = False

        # Battle power-up inventory (max 2)
        self.powerups: List[BattlePowerUpType] = []

        # Active debuffs (from opponent's attacks)
        self.active_debuffs: dict = {}  # {debuff_type: end_time}

        # Pending garbage lines to receive
        self.pending_garbage = 0

        # Game over flag
        self.is_dead = False

        # Name for display
        self.name = f"P{player_id}"

        # Online mode: is this player controlled locally?
        self.is_local = True  # Default True for local battle mode

    def get_fall_speed(self) -> float:
        """Get current fall speed, considering debuffs."""
        base_speed = INITIAL_FALL_SPEED * (SPEED_INCREASE_PER_LEVEL ** (self.level - 1))

        # Speed up debuff doubles fall speed (halves the interval)
        if BattlePowerUpType.SPEED_UP in self.active_debuffs:
            base_speed *= 0.5

        return base_speed

    def is_controls_reversed(self) -> bool:
        """Check if controls are reversed by debuff."""
        return BattlePowerUpType.REVERSE in self.active_debuffs

    def is_ink_active(self) -> bool:
        """Check if ink debuff is active."""
        return BattlePowerUpType.INK in self.active_debuffs

    def is_fog_active(self) -> bool:
        """Check if fog debuff is active (hide next block)."""
        return BattlePowerUpType.FOG in self.active_debuffs

    def get_earthquake_offset(self) -> int:
        """Get horizontal shake offset if earthquake is active."""
        if BattlePowerUpType.EARTHQUAKE in self.active_debuffs:
            return random.randint(-2, 2) * 3  # Shake by 3 pixels
        return 0

    def update_debuffs(self, current_time: float) -> None:
        """Remove expired debuffs."""
        expired = [d for d, end_time in self.active_debuffs.items()
                   if current_time > end_time]
        for d in expired:
            del self.active_debuffs[d]

    def apply_debuff(self, debuff: BattlePowerUpType, current_time: float) -> None:
        """Apply a debuff from opponent."""
        duration = BATTLE_POWERUP_DURATION.get(debuff, 5.0)
        self.active_debuffs[debuff] = current_time + duration

    def add_powerup(self, powerup: BattlePowerUpType) -> bool:
        """Add a power-up to inventory.

        Returns:
            True if added, False if inventory full
        """
        if len(self.powerups) < 2:
            self.powerups.append(powerup)
            return True
        return False

    def use_powerup(self) -> Optional[BattlePowerUpType]:
        """Use the first power-up in inventory.

        Returns:
            The power-up type used, or None if empty
        """
        if self.powerups:
            return self.powerups.pop(0)
        return None


class BattleGame:
    """Battle mode game controller for 2-player local multiplayer."""

    # Battle mode needs a wider window for split screen
    BATTLE_WINDOW_WIDTH = 1000
    BATTLE_WINDOW_HEIGHT = 750

    def __init__(self):
        """Initialize battle game."""
        pygame.init()

        # Create window (wider for split screen)
        self.screen = pygame.display.set_mode((self.BATTLE_WINDOW_WIDTH, self.BATTLE_WINDOW_HEIGHT))
        pygame.display.set_caption("Claire's Tetris - BATTLE MODE")

        self.clock = pygame.time.Clock()

        # Create two players with their own boards
        self.player1 = BattlePlayer(1, Board(BATTLE_GRID[0], BATTLE_GRID[1]))
        self.player2 = BattlePlayer(2, Board(BATTLE_GRID[0], BATTLE_GRID[1]))

        # Game state
        self.state = GameState.PLAYING
        self.game_start_time = 0
        self.time_remaining = BATTLE_DURATION

        # Winner (1, 2, or 0 for tie)
        self.winner = 0

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Initialize blocks for both players
        self._spawn_block(self.player1)
        self._spawn_block(self.player2)
        self.player1.next_block = get_random_tetromino()
        self.player2.next_block = get_random_tetromino()

        # Input timing
        self.last_input_time = {1: {}, 2: {}}
        self.input_delay = 0.08  # 80ms between repeated inputs

    def _spawn_block(self, player: BattlePlayer) -> bool:
        """Spawn a new block for a player.

        Returns:
            True if spawned successfully, False if game over
        """
        if player.next_block:
            player.current_block = player.next_block
        else:
            player.current_block = get_random_tetromino()

        # Maybe spawn a battle power-up
        if random.random() < BATTLE_POWERUP_SPAWN_RATE:
            powerup = random.choice(list(BattlePowerUpType))
            player.add_powerup(powerup)

        player.next_block = get_random_tetromino()

        # Center the block - use current rotation's shape to get actual width
        current_shape = player.current_block.shape[player.current_block.rotation]
        block_width = len(current_shape[0]) if current_shape else 0
        player.current_block.x = (player.board.width - block_width) // 2
        player.current_block.y = 0
        player.current_block.rotation = 0  # Reset rotation for new block

        # Check if spawn position is valid (is_valid_position returns True if OK)
        if not player.board.is_valid_position(player.current_block):
            player.is_dead = True
            return False

        player.fall_timer = 0
        player.lock_timer = 0
        player.is_on_ground = False
        player.can_hold = True

        return True

    def _add_garbage_lines(self, player: BattlePlayer, count: int) -> None:
        """Add garbage lines to a player's board from the bottom."""
        if count <= 0:
            return

        # Move existing blocks up
        for y in range(count, player.board.height):
            for x in range(player.board.width):
                player.board.grid[y - count][x] = player.board.grid[y][x]

        # Add garbage lines at bottom
        for y in range(player.board.height - count, player.board.height):
            gap = random.randint(0, player.board.width - 1)
            for x in range(player.board.width):
                if x == gap:
                    player.board.grid[y][x] = None
                else:
                    # Gray garbage block
                    player.board.grid[y][x] = COLOR_GRAY

    def _lock_block(self, player: BattlePlayer, opponent: BattlePlayer) -> None:
        """Lock current block and handle line clears."""
        if not player.current_block:
            return

        # Place block on board
        player.board.place_block(player.current_block)

        # Check for line clears
        lines_cleared = player.board.clear_lines()

        if lines_cleared > 0:
            # Update score
            line_scores = {1: SCORE_SINGLE_LINE, 2: SCORE_DOUBLE_LINE,
                          3: SCORE_TRIPLE_LINE, 4: SCORE_QUAD_LINE}
            player.score += line_scores.get(lines_cleared, SCORE_QUAD_LINE) * player.level
            player.lines += lines_cleared

            # Level up
            if player.lines >= player.level * LINES_PER_LEVEL:
                player.level += 1

            # Send garbage to opponent
            garbage = GARBAGE_LINES.get(lines_cleared, 0)
            if garbage > 0:
                opponent.pending_garbage += garbage

        # Process pending garbage for current player
        if player.pending_garbage > 0:
            self._add_garbage_lines(player, player.pending_garbage)
            player.pending_garbage = 0

        # Spawn new block
        self._spawn_block(player)

    def _move_block(self, player: BattlePlayer, dx: int, dy: int) -> bool:
        """Move player's block."""
        if not player.current_block:
            return False

        # Apply control reversal debuff
        if player.is_controls_reversed() and dx != 0:
            dx = -dx

        player.current_block.x += dx
        player.current_block.y += dy

        if not player.board.is_valid_position(player.current_block):
            player.current_block.x -= dx
            player.current_block.y -= dy
            return False

        # After horizontal move, re-check if block is still on ground
        if dx != 0:
            # Check if there's space below
            player.current_block.y += 1
            if player.board.is_valid_position(player.current_block):
                # Not on ground anymore - reset lock timer and ground state
                player.is_on_ground = False
                player.lock_timer = 0
            player.current_block.y -= 1

        if dy > 0:
            player.lock_timer = 0

        return True

    def _rotate_block(self, player: BattlePlayer, clockwise: bool = True) -> bool:
        """Rotate player's block with wall kicks."""
        if not player.current_block:
            return False

        # Save original rotation state
        original_rotation = player.current_block.rotation
        original_x = player.current_block.x
        original_y = player.current_block.y

        # Rotate using Block API (modifies rotation index, not shape)
        if clockwise:
            player.current_block.rotate_cw()
        else:
            player.current_block.rotate_ccw()

        # Wall kick offsets
        kicks = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1), (0, -2)]

        for kick_x, kick_y in kicks:
            player.current_block.x = original_x + kick_x
            player.current_block.y = original_y + kick_y

            if player.board.is_valid_position(player.current_block):
                player.lock_timer = 0
                return True

        # Restore original state if all kicks fail
        player.current_block.rotation = original_rotation
        player.current_block.x = original_x
        player.current_block.y = original_y
        return False

    def _hard_drop(self, player: BattlePlayer, opponent: BattlePlayer) -> None:
        """Hard drop player's block."""
        if not player.current_block:
            return

        drop_distance = 0
        while player.board.is_valid_position(player.current_block):
            player.current_block.y += 1
            drop_distance += 1

        player.current_block.y -= 1
        drop_distance -= 1  # Subtract 1 since last move was invalid
        player.score += drop_distance * SCORE_HARD_DROP

        self._lock_block(player, opponent)

    def _hold_block(self, player: BattlePlayer) -> None:
        """Hold current block."""
        if not player.can_hold or not player.current_block:
            return

        if player.hold_block:
            # Swap
            player.current_block, player.hold_block = player.hold_block, player.current_block
            # Reset and center the swapped-in block
            player.current_block.rotation = 0
            current_shape = player.current_block.shape[0]  # Use rotation 0
            block_width = len(current_shape[0]) if current_shape else 0
            player.current_block.x = (player.board.width - block_width) // 2
            player.current_block.y = 0
        else:
            player.hold_block = player.current_block
            self._spawn_block(player)

        # Reset hold block's rotation for display
        if player.hold_block:
            player.hold_block.rotation = 0

        player.can_hold = False

    def _use_powerup(self, player: BattlePlayer, opponent: BattlePlayer) -> None:
        """Use player's power-up against opponent."""
        powerup = player.use_powerup()
        if powerup:
            current_time = time.time()
            opponent.apply_debuff(powerup, current_time)

    def handle_input(self) -> None:
        """Handle keyboard input for both players."""
        keys = pygame.key.get_pressed()
        current_time = time.time()

        # Player 1: WASD + Space + Q/E
        p1_inputs = self.last_input_time[1]
        if self.state == GameState.PLAYING and not self.player1.is_dead:
            # Movement
            if keys[pygame.K_a] and current_time - p1_inputs.get('left', 0) > self.input_delay:
                self._move_block(self.player1, -1, 0)
                p1_inputs['left'] = current_time
            if keys[pygame.K_d] and current_time - p1_inputs.get('right', 0) > self.input_delay:
                self._move_block(self.player1, 1, 0)
                p1_inputs['right'] = current_time
            if keys[pygame.K_s] and current_time - p1_inputs.get('down', 0) > self.input_delay:
                if self._move_block(self.player1, 0, 1):
                    self.player1.score += SCORE_SOFT_DROP
                p1_inputs['down'] = current_time

        # Player 2: Arrow keys + Enter + / and .
        p2_inputs = self.last_input_time[2]
        if self.state == GameState.PLAYING and not self.player2.is_dead:
            if keys[pygame.K_LEFT] and current_time - p2_inputs.get('left', 0) > self.input_delay:
                self._move_block(self.player2, -1, 0)
                p2_inputs['left'] = current_time
            if keys[pygame.K_RIGHT] and current_time - p2_inputs.get('right', 0) > self.input_delay:
                self._move_block(self.player2, 1, 0)
                p2_inputs['right'] = current_time
            if keys[pygame.K_DOWN] and current_time - p2_inputs.get('down', 0) > self.input_delay:
                if self._move_block(self.player2, 0, 1):
                    self.player2.score += SCORE_SOFT_DROP
                p2_inputs['down'] = current_time

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events.

        Returns:
            False if should quit, True otherwise
        """
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            # Escape to pause/quit
            if event.key == pygame.K_ESCAPE:
                if self.state == GameState.PLAYING:
                    self.state = GameState.PAUSED
                elif self.state == GameState.PAUSED:
                    self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER:
                    return False

            # Player 1 controls
            if self.state == GameState.PLAYING and not self.player1.is_dead:
                if event.key == pygame.K_w:
                    self._rotate_block(self.player1)
                elif event.key == pygame.K_SPACE:
                    self._hard_drop(self.player1, self.player2)
                elif event.key == pygame.K_q:
                    self._use_powerup(self.player1, self.player2)
                elif event.key == pygame.K_e:
                    self._hold_block(self.player1)

            # Player 2 controls
            if self.state == GameState.PLAYING and not self.player2.is_dead:
                if event.key == pygame.K_UP:
                    self._rotate_block(self.player2)
                elif event.key == pygame.K_RETURN:
                    self._hard_drop(self.player2, self.player1)
                elif event.key == pygame.K_SLASH:
                    self._use_powerup(self.player2, self.player1)
                elif event.key == pygame.K_PERIOD:
                    self._hold_block(self.player2)

            # Restart on R when game over
            if event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                self.restart()

        return True

    def update(self, dt: float) -> None:
        """Update game logic."""
        if self.state != GameState.PLAYING:
            return

        current_time = time.time()

        # Update timer
        elapsed = current_time - self.game_start_time
        self.time_remaining = max(0, BATTLE_DURATION - elapsed)

        # Check time up
        if self.time_remaining <= 0:
            self._end_game()
            return

        # Update debuffs
        self.player1.update_debuffs(current_time)
        self.player2.update_debuffs(current_time)

        # Update each player
        for player, opponent in [(self.player1, self.player2), (self.player2, self.player1)]:
            if player.is_dead:
                continue

            # Fall timer
            player.fall_timer += dt
            fall_speed = player.get_fall_speed()

            if player.fall_timer >= fall_speed:
                player.fall_timer = 0
                if not self._move_block(player, 0, 1):
                    player.is_on_ground = True

            # Lock delay
            if player.is_on_ground:
                player.lock_timer += dt
                if player.lock_timer >= LOCK_DELAY:
                    self._lock_block(player, opponent)

            # Check if player died
            if player.is_dead:
                self._end_game()
                return

    def _end_game(self) -> None:
        """End the game and determine winner."""
        self.state = GameState.GAME_OVER

        if self.player1.is_dead and not self.player2.is_dead:
            self.winner = 2
        elif self.player2.is_dead and not self.player1.is_dead:
            self.winner = 1
        elif self.player1.score > self.player2.score:
            self.winner = 1
        elif self.player2.score > self.player1.score:
            self.winner = 2
        else:
            self.winner = 0  # Tie

    def restart(self) -> None:
        """Restart the game."""
        self.player1 = BattlePlayer(1, Board(BATTLE_GRID[0], BATTLE_GRID[1]))
        self.player2 = BattlePlayer(2, Board(BATTLE_GRID[0], BATTLE_GRID[1]))

        self._spawn_block(self.player1)
        self._spawn_block(self.player2)
        self.player1.next_block = get_random_tetromino()
        self.player2.next_block = get_random_tetromino()

        self.state = GameState.PLAYING
        self.game_start_time = time.time()
        self.time_remaining = BATTLE_DURATION
        self.winner = 0

    def render(self) -> None:
        """Render the game."""
        self.screen.fill(COLOR_WHITE)

        # Calculate layout
        board_width = BATTLE_GRID[0] * CELL_SIZE
        board_height = BATTLE_GRID[1] * CELL_SIZE
        side_panel_width = 100

        # Player 1 (left side) - board + side panel
        p1_board_x = 50
        p1_board_y = 100

        # Player 2 (right side) - leave space for side panel on left
        p2_board_x = self.BATTLE_WINDOW_WIDTH - 50 - board_width - side_panel_width
        p2_board_y = 100

        # Draw timer at top center
        self._draw_timer()

        # Draw both players
        self._draw_player(self.player1, p1_board_x, p1_board_y, board_width, board_height)
        self._draw_player(self.player2, p2_board_x, p2_board_y, board_width, board_height)

        # Draw game over overlay if needed
        if self.state == GameState.GAME_OVER:
            self._draw_game_over()
        elif self.state == GameState.PAUSED:
            self._draw_paused()

        pygame.display.flip()

    def _draw_timer(self) -> None:
        """Draw the countdown timer."""
        minutes = int(self.time_remaining) // 60
        seconds = int(self.time_remaining) % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"

        text_surface = self.font_large.render(timer_text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, 40))
        self.screen.blit(text_surface, text_rect)

        # Battle mode title
        title = self.font_medium.render("BATTLE MODE", True, COLOR_RED)
        title_rect = title.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, 75))
        self.screen.blit(title, title_rect)

    def _draw_player(self, player: BattlePlayer, board_x: int, board_y: int,
                     board_width: int, board_height: int) -> None:
        """Draw a player's game area."""
        # Apply earthquake shake
        shake_offset = player.get_earthquake_offset()
        board_x += shake_offset

        # Player name and score
        name_text = self.font_medium.render(f"P{player.player_id}: {player.name}", True, COLOR_TEXT)
        score_text = self.font_small.render(f"Score: {player.score}  Lines: {player.lines}  Lv.{player.level}", True, COLOR_TEXT)

        name_x = board_x + board_width // 2 - name_text.get_width() // 2
        self.screen.blit(name_text, (name_x, board_y - 60))
        self.screen.blit(score_text, (board_x, board_y - 30))

        # Draw board background
        pygame.draw.rect(self.screen, (240, 240, 245),
                        (board_x, board_y, board_width, board_height))
        pygame.draw.rect(self.screen, COLOR_GRAY,
                        (board_x, board_y, board_width, board_height), 2)

        # Draw grid
        for y in range(player.board.height):
            for x in range(player.board.width):
                cell_x = board_x + x * CELL_SIZE
                cell_y = board_y + y * CELL_SIZE

                cell = player.board.grid[y][x]
                if cell:
                    pygame.draw.rect(self.screen, cell,
                                    (cell_x + 1, cell_y + 1, CELL_SIZE - 2, CELL_SIZE - 2))

        # Draw current block using get_cells() for correct rotation handling
        if player.current_block and not player.is_dead:
            for cell_x, cell_y in player.current_block.get_cells():
                if cell_y >= 0:  # Only draw visible cells
                    draw_x = board_x + cell_x * CELL_SIZE
                    draw_y = board_y + cell_y * CELL_SIZE
                    pygame.draw.rect(self.screen, player.current_block.color,
                                    (draw_x + 1, draw_y + 1, CELL_SIZE - 2, CELL_SIZE - 2))

        # Draw ink overlay (covers bottom 2/3 of the board - more opaque black)
        if player.is_ink_active():
            ink_height = int(board_height * 0.67)  # Cover 2/3 of the board
            ink_surface = pygame.Surface((board_width, ink_height))
            ink_surface.fill((5, 5, 10))  # Very dark black
            ink_surface.set_alpha(245)  # Almost fully opaque
            self.screen.blit(ink_surface, (board_x, board_y + board_height - ink_height))

        # Draw next block (or fog)
        next_x = board_x + board_width + 10
        next_y = board_y
        next_label = self.font_small.render("NEXT", True, COLOR_TEXT)
        self.screen.blit(next_label, (next_x, next_y))

        if player.is_fog_active():
            fog_text = self.font_small.render("???", True, COLOR_GRAY)
            self.screen.blit(fog_text, (next_x, next_y + 25))
        elif player.next_block:
            self._draw_mini_block(player.next_block, next_x, next_y + 25)

        # Draw hold block
        hold_y = next_y + 80
        hold_label = self.font_small.render("HOLD", True, COLOR_TEXT)
        self.screen.blit(hold_label, (next_x, hold_y))
        if player.hold_block:
            self._draw_mini_block(player.hold_block, next_x, hold_y + 25)

        # Draw power-ups
        powerup_y = hold_y + 80
        powerup_label = self.font_small.render("PWR", True, COLOR_TEXT)
        self.screen.blit(powerup_label, (next_x, powerup_y))
        for i, pwr in enumerate(player.powerups):
            pwr_text = self.font_small.render(pwr.value[:3].upper(), True, COLOR_BLUE)
            self.screen.blit(pwr_text, (next_x, powerup_y + 25 + i * 20))

        # Draw active debuffs
        if player.active_debuffs:
            debuff_y = powerup_y + 80
            debuff_label = self.font_small.render("DEBUFF", True, COLOR_RED)
            self.screen.blit(debuff_label, (next_x - 10, debuff_y))
            for i, debuff in enumerate(player.active_debuffs.keys()):
                debuff_text = self.font_small.render(debuff.value[:3].upper(), True, COLOR_RED)
                self.screen.blit(debuff_text, (next_x, debuff_y + 20 + i * 15))

        # Draw dead overlay
        if player.is_dead:
            dead_surface = pygame.Surface((board_width, board_height))
            dead_surface.fill((100, 50, 50))
            dead_surface.set_alpha(150)
            self.screen.blit(dead_surface, (board_x, board_y))

            dead_text = self.font_large.render("K.O.", True, COLOR_WHITE)
            dead_rect = dead_text.get_rect(center=(board_x + board_width // 2,
                                                    board_y + board_height // 2))
            self.screen.blit(dead_text, dead_rect)

    def _draw_mini_block(self, block: Block, x: int, y: int) -> None:
        """Draw a small preview of a block."""
        mini_size = 12
        # Use shape[rotation] to get the correct rotation state
        current_shape = block.shape[block.rotation]
        for row_idx, row in enumerate(current_shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, block.color,
                                    (x + col_idx * mini_size, y + row_idx * mini_size,
                                     mini_size - 1, mini_size - 1))

    def _draw_game_over(self) -> None:
        """Draw game over overlay."""
        overlay = pygame.Surface((self.BATTLE_WINDOW_WIDTH, self.BATTLE_WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # Winner announcement
        if self.winner == 1:
            winner_text = "PLAYER 1 WINS!"
            color = COLOR_GREEN
        elif self.winner == 2:
            winner_text = "PLAYER 2 WINS!"
            color = COLOR_BLUE
        else:
            winner_text = "IT'S A TIE!"
            color = COLOR_YELLOW

        text = self.font_large.render(winner_text, True, color)
        text_rect = text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)

        # Final scores
        score_text = f"P1: {self.player1.score}  vs  P2: {self.player2.score}"
        score_surface = self.font_medium.render(score_text, True, COLOR_WHITE)
        score_rect = score_surface.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 20))
        self.screen.blit(score_surface, score_rect)

        # Restart hint
        hint = self.font_small.render("Press R to restart, ESC to quit", True, COLOR_GRAY)
        hint_rect = hint.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 80))
        self.screen.blit(hint, hint_rect)

    def _draw_paused(self) -> None:
        """Draw pause overlay."""
        overlay = pygame.Surface((self.BATTLE_WINDOW_WIDTH, self.BATTLE_WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render("PAUSED", True, COLOR_WHITE)
        text_rect = text.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2))
        self.screen.blit(text, text_rect)

        hint = self.font_small.render("Press ESC to resume", True, COLOR_GRAY)
        hint_rect = hint.get_rect(center=(self.BATTLE_WINDOW_WIDTH // 2, self.BATTLE_WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(hint, hint_rect)

    def run(self) -> None:
        """Main game loop."""
        self.game_start_time = time.time()
        running = True

        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False

            self.handle_input()
            self.update(dt)
            self.render()

        pygame.quit()


def run_battle_mode():
    """Entry point for battle mode."""
    game = BattleGame()
    game.run()


if __name__ == "__main__":
    run_battle_mode()
