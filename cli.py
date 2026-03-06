#!/usr/bin/env python3
"""
cli.py — Command Line Interface for KaliAI
Usage: python cli.py
"""

import os
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    print("""
\033[0;36m  ██╗  ██╗ █████╗ ██╗     ██╗     █████╗ ██╗
  ██║ ██╔╝██╔══██╗██║     ██║    ██╔══██╗██║
  █████╔╝ ███████║██║     ██║    ███████║██║
  ██╔═██╗ ██╔══██║██║     ██║    ██╔══██║██║
  ██║  ██╗██║  ██║███████╗██║    ██║  ██║██║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝    ╚═╝  ╚═╝╚═╝\033[0m
\033[0;32m  Your Kali Linux AI Assistant — Powered by Claude\033[0m
\033[0;90m  Type 'help' for commands, 'exit' to quit\033[0m
""")

def print_help():
    print("""
\033[1mCommands:\033[0m
  help          Show this help
  clear         Clear conversation memory
  root on/off   Toggle root mode
  exit/quit     Exit

\033[1mJust type naturally:\033[0m
  "scan 192.168.1.1 for open ports"
  "crack this hash: 5f4dcc3b5aa765d61d8327deb882cf99"
  "what processes are running?"
  "write a python script that..."
  "explain what SQL injection is"
""")

def get_api_key() -> str:
    # Try env var first
    key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY_ANTHROPIC")
    if key:
        return key

    # Try .env file in agent-zero or home dir
    for env_path in [
        Path.home() / "agent-zero" / ".env",
        Path(__file__).parent / ".env",
        Path.home() / ".env"
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("API_KEY_ANTHROPIC=") or line.startswith("ANTHROPIC_API_KEY="):
                    val = line.split("=", 1)[1].strip()
                    if val and not val.startswith("sk-ant-YOUR"):
                        return val

    # Ask user
    print("\033[1;33m[?] Anthropic API key not found.\033[0m")
    key = input("Enter your API key (sk-ant-...): ").strip()
    return key


def format_command_results(results: list) -> str:
    if not results:
        return ""
    output = []
    for r in results:
        output.append(f"\n\033[0;90m$ {r['command']}\033[0m")
        if r['stdout']:
            output.append(f"\033[0;32m{r['stdout']}\033[0m")
        if r['stderr']:
            output.append(f"\033[0;31m{r['stderr']}\033[0m")
        if r['returncode'] != 0:
            output.append(f"\033[0;31m[Exit code: {r['returncode']}]\033[0m")
    return "\n".join(output)


def main():
    print_banner()

    api_key = get_api_key()
    if not api_key:
        print("\033[0;31m[✗] No API key provided. Exiting.\033[0m")
        sys.exit(1)

    try:
        from agent import KaliAI
        ai = KaliAI(api_key)
    except RuntimeError as e:
        print(f"\033[0;31m[✗] {e}\033[0m")
        print("Run: pip install anthropic")
        sys.exit(1)

    print("\033[0;32m[+] KaliAI ready. How can I help?\033[0m\n")

    while True:
        try:
            user_input = input("\033[1;36m[You]\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\033[0;90mGoodbye!\033[0m")
            break

        if not user_input:
            continue

        # Built-in commands
        if user_input.lower() in ("exit", "quit"):
            print("\033[0;90mGoodbye!\033[0m")
            break
        elif user_input.lower() == "help":
            print_help()
            continue
        elif user_input.lower() == "clear":
            ai.clear_memory()
            print("\033[0;32m[+] Memory cleared.\033[0m")
            continue
        elif user_input.lower() == "root on":
            ai.shell.use_root = True
            print("\033[0;33m[!] Root mode enabled.\033[0m")
            continue
        elif user_input.lower() == "root off":
            ai.shell.use_root = False
            print("\033[0;32m[+] Root mode disabled.\033[0m")
            continue

        print("\033[0;90m[thinking...]\033[0m")

        response = ai.chat(user_input)

        # Handle root request
        if response["needs_root"]:
            print(f"\n\033[0;33m[!] Root required: {response['root_reason']}\033[0m")
            confirm = input("\033[1;33m[?] Switch to root? (y/N): \033[0m").strip().lower()
            if confirm == "y":
                response = ai.chat(user_input, root_confirmed=True)
            else:
                print("\033[0;90m[Cancelled — continuing without root]\033[0m")
                continue

        # Print command outputs
        if response["command_results"]:
            print(format_command_results(response["command_results"]))

        # Print AI response
        if response["text"]:
            print(f"\n\033[1;32m[KaliAI]\033[0m {response['text']}\n")

        if response.get("error"):
            print(f"\033[0;31m[Error]\033[0m {response['text']}\n")


if __name__ == "__main__":
    main()
