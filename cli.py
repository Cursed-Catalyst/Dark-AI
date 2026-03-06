#!/usr/bin/env python3
"""
DarkAI - Command Line Interface
Usage: python cli.py  (or launched from darkai.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    print("""
\033[0;36m  ██╗  ██╗ █████╗ ██╗     ██╗     █████╗ ██╗
  ██║ ██╔╝██╔══██╗██║     ██║    ██╔══██╗██║
  █████╔╝ ███████║██║     ██║    ███████║██║
  ██╔═██╗ ██╔══██║██║     ██║    ██╔══██║██║
  ██║  ██╗██║  ██║███████╗██║    ██║  ██║██║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝    ╚═╝  ╚═╝╚═╝\033[0m
\033[0;32m  Your Kali Linux AI Assistant — Powered by DarkAI\033[0m
\033[0;90m  Type 'help' for commands, 'exit' to quit\033[0m
""")


def print_help():
    print("""
\033[1mCommands:\033[0m
  help          Show this help
  clear         Clear conversation memory
  exit / quit   Exit

\033[1mJust type naturally:\033[0m
  "scan 192.168.1.1 for open ports"
  "crack this hash: 5f4dcc3b5aa765d61d8327deb882cf99"
  "what processes are running?"
  "write a python script that..."
  "explain what SQL injection is"
""")


def format_exec_results(results: list) -> str:
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

    # Import the global agent instance from agent.py
    from agent import agent, clear_history

    if not agent.provider:
        print("\033[0;31m[✗] No provider configured. Please run darkai.py first.\033[0m")
        sys.exit(1)

    print(f"\033[0;32m[+] DarkAI ready ({agent.provider['name']} / {agent.model}). How can I help?\033[0m\n")

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
            clear_history()
            print("\033[0;32m[+] Memory cleared.\033[0m")
            continue

        print("\033[0;90m[thinking...]\033[0m")

        response = agent.chat(user_input)

        if not response["success"]:
            print(f"\033[0;31m[Error]\033[0m {response['response']}\n")
            continue

        # Handle root confirmation
        if response["needs_root_confirm"]:
            print(f"\n\033[0;33m[!] Root required for: {response['root_command']}\033[0m")
            confirm = input("\033[1;33m[?] Allow sudo? (y/N): \033[0m").strip().lower()
            if confirm == "y":
                response = agent.chat(user_input, confirm_root=True)
            else:
                print("\033[0;90m[Cancelled — skipping root command]\033[0m\n")
                continue

        # Print command outputs
        exec_output = format_exec_results(response.get("exec_results", []))
        if exec_output:
            print(exec_output)

        # Print AI response
        if response["response"]:
            print(f"\n\033[1;32m[DarkAI]\033[0m {response['response']}\n")


if __name__ == "__main__":
    main()
