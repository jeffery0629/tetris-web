# Online Battle Mode - Architecture & Development Plan

## Overview
線上對戰模式，讓兩位玩家透過網路進行即時俄羅斯方塊對戰。

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Pages                              │
│                   (Static Game Frontend)                         │
│                                                                  │
│   ┌──────────────┐                      ┌──────────────┐        │
│   │   Player A   │                      │   Player B   │        │
│   │  (Pygbag)    │                      │  (Pygbag)    │        │
│   └──────┬───────┘                      └──────┬───────┘        │
└──────────┼──────────────────────────────────────┼───────────────┘
           │ WebSocket                   WebSocket │
           │                                       │
           ▼                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cloudflare Worker + Durable Objects                 │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Worker (Entry)                        │   │
│   │  - Handle WebSocket upgrade                              │   │
│   │  - Route to GameRoom Durable Object                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              GameRoom (Durable Object)                   │   │
│   │                                                          │   │
│   │  - Matchmaking queue                                     │   │
│   │  - WebSocket session management                          │   │
│   │  - Message relay between players                         │   │
│   │  - Game timer synchronization                            │   │
│   │  - Disconnect detection                                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Message Protocol

### Client → Server

```json
// Join matchmaking queue
{"type": "JOIN", "player_name": "Claire"}

// Game state update (sent every 3 frames)
{
  "type": "STATE",
  "grid": [[0, [255,0,0], ...], ...],  // 10x20 grid, 0=empty, [r,g,b]=filled
  "score": 1500,
  "lines": 12,
  "piece": {
    "x": 4,
    "y": 2,
    "rotation": 0,
    "color": [0, 255, 255]
  }
}

// Send garbage lines to opponent
{"type": "GARBAGE", "lines": 2}

// Player action (for input sync, optional)
{"type": "ACTION", "action": "HARD_DROP"}

// Player topped out
{"type": "GAME_OVER"}
```

### Server → Client

```json
// Waiting for opponent
{"type": "WAITING"}

// Match found
{
  "type": "MATCH_START",
  "game_id": "abc123",
  "role": 1,  // 1=left, 2=right
  "opponent_name": "Jeffery",
  "server_time": 1700000000000
}

// Relay opponent state
{
  "type": "OPPONENT_STATE",
  "grid": [...],
  "score": 1200,
  "lines": 10,
  "piece": {...}
}

// Receive garbage from opponent
{"type": "GARBAGE", "lines": 2}

// Opponent disconnected
{"type": "OPPONENT_DISCONNECTED"}

// Game time sync (every 5 seconds)
{"type": "TIME_SYNC", "remaining": 540000}  // ms

// Game ended
{
  "type": "GAME_END",
  "reason": "TIMEOUT" | "OPPONENT_TOPPED_OUT" | "OPPONENT_DISCONNECTED",
  "winner": 1 | 2 | 0,  // 0=draw
  "final_scores": {"player1": 15000, "player2": 12000}
}
```

## File Structure

```
src/tetris/
├── online_battle.py      # Online game logic (inherits BattleGame)
├── network_manager.py    # WebSocket client for Pygbag
└── ...

docs/
├── ONLINE_BATTLE.md      # This file
└── cloudflare-worker-online.js  # Worker source code

server_simple.py          # Local testing server (development only)
run_online.py             # Local testing entry point
```

## Development Phases

### Phase 1: Core Infrastructure ✅
- [x] Create Cloudflare Worker with Durable Objects
- [x] Implement matchmaking queue
- [x] Implement WebSocket relay
- [ ] Deploy and test basic connectivity

### Phase 2: Client Integration ✅
- [x] Fix `BattlePlayer.is_local` attribute
- [x] Update `network_manager.py` for Pygbag (browser WebSocket)
- [x] Add missing controls (rotate, hard drop)
- [ ] Test on GitHub Pages

### Phase 3: Game Sync ✅
- [x] Implement server-side timer
- [x] Add garbage line sync
- [x] Sync opponent's current piece display
- [x] Handle game over conditions

### Phase 4: Polish 🔄
- [x] Add disconnect handling with UI feedback
- [ ] Add reconnection logic (optional)
- [ ] Add player name input
- [ ] Add latency indicator
- [ ] Test cross-browser compatibility

## Technical Notes

### Pygbag WebSocket Limitations
Pygbag (WebAssembly) 環境下無法使用 Python `websockets` 庫，需要透過 JavaScript interop：

```python
# In Pygbag environment, use browser's WebSocket
if sys.platform == "emscripten":
    # Use JavaScript WebSocket via platform module
    from platform import window
    ws = window.eval("new WebSocket('wss://...')")
else:
    # Desktop: use Python websockets
    import websockets
```

### Cloudflare Durable Objects
- 每個 GameRoom 是一個 Durable Object instance
- 自動處理 WebSocket 連線
- 具有持久化狀態（遊戲進行中）
- 全球分佈，低延遲

### Rate Limiting
- 狀態更新限制：每 50ms 一次（20 FPS）
- 防止惡意大量發送

## Environment Variables

```bash
# Cloudflare Worker (stored as secrets)
# None required for MVP - stateless matchmaking

# Optional future additions:
# ANALYTICS_TOKEN - for tracking matches
```

## Testing Checklist

### Local Development
- [ ] `server_simple.py` runs without errors
- [ ] Two clients can connect and match
- [ ] Grid state syncs correctly
- [ ] Garbage lines work

### Production (GitHub Pages + Cloudflare)
- [ ] WebSocket connects from browser
- [ ] Matchmaking works
- [ ] Game plays smoothly (< 100ms latency)
- [ ] Disconnect handled gracefully
- [ ] Mobile browser support

## Known Issues & TODOs

1. ~~**BattlePlayer.is_local** - 屬性不存在，需要新增~~ ✅ Fixed
2. ~~**Missing controls** - `handle_input()` 缺少旋轉和硬落下~~ ✅ Fixed
3. ~~**Time desync** - 需要伺服器同步時間~~ ✅ Fixed (server sends TIME_SYNC)
4. **No opponent piece** - 對手的 current_piece 渲染待優化

## Next Steps (從這裡繼續)

### ⏭️ 下一步：部署 Cloudflare Worker

**前置需求**：
- Node.js 已安裝
- Cloudflare 帳號（你已有，用於排行榜）

**執行步驟**：

```bash
# Step 1: 安裝 Wrangler CLI（如果還沒裝）
npm install -g wrangler

# Step 2: 登入 Cloudflare
wrangler login

# Step 3: 部署 Worker（在專案根目錄執行）
cd d:\Jeffery\claire
wrangler deploy
```

**部署成功後**：
- 會顯示 Worker URL，例如：`https://tetris-online.xxx.workers.dev`
- 確認 URL 與 `network_manager.py` 第 27 行的 `DEFAULT_URL` 一致
- 如果不同，需要更新程式碼

### 後續步驟

2. **本地測試**
   - 開兩個瀏覽器視窗訪問 GitHub Pages
   - 確認配對和遊戲同步正常

3. **整合到主選單**
   - 在 `main.py` 加入 Online Battle 選項
   - 加入玩家名稱輸入功能

## References

- [Cloudflare Durable Objects](https://developers.cloudflare.com/durable-objects/)
- [Cloudflare WebSocket](https://developers.cloudflare.com/workers/runtime-apis/websockets/)
- [Pygbag Documentation](https://pygame-web.github.io/)
