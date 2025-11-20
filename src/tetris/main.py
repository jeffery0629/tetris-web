"""Complete main entry point with mode selection and save system."""

import sys
from .menu import ModeSelectionMenu
from .game import GameEnhanced
from .save_manager import SaveManager


def main():
    """Run the complete game with mode selection."""
    # Initialize save manager
    save_manager = SaveManager()

    while True:
        # Show mode selection menu
        menu = ModeSelectionMenu(save_manager)
        selected_mode = menu.run()
        menu.quit()

        if selected_mode is None:
            # User quit
            break

        # Run game with selected mode
        game = GameEnhanced(mode=selected_mode)
        game.high_score = save_manager.get_high_score(selected_mode.value)
        game.run()

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
    main()
