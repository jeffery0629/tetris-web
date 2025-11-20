# Claire's Tetris - Project Guidelines

## Project Overview
俄羅斯方塊遊戲，給女朋友玩的休閒遊戲專案。包含 3 種遊戲模式（Simple/Classic/Crazy）和特殊方塊系統。

## Tech Stack
- **Language**: Python 3.10+
- **Package Manager**: uv
- **Graphics**: Pygame 2.5.0+
- **Testing**: pytest 7.0+
- **Packaging**: PyInstaller 6.0+
- **Data Storage**: JSON (stdlib)

## Development Principles

### Code Style
- **Language**: 英文註解與文檔
- **Style Guide**: PEP 8
- **Architecture**: MVC pattern
  - Model: Game logic (board, blocks, scoring)
  - View: Rendering (Pygame)
  - Controller: Input handling

### File Organization
```
src/tetris/
├── main.py           # Entry point & game loop
├── game.py           # Game controller
├── board.py          # Board logic
├── tetromino.py      # 4-block shapes (7 types)
├── pentomino.py      # 5-block shapes (18 types)
├── tromino.py        # 3-block shapes (2 types)
├── powerup.py        # Special blocks system
├── modes.py          # Mode configurations
├── renderer.py       # Pygame rendering
├── effects.py        # Visual effects
├── save_manager.py   # JSON save/load
├── constants.py      # Game constants
└── utils.py          # Helper functions
```

### Testing Requirements
- **Coverage**: 80%+ for core logic
- **Test Types**:
  - Unit tests: board, blocks, collision, scoring
  - Integration tests: game flow, mode switching
  - Manual tests: gameplay balance, UX

### Git Workflow
- **Commit Message**: Conventional Commits (feat:, fix:, docs:, test:)
- **Branch Naming**: feature/*, bugfix/*, hotfix/*

## Audio & Assets
- **Audio**: Pygame built-in beep/simple sounds
- **Fonts**: System default (Arial or any available sans-serif)
- **Colors**: Defined in constants.py

## Game Modes Configuration

### Simple Mode
- Grid: 8×16
- Blocks: 2 trominoes (I3, L3)
- Power-ups: Enabled
- Score multiplier: ×0.5
- Speed: Slower progression

### Classic Mode
- Grid: 10×20
- Blocks: 7 tetrominoes (I, O, T, S, Z, J, L)
- Power-ups: **Disabled** (pure gameplay)
- Score multiplier: ×1.0
- Speed: Standard Tetris

### Crazy Mode
- Grid: 12×22
- Blocks: 18 pentominoes
- Power-ups: Enabled
- Score multiplier: ×2.0
- Speed: Faster progression
- Unlock: 50 lines in Classic Mode

## Power-Up System
- **Spawn Rate**: 5% (1 in 20 blocks)
- **Max Inventory**: 2 power-ups
- **Types**: Bomb, Rainbow, Time Freeze, Gravity Reverse, Line Eraser, Ghost Mode
- **Disabled in**: Classic Mode

## Constants to Define
```python
# Grid sizes
SIMPLE_GRID = (8, 16)
CLASSIC_GRID = (10, 20)
CRAZY_GRID = (12, 22)

# Timing
FPS = 60
INITIAL_FALL_SPEED = 1.0  # seconds per row
LOCK_DELAY = 0.5  # seconds

# Scoring
SCORE_MULTIPLIERS = {
    'simple': 0.5,
    'classic': 1.0,
    'crazy': 2.0
}

# Power-ups
POWERUP_SPAWN_RATE = 0.05
MAX_POWERUP_INVENTORY = 2
```

## Development Priorities

### Phase 1: MVP (Classic Mode Only) - 8-10 hours
1. Environment setup with uv
2. Basic game loop & rendering
3. Tetromino implementation (7 shapes)
4. Board logic & collision
5. Rotation with SRS
6. Line clearing & scoring
7. Game over detection

### Phase 2: Simple Mode - 2-3 hours
8. Tromino implementation
9. Smaller grid support
10. Mode selection screen

### Phase 3: Crazy Mode - 4-5 hours
11. Pentomino implementation (18 shapes)
12. Extended rotation system
13. Mode unlock system

### Phase 4: Power-Ups - 3-4 hours
14. Power-up block spawning
15. 6 power-up effects
16. Inventory system
17. Visual effects

### Phase 5: Polish - 2-3 hours
18. Save/load system
19. Audio integration
20. UI improvements
21. Testing & bug fixes

### Phase 6: Packaging - 1-2 hours
22. PyInstaller configuration
23. .exe testing
24. Final delivery

## Save File Structure
```json
{
  "version": "1.0",
  "high_scores": {
    "simple": 5000,
    "classic": 12500,
    "crazy": 0
  },
  "total_lines": {
    "simple": 120,
    "classic": 250,
    "crazy": 0
  },
  "total_playtime": {
    "simple": 3600,
    "classic": 7200,
    "crazy": 0
  },
  "unlocked_modes": ["simple", "classic"],
  "settings": {
    "volume": 0.7,
    "show_ghost": true
  }
}
```

## Important Notes
- **No placeholders**: Always write complete, working code
- **Test as you go**: Write tests alongside features
- **Performance**: Maintain 60 FPS with all effects
- **User-friendly**: Clear visual feedback for all actions
- **Fail gracefully**: Handle corrupted save files, missing assets

## Common Pitfalls to Avoid
- ❌ Hardcoding grid size (use mode config)
- ❌ Forgetting wall kicks in rotation
- ❌ Not testing pentomino rotations (18 shapes!)
- ❌ Power-up balance issues (test thoroughly)
- ❌ Save file corruption (validate JSON)
- ❌ Assets not bundled in .exe (test PyInstaller early)

## Success Criteria
- ✅ All 3 modes playable
- ✅ All 27 block types working (2+7+18)
- ✅ 6 power-ups functional
- ✅ Save/load persists across sessions
- ✅ .exe runs standalone on Windows
- ✅ No crashes during normal gameplay
- ✅ Girlfriend enjoys playing it! 💝
