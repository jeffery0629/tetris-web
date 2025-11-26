/**
 * Cloudflare Worker for Online Battle Mode
 *
 * Features:
 * - WebSocket-based matchmaking
 * - Real-time game state relay
 * - Server-side timer synchronization
 * - Disconnect detection
 *
 * Deploy: wrangler deploy
 */

// Configuration
const GAME_DURATION_MS = 10 * 60 * 1000; // 10 minutes
const MAX_STATE_SIZE = 10000; // bytes
const STATE_RATE_LIMIT_MS = 50; // 20 FPS max

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // WebSocket endpoint
    if (url.pathname === '/ws') {
      // Check for WebSocket upgrade
      const upgradeHeader = request.headers.get('Upgrade');
      if (!upgradeHeader || upgradeHeader !== 'websocket') {
        return new Response('Expected WebSocket', { status: 426 });
      }

      // Route to the matchmaking Durable Object
      const id = env.GAME_LOBBY.idFromName('global-lobby');
      const lobby = env.GAME_LOBBY.get(id);
      return lobby.fetch(request);
    }

    return new Response('Not Found', { status: 404 });
  }
};

/**
 * GameLobby Durable Object
 * Handles matchmaking and creates game rooms
 */
export class GameLobby {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.waitingPlayer = null;
    this.activeGames = new Map(); // gameId -> {player1, player2, startTime}
  }

  async fetch(request) {
    // Create WebSocket pair
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);

    // Accept the WebSocket
    server.accept();

    // Handle this player
    this.handlePlayer(server);

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }

  handlePlayer(ws) {
    const playerId = crypto.randomUUID();
    let playerName = 'Player';
    let currentGameId = null;
    let lastStateTime = 0;

    ws.addEventListener('message', async (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'JOIN':
            playerName = data.player_name || 'Player';
            this.matchPlayer(ws, playerId, playerName);
            break;

          case 'STATE':
            // Rate limiting
            const now = Date.now();
            if (now - lastStateTime < STATE_RATE_LIMIT_MS) {
              return;
            }
            lastStateTime = now;

            // Size check
            if (event.data.length > MAX_STATE_SIZE) {
              return;
            }

            // Relay to opponent
            if (currentGameId) {
              const game = this.activeGames.get(currentGameId);
              if (game) {
                const opponent = game.player1.id === playerId ? game.player2 : game.player1;
                if (opponent.ws.readyState === WebSocket.OPEN) {
                  opponent.ws.send(JSON.stringify({
                    type: 'OPPONENT_STATE',
                    grid: data.grid,
                    score: data.score,
                    lines: data.lines,
                    piece: data.piece
                  }));
                }
              }
            }
            break;

          case 'GARBAGE':
            // Relay garbage to opponent
            if (currentGameId) {
              const game = this.activeGames.get(currentGameId);
              if (game) {
                const opponent = game.player1.id === playerId ? game.player2 : game.player1;
                if (opponent.ws.readyState === WebSocket.OPEN) {
                  opponent.ws.send(JSON.stringify({
                    type: 'GARBAGE',
                    lines: data.lines
                  }));
                }
              }
            }
            break;

          case 'GAME_OVER':
            // Player topped out
            if (currentGameId) {
              const game = this.activeGames.get(currentGameId);
              if (game) {
                const isPlayer1 = game.player1.id === playerId;
                const winner = isPlayer1 ? 2 : 1;

                this.endGame(currentGameId, 'OPPONENT_TOPPED_OUT', winner);
              }
            }
            break;
        }
      } catch (e) {
        console.error('Message handling error:', e);
      }
    });

    ws.addEventListener('close', () => {
      // Remove from waiting queue
      if (this.waitingPlayer && this.waitingPlayer.id === playerId) {
        this.waitingPlayer = null;
      }

      // Handle disconnect during game
      if (currentGameId) {
        const game = this.activeGames.get(currentGameId);
        if (game) {
          const isPlayer1 = game.player1.id === playerId;
          const opponent = isPlayer1 ? game.player2 : game.player1;

          // Notify opponent
          if (opponent.ws.readyState === WebSocket.OPEN) {
            opponent.ws.send(JSON.stringify({
              type: 'OPPONENT_DISCONNECTED'
            }));
          }

          // End game
          this.endGame(currentGameId, 'OPPONENT_DISCONNECTED', isPlayer1 ? 2 : 1);
        }
      }
    });

    // Store reference to update currentGameId
    ws._playerId = playerId;
    ws._setGameId = (id) => { currentGameId = id; };
  }

  matchPlayer(ws, playerId, playerName) {
    if (this.waitingPlayer === null) {
      // No one waiting, join queue
      this.waitingPlayer = { ws, id: playerId, name: playerName };
      ws.send(JSON.stringify({ type: 'WAITING' }));
    } else {
      // Match found!
      const opponent = this.waitingPlayer;
      this.waitingPlayer = null;

      const gameId = crypto.randomUUID();
      const startTime = Date.now();

      // Create game
      const game = {
        player1: opponent,
        player2: { ws, id: playerId, name: playerName },
        startTime,
        timerId: null
      };
      this.activeGames.set(gameId, game);

      // Set game IDs
      opponent.ws._setGameId(gameId);
      ws._setGameId(gameId);

      // Notify both players
      opponent.ws.send(JSON.stringify({
        type: 'MATCH_START',
        game_id: gameId,
        role: 1,
        opponent_name: playerName,
        server_time: startTime
      }));

      ws.send(JSON.stringify({
        type: 'MATCH_START',
        game_id: gameId,
        role: 2,
        opponent_name: opponent.name,
        server_time: startTime
      }));

      // Start game timer
      this.startGameTimer(gameId);
    }
  }

  startGameTimer(gameId) {
    const game = this.activeGames.get(gameId);
    if (!game) return;

    // Send time sync every 5 seconds
    const syncInterval = setInterval(() => {
      const elapsed = Date.now() - game.startTime;
      const remaining = Math.max(0, GAME_DURATION_MS - elapsed);

      const timeMsg = JSON.stringify({
        type: 'TIME_SYNC',
        remaining
      });

      if (game.player1.ws.readyState === WebSocket.OPEN) {
        game.player1.ws.send(timeMsg);
      }
      if (game.player2.ws.readyState === WebSocket.OPEN) {
        game.player2.ws.send(timeMsg);
      }

      // Check if game ended
      if (remaining <= 0) {
        clearInterval(syncInterval);
        this.endGame(gameId, 'TIMEOUT', 0); // 0 = compare scores
      }
    }, 5000);

    game.timerId = syncInterval;
  }

  endGame(gameId, reason, winner) {
    const game = this.activeGames.get(gameId);
    if (!game) return;

    // Clear timer
    if (game.timerId) {
      clearInterval(game.timerId);
    }

    // Send game end to both players
    const endMsg = JSON.stringify({
      type: 'GAME_END',
      reason,
      winner
    });

    if (game.player1.ws.readyState === WebSocket.OPEN) {
      game.player1.ws.send(endMsg);
    }
    if (game.player2.ws.readyState === WebSocket.OPEN) {
      game.player2.ws.send(endMsg);
    }

    // Cleanup
    this.activeGames.delete(gameId);
  }
}
