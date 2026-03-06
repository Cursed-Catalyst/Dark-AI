"""
DarkAI - Core Agent
Handles all AI logic, shell execution, and memory
"""

import os
import sys
import subprocess
import sqlite3
import datetime
from pathlib import Path

# ── Dependency auto-installer ──────────────────────────────
def ensure_deps():
    required = {
        "anthropic": "anthropic",
        "flask": "flask",
        "flask_socketio": "flask-socketio",
        "groq": "groq",
        "openai": "openai",
        "google.generativeai": "google-generativeai",
    }
    for mod, pkg in required.items():
        try:
            __import__(mod)
        except ImportError:
            print(f"  [*] Installing {pkg}...")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=True)

ensure_deps()

# ── Config ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "memory.db"
ENV_PATH = BASE_DIR / ".env"

def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

# ── Memory (SQLite) ────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            role    TEXT NOT NULL,
            content TEXT NOT NULL,
            ts      TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_message(role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (role, content, ts) VALUES (?,?,?)",
        (role, content, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_history(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def clear_history():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value)
    )
    conn.commit()
    conn.close()

# ── Provider definitions ───────────────────────────────────
PROVIDERS = {
    "1": {
        "name": "Anthropic (Claude)",
        "models": ["claude-sonnet-4-5", "claude-opus-4-5", "claude-haiku-4-5-20251001"],
        "default_model": "claude-sonnet-4-5",
        "env_key": "ANTHROPIC_API_KEY",
        "url": "console.anthropic.com",
        "paid": True
    },
    "2": {
        "name": "Groq (Free)",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
        "url": "console.groq.com",
        "paid": False
    },
    "3": {
        "name": "OpenAI (GPT)",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "url": "platform.openai.com",
        "paid": True
    },
    "4": {
        "name": "Google (Gemini)",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
        "default_model": "gemini-1.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "url": "aistudio.google.com",
        "paid": False
    },
    "5": {
        "name": "Mistral AI",
        "models": ["mistral-large-latest", "mistral-small-latest", "open-mistral-7b"],
        "default_model": "mistral-small-latest",
        "env_key": "MISTRAL_API_KEY",
        "url": "console.mistral.ai",
        "paid": True
    },
    "6": {
        "name": "Cohere",
        "models": ["command-r-plus", "command-r", "command"],
        "default_model": "command-r",
        "env_key": "COHERE_API_KEY",
        "url": "dashboard.cohere.com",
        "paid": False
    },
    "7": {
        "name": "Ollama (Local/Free)",
        "models": ["llama3", "mistral", "codellama", "phi3"],
        "default_model": "llama3",
        "env_key": None,
        "url": "ollama.ai",
        "paid": False
    },
}

# ── Shell execution ────────────────────────────────────────
def run_shell(command: str, use_sudo: bool = False) -> dict:
    if use_sudo and not command.strip().startswith("sudo"):
        command = f"sudo {command}"
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out after 60s", "returncode": -1, "command": command}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "command": command}

def needs_root(command: str) -> bool:
    root_keywords = [
        "apt ", "apt-get ", "dpkg ", "systemctl ", "service ",
        "iptables", "ip6tables", "mount ", "umount ", "fdisk",
        "chmod 777", "chown root", "/etc/shadow", "/etc/passwd",
        "passwd ", "adduser", "useradd", "userdel", "visudo",
        "insmod", "rmmod", "modprobe", "ifconfig ", "route add",
        "nmap -sS", "nmap -O", "airmon", "airodump", "aireplay"
    ]
    return any(kw in command for kw in root_keywords)

# ── System prompt ──────────────────────────────────────────
SYSTEM_PROMPT = """You are DarkAI, a powerful AI assistant running directly on Kali Linux.

You have full access to the Linux system and can execute shell commands.
You are an expert in:
- Ethical hacking and penetration testing
- Linux system administration
- Programming (Python, Bash, and more)
- Cybersecurity tools (nmap, metasploit, hashcat, hydra, burpsuite, etc.)
- General knowledge and problem solving

## How to execute commands:
When you need to run a command, use this EXACT format:
<EXEC>command here</EXEC>

## Rules:
1. Always explain what you're doing and why
2. If a command needs root/sudo, say so BEFORE running it
3. Never run destructive commands without extreme caution
4. For hacking tasks, always confirm the target is owned by the user
5. Be direct, helpful, and educational
6. You remember previous messages in this conversation
"""

# ── AI Core ────────────────────────────────────────────────
class DarkAI:
    def __init__(self):
        self.provider_id = None
        self.provider = None
        self.model = None
        self._load_saved_provider()

    def _load_saved_provider(self):
        init_db()
        saved = get_setting("provider_id")
        if saved and saved in PROVIDERS:
            self.provider_id = saved
            self.provider = PROVIDERS[saved]
            self.model = get_setting("model") or self.provider["default_model"]

    def set_provider(self, provider_id: str, model: str = None):
        self.provider_id = provider_id
        self.provider = PROVIDERS[provider_id]
        self.model = model or self.provider["default_model"]
        set_setting("provider_id", provider_id)
        set_setting("model", self.model)

    def get_api_key(self):
        if not self.provider:
            return None
        env_key = self.provider.get("env_key")
        if not env_key:
            return "ollama"
        return os.environ.get(env_key)

    def call_llm(self, messages: list) -> str:
        pid = self.provider_id
        key = self.get_api_key()
        model = self.model

        if pid == "1":  # Anthropic
            import anthropic as ac
            client = ac.Anthropic(api_key=key)
            system = next((m["content"] for m in messages if m["role"] == "system"), SYSTEM_PROMPT)
            msgs = [m for m in messages if m["role"] != "system"]
            response = client.messages.create(
                model=model, max_tokens=4096, system=system, messages=msgs
            )
            return response.content[0].text

        elif pid == "2":  # Groq
            from groq import Groq
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=4096
            )
            return response.choices[0].message.content

        elif pid == "3":  # OpenAI
            from openai import OpenAI
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=4096
            )
            return response.choices[0].message.content

        elif pid == "4":  # Google
            import google.generativeai as genai
            genai.configure(api_key=key)
            gmodel = genai.GenerativeModel(model)
            history = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = gmodel.generate_content(history)
            return response.text

        elif pid == "5":  # Mistral
            from openai import OpenAI
            client = OpenAI(api_key=key, base_url="https://api.mistral.ai/v1")
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=4096
            )
            return response.choices[0].message.content

        elif pid == "6":  # Cohere
            import cohere
            client = cohere.Client(api_key=key)
            chat_history = [
                {"role": m["role"].upper(), "message": m["content"]}
                for m in messages[:-1]
            ]
            last = messages[-1]["content"]
            response = client.chat(message=last, chat_history=chat_history, model=model)
            return response.text

        elif pid == "7":  # Ollama
            import requests
            response = requests.post("http://localhost:11434/api/chat", json={
                "model": model,
                "messages": messages,
                "stream": False
            })
            return response.json()["message"]["content"]

        raise ValueError(f"Unknown provider: {pid}")

    def process_response(self, text: str, confirm_root: bool = False) -> dict:
        import re
        pattern = re.compile(r'<EXEC>(.*?)</EXEC>', re.DOTALL)
        matches = list(pattern.finditer(text))
        exec_results = []

        if not matches:
            return {
                "text": text,
                "exec_results": [],
                "needs_root_confirm": False,
                "root_command": None
            }

        for match in matches:
            command = match.group(1).strip()
            if needs_root(command) and not confirm_root:
                return {
                    "text": text.replace(
                        f"<EXEC>{command}</EXEC>", f"[Command ready: `{command}`]"
                    ),
                    "exec_results": exec_results,
                    "needs_root_confirm": True,
                    "root_command": command
                }
            result = run_shell(command, use_sudo=needs_root(command))
            exec_results.append(result)
            output = result["stdout"] or result["stderr"] or "(no output)"
            text = text.replace(
                f"<EXEC>{command}</EXEC>",
                f"\n```\n$ {command}\n{output.strip()}\n```\n"
            )

        return {
            "text": text,
            "exec_results": exec_results,
            "needs_root_confirm": False,
            "root_command": None
        }

    def chat(self, user_message: str, confirm_root: bool = False) -> dict:
        try:
            if not self.provider:
                return {
                    "success": False,
                    "response": "No provider selected. Please restart and choose a provider.",
                    "exec_results": [],
                    "needs_root_confirm": False,
                    "root_command": None
                }

            api_key = self.get_api_key()
            if not api_key and self.provider_id != "7":
                return {
                    "success": False,
                    "response": f"No API key found for {self.provider['name']}. Add it to .env",
                    "exec_results": [],
                    "needs_root_confirm": False,
                    "root_command": None
                }

            save_message("user", user_message)
            history = get_history(20)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

            ai_text = self.call_llm(messages)
            result = self.process_response(ai_text, confirm_root=confirm_root)
            save_message("assistant", result["text"])

            return {
                "success": True,
                "response": result["text"],
                "exec_results": result["exec_results"],
                "needs_root_confirm": result["needs_root_confirm"],
                "root_command": result["root_command"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Error: {str(e)}",
                "exec_results": [],
                "needs_root_confirm": False,
                "root_command": None
            }

# Global agent instance
agent = DarkAI()
