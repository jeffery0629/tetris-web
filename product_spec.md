# Tetris Game - Product Specification

## 1. Project Overview

### 1.1 Project Name
**Claire's Tetris** - A classic Tetris game implementation

### 1.2 Target Audience
- Primary user: Girlfriend (casual gaming)
- Platform: Windows PC
- Skill level: Beginner to intermediate players

### 1.3 Project Goals
- Create a fully functional Tetris game with multiple game modes
- Provide smooth gameplay experience with exciting power-ups
- Package as standalone executable (.exe)
- No installation required for end user
- Offer variety and replayability through different challenges

---

## 2. Technical Stack

### 2.1 Core Technologies
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10+ | Core implementation |
| Graphics Library | Pygame | 2.5.0+ | Rendering & audio |
| Package Manager | uv | Latest | Fast dependency management |
| Packaging Tool | PyInstaller | 6.0+ | .exe bundling |
| Testing Framework | pytest | 7.0+ | Unit & integration tests |
| Data Serialization | JSON (stdlib) | - | Save game state & settings |

### 2.2 Development Environment
- **IDE**: VS Code with Python extensions
- **Version Control**: Git
- **Virtual Environment**: `.venv` managed by uv
- **Dependency Management**: `pyproject.toml` + `requirements.txt`

---

## 3. Core Features

### 3.1 Game Modes (Priority 1)

#### 3.1.1 Classic Mode (MVP)
**Standard Tetris with 7 tetrominoes**

| Shape | Color | Composition | Rotation States |
|-------|-------|-------------|-----------------|
| I | Cyan | 4 blocks in line | 2 states |
| O | Yellow | 2x2 square | 1 state |
| T | Purple | T-shape | 4 states |
| S | Green | S-shape | 2 states |
| Z | Red | Z-shape | 2 states |
| J | Blue | J-shape | 4 states |
| L | Orange | L-shape | 4 states |

- **Rotation System**: Super Rotation System (SRS) with wall kicks
- **Grid**: 10 columns × 20 rows
- **Goal**: Survive as long as possible, achieve high score

#### 3.1.2 Crazy Mode (Priority 1)
**Pentominoes - 5-block shapes for advanced players**

Uses 18 different pentomino shapes (F, I, L, N, P, T, U, V, W, X, Y, Z + 6 mirrored variants)

| Category | Count | Example Shapes |
|----------|-------|----------------|
| Standard Pentominoes | 12 | F, I, L, N, P, T, U, V, W, X, Y, Z |
| Mirrored Variants | 6 | F', L', N', P', Y', Z' |

- **Rotation System**: Extended SRS for 5-block shapes
- **Grid**: 12 columns × 22 rows (larger for complexity)
- **Difficulty**: Higher - more complex shapes, faster progression
- **Unlock**: Available after clearing 50 lines in Classic Mode

#### 3.1.3 Simple Mode (Priority 1)
**Trominoes - 3-block shapes for beginners**

| Shape | Color | Composition | Rotation States |
|-------|-------|-------------|-----------------|
| I (3-line) | Light Blue | ■■■ | 2 states |
| L (3-L) | Orange | ■■<br>■ | 4 states |

- **Rotation System**: Simplified rotation
- **Grid**: 8 columns × 16 rows (smaller, easier)
- **Difficulty**: Lower - slower fall speed, simpler shapes
- **Purpose**: Tutorial mode for new players

### 3.2 Game Mechanics (MVP - Must Have)

#### 3.2.1 Game Board
- **Grid Size**: Varies by mode (see section 3.1)
- **Visible Area**: Full grid visible + 2 rows buffer above
- **Spawn Position**: Top-center
- **Border**: Clear visual boundary with shadow effect

#### 3.2.2 Controls
| Action | Key | Description |
|--------|-----|-------------|
| Move Left | ← (Left Arrow) | Move block one cell left |
| Move Right | → (Right Arrow) | Move block one cell right |
| Soft Drop | ↓ (Down Arrow) | Accelerate downward movement |
| Hard Drop | Space | Instantly drop to bottom |
| Rotate CW | ↑ (Up Arrow) | Rotate 90° clockwise |
| Rotate CCW | Z | Rotate 90° counter-clockwise |
| Pause | P / ESC | Pause/Resume game |
| Restart | R | Restart game (on game over) |
| Switch Mode | M | Open mode selection (on start screen) |
| Use Power-Up | E | Activate collected power-up |

