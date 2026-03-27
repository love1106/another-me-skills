#!/usr/bin/env node
/**
 * git-nexus-mcp-bridge.js — GitNexus MCP Client for OpenClaw
 * 
 * Calls GitNexus MCP tools directly via JSON-RPC 2.0 over stdio.
 * No MCP client library needed — just spawn + pipe.
 * 
 * Usage:
 *   node git-nexus-mcp-bridge.js <tool> [args-json] [--repo <name>] [--timeout <ms>]
 * 
 * Tools:
 *   list_repos                          — List all indexed repositories
 *   query '{"query":"auth handler"}'    — Hybrid search (BM25 + semantic)
 *   context '{"symbol":"UserService"}'  — 360° symbol view
 *   impact '{"symbol":"validate"}'      — Blast radius analysis
 *   detect_changes '{}'                 — Git diff → affected symbols
 *   rename '{"old":"foo","new":"bar"}'  — Multi-file rename plan
 *   cypher '{"query":"MATCH (n) ..."}'  — Raw Cypher query
 * 
 * Examples:
 *   node git-nexus-mcp-bridge.js list_repos
 *   node git-nexus-mcp-bridge.js query '{"query":"auth flow"}' --repo another-me
 *   node git-nexus-mcp-bridge.js impact '{"symbol":"UserService.validate"}' --timeout 30000
 */

const { spawn } = require('child_process');
const path = require('path');

// Parse CLI args
const args = process.argv.slice(2);
let tool = null;
let toolArgs = {};
let repoOverride = null;
let timeout = 30000; // 30s default (npx first-run download can be slow)

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--repo' && args[i + 1]) {
    repoOverride = args[++i];
  } else if (args[i] === '--timeout' && args[i + 1]) {
    timeout = parseInt(args[++i], 10);
  } else if (!tool) {
    tool = args[i];
  } else {
    try {
      toolArgs = JSON.parse(args[i]);
    } catch (e) {
      // Treat as simple query string
      toolArgs = { query: args[i] };
    }
  }
}

if (!tool) {
  console.error('Usage: node git-nexus-mcp-bridge.js <tool> [args-json] [--repo <name>] [--timeout <ms>]');
  console.error('Tools: list_repos, query, context, impact, detect_changes, rename, cypher');
  process.exit(1);
}

// Inject repo if specified
if (repoOverride && tool !== 'list_repos') {
  toolArgs.repo = repoOverride;
}

// Resolve GitNexus binary: prefer global install over npx (avoids re-download each call)
const { execSync } = require('child_process');
let gnCmd, gnArgs;
try {
  const gnBin = execSync('which gitnexus', { encoding: 'utf8' }).trim();
  gnCmd = gnBin;
  gnArgs = ['mcp'];
} catch (_) {
  gnCmd = 'npx';
  gnArgs = ['-y', 'gitnexus@latest', 'mcp'];
}

// Spawn GitNexus MCP server
const server = spawn(gnCmd, gnArgs, {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: { ...process.env, NODE_NO_WARNINGS: '1' }
});

let buffer = '';
let msgId = 0;
let phase = 'init'; // init → initialized → call → done
let timeoutId = null;

function send(method, params = {}) {
  const msg = JSON.stringify({ jsonrpc: '2.0', id: ++msgId, method, params });
  server.stdin.write(msg + '\n');
}

function cleanup(code = 0) {
  if (timeoutId) clearTimeout(timeoutId);
  try { server.kill('SIGTERM'); } catch (_) {}
  process.exit(code);
}

// Timeout guard
timeoutId = setTimeout(() => {
  console.error(JSON.stringify({ error: 'timeout', message: `MCP bridge timed out after ${timeout}ms` }));
  cleanup(1);
}, timeout);

// Handle server crash
server.on('error', (err) => {
  console.error(JSON.stringify({ error: 'spawn_failed', message: err.message }));
  cleanup(1);
});

server.on('exit', (code) => {
  if (phase !== 'done') {
    console.error(JSON.stringify({ error: 'server_exit', message: `MCP server exited with code ${code}`, stderr: stderrBuf.slice(-500) || undefined }));
    cleanup(1);
  }
});

// Collect stderr for diagnostics
let stderrBuf = '';
server.stderr.on('data', (chunk) => {
  stderrBuf += chunk.toString();
});

// Parse JSON-RPC responses from stdout
server.stdout.on('data', (chunk) => {
  buffer += chunk.toString();

  // Try to parse complete JSON messages (newline-delimited)
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    let msg;
    try {
      msg = JSON.parse(trimmed);
    } catch (_) {
      continue; // skip non-JSON lines (e.g. npx download messages)
    }

    handleMessage(msg);
  }
});

function handleMessage(msg) {
  // Handle notifications (no id)
  if (!msg.id && msg.method) {
    // Server notification — ignore or handle specific ones
    return;
  }

  if (msg.error) {
    console.error(JSON.stringify({ error: 'mcp_error', code: msg.error.code, message: msg.error.message, stderr: stderrBuf.slice(-500) || undefined }));
    cleanup(1);
    return;
  }

  switch (phase) {
    case 'init':
      // Response to initialize
      phase = 'initialized';
      // Send initialized notification
      server.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
      // Now call the tool
      phase = 'call';
      send('tools/call', { name: tool, arguments: toolArgs });
      break;

    case 'call':
      // Response to tools/call
      phase = 'done';
      if (msg.result) {
        // Extract text content
        const content = msg.result.content || [];
        const texts = content
          .filter(c => c.type === 'text')
          .map(c => c.text);

        if (texts.length === 1) {
          // Try to parse as JSON for pretty output
          try {
            const parsed = JSON.parse(texts[0]);
            console.log(JSON.stringify(parsed, null, 2));
          } catch (_) {
            console.log(texts[0]);
          }
        } else if (texts.length > 1) {
          console.log(texts.join('\n---\n'));
        } else {
          console.log(JSON.stringify(msg.result, null, 2));
        }
      } else {
        console.log(JSON.stringify(msg, null, 2));
      }
      cleanup(0);
      break;

    default:
      break;
  }
}

// Start handshake
send('initialize', {
  protocolVersion: '2024-11-05',
  capabilities: {},
  clientInfo: { name: 'openclaw-mcp-bridge', version: '1.0.0' }
});
