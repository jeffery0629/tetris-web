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
├── game.py           # Game controller (single player)
├── battle_game.py    # Battle Mode controller (2-player)
├── board.py          # Board logic
├── tetromino.py      # 4-block shapes (7 types)
├── pentomino.py      # 5-block shapes (18 types)
├── tromino.py        # 3-block shapes (2 types)
├── powerup.py        # Special blocks system
├── modes.py          # Mode configurations
├── renderer.py       # Pygame rendering
├── effects.py        # Visual effects
├── save_manager.py   # JSON save/load
├── leaderboard_manager.py  # GitHub Gist leaderboard
├── text_input.py     # Player ID input widget
├── touch_controls.py # Mobile touch controls
├── constants.py      # Game constants
└── utils.py          # Helper functions

docs/
├── HOW_TO_PLAY.md           # Game rules
├── product_spec.md          # Product specification
├── PROGRESS.md              # Development history
├── LEADERBOARD_SETUP.md     # Leaderboard setup guide
├── SETUP_CHECKLIST.md       # Quick setup checklist
└── INTEGRATION_EXAMPLE.py   # Code integration example
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

---

## Web Version Deployment (Phase 7) - COMPLETED ✅

### Deployment Platform
- **Target**: GitHub Pages (https://jeffery0629.github.io/tetris-web)
- **Technology**: Pygbag (Pygame → WebAssembly)
- **Repository**: https://github.com/jeffery0629/tetris-web
- **Auto-deploy**: GitHub Actions on push to main branch

### Web Conversion Changes

#### 1. Async Support
- Converted all main game loops to async/await
- Added `asyncio.sleep(0)` in game loop for web compatibility
- Modified `main.py`, `game.py`, `menu.py` with `async def` and `await`

#### 2. Mobile Touch Controls (`touch_controls.py`)
- **Layout**:
  - Left/Right screen tap zones for horizontal movement
  - Bottom buttons: PWR (power-up), HLD (hold)
  - Right side buttons: DROP (hard drop), ROT (rotate) stacked vertically
  - Top-left: Pause button
- **Touch zones expanded**: From top (0px) to bottom buttons for maximum responsiveness
- **Priority**: Functional buttons > Movement zones > Pause button

#### 3. Visual Adjustments
- **Removed emoji/Chinese text**: Web fonts don't support, replaced with English labels
- **Classic Tetris block style**: 3D beveled blocks with light/dark edges
- **Cat icon**: Loaded from `images/cat.jpg` and displayed next to title
- **POWER-UPS panel**: Compact 250×120px with horizontal layout

#### 4. Game Over Screen Enhancement
- Dark overlay (alpha 220) for prominence
- Large modal (500×420px) with shadow
- Red "GAME OVER" text (font_large)
- Touch-friendly buttons: RESTART (200×70px) and MENU
- Shows Score + Lines + High Score notification

#### 5. Configuration (`pygbag.json`)
```json
{
  "width": 800,
  "height": 750,
  "title": "Claire's Tetris 💖",
  "orientation": "portrait",
  "icon": "favicon.png",
  "pygame": {
    "no_user_action": true
  },
  "renderer": "canvas"
}
```

#### 6. GitHub Actions Workflow
```yaml
- Clear Pygbag cache (rm -rf build/web-cache)
- Build: pygbag --ume_block 0 --build .
- Deploy to GitHub Pages automatically
```

### Critical Bug Fixes

#### Fix 1: Ghost Mode Out of Bounds
- **Problem**: Blocks could move outside screen boundaries
- **Root cause**: Ghost mode bypassed ALL position checks including bounds
- **Solution**:
  - Added `Board.is_within_bounds()` method
  - Ghost mode now checks boundaries, only ignores block collisions
  - `move_block()` and `rotate_block()` now validate bounds in ghost mode

#### Fix 2: Ghost Mode Can't Stop
- **Problem**: Blocks couldn't lock down after phasing through
- **Root cause**: `is_on_ground` forced to False during ghost mode
- **Solution**: Check bottom boundary even in ghost mode
  ```python
  if ghost_mode:
      self.is_on_ground = not self.board.is_within_bounds(test_block)
  ```

#### Fix 3: Smart Bomb Targeting
- **Problem**: Bomb cleared bottom-center (useless when blocks stack high)
- **User feedback**: "炸下面沒意義, 空白和方塊夾雜的部分才需要炸"
- **Solution**:
  - Added `Board.find_most_problematic_area()` method
  - Algorithm: `problem_score = filled × empty` (maximizes at 50/50 mix)
  - Targets chaotic mixed areas that create holes

#### Fix 4: Crazy Mode Unlock
- **Problem**: Hardcoded 50-line requirement in SaveManager
- **Solution**:
  - Changed default `unlocked_modes` to include "crazy"
  - Modified `check_and_unlock_modes()` to read `UNLOCK_REQUIREMENTS` dynamically
  - All modes now unlocked by default (UNLOCK_REQUIREMENTS = 0)

#### Fix 5: Touch Zone Expansion
- **User feedback**: "左右邊的觸控範圍不夠大"
- **Changes**:
  - Vertical: 70px → 0px (top), expanded to bottom buttons
  - Horizontal: Removed 10px safety margin
  - Button priority: Functional buttons > Movement zones > Pause

### File Organization
```
/
├── images/          # Cat icon, favicon
├── docs/            # Documentation (HOW_TO_PLAY, product_spec, PROGRESS)
├── src/tetris/      # Game source code
│   ├── touch_controls.py  # Mobile touch handling
│   └── ...
├── pygbag.json      # Pygbag configuration
├── favicon.png      # 64×64 PNG (converted from cat.jpg)
└── .github/workflows/deploy-pygbag.yml
```

### Known Issues & Solutions
- ✅ **READY TO START touch offset**: Fixed with `--ume_block 0` flag
- ✅ **Cat icon not displaying**: Converted to proper 64×64 PNG format
- ✅ **Emoji showing as squares**: Replaced all emoji with text labels
- ✅ **Black screen crash**: Fixed negative button height calculation
- ✅ **SaveManager cache**: Force rebuild with `rm -rf build/web-cache`

### Deployment Status
- **Current Version**: Live at https://jeffery0629.github.io/tetris-web
- **Auto-deploy**: Enabled on main branch push
- **Build time**: ~3-5 minutes via GitHub Actions
- **Browser compatibility**: Chrome, Safari, Edge (requires iOS 15+ for Safari)

### Testing Checklist
- ✅ All 3 modes accessible (Casual, Classic, Crazy)
- ✅ Touch controls responsive on mobile
- ✅ Cat icon displays in title
- ✅ Game Over screen shows with restart button
- ✅ Bomb targets problematic mixed areas
- ✅ Ghost mode respects boundaries
- ✅ Left/right touch zones maximized
- ✅ Classic block style renders correctly

---

## Secure Leaderboard System (Phase 8) - COMPLETED ✅

### Architecture Overview
```
Web Game → Cloudflare Worker (Proxy) → GitHub Gist (Database)
                ↑ Token stored securely here
```

**Security Benefits**:
- ✅ GitHub Token never exposed to players
- ✅ Built-in anti-cheat (score limits)
- ✅ Free with no server maintenance
- ✅ Global CDN acceleration

### Implementation Details

#### 1. Cloudflare Worker Proxy
- **Worker URL**: `https://tetris-leaderboard.jefferysung860629.workers.dev`
- **Endpoints**:
  - `GET /leaderboard` - Fetch all scores
  - `POST /submit` - Submit new score
- **Environment Variables** (stored as Secrets):
  - `GIST_ID`: GitHub Gist ID for data storage
  - `GITHUB_TOKEN`: Token with `gist` scope only
- **Anti-cheat Score Limits**:
  - Casual: 50,000
  - Classic: 100,000
  - Crazy: 200,000
- **CORS**: Only allows `jeffery0629.github.io` and `localhost:8000`

#### 2. Web Version HTTP Requests
- **Problem**: Pygbag/WebAssembly doesn't support `requests` library or async `fetch` with `await`
- **Solution**: Synchronous `XMLHttpRequest` via `window.eval()`
```python
# Both GET and POST use this pattern
js_code = f'''
(function() {{
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "{url}", false);  // false = synchronous
    xhr.setRequestHeader("Content-Type", "application/json");
    try {{
        xhr.send('{body}');
        return JSON.stringify({{ok: xhr.status === 200, status: xhr.status, text: xhr.responseText}});
    }} catch (e) {{
        return JSON.stringify({{ok: false, status: 0, text: e.toString()}});
    }}
}})()
'''
result_str = window.eval(js_code)
```

#### 3. Desktop Version
- Uses standard `requests` library
- Reads `WORKER_URL` from `.env` file or uses default

### Files Modified/Created
- `src/tetris/leaderboard_manager.py` - Refactored to use Worker API
- `src/tetris/game.py` - Added `SUBMITTING_SCORE` state for async handling
- `src/tetris/constants.py` - Added `SUBMITTING_SCORE` enum
- `docs/cloudflare-worker.js` - Worker source code reference
- `docs/LEADERBOARD_SETUP.md` - Updated setup guide
- `.github/workflows/deploy-pygbag.yml` - Removed token exposure

### Critical Bug Fixes

#### Fix 1: Token Exposure in Web Build
- **Problem**: GitHub Token was being injected into `web_config.py` during GitHub Actions build
- **Solution**: Removed token generation, use Cloudflare Worker as secure proxy

#### Fix 2: Async Fetch Hanging (30+ seconds)
- **Problem**: `await result_promise` from `window.eval()` async IIFE didn't work in Pygbag
- **Solution**: Changed to synchronous `XMLHttpRequest` with `xhr.open(method, url, false)`

### Data Storage (GitHub Gist)
```json
{
  "casual": [
    {"player_id": "Claire", "score": 240604, "lines": 50, "level": 5, ...}
  ],
  "classic": [],
  "crazy": []
}
```

### Testing Checklist
- ✅ Score submission works without hanging
- ✅ Leaderboard displays correctly
- ✅ Player's own scores highlighted in orange
- ✅ Token not exposed in browser DevTools
- ✅ Anti-cheat rejects invalid scores
- ✅ Desktop version works with `.env` config

---

## Battle Mode (Phase 9) - COMPLETED ✅

### Overview
2-player local multiplayer mode with garbage line mechanics and 10-minute timer.

### Game Rules
- **Players**: 2 (Player 1 on left, Player 2 on right)
- **Timer**: 10 minutes countdown
- **Win Condition**: Opponent tops out OR higher score when timer ends
- **Grid**: 10×20 (Classic Tetris standard)

### Garbage Line Mechanics
- Clearing 2+ lines sends garbage to opponent
- Garbage lines appear at bottom with one random gap
- Sent lines: `lines_cleared - 1` (2 lines = 1 garbage, 4 lines = 3 garbage)

### Controls
| Action | Player 1 | Player 2 |
|--------|----------|----------|
| Move Left | A | ← |
| Move Right | D | → |
| Soft Drop | S | ↓ |
| Hard Drop | W | ↑ |
| Rotate CW | E | / |
| Rotate CCW | Q | . |
| Hold | Tab | Shift |
| Power-up | Space | Enter |

### Implementation Details
- **Window Size**: 1000×750 (wider for two boards)
- **File**: `src/tetris/battle_game.py`
- **Entry Point**: Selected from mode menu, handled in `main.py`

### Bug Fixes

#### Fix 1: Collision Detection Method Name
- **Problem**: `AttributeError: 'Board' object has no attribute 'check_collision'`
- **Root Cause**: Battle mode used `check_collision()` but Board class uses `is_valid_position()`
- **Solution**: Replaced all `check_collision()` calls with `is_valid_position()` and inverted logic
  - `check_collision()` returns True when collision exists
  - `is_valid_position()` returns True when NO collision (valid move)

#### Fix 2: Block Shape Structure Misuse
- **Problem**: Blocks rendered incorrectly, rotation destroyed block shapes
- **Root Cause**: `Block.shape` is a list of 4 rotation states (2D matrices), not a single 2D matrix
- **Solution**:
  - `_spawn_block()`: Use `shape[rotation][0]` for width calculation
  - `_rotate_block()`: Use `Block.rotate_cw()/rotate_ccw()` API instead of manual rotation
  - `_draw_player()`: Use `Block.get_cells()` for correct cell positions
  - `_draw_mini_block()`: Use `shape[rotation]` for preview rendering

#### Fix 3: Floating Block Bug
- **Problem**: Blocks could float in air after horizontal movement while on ground
- **Root Cause**: Lock delay didn't re-check ground state after horizontal move
- **Solution**: After any horizontal movement in `_move_block()`, check if space exists below
  ```python
  if dx != 0:
      player.current_block.y += 1
      if player.board.is_valid_position(player.current_block):
          player.is_on_ground = False
          player.lock_timer = 0
      player.current_block.y -= 1
  ```

#### Fix 4: Ink Overlay Too Light
- **Problem**: User feedback "墨汁感覺不夠黑" (ink not dark enough)
- **Solution**: Enhanced ink effect
  - Color: `(20, 20, 30)` → `(5, 5, 10)` (darker)
  - Alpha: `220` → `245` (more opaque)
  - Coverage: 50% → 67% (covers more of screen)

#### Fix 5: Pygame Initialization Order
- **Problem**: Battle Mode entry caused lag/freeze
- **Root Cause**: Menu's pygame instance conflicted with Battle Mode's initialization
- **Solution**: Call `menu.quit()` before creating `BattleGame()` instance

---

## Dynamic UI Layout Fix - COMPLETED ✅

### Problem
Crazy Mode (12×22 grid) caused UI overlap with game board on desktop/web version.

### Solution: Dynamic Cell Size & Panel Positioning

#### 1. Dynamic Cell Size (`renderer.py`)
```python
# Calculate based on board height
max_board_height = WINDOW_HEIGHT - 130  # Leave space for title/buttons
ideal_cell_size = max_board_height // board.height
cell_size = min(30, max(24, ideal_cell_size))
```
- Simple Mode (8×16): Uses 30px cells
- Classic Mode (10×20): Uses 30px cells
- Crazy Mode (12×22): Uses ~28px cells

#### 2. Dynamic Panel Positioning (`game.py` + `renderer.py`)
```python
# Calculate where board ends
board_end_x = offset_x + board.width * cell_size + 10

# Position UI panels relative to board end
def draw_ui(self, ..., board_end_x: int = 380):
    ui_x = board_end_x + 10  # 10px gap after board
```

#### 3. Reduced Touch Button Sizes (`touch_controls.py`)
```python
# Before → After
button_height = 78 → 55
button_margin = 12 → 8
button_gap = 12 → 8
hold_height = 70 → 50
```

### Files Modified
- `src/tetris/renderer.py` - Added `cell_size` property, dynamic positioning
- `src/tetris/game.py` - Calculate `board_end_x` based on actual board width
- `src/tetris/touch_controls.py` - Reduced button dimensions

### Result
- All 3 modes now display correctly without overlap
- UI panels always positioned to the right of the game board
- Touch buttons fit better on mobile screens
