"""
server.py — Web GUI server for KaliAI
Serves the chat interface at http://localhost:PORT
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from flask import Flask, request, jsonify, render_template_string
    _FLASK_OK = True
except ImportError:
    _FLASK_OK = False

from agent import KaliAI

# ── Load API key ───────────────────────────────────────────
def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY_ANTHROPIC")
    if key:
        return key
    for env_path in [
        Path.home() / "agent-zero" / ".env",
        Path(__file__).parent / ".env",
        Path.home() / ".env"
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith(("API_KEY_ANTHROPIC=", "ANTHROPIC_API_KEY=")):
                    val = line.split("=", 1)[1].strip()
                    if val and not val.startswith("sk-ant-YOUR"):
                        return val
    return ""

# ── HTML Template ──────────────────────────────────────────
HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KaliAI</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;700;800&display=swap');

  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --border: #1e1e2e;
    --accent: #00ff88;
    --accent2: #0088ff;
    --danger: #ff4444;
    --warn: #ffaa00;
    --text: #e0e0e0;
    --muted: #666680;
    --code-bg: #0d0d15;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Header */
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    flex-shrink: 0;
  }

  .logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.3rem;
    color: var(--accent);
    letter-spacing: 2px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .logo-dot {
    width: 8px; height: 8px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
  }

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .badge {
    font-size: 0.65rem;
    padding: 3px 8px;
    border-radius: 3px;
    border: 1px solid var(--border);
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .badge.root-on {
    border-color: var(--warn);
    color: var(--warn);
  }

  .btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 5px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    transition: all 0.2s;
    letter-spacing: 0.5px;
  }

  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .btn.danger:hover { border-color: var(--danger); color: var(--danger); }

  /* Chat area */
  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }

  .message {
    display: flex;
    flex-direction: column;
    gap: 6px;
    animation: fadeIn 0.3s ease;
    max-width: 900px;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .message.user { align-self: flex-end; align-items: flex-end; }
  .message.ai { align-self: flex-start; align-items: flex-start; }

  .msg-label {
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 0 4px;
  }

  .message.user .msg-label { color: var(--accent2); }
  .message.ai .msg-label { color: var(--accent); }

  .msg-bubble {
    padding: 12px 16px;
    border-radius: 6px;
    line-height: 1.7;
    font-size: 0.88rem;
    max-width: 100%;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message.user .msg-bubble {
    background: #0d1a2e;
    border: 1px solid #1a3050;
    color: #c8d8f0;
    border-radius: 6px 6px 0 6px;
  }

  .message.ai .msg-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px 6px 6px 0;
  }

  /* Command blocks */
  .cmd-block {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.82rem;
    max-width: 860px;
    animation: fadeIn 0.3s ease;
  }

  .cmd-label {
    color: var(--muted);
    font-size: 0.65rem;
    letter-spacing: 1px;
    margin-bottom: 6px;
    text-transform: uppercase;
  }

  .cmd-text {
    color: var(--accent);
    font-weight: 500;
  }

  .cmd-output {
    color: #a0a0b0;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    white-space: pre-wrap;
    word-break: break-word;
  }

  .cmd-output.error { color: var(--danger); }

  /* Root confirmation */
  .root-confirm {
    background: #1a1200;
    border: 1px solid var(--warn);
    border-radius: 6px;
    padding: 14px 18px;
    max-width: 600px;
    animation: fadeIn 0.3s ease;
  }

  .root-confirm p {
    color: var(--warn);
    font-size: 0.85rem;
    margin-bottom: 10px;
  }

  .root-confirm-btns {
    display: flex;
    gap: 8px;
  }

  .btn-confirm {
    background: var(--warn);
    color: #000;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
  }

  .btn-deny {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 6px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
  }

  /* Thinking indicator */
  .thinking {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--muted);
    font-size: 0.8rem;
    padding: 8px 0;
  }

  .thinking-dots span {
    display: inline-block;
    width: 5px; height: 5px;
    background: var(--accent);
    border-radius: 50%;
    margin: 0 2px;
    animation: bounce 1.2s infinite;
  }

  .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
  .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-6px); }
  }

  /* Input area */
  .input-area {
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    background: var(--surface);
    flex-shrink: 0;
  }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }

  #userInput {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 12px 16px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    resize: none;
    min-height: 46px;
    max-height: 160px;
    outline: none;
    transition: border-color 0.2s;
    line-height: 1.5;
  }

  #userInput:focus { border-color: var(--accent); }
  #userInput::placeholder { color: var(--muted); }

  #sendBtn {
    background: var(--accent);
    color: #000;
    border: none;
    padding: 12px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    transition: all 0.2s;
    white-space: nowrap;
    align-self: stretch;
  }

  #sendBtn:hover { background: #00cc6a; }
  #sendBtn:disabled { background: var(--border); color: var(--muted); cursor: not-allowed; }

  .input-hint {
    font-size: 0.65rem;
    color: var(--muted);
    margin-top: 6px;
    letter-spacing: 0.5px;
  }

  /* Welcome */
  .welcome {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
  }

  .welcome h2 {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    color: var(--accent);
    margin-bottom: 10px;
    letter-spacing: 3px;
  }

  .welcome p { font-size: 0.85rem; line-height: 1.8; }

  .suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 24px;
  }

  .suggestion {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 7px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.2s;
  }

  .suggestion:hover { border-color: var(--accent); color: var(--accent); }

  /* Scrollbar */
  #chat::-webkit-scrollbar { width: 4px; }
  #chat::-webkit-scrollbar-track { background: transparent; }
  #chat::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-dot"></div>
    KALI<span style="color:#0088ff">AI</span>
  </div>
  <div class="header-actions">
    <span class="badge" id="rootBadge">ROOT: OFF</span>
    <button class="btn" onclick="clearMemory()">CLEAR</button>
    <button class="btn danger" onclick="toggleRoot()">ROOT</button>
  </div>
</header>

<div id="chat">
  <div class="welcome" id="welcome">
    <h2>KALI AI</h2>
    <p>Your intelligent Kali Linux assistant.<br>Powered by Claude claude-sonnet-4-5</p>
    <div class="suggestions">
      <div class="suggestion" onclick="suggest(this)">scan 192.168.1.1 for open ports</div>
      <div class="suggestion" onclick="suggest(this)">what processes are using port 80?</div>
      <div class="suggestion" onclick="suggest(this)">crack this MD5 hash: 5f4dcc3b5aa765d61d8327deb882cf99</div>
      <div class="suggestion" onclick="suggest(this)">show me running services</div>
      <div class="suggestion" onclick="suggest(this)">write a python port scanner</div>
      <div class="suggestion" onclick="suggest(this)">what is SQL injection?</div>
    </div>
  </div>
</div>

<div class="input-area">
  <div class="input-row">
    <textarea id="userInput" placeholder="Ask anything or give a command..." rows="1"
      onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
    <button id="sendBtn" onclick="sendMessage()">SEND</button>
  </div>
  <div class="input-hint">Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>
</div>

<script>
  let rootEnabled = false;
  let pendingRootInput = null;

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function suggest(el) {
    document.getElementById('userInput').value = el.textContent;
    sendMessage();
  }

  function scrollBottom() {
    const chat = document.getElementById('chat');
    chat.scrollTop = chat.scrollHeight;
  }

  function hideWelcome() {
    const w = document.getElementById('welcome');
    if (w) w.style.display = 'none';
  }

  function addMessage(role, text, commands) {
    hideWelcome();
    const chat = document.getElementById('chat');

    const msg = document.createElement('div');
    msg.className = `message ${role}`;

    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = role === 'user' ? 'YOU' : 'KALI AI';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    msg.appendChild(label);
    msg.appendChild(bubble);
    chat.appendChild(msg);

    // Add command blocks
    if (commands && commands.length > 0) {
      commands.forEach(cmd => {
        const block = document.createElement('div');
        block.className = 'cmd-block';

        const lbl = document.createElement('div');
        lbl.className = 'cmd-label';
        lbl.textContent = '▸ EXECUTED';

        const cmdText = document.createElement('div');
        cmdText.className = 'cmd-text';
        cmdText.textContent = '$ ' + cmd.command;

        block.appendChild(lbl);
        block.appendChild(cmdText);

        if (cmd.stdout || cmd.stderr) {
          const out = document.createElement('div');
          out.className = 'cmd-output' + (cmd.returncode !== 0 ? ' error' : '');
          out.textContent = cmd.stdout || cmd.stderr;
          block.appendChild(out);
        }

        chat.appendChild(block);
      });
    }

    scrollBottom();
    return msg;
  }

  function addThinking() {
    hideWelcome();
    const chat = document.getElementById('chat');
    const div = document.createElement('div');
    div.className = 'thinking';
    div.id = 'thinking';
    div.innerHTML = `<div class="thinking-dots"><span></span><span></span><span></span></div> thinking...`;
    chat.appendChild(div);
    scrollBottom();
  }

  function removeThinking() {
    const t = document.getElementById('thinking');
    if (t) t.remove();
  }

  function showRootConfirm(reason, originalInput) {
    hideWelcome();
    const chat = document.getElementById('chat');
    const div = document.createElement('div');
    div.id = 'rootConfirm';
    div.className = 'root-confirm';
    div.innerHTML = `
      <p>⚠️ Root access required: ${reason}</p>
      <div class="root-confirm-btns">
        <button class="btn-confirm" onclick="confirmRoot('${escapeJs(originalInput)}')">YES, USE ROOT</button>
        <button class="btn-deny" onclick="denyRoot()">NO, CANCEL</button>
      </div>`;
    chat.appendChild(div);
    scrollBottom();
  }

  function escapeJs(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n');
  }

  async function confirmRoot(originalInput) {
    const confirm = document.getElementById('rootConfirm');
    if (confirm) confirm.remove();
    await sendMessage(originalInput, true);
  }

  function denyRoot() {
    const confirm = document.getElementById('rootConfirm');
    if (confirm) confirm.remove();
    addMessage('ai', 'Okay, continuing without root. Some operations may be limited.');
  }

  async function sendMessage(overrideInput, rootConfirmed) {
    const input = document.getElementById('userInput');
    const text = (overrideInput || input.value).trim();
    if (!text) return;

    if (!overrideInput) {
      input.value = '';
      input.style.height = 'auto';
    }

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    addMessage('user', text);
    addThinking();

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, root_confirmed: !!rootConfirmed })
      });

      const data = await res.json();
      removeThinking();

      if (data.needs_root) {
        showRootConfirm(data.root_reason, text);
      } else {
        addMessage('ai', data.text || '(no response)', data.command_results);
      }

      if (data.error) {
        addMessage('ai', '⚠️ Error: ' + data.text);
      }

    } catch (err) {
      removeThinking();
      addMessage('ai', '⚠️ Connection error. Is the server running?');
    }

    sendBtn.disabled = false;
    document.getElementById('userInput').focus();
  }

  async function clearMemory() {
    await fetch('/clear', { method: 'POST' });
    document.getElementById('chat').innerHTML = '';
    const welcome = document.createElement('div');
    welcome.id = 'welcome';
    welcome.className = 'welcome';
    welcome.innerHTML = `<h2>KALI AI</h2><p>Memory cleared. Ready for a new session.</p>`;
    document.getElementById('chat').appendChild(welcome);
  }

  async function toggleRoot() {
    const res = await fetch('/root', { method: 'POST' });
    const data = await res.json();
    rootEnabled = data.root_enabled;
    const badge = document.getElementById('rootBadge');
    badge.textContent = 'ROOT: ' + (rootEnabled ? 'ON' : 'OFF');
    badge.className = 'badge' + (rootEnabled ? ' root-on' : '');
  }
</script>
</body>
</html>'''


def create_app(api_key: str) -> Flask:
    app = Flask(__name__)
    ai = KaliAI(api_key)

    @app.route("/")
    def index():
        return render_template_string(HTML)

    @app.route("/chat", methods=["POST"])
    def chat():
        data = request.get_json()
        message = data.get("message", "").strip()
        root_confirmed = data.get("root_confirmed", False)

        if not message:
            return jsonify({"text": "No message provided.", "error": True})

        response = ai.chat(message, root_confirmed=root_confirmed)
        return jsonify(response)

    @app.route("/clear", methods=["POST"])
    def clear():
        ai.clear_memory()
        return jsonify({"status": "ok"})

    @app.route("/root", methods=["POST"])
    def toggle_root():
        ai.shell.use_root = not ai.shell.use_root
        return jsonify({"root_enabled": ai.shell.use_root})

    return app


if __name__ == "__main__":
    if not _FLASK_OK:
        print("[✗] Flask not installed. Run: pip install flask")
        sys.exit(1)

    api_key = get_api_key()
    if not api_key:
        print("[✗] No API key found.")
        sys.exit(1)

    app = create_app(api_key)
    port = int(os.environ.get("PORT", 5000))
    print(f"\n\033[0;36m  KaliAI GUI starting at http://localhost:{port}\033[0m\n")
    app.run(host="127.0.0.1", port=port, debug=False)
