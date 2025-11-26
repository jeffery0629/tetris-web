import asyncio
import pygame
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from tetris.online_battle import OnlineBattleGame

async def main():
    print("Starting Online Battle Mode...")
    game = OnlineBattleGame()
    await game.run_async()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Game stopped.")