#### 3.2.3 Game Logic
- **Line Clear**: Remove full rows and shift above rows down
- **Gravity**: Blocks fall automatically at increasing speeds
- **Lock Delay**: 0.5 second delay before block locks on landing
- **Collision Detection**: Prevent blocks from overlapping or going out of bounds
- **Game Over Condition**: New block cannot spawn (stack reaches top)

#### 3.2.4 Scoring System
| Action | Points |
|--------|--------|
| Single Line | 100 |
| Double Lines | 300 |
| Triple Lines | 500 |
| Tetris (4 Lines) | 800 |
| Soft Drop | 1 per cell |
| Hard Drop | 2 per cell |

- **Level System**: Level increases every 10 lines cleared
- **Speed Increase**: Fall speed increases by 10% per level
- **Mode Multipliers**:
  - Simple Mode: ×0.5 score
  - Classic Mode: ×1.0 score
  - Crazy Mode: ×2.0 score

### 3.3 Special Blocks System (Priority 2)

#### 3.3.1 Power-Up Blocks
**Rare special blocks that spawn randomly (5% chance)**

| Power-Up | Icon | Effect | Duration |
|----------|------|--------|----------|
| **Bomb Block** | 💣 | Clears 3×3 area around landing point | Instant |
| **Rainbow Block** | 🌈 | Acts as wildcard, clears any adjacent line | Instant |
| **Time Freeze** | ⏸️ | Pauses falling for 5 seconds | 5 sec |
| **Gravity Reverse** | 🔄 | Blocks fall upward temporarily | 8 sec |
| **Line Eraser** | ⚡ | Clears bottom 2 rows | Instant |
| **Ghost Mode** | 👻 | Next 3 blocks can overlap existing blocks | 3 blocks |

#### 3.3.2 Power-Up Mechanics
- **Spawn Rate**: 1 in 20 blocks (5%)
- **Visibility**: Glowing border with icon overlay
- **Collection**: Automatic on placement
- **Storage**: Hold up to 2 power-ups in inventory
- **Activation**: Press **E** to use oldest power-up
- **Visual Feedback**: Screen flash + particle effect on activation

#### 3.3.3 Power-Up Balancing
- Power-ups **disabled** in Classic Mode (pure gameplay)
- Power-ups **enabled** in Simple & Crazy modes
- No power-ups in last 10 seconds of timed modes

### 3.4 User Interface (Enhanced)

#### 3.4.1 Game Screen Layout
```
┌───────────────────────────────────────────┐
│  CLAIRE'S TETRIS       MODE: Classic      │
├──────────────┬────────────────────────────┤
│              │  SCORE: 0   HIGH: 12500    │
│              │  LEVEL: 1   LINES: 0       │
│              │                            │
│              │  NEXT:                     │
│  Game Board  │  ┌────┐                    │
│  (size vary) │  │    │                    │
│              │  └────┘                    │
│              │                            │
│              │  HOLD:                     │
│              │  ┌────┐                    │
│              │  │    │                    │
│              │  └────┘                    │
│              │                            │
│              │  POWER-UPS:                │
│              │  [💣] [⏸️]                 │
│              │  (press E to use)          │
└──────────────┴────────────────────────────┘
```

#### 3.4.2 Screen States
1. **Start Screen**
   - Animated game title
   - Mode selection menu:
     - **[1] Simple Mode** - Easy (Unlocked)
     - **[2] Classic Mode** - Normal (Unlocked)
     - **[3] Crazy Mode** - Hard (🔒 Unlock: 50 lines)
   - High scores for each mode
   - "Press 1-3 to Select Mode"
   - Controls reference (toggle with F1)

2. **Playing Screen**
   - Active game board with grid
   - Current falling block + ghost piece
   - Score/Level/Lines/High Score display
   - Current mode indicator
   - Next block preview
   - Hold block area
   - Power-up inventory (if enabled)
   - Active effects timer (if any)

3. **Paused Screen**
   - Semi-transparent overlay
   - "PAUSED" text
   - Current stats visible but dimmed
   - "Press P to Resume"
   - "Press M to Quit to Menu"

