"""Entry point for Claire's Tetris game."""

import asyncio

# Load environment variables BEFORE importing game modules
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    pass  # dotenv not available (Web version)

from src.tetris.main import main

if __name__ == "__main__":
    asyncio.run(main())
