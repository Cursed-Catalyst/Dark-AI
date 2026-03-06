"""
agent.py — Core AI Agent
Handles Claude API calls, shell execution, memory, and root escalation logic.
Compatible with Python 3.8+
"""

import os
import subprocess
import sqlite3
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Anthropic client (lazy import so we can show helpful error) ────────────
try:
    import anthropic
    _ANTHROPIC_OK = True
except ImportError:
    _ANTHROPIC_OK = False

DB_PATH = Path(__file__).parent / "memory.db"
SYSTEM_PROMPT = """You are KaliAI — a powerful, expert AI assistant running directly on a Kali Linux machine.

You have full access to the Linux shell and can execute any command the user requests.
You are an expert in:
- Ethical hacking and penetration testing (nmap, metasploit, hashcat, hydra, sqlmap, gobuster, nikto, etc.)
- Linux system administration
- Programming (Python, Bash, Ruby, C, etc.)
- Networking and security
- CTF challenges and vulnerability research
- General knowledge and conversation

SHELL EXECUTION:
When you need to run a command, output it in this exact format:
<execute>command here</execute>

You can chain multiple commands:
<execute>nmap -sV 192.168.1.1</execute>

ROOT ESCALATION:
If a task requires root and the user hasn't confirmed, output:
<need_root>reason why root is needed</need_root>

RULES:
- Always explain what you're doing and why
- After running a command, explain the output
- For hacking tasks, always confirm the target is owned by the user or they have permission
- Be conversational and helpful for general questions
- If unsure about something, say so
- Never run destructive commands without explicit user confirmation

You are running on: Kali Linux
Current user: {username}
Root available: {root_available}
"""


class Memory:
    """Simple SQLite-backed conversation memory."""

    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add(self, role: str, content: str):
        self.conn.execute(
            "INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_recent(self, limit: int = 20) -> list:
        cursor = self.conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def clear(self):
        self.conn.execute("DELETE FROM messages")
        self.conn.commit()


class ShellExecutor:
    """Executes shell commands safely with sudo support."""

    def __init__(self):
        self.use_root = False
        self.username = os.environ.get("USER", os.environ.get("LOGNAME", "kali"))

    def run(self, command: str, force_root: bool = False) -> dict:
        """Run a shell command, return stdout/stderr/returncode."""
        try:
            if force_root or self.use_root:
                if not command.strip().startswith("sudo"):
                    command = f"sudo {command}"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                executable="/bin/bash"
            )
            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
                "command": command,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out after 60 seconds.",
                "returncode": -1,
                "command": command,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "command": command,
                "success": False
            }

    def check_sudo(self) -> bool:
        """Check if sudo is available without password."""
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0


class KaliAI:
    """Main AI agent — orchestrates Claude, shell, and memory."""

    def __init__(self, api_key: str):
        if not _ANTHROPIC_OK:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.memory = Memory()
        self.shell = ShellExecutor()
        self.pending_root_request = None  # stores reason when root is needed

    def _build_system(self) -> str:
        return SYSTEM_PROMPT.format(
            username=self.shell.username,
            root_available=self.shell.check_sudo()
        )

    def _parse_response(self, text: str) -> dict:
        """Parse Claude's response for execute/need_root tags."""
        commands = re.findall(r'<execute>(.*?)</execute>', text, re.DOTALL)
        root_needed = re.findall(r'<need_root>(.*?)</need_root>', text, re.DOTALL)

        # Clean text for display
        clean = re.sub(r'<execute>.*?</execute>', '', text, flags=re.DOTALL)
        clean = re.sub(r'<need_root>.*?</need_root>', '', clean, flags=re.DOTALL)
        clean = clean.strip()

        return {
            "text": clean,
            "commands": [c.strip() for c in commands],
            "root_needed": root_needed[0].strip() if root_needed else None
        }

    def _execute_commands(self, commands: list) -> list:
        """Run a list of shell commands and return results."""
        results = []
        for cmd in commands:
            result = self.shell.run(cmd)
            results.append(result)
        return results

    def chat(self, user_input: str, root_confirmed: bool = False) -> dict:
        """
        Send a message and get a response.
        Returns dict with: text, commands, command_results, needs_root, root_reason
        """
        # Handle root confirmation
        if root_confirmed and self.pending_root_request:
            self.shell.use_root = True
            self.pending_root_request = None

        # Store user message
        self.memory.add("user", user_input)

        # Build messages for API
        messages = self.memory.get_recent(20)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                system=self._build_system(),
                messages=messages
            )
            raw_text = response.content[0].text
        except Exception as e:
            return {
                "text": f"Error communicating with Claude API: {str(e)}",
                "commands": [],
                "command_results": [],
                "needs_root": False,
                "root_reason": None,
                "error": True
            }

        # Parse response
        parsed = self._parse_response(raw_text)

        # Check if root is needed
        if parsed["root_needed"] and not self.shell.use_root:
            self.pending_root_request = parsed["root_needed"]
            self.memory.add("assistant", raw_text)
            return {
                "text": parsed["text"],
                "commands": [],
                "command_results": [],
                "needs_root": True,
                "root_reason": parsed["root_needed"],
                "error": False
            }

        # Execute commands if any
        command_results = []
        if parsed["commands"]:
            command_results = self._execute_commands(parsed["commands"])

            # Feed results back to Claude for explanation
            if command_results:
                results_text = "\n".join([
                    f"$ {r['command']}\n{r['stdout']}" +
                    (f"\nSTDERR: {r['stderr']}" if r['stderr'] else "") +
                    (f"\n[Exit code: {r['returncode']}]" if r['returncode'] != 0 else "")
                    for r in command_results
                ])

                # Get Claude to explain the output
                self.memory.add("assistant", raw_text)
                self.memory.add("user", f"Command output:\n{results_text}\n\nPlease explain the results.")

                try:
                    explain_response = self.client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=2048,
                        system=self._build_system(),
                        messages=self.memory.get_recent(20)
                    )
                    explanation = explain_response.content[0].text
                    self.memory.add("assistant", explanation)
                    parsed["text"] = parsed["text"] + "\n\n" + explanation if parsed["text"] else explanation
                except Exception:
                    pass
        else:
            self.memory.add("assistant", raw_text)

        return {
            "text": parsed["text"],
            "commands": parsed["commands"],
            "command_results": command_results,
            "needs_root": False,
            "root_reason": None,
            "error": False
        }

    def clear_memory(self):
        self.memory.clear()
        self.shell.use_root = False
        self.pending_root_request = None