4. **Game Over Screen**
   - "GAME OVER" with animation
   - Final score & lines cleared
   - High score comparison (New Record!)
   - Statistics breakdown
   - "Press R to Restart Same Mode"
   - "Press M to Mode Selection"
   - "Press ESC to Quit"

5. **Mode Unlock Screen**
   - "NEW MODE UNLOCKED!" celebration
   - Mode description and preview
   - "Press SPACE to Try Now"

---

## 4. Advanced Features (Nice to Have)

### 4.1 Hold Function
- Press **C** to hold current block
- Swap with held block
- Can only hold once per turn

### 4.2 Ghost Piece
- Semi-transparent preview showing where block will land
- Same shape as current block

### 4.3 Visual Effects
- Line clear animation (flash effect)
- Block lock animation
- Background grid pattern

### 4.4 Audio (Optional)
- Background music (loop)
- Sound effects:
  - Block rotation
  - Block landing
  - Line clear
  - Level up
  - Game over

### 4.5 Persistent Storage (Enhanced)
- **Save File Format**: JSON (`tetris_save.json`)
- **Stored Data**:
  - High scores for each mode (Simple/Classic/Crazy)
  - Total lines cleared per mode
  - Total playtime per mode
  - Unlocked modes
  - Game settings (volume, controls)
- **Auto-save**: After every game over
- **Cloud Sync**: Not implemented (local only)

---

## 5. Technical Requirements

### 5.1 Performance
- **Target FPS**: 60 FPS
- **Window Size**: 800×600 pixels (scalable)
- **Memory Usage**: < 100 MB
- **Startup Time**: < 2 seconds

### 5.2 Compatibility
- **OS**: Windows 10/11 (64-bit)
- **No dependencies**: Standalone .exe file
- **File Size**: < 50 MB (packaged)

### 5.3 Code Quality
- **Test Coverage**: 80%+ for core game logic
- **Code Style**: PEP 8 compliant
- **Documentation**: English comments in code
- **Architecture**: MVC pattern
  - Model: Game state and logic
  - View: Pygame rendering
  - Controller: Input handling

---

## 6. Project Structure

```
claire/
├── .venv/                      # Virtual environment (uv managed)
├── .gitignore                  # Git ignore file
├── pyproject.toml              # Project configuration
├── requirements.txt            # Locked dependencies
├── README.md                   # Project documentation
├── product_spec.md             # This file
│
├── src/
│   └── tetris/
│       ├── __init__.py
│       ├── main.py             # Entry point
│       ├── game.py             # Game controller
│       ├── board.py            # Game board logic
│       ├── tetromino.py        # Block definitions (tetrominoes)
│       ├── pentomino.py        # 5-block shapes for Crazy mode
│       ├── tromino.py          # 3-block shapes for Simple mode
│       ├── powerup.py          # Special blocks system
│       ├── modes.py            # Game mode configurations
│       ├── renderer.py         # Pygame rendering
│       ├── effects.py          # Visual effects & animations
│       ├── constants.py        # Game constants
│       ├── save_manager.py     # Save/load high scores
│       └── utils.py            # Helper functions
│
├── assets/                     # Game assets
│   ├── fonts/                  # TTF fonts
│   ├── sounds/                 # Audio files (optional)
│   └── images/                 # Sprites (optional)
│
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── test_board.py
│   ├── test_tetromino.py
│   └── test_game.py
│
└── build/                      # PyInstaller output
    └── tetris.exe              # Final executable
```

---

## 7. Development Phases

### Phase 1: Setup (1-2 hours)
- [x] Environment setup with uv
- [x] Install pygame, pytest, pyinstaller
- [x] Create project structure
- [x] Initialize git repository

### Phase 2: Core Logic (6-8 hours)
- [ ] Implement tetromino classes (7 shapes)
- [ ] Implement tromino classes (2 shapes) - Simple mode
- [ ] Implement pentomino classes (18 shapes) - Crazy mode
- [ ] Implement game board (grid system with flexible sizing)
- [ ] Movement and rotation logic with SRS
- [ ] Collision detection
- [ ] Line clear mechanism
- [ ] Scoring system with mode multipliers
- [ ] Mode configuration system

