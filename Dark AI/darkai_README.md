# Dark-AI — Kali Linux AI Agent

Your personal AI agent built for Kali Linux. Choose from 7 AI providers including free options.

## Features
- 🖥️ **GUI mode** — clean browser chat interface
- ⌨️ **CLI mode** — terminal chat, no browser needed
- 🤖 **7 AI providers** — Anthropic, Groq (free), OpenAI, Google, Mistral, Cohere, Ollama
- 🐚 **Full shell access** — runs any Linux command
- 🔐 **Smart root handling** — asks before using sudo
- 🧠 **Memory** — remembers your conversation
- ⚡ **Minimal dependencies** — auto-installs everything

## Supported Providers

| # | Provider | Free? | Get Key |
|---|----------|-------|---------|
| 1 | Anthropic (Claude) | Paid | console.anthropic.com |
| 2 | Groq (Llama 3) | ✅ FREE | console.groq.com |
| 3 | OpenAI (GPT) | Paid | platform.openai.com |
| 4 | Google (Gemini) | ✅ FREE tier | aistudio.google.com |
| 5 | Mistral AI | Paid | console.mistral.ai |
| 6 | Cohere | ✅ FREE tier | dashboard.cohere.com |
| 7 | Ollama (Local) | ✅ FREE | ollama.ai |

## Install

```bash
git clone https://github.com/Cursed-Catalyst/Dark-AI.git
cd Dark-AI
chmod +x install.sh
./install.sh
```

## Run

```bash
# From install directory
cd ~/darkai && ./start.sh

# Or from anywhere (if added to PATH during install)
darkai
```

## Usage

When you start DarkAI:
1. Choose your AI provider (1-7)
2. Enter your API key if prompted
3. Choose GUI (browser) or CLI (terminal)

### Example prompts
- `scan 192.168.1.1 for open ports`
- `crack this hash: 5f4dcc3b5aa765d61d8327deb882cf99`
- `show all running processes`
- `what hacking tools are installed?`
- `write a python port scanner`
- `check my network interfaces`

## Requirements
- Kali Linux
- Python 3.x (any version including 3.13)
- API key for your chosen provider (Groq is free!)
