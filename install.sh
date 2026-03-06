#!/bin/bash
# ============================================================
#  DarkAI - Kali Linux Installer
#  Custom AI Agent — No dependency hell!
#  Only 3 core packages needed
# ============================================================

C='\033[0;36m'
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
W='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

INSTALL_DIR="$HOME/darkai"

echo -e "${C}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║       DarkAI — Kali Linux Setup          ║"
echo "  ║       Custom AI Agent                    ║"
echo "  ║       Only 3 dependencies!               ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

log()  { echo -e "${G}[+]${NC} $1"; }
warn() { echo -e "${Y}[!]${NC} $1"; }

# ── 1. Install Python deps ─────────────────────────────────
log "Updating package list..."
sudo apt-get update -qq

log "Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv -qq

# ── 2. Create install dir ──────────────────────────────────
log "Setting up DarkAI directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copy files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/darkai.py"  "$INSTALL_DIR/"
cp "$SCRIPT_DIR/agent.py"   "$INSTALL_DIR/"
cp "$SCRIPT_DIR/server.py"  "$INSTALL_DIR/"
cp "$SCRIPT_DIR/cli.py"     "$INSTALL_DIR/"

# ── 3. Create venv ─────────────────────────────────────────
log "Creating virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"
source "$INSTALL_DIR/.venv/bin/activate"

# ── 4. Install ONLY what's needed ─────────────────────────
log "Installing core packages (anthropic, flask, flask-socketio)..."
pip install anthropic flask flask-socketio -q
log "Core packages installed!"

# ── 5. API Key ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}${C}[?] Enter your Anthropic API key (sk-ant-...):${NC}"
read -r -s API_KEY
echo ""

# ── 6. Write .env ─────────────────────────────────────────
log "Writing .env..."
cat > "$INSTALL_DIR/.env" << EOF
ANTHROPIC_API_KEY=${API_KEY}
API_KEY_ANTHROPIC=${API_KEY}
PORT=5000
EOF

# ── 7. Write launcher ─────────────────────────────────────
log "Writing launcher script..."
cat > "$INSTALL_DIR/start.sh" << 'LAUNCHER'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python3 darkai.py
LAUNCHER
chmod +x "$INSTALL_DIR/start.sh"

# ── 8. Add to PATH (optional) ─────────────────────────────
echo ""
echo -e "${BOLD}${C}[?] Add 'darkai' command to run from anywhere? [Y/n]${NC}"
read -r ADD_PATH
if [[ ! "$ADD_PATH" =~ ^[Nn]$ ]]; then
  cat > /usr/local/bin/darkai << PATHSCRIPT
#!/bin/bash
cd $INSTALL_DIR
source .venv/bin/activate
python3 darkai.py
PATHSCRIPT
  chmod +x /usr/local/bin/darkai 2>/dev/null || sudo chmod +x /usr/local/bin/darkai
  log "You can now run 'darkai' from anywhere!"
fi

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${G}${BOLD}╔══════════════════════════════════════════╗"
echo -e "║   ✅  DarkAI Installed!                  ║"
echo -e "╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e " ${C}To start DarkAI:${NC}"
echo -e "   cd ~/darkai && ./start.sh"
echo ""
echo -e " ${C}Or from anywhere:${NC}"
echo -e "   darkai"
echo ""