### Phase 3: Rendering (4-5 hours)
- [ ] Basic pygame window with adaptive sizing
- [ ] Draw game board and grid (flexible dimensions)
- [ ] Draw blocks with colors (all 3 shape types)
- [ ] Draw UI elements (score, level, lines, mode, high score)
- [ ] Next block preview
- [ ] Power-up inventory display
- [ ] Mode selection screen
- [ ] Game state screens with animations

### Phase 4: Game Flow (2-3 hours)
- [ ] Start screen
- [ ] Game loop with FPS control
- [ ] Pause/resume functionality
- [ ] Game over detection and screen
- [ ] Restart mechanism

### Phase 5: Polish (2-3 hours)
- [ ] Hold function
- [ ] Ghost piece
- [ ] Visual effects (animations)
- [ ] Audio integration (optional)
- [ ] High score persistence

### Phase 6: Testing & Packaging (1-2 hours)
- [ ] Unit tests for core logic
- [ ] Manual gameplay testing
- [ ] Balance adjustments
- [ ] PyInstaller configuration
- [ ] Build .exe and test on clean system

**Total Estimated Time**: 13-20 hours

---

## 8. Testing Strategy

### 8.1 Unit Tests
- **Board Logic**: Grid operations, line clearing
- **Tetromino Logic**: Rotation matrices, collision detection
- **Scoring System**: Point calculation accuracy

### 8.2 Integration Tests
- **Game Flow**: Start → Play → Game Over → Restart
- **Input Handling**: Keyboard events processing

### 8.3 Manual Testing Checklist
- [ ] All 7 blocks spawn correctly
- [ ] Rotation works for all shapes
- [ ] Collision detection prevents invalid moves
- [ ] Lines clear properly
- [ ] Score increments correctly
- [ ] Game over triggers when appropriate
- [ ] Pause/resume works
- [ ] .exe runs on different Windows machines

---

## 9. Packaging & Deployment

### 9.1 PyInstaller Configuration
```bash
# Build command
pyinstaller --onefile --windowed \
  --name "Tetris" \
  --icon assets/icon.ico \
  --add-data "assets;assets" \
  src/tetris/main.py
```

### 9.2 Build Output
- **Single File**: `tetris.exe` (one-file bundle)
- **No Console**: Windowed mode (no terminal)
- **Includes Assets**: Fonts and sounds embedded

### 9.3 Delivery
- Provide `.exe` file directly to user
- No installation required
- Double-click to run

---

## 10. Future Enhancements (Out of Scope)

### 10.1 Multiplayer
- Local 2-player split screen
- Network multiplayer

### 10.2 Game Modes
- Marathon mode (endless)
- Sprint mode (40 lines race)
- Ultra mode (2-minute time attack)

### 10.3 Customization
- Custom color themes
- Adjustable grid size
- Custom key bindings

### 10.4 Advanced Mechanics
- T-spin detection and bonus scoring
- Combo system
- Back-to-back Tetris bonus

---

## 11. Success Criteria

### 11.1 Functional Requirements Met
- ✅ All 7 tetrominoes implemented
- ✅ Smooth rotation and movement
- ✅ Accurate collision detection
- ✅ Line clearing works correctly
- ✅ Game over detection functional
- ✅ Scoring system accurate

### 11.2 User Experience
- ✅ Responsive controls (no input lag)
- ✅ Clear visual feedback
- ✅ Intuitive UI
- ✅ Stable performance (60 FPS)

### 11.3 Deliverables
- ✅ Working `.exe` file
- ✅ Runs without dependencies
- ✅ File size < 50 MB
- ✅ No crashes during normal gameplay

---

## 12. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PyInstaller compatibility issues | Medium | High | Test early, use proven config |
| Performance degradation | Low | Medium | Profile code, optimize rendering |
| Rotation collision bugs | Medium | High | Thorough unit testing |
| User finds controls confusing | Low | Medium | Add in-game help screen |

---

## 13. References

### 13.1 Tetris Guidelines
- [Tetris Wiki](https://tetris.wiki) - Official mechanics reference
- [Pygame Documentation](https://www.pygame.org/docs/) - Graphics library docs

### 13.2 Rotation System
- Using **Super Rotation System (SRS)** - Modern Tetris standard
- Includes wall kicks for edge cases

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Author**: Claude Code Assistant
**Project Code**: claire-tetris
