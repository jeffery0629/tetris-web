import asyncio
import json
import uuid
import websockets

# Simple matchmaking queue
waiting_player = None
active_games = {}

async def handler(websocket):
    global waiting_player
    player_id = str(uuid.uuid4())
    print(f"Player connected: {player_id}")

    try:
        # 1. Matchmaking Logic
        if waiting_player is None:
            # No one is waiting, join the waiting queue
            waiting_player = websocket
            await websocket.send(json.dumps({"type": "WAITING"}))
            print(f"{player_id} is waiting")
            # Keep connection alive until matched
            await websocket.wait_closed()
        else:
            # Someone is waiting, start the game
            opponent_ws = waiting_player
            waiting_player = None # Clear waiting queue
            
            # Notify both players
            game_id = str(uuid.uuid4())
            # Assign player roles (1 or 2)
            # The waiting player is Player 1 (Host-like), the joining player is Player 2
            await opponent_ws.send(json.dumps({"type": "MATCH_START", "game_id": game_id, "role": 1}))
            await websocket.send(json.dumps({"type": "MATCH_START", "game_id": game_id, "role": 2}))
            
            print(f"Match started: {game_id}")
            
            # 2. Start relay loops
            await asyncio.gather(
                relay_messages(websocket, opponent_ws),
                relay_messages(opponent_ws, websocket)
            )

    except Exception as e:
        print(f"Error handling connection {player_id}: {e}")
    finally:
        # Cleanup
        if waiting_player == websocket:
            waiting_player = None
        print(f"Player disconnected: {player_id}")

async def relay_messages(source, target):
    try:
        async for message in source:
            # Relay message directly to target
            await target.send(message)
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Relay error: {e}")

async def main():
    print("Starting WebSocket server on port 8765...")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")

