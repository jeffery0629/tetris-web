"""Complete main entry point with mode selection and save system."""

import sys
import asyncio
import pygame
from .menu import ModeSelectionMenu
from .game import GameEnhanced
from .save_manager import SaveManager
from .constants import GameMode


async def main():
    """Run the complete game with mode selection."""
    # Initialize save manager
    save_manager = SaveManager()

    while True:
        # Show mode selection menu
        menu = ModeSelectionMenu(save_manager)
        selected_mode = await menu.run_async()

        if selected_mode is None:
            # User quit
            menu.quit()
            break

        # Handle Battle mode separately (desktop only for now)
        if selected_mode == GameMode.BATTLE:
            # Quit menu first, then run battle mode with its own window
            menu.quit()
            from .battle_game import BattleGame
            battle_game = BattleGame()
            battle_game.run()
            # Battle mode's run() already calls pygame.quit() at the end
            continue

        # Handle Online Battle mode (mobile-friendly version)
        if selected_mode == GameMode.ONLINE_BATTLE:
            menu.quit()
            from .mobile_online_battle import MobileOnlineBattleGame
            online_game = MobileOnlineBattleGame()
            # TODO: Add player name input in future
            player_name = "Player"
            await online_game.run_async(player_name)
            continue

        # For non-battle modes, quit menu before starting game
        menu.quit()

        # Run game with selected mode
        game = GameEnhanced(mode=selected_mode)
        game.high_score = save_manager.get_high_score(selected_mode.value)
        await game.run_async()

        # Save high score and stats
        if game.score > 0:
            save_manager.update_high_score(selected_mode.value, game.score)
            save_manager.add_lines(selected_mode.value, game.lines_cleared)

        # Check for mode unlocks
        newly_unlocked = save_manager.check_and_unlock_modes()
        if newly_unlocked:
            print(f"Unlocked modes: {', '.join(newly_unlocked)}")

        # Game ended, loop back to menu


if __name__ == "__main__":
    asyncio.run(main())
