#!/usr/bin/env python3
"""
DarkAI - Launcher
Choose your AI provider, then GUI or CLI mode
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
    packages = {
        "anthropic": "anthropic",
        "flask": "flask",
        "flask_socketio": "flask-socketio",
        "groq": "groq",
        "openai": "openai",
    }
    for mod, pkg in packages.items():
        try:
            __import__(mod)
        except ImportError:
            print(f"  [*] Installing {pkg}...")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=True)

C    = "\033[0;36m"
G    = "\033[0;32m"
Y    = "\033[1;33m"
W    = "\033[1;37m"
R    = "\033[0;31m"
DIM  = "\033[2m"
NC   = "\033[0m"
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
║         {DIM}Kali Linux AI Agent v1.0{NC}{C}             ║
╚══════════════════════════════════════════════╝{NC}
""")

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path).readlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def select_provider():
    from agent import PROVIDERS, set_setting

    print(f"  {W}{BOLD}Select your AI Provider:{NC}\n")

    for pid, info in PROVIDERS.items():
        free_tag = f"{G}FREE{NC}" if not info["paid"] else f"{DIM}paid{NC}"
        print(f"  {C}[{pid}]{NC} {info['name']}  {free_tag}")
        print(f"      {DIM}Get key: {info['url']}{NC}")
        print()

    while True:
        choice = input(f"  {C}Enter choice (1-7): {NC}").strip()
        if choice in PROVIDERS:
            break
        print(f"  {Y}Please enter a number between 1 and 7{NC}")

    provider = PROVIDERS[choice]
    print(f"\n  {G}[+] Selected: {provider['name']}{NC}")

    # Show models
    print(f"\n  {W}Select model:{NC}")
    for i, m in enumerate(provider["models"], 1):
        default = f" {G}(default){NC}" if m == provider["default_model"] else ""
        print(f"  {C}[{i}]{NC} {m}{default}")

    model_choice = input(f"\n  {C}Enter model number (or Enter for default): {NC}").strip()
    if model_choice.isdigit() and 1 <= int(model_choice) <= len(provider["models"]):
        model = provider["models"][int(model_choice) - 1]
    else:
        model = provider["default_model"]

    print(f"  {G}[+] Model: {model}{NC}\n")

    # Check/get API key
    env_key = provider.get("env_key")
    if env_key and choice != "7":
        existing = os.environ.get(env_key)
        if not existing:
            print(f"  {Y}[!] No API key found for {provider['name']}{NC}")
            print(f"  {DIM}    Get yours at: {provider['url']}{NC}\n")
            key = input(f"  {C}Enter API key: {NC}").strip()
            if key:
                os.environ[env_key] = key
                env_path = os.path.join(os.path.dirname(__file__), ".env")
                with open(env_path, "a") as f:
                    f.write(f"\n{env_key}={key}\n")
                print(f"  {G}[+] API key saved!{NC}\n")
            else:
                print(f"  {R}[!] No key provided.{NC}\n")
        else:
            print(f"  {G}[+] API key found ✓{NC}\n")

    return choice, model

def main():
    banner()

    print(f"  {DIM}Checking dependencies...{NC}")
    ensure_deps()
    load_env()
    print(f"  {G}[+] Dependencies ready{NC}\n")

    # Import agent after deps are ready
    from agent import agent

    # Check if provider already saved
    if agent.provider:
        print(f"  {DIM}Using saved provider: {agent.provider['name']} / {agent.model}{NC}")
        change = input(f"  {C}Change provider? [y/N]: {NC}").strip().lower()
        if change == 'y':
            provider_id, model = select_provider()
            agent.set_provider(provider_id, model)
    else:
        provider_id, model = select_provider()
        agent.set_provider(provider_id, model)

    # Choose GUI or CLI
    print(f"  {W}{BOLD}How would you like to run DarkAI?{NC}\n")
    print(f"  {C}[1]{NC} GUI  — Browser interface at http://localhost:5000")
    print(f"  {C}[2]{NC} CLI  — Terminal chat mode\n")

    while True:
        choice = input(f"  {C}Enter choice (1 or 2): {NC}").strip()
        if choice in ["1", "2"]:
            break
        print(f"  {Y}Please enter 1 or 2{NC}")

    if choice == "1":
        port = 5000
        local_ip = get_local_ip()
        print(f"""
  {G}[+] Starting GUI mode...{NC}
  {C}╔════════════════════════════════════════╗
  ║  {W}DarkAI is running!{NC}{C}                   ║
  ║                                        ║
  ║  Local:    {G}http://localhost:{port}{NC}{C}       ║
  ║  Network:  {G}http://{local_ip}:{port}{NC}{C}  ║
  ║                                        ║
  ║  {DIM}Press CTRL+C to stop{NC}{C}                 ║
  ╚════════════════════════════════════════╝{NC}
""")
        try:
            subprocess.Popen(["xdg-open", f"http://localhost:{port}"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

        os.environ["PORT"] = str(port)
        import server
        server.app.run(host="0.0.0.0", port=port, debug=False)

    elif choice == "2":
        print(f"\n  {G}[+] Starting CLI mode...{NC}\n")
        import cli
        cli.main()

if __name__ == "__main__":
    main()
