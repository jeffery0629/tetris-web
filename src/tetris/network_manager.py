"""
Network Manager for Online Battle Mode

Supports both desktop (Python websockets) and web (Pygbag/browser WebSocket).
"""

import asyncio
import json
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detect if running in Pygbag (WebAssembly)
IS_WEB = sys.platform == "emscripten"

if IS_WEB:
    from platform import window


class NetworkManager:
    """Handles WebSocket communication for online battle mode."""

    # Default server URL (override with connect())
    DEFAULT_URL = "wss://tetris-online.jefferysung860629.workers.dev/ws"

    def __init__(self):
        self.websocket = None
        self.connected = False
        self.message_queue = asyncio.Queue()
        self.role = None  # 1 or 2, assigned by server
        self.game_id = None
        self.opponent_name = None
        self.server_time_offset = 0  # For time sync
        self._js_ws = None  # JavaScript WebSocket reference (web only)

    async def connect(self, uri: str = None):
        """Connect to the WebSocket server."""
        uri = uri or self.DEFAULT_URL

        if IS_WEB:
            return await self._connect_web(uri)
        else:
            return await self._connect_desktop(uri)

    async def _connect_web(self, uri: str):
        """Connect using browser WebSocket (Pygbag)."""
        try:
            logger.info(f"[Web] Connecting to {uri}...")

            # Create WebSocket using JavaScript
            js_code = f"""
            (function() {{
                window._tetris_ws = new WebSocket("{uri}");
                window._tetris_ws_messages = [];
                window._tetris_ws_connected = false;
                window._tetris_ws_error = null;

                window._tetris_ws.onopen = function() {{
                    window._tetris_ws_connected = true;
                    console.log("WebSocket connected");
                }};

                window._tetris_ws.onmessage = function(event) {{
                    window._tetris_ws_messages.push(event.data);
                }};

                window._tetris_ws.onerror = function(error) {{
                    window._tetris_ws_error = "Connection error";
                    console.error("WebSocket error:", error);
                }};

                window._tetris_ws.onclose = function() {{
                    window._tetris_ws_connected = false;
                    console.log("WebSocket closed");
                }};

                return "ok";
            }})()
            """
            window.eval(js_code)

            # Wait for connection (up to 5 seconds)
            for _ in range(50):
                await asyncio.sleep(0.1)
                if window.eval("window._tetris_ws_connected"):
                    self.connected = True
                    logger.info("[Web] Connected!")
                    # Start receive loop
                    asyncio.create_task(self._receive_loop_web())
                    return True
                if window.eval("window._tetris_ws_error"):
                    error = window.eval("window._tetris_ws_error")
                    logger.error(f"[Web] Connection failed: {error}")
                    return False

            logger.error("[Web] Connection timeout")
            return False

        except Exception as e:
            logger.error(f"[Web] Connection failed: {e}")
            return False

    async def _connect_desktop(self, uri: str):
        """Connect using Python websockets library (desktop)."""
        try:
            import websockets
            logger.info(f"[Desktop] Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.connected = True
            logger.info("[Desktop] Connected!")

            # Start receive loop
            asyncio.create_task(self._receive_loop_desktop())
            return True

        except ImportError:
            logger.error("websockets library not installed. Run: pip install websockets")
            return False
        except Exception as e:
            logger.error(f"[Desktop] Connection failed: {e}")
            self.connected = False
            return False

    async def _receive_loop_web(self):
        """Listen for incoming messages (web version)."""
        try:
            while self.connected:
                # Check for new messages from JavaScript queue
                js_code = """
                (function() {
                    if (window._tetris_ws_messages && window._tetris_ws_messages.length > 0) {
                        return window._tetris_ws_messages.shift();
                    }
                    return null;
                })()
                """
                message = window.eval(js_code)

                if message:
                    data = json.loads(message)
                    await self.message_queue.put(data)

                # Check connection status
                if not window.eval("window._tetris_ws_connected"):
                    self.connected = False
                    break

                await asyncio.sleep(0.016)  # ~60 FPS check rate

        except Exception as e:
            logger.error(f"[Web] Receive loop error: {e}")
            self.connected = False

    async def _receive_loop_desktop(self):
        """Listen for incoming messages (desktop version)."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.message_queue.put(data)
        except Exception as e:
            logger.error(f"[Desktop] Connection lost: {e}")
            self.connected = False

    async def get_event(self):
        """Get the next event from the queue (non-blocking)."""
        if self.message_queue.empty():
            return None
        return await self.message_queue.get()

    async def send(self, data: dict):
        """Send data to the server."""
        if not self.connected:
            return False

        try:
            message = json.dumps(data)

            if IS_WEB:
                # Send via JavaScript WebSocket
                js_code = f"""
                (function() {{
                    if (window._tetris_ws && window._tetris_ws.readyState === WebSocket.OPEN) {{
                        window._tetris_ws.send('{message.replace("'", "\\'")}');
                        return true;
                    }}
                    return false;
                }})()
                """
                return window.eval(js_code)
            else:
                await self.websocket.send(message)
                return True

        except Exception as e:
            logger.error(f"Send failed: {e}")
            self.connected = False
            return False

    async def join_matchmaking(self, player_name: str = "Player"):
        """Join the matchmaking queue."""
        return await self.send({
            "type": "JOIN",
            "player_name": player_name
        })

    async def send_state(self, grid, score: int, lines: int, piece=None):
        """Send game state to opponent."""
        payload = {
            "type": "STATE",
            "score": score,
            "lines": lines,
        }

        # Serialize grid: None -> 0, (r,g,b) -> [r,g,b]
        if grid:
            simple_grid = []
            for row in grid:
                simple_row = [list(cell) if cell else 0 for cell in row]
                simple_grid.append(simple_row)
            payload["grid"] = simple_grid

        # Serialize current piece
        if piece:
            payload["piece"] = {
                "x": piece.x,
                "y": piece.y,
                "rotation": piece.rotation,
                "color": list(piece.color) if piece.color else [128, 128, 128]
            }

        return await self.send(payload)

    async def send_garbage(self, lines: int):
        """Send garbage lines to opponent."""
        if lines > 0:
            return await self.send({
                "type": "GARBAGE",
                "lines": lines
            })
        return True

    async def send_game_over(self):
        """Notify server that this player topped out."""
        return await self.send({"type": "GAME_OVER"})

    def close(self):
        """Close the WebSocket connection."""
        self.connected = False

        if IS_WEB:
            try:
                window.eval("""
                (function() {
                    if (window._tetris_ws) {
                        window._tetris_ws.close();
                        window._tetris_ws = null;
                    }
                })()
                """)
            except Exception:
                pass
        elif self.websocket:
            asyncio.create_task(self.websocket.close())
