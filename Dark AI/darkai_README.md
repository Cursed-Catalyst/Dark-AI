# DarkAI — Kali Linux AI Agent

Your personal AI agent built for Kali Linux. Powered by Claude claude-sonnet-4-5.

## Features
- 🖥️ **GUI mode** — clean browser chat interface
- ⌨️ **CLI mode** — terminal chat, no browser needed
- 🐚 **Full shell access** — runs any Linux command
- 🔐 **Smart root handling** — asks before using sudo
- 🧠 **Memory** — remembers your conversation
- ⚡ **Only 3 dependencies** — anthropic, flask, flask-socketio

## Install

```bash
git clone https://github.com/Cursed-Catalyst/darkai.git
cd darkai
chmod +x install.sh
./install.sh
```

## Run

```bash
# From install directory
cd ~/darkai && ./start.sh

# Or from anywhere (if added to PATH)
darkai
```

## Usage

When you start DarkAI, choose:
- **1** = GUI (browser at http://localhost:5000)
- **2** = CLI (terminal mode)

### Example prompts
- `scan 192.168.1.1 for open ports`
- `crack this hash: 5f4dcc3b5aa765d61d8327deb882cf99`
- `show all running processes`
- `what tools are installed for web testing?`
- `write a python script to ping sweep 192.168.1.0/24`

## Requirements
- Kali Linux
- Python 3.x (any version)
- Anthropic API key (console.anthropic.com)
