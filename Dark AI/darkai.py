#!/usr/bin/env python3
"""
DarkAI - Launcher
Choose between GUI (browser) or CLI (terminal) mode
"""

import sys
import os
import subprocess
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def ensure_deps():
    """Auto-install all required packages."""
    packages = [
        "anthropic",
        "flask",
        "flask-socketio",
    ]
    for pkg in packages:
        mod = pkg.replace("-", "_").split("[")[0]
        try:
            __import__(mod)
        except ImportError:
            print(f"  [*] Installing {pkg}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                check=True
            )

# Colors
C  = "\033[0;36m"
G  = "\033[0;32m"
Y  = "\033[1;33m"
W  = "\033[1;37m"
R  = "\033[0;31m"
DIM = "\033[2m"
NC = "\033[0m"
BOLD = "\033[1m"

def banner():
    print(f"""
{C}╔══════════════════════════════════════════════╗
║                                              ║
║   {W}{BOLD}██████   █████  ██████  ██   ██  █████  ██{NC}{C}  ║
║   {W}{BOLD}██   ██ ██   ██ ██   ██ ██  ██  ██   ██ ██{NC}{C}  ║
║   {W}{BOLD}██   ██ ███████ ██████  █████   ███████ ██{NC}{C}  ║
║   {W}{BOLD}██   ██ ██   ██ ██   ██ ██  ██  ██   ██ ██{NC}{C}  ║
║   {W}{BOLD}██████  ██   ██ ██   ██ ██   ██ ██   ██ ██{NC}{C}  ║
║                                              ║
║      {DIM}Kali Linux AI Agent — claude-sonnet-4-5{NC}{C}     ║
╚══════════════════════════════════════════════╝{NC}
""")

def check_api_key():
    """Check and set up API key if missing."""
    # Load .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path).readlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY_ANTHROPIC")
    
    if not api_key:
        print(f"{Y}[!] No Anthropic API key found.{NC}")
        print(f"{DIM}    Get yours at: console.anthropic.com{NC}\n")
        key = input(f"{C}Enter your API key (sk-ant-...): {NC}").strip()
        if not key:
            print(f"{R}[!] No key provided. Exiting.{NC}")
            sys.exit(1)
        os.environ["ANTHROPIC_API_KEY"] = key
        # Save to .env
        with open(env_path, "a") as f:
            f.write(f"\nANTHROPIC_API_KEY={key}\n")
        print(f"{G}[+] API key saved to .env{NC}\n")

def main():
    banner()
    
    print(f"  {DIM}Installing/checking dependencies...{NC}")
    ensure_deps()
    print(f"  {G}[+] Dependencies ready{NC}\n")
    
    check_api_key()

    print(f"  {W}How would you like to run DarkAI?{NC}\n")
    print(f"  {C}[1]{NC} GUI  — Browser interface at http://localhost:5000")
    print(f"  {C}[2]{NC} CLI  — Terminal chat mode\n")
    
    while True:
        choice = input(f"  {C}Enter choice (1 or 2): {NC}").strip()
        if choice in ["1", "2"]:
            break
        print(f"  {Y}Please enter 1 or 2{NC}")

    if choice == "1":
        # GUI mode
        port = 5000
        local_ip = get_local_ip()
        
        print(f"\n  {G}[+] Starting GUI mode...{NC}")
        print(f"""
  {C}╔════════════════════════════════════════╗
  ║  {W}DarkAI is running!{NC}{C}                   ║
  ║                                        ║
  ║  Local:    {G}http://localhost:{port}{NC}{C}       ║
  ║  Network:  {G}http://{local_ip}:{port}{NC}{C}   ║
  ║                                        ║
  ║  {DIM}Press CTRL+C to stop{NC}{C}                 ║
  ╚════════════════════════════════════════╝{NC}
""")
        # Auto-open browser
        try:
            subprocess.Popen(["xdg-open", f"http://localhost:{port}"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        
        # Start server
        os.environ["PORT"] = str(port)
        import server
        server.app.run(host="0.0.0.0", port=port, debug=False)

    elif choice == "2":
        # CLI mode
        print(f"\n  {G}[+] Starting CLI mode...{NC}\n")
        import cli
        cli.main()

if __name__ == "__main__":
    main()
