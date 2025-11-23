"""
Example: How to integrate leaderboard into game.py

This file shows the key changes needed to add leaderboard functionality.
DO NOT run this file directly - it's just a reference!
"""

# ============================================
# 1. Add imports at the top of game.py
# ============================================
from .text_input import TextInput
from .leaderboard_manager import GistLeaderboardManager, LeaderboardEntry

# ============================================
# 2. In GameEnhanced.__init__(), add:
# ============================================
def __init__(self, mode: GameMode = GameMode.CLASSIC):
    # ... existing init code ...

    # Leaderboard system
    self.leaderboard_manager = GistLeaderboardManager()
    self.text_input = TextInput(
        x=300, y=400, width=200, height=40,
        font=self.renderer.font_small, max_length=12
    )
    self.leaderboard_entries = []  # Current leaderboard data
    self.current_player_id = ""  # Last entered player ID

    # Try to load last used player ID from save
    # (Optional: you can save it in SaveManager)

# ============================================
# 3. In lock_block(), change game over logic:
# ============================================
def lock_block(self) -> None:
    # ... existing lock block code ...

    # Check game over
    if self.board.is_game_over(spawn_y=1):
        # Change this line:
        # self.state = GameState.GAME_OVER

        # To:
        if self.leaderboard_manager.online_mode:
            self.state = GameState.GAME_OVER_INPUT  # Show input screen
            self.text_input.active = True  # Auto-activate input
        else:
            self.state = GameState.GAME_OVER  # Offline mode, skip input

        if self.score > self.high_score:
            self.high_score = self.score
    else:
        self.spawn_new_block()

# ============================================
# 4. In handle_event(), add leaderboard handling:
# ============================================
def handle_event(self, event: pygame.event.Event) -> None:
    """Handle pygame events (keyboard + touch)."""

    # NEW: Handle text input during game over
    if self.state == GameState.GAME_OVER_INPUT:
        # Let text input handle keyboard events
        modified = self.text_input.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            # User pressed Enter - submit score
            player_id = self.text_input.get_text()
            if player_id:
                self._submit_score_to_leaderboard(player_id)
            else:
                # Skip if no ID entered
                self.state = GameState.GAME_OVER

        return  # Don't process other events during input

    # NEW: Handle leaderboard screen
    if self.state == GameState.LEADERBOARD:
        if event.type == pygame.MOUSEBUTTONDOWN:
            action = self.renderer.get_leaderboard_button_clicked(event.pos)
            if action == "close":
                self.state = GameState.GAME_OVER
        return

    # ... existing event handling code (touch controls, keyboard, etc.) ...

# ============================================
# 5. Add new helper method:
# ============================================
def _submit_score_to_leaderboard(self, player_id: str) -> None:
    """Submit score to leaderboard and show rankings.

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

    # Submit to cloud
    success, message = self.leaderboard_manager.submit_score(entry)

    if success:
        self.show_notification(message)
    else:
        self.show_notification(f"Upload failed: {message}")

    # Fetch and show leaderboard (even if upload failed)
    self.leaderboard_entries = self.leaderboard_manager.get_leaderboard(
        mode=self.mode.value,
        limit=10
    )

    # Switch to leaderboard view
    self.state = GameState.LEADERBOARD

# ============================================
# 6. In update(), add text input update:
# ============================================
def update(self, dt: float) -> None:
    """Update game state."""
    # ... existing update code ...

    # NEW: Update text input cursor animation
    if self.state == GameState.GAME_OVER_INPUT:
        self.text_input.update(dt)

# ============================================
# 7. In render(), add new screens:
# ============================================
def render(self) -> None:
    """Render current game state."""
    self.renderer.clear_screen()

    # ... existing rendering code (board, blocks, UI, etc.) ...

    # Draw overlays
    if self.state == GameState.PAUSED:
        self.renderer.draw_pause_screen()

    # NEW: Game over with input
    elif self.state == GameState.GAME_OVER_INPUT:
        self.renderer.draw_game_over_screen(
            self.score, self.lines_cleared, self.high_score
        )
        # Draw input prompt overlay
        self._draw_input_overlay()

    # NEW: Leaderboard screen
    elif self.state == GameState.LEADERBOARD:
        self.renderer.draw_leaderboard_screen(
            mode=self.mode.value,
            entries=self.leaderboard_entries,
            player_id=self.current_player_id
        )

    # Original game over (offline mode)
    elif self.state == GameState.GAME_OVER:
        self.renderer.draw_game_over_screen(
            self.score, self.lines_cleared, self.high_score
        )

    self.renderer.update_display()

# ============================================
# 8. Add input overlay drawing method:
# ============================================
def _draw_input_overlay(self) -> None:
    """Draw player ID input overlay on top of game over screen."""
    # Small overlay panel
    panel_width = 400
    panel_height = 200
    panel_x = (self.renderer.screen.get_width() - panel_width) // 2
    panel_y = 250

    # Semi-transparent background
    overlay = pygame.Surface((panel_width, panel_height))
    overlay.set_alpha(240)
    overlay.fill((255, 255, 255))
    self.renderer.screen.blit(overlay, (panel_x, panel_y))

    # Border
    import pygame
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

    # Text input box
    self.text_input.rect.centerx = panel_x + panel_width // 2
    self.text_input.rect.y = panel_y + 80
    self.text_input.draw(self.renderer.screen, placeholder="Your Name")

    # Hint text
    self.renderer.draw_text(
        "Press ENTER to submit",
        panel_x + panel_width // 2,
        panel_y + 150,
        self.renderer.font_small,
        (150, 150, 150),
        center=True
    )

# ============================================
# 9. In restart(), clear leaderboard state:
# ============================================
def restart(self) -> None:
    """Restart the game."""
    # ... existing restart code ...

    # NEW: Clear leaderboard state
    self.text_input.clear()
    self.leaderboard_entries = []
    # Don't clear current_player_id - keep it for next game

# ============================================
# SUMMARY OF CHANGES:
# ============================================
"""
Files to modify:
1. game.py - Add all the code above
2. constants.py - Already updated (added new GameStates)
3. renderer.py - Already updated (draw_leaderboard_screen added)

New files created:
1. leaderboard_manager.py - Backend logic
2. text_input.py - Input widget
3. LEADERBOARD_SETUP.md - Setup guide
4. INTEGRATION_EXAMPLE.py - This file

Setup required:
1. Create GitHub Gist
2. Create GitHub Token
3. Add to .env file:
   GIST_ID=your_gist_id
   GITHUB_TOKEN=your_token
4. Install: uv pip install requests

Test flow:
1. Play game → Game Over
2. If online: Input screen appears
3. Type player ID → Press Enter
4. Score uploads → Leaderboard shows
5. Click CLOSE → Back to game over screen
6. Click RESTART or MENU
"""
