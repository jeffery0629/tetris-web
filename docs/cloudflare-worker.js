// Cloudflare Worker: tetris-leaderboard
// Proxy requests to GitHub Gist with server-side token
//
// Setup:
// 1. Create a new Worker at https://dash.cloudflare.com
// 2. Copy this code to the Worker editor
// 3. Set environment variables (Settings → Variables):
//    - GIST_ID (Secret)
//    - GITHUB_TOKEN (Secret)
// 4. Save and Deploy

const ALLOWED_ORIGINS = [
  'https://jeffery0629.github.io',
  'http://localhost:8000',  // For local testing
];

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === 'OPTIONS') {
      return handleCORS(request);
    }

    const origin = request.headers.get('Origin') || '';
    const corsHeaders = getCORSHeaders(origin);

    try {
      const url = new URL(request.url);
      const path = url.pathname;

      // GET /leaderboard - Read leaderboard
      if (path === '/leaderboard' && request.method === 'GET') {
        return await getLeaderboard(env, corsHeaders);
      }

      // POST /submit - Submit score
      if (path === '/submit' && request.method === 'POST') {
        const data = await request.json();
        return await submitScore(env, data, corsHeaders);
      }

      return new Response(JSON.stringify({ error: 'Not Found' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};

function handleCORS(request) {
  const origin = request.headers.get('Origin') || '';
  return new Response(null, {
    status: 204,
    headers: getCORSHeaders(origin)
  });
}

function getCORSHeaders(origin) {
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

async function getLeaderboard(env, corsHeaders) {
  const response = await fetch(`https://api.github.com/gists/${env.GIST_ID}`, {
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `token ${env.GITHUB_TOKEN}`,
      'User-Agent': 'tetris-leaderboard-worker'
    }
  });

  if (!response.ok) {
    throw new Error(`GitHub API error: ${response.status}`);
  }

  const gist = await response.json();
  const content = gist.files['tetris_leaderboard.json']?.content || '{"casual":[],"classic":[],"crazy":[]}';

  return new Response(content, {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function submitScore(env, data, corsHeaders) {
  // Validate required fields
  const required = ['player_id', 'score', 'lines', 'level', 'mode'];
  for (const field of required) {
    if (data[field] === undefined) {
      return new Response(JSON.stringify({ error: `Missing field: ${field}` }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }

  // Anti-cheat: score limit check
  const MAX_SCORES = { casual: 50000, classic: 100000, crazy: 200000 };
  const maxScore = MAX_SCORES[data.mode] || 100000;
  if (data.score > maxScore || data.score < 0) {
    return new Response(JSON.stringify({ error: 'Invalid score' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Fetch current leaderboard
  const getResponse = await fetch(`https://api.github.com/gists/${env.GIST_ID}`, {
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `token ${env.GITHUB_TOKEN}`,
      'User-Agent': 'tetris-leaderboard-worker'
    }
  });

  if (!getResponse.ok) {
    throw new Error(`GitHub API error: ${getResponse.status}`);
  }

  const gist = await getResponse.json();
  const content = gist.files['tetris_leaderboard.json']?.content || '{"casual":[],"classic":[],"crazy":[]}';
  const leaderboard = JSON.parse(content);

  // Add new entry
  const entry = {
    player_id: String(data.player_id).slice(0, 12),  // Limit length
    score: Math.floor(data.score),
    lines: Math.floor(data.lines),
    level: Math.floor(data.level),
    mode: data.mode,
    timestamp: Date.now() / 1000,
    date: new Date().toISOString().slice(0, 16).replace('T', ' ')
  };

  if (!leaderboard[data.mode]) {
    leaderboard[data.mode] = [];
  }
  leaderboard[data.mode].push(entry);

  // Sort and keep top 100
  leaderboard[data.mode].sort((a, b) => b.score - a.score);
  leaderboard[data.mode] = leaderboard[data.mode].slice(0, 100);

  // Update Gist
  const updateResponse = await fetch(`https://api.github.com/gists/${env.GIST_ID}`, {
    method: 'PATCH',
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `token ${env.GITHUB_TOKEN}`,
      'Content-Type': 'application/json',
      'User-Agent': 'tetris-leaderboard-worker'
    },
    body: JSON.stringify({
      files: {
        'tetris_leaderboard.json': {
          content: JSON.stringify(leaderboard, null, 2)
        }
      }
    })
  });

  if (!updateResponse.ok) {
    throw new Error(`Failed to update: ${updateResponse.status}`);
  }

  // Calculate rank
  const rank = leaderboard[data.mode].findIndex(e =>
    e.timestamp === entry.timestamp && e.player_id === entry.player_id
  ) + 1;

  return new Response(JSON.stringify({
    success: true,
    rank,
    message: `Score submitted! Rank: #${rank}`
  }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}
