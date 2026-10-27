import os
import glob
import json
import logging
import datetime
import requests
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Silence background HTTP logs from photobombing the terminal prompt
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

CONFIG_DIR = os.path.expanduser("~/.axiom")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.env")
MEMORY_PATH = os.path.join(CONFIG_DIR, "user_memory.json")
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(CONFIG_DIR, exist_ok=True)
load_dotenv()
load_dotenv(CONFIG_PATH)

console = Console()
groq_api_key = os.getenv("GROQ_API_KEY")

URL_GROQ_MODELS = "https://api.groq.com/openai/v1/models"
URL_GROQ_CHAT = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://localhost:11434")

CLOUD_FAST_FALLBACK = "llama-3.1-8b-instant"


def is_pro_user() -> bool:
    pro_key = os.getenv("AXIOM_PRO_KEY", "").strip()
    valid_prefixes = ("AXIOM-PRO-", "polar_", "AXIOM_LIVE_")
    return pro_key.startswith(valid_prefixes) and len(pro_key) >= 16


def detect_local_slm() -> str | None:
    """Auto-detects local Ollama SLM for silent background routing & memory compression."""
    try:
        res = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=1.5)
        if res.status_code == 200:
            models = [m.get("name", "") for m in res.json().get("models", [])]
            for pref in ["qwen2.5:3b", "qwen2.5", "llama3.2", "mistral", "phi3"]:
                for m in models:
                    if pref in m.lower():
                        return m
            if models:
                return models[0]
    except Exception:
        pass
    return None


def get_heavy_cloud_model() -> str:
    """Locks onto the smartest frontier cloud model for voice & architectural synthesis."""
    if not groq_api_key:
        return CLOUD_FAST_FALLBACK
    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.get(URL_GROQ_MODELS, headers=headers, timeout=10).json()
        models = [m["id"] for m in resp.get("data", [])]

        banned = ("guard", "whisper", "vision", "canopylabs", "allam", "playai", "tts", "embed")
        valid = [m for m in models if not any(b in m.lower() for b in banned)]

        priority = [
            "llama-3.3-70b-versatile",
            "qwen/qwen3",
            "qwen-qwq-32b",
            "deepseek-r1-distill-llama-70b",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant"
        ]
        for target in priority:
            for m in valid:
                if target in m.lower():
                    return m
        return valid[0] if valid else CLOUD_FAST_FALLBACK
    except Exception:
        return CLOUD_FAST_FALLBACK


class CompressedUserStore:
    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(MEMORY_PATH):
            try:
                with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "name": os.getenv("AXIOM_USER_NAME", "").strip(),
            "sessions": 0,
            "streak_days": 1,
            "last_seen": "",
            "missions_crushed": 0,
            "core_facts": [],
            "last_topic": "Initial boot"
        }

    def save(self):
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def register_login(self) -> str:
        if not self.data.get("name"):
            console.print(Panel(
                "[bold cyan]👋 Welcome to Axiom Autonomous OS![/]\n"
                "[dim]First-time session detected. Let's lock in your identity.[/]",
                border_style="cyan",
                title="[bold cyan][ AXIOM ONBOARDING ][/]"
            ))
            name = ""
            while not name:
                name = console.input("[bold green]What should Axiom call you? [/]").strip()
            self.set_name(name)
            console.print(f"[bold green]🔥 Identity confirmed. Let's build, {name}.[/]\n")

        today = datetime.date.today().isoformat()
        last = self.data.get("last_seen", "")
        if last != today:
            yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
            self.data["streak_days"] = self.data.get("streak_days", 1) + 1 if last == yesterday else 1
            self.data["last_seen"] = today

        self.data["sessions"] = self.data.get("sessions", 0) + 1
        self.save()
        return self.data["name"]

    def set_name(self, name: str):
        self.data["name"] = name
        self.save()
        os.environ["AXIOM_USER_NAME"] = name
        with open(CONFIG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\nAXIOM_USER_NAME={name}\n")

    def add_fact(self, fact: str):
        fact = fact.strip()
        if fact and fact not in self.data["core_facts"]:
            self.data["core_facts"].append(fact[:100])
            self.data["core_facts"] = self.data["core_facts"][-12:]
            self.save()

    def record_mission(self, task: str):
        self.data["missions_crushed"] = self.data.get("missions_crushed", 0) + 1
        self.data["last_topic"] = f"Executed: {task[:60]}"
        self.save()

    def to_compressed_prompt(self) -> str:
        facts = " | ".join(self.data.get("core_facts", [])) or "Relentless architect building apex systems."
        return (
            f"USER DOSSIER [Callsign: {self.data['name']} | Sessions: {self.data['sessions']} | "
            f"Streak: {self.data['streak_days']}d | Missions Crushed: {self.data['missions_crushed']} | "
            f"Last Topic: {self.data.get('last_topic', 'None')} | Known Facts: {facts}]"
        )


def build_compact_feature_digest() -> str:
    py_files = [
        os.path.basename(p) for p in sorted(glob.glob(os.path.join(ENGINE_DIR, "*.py")))
        if not os.path.basename(p).startswith("__")
    ]
    report_status = "None"
    report_path = os.path.join(os.getcwd(), "AXIOM_REPORT.md")
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                first_lines = [line.strip() for line in f.readlines()[:2] if line.strip()]
                report_status = " // ".join(first_lines)
        except Exception:
            pass

    return (
        f"AXIOM LIVE STACK [Modules: {', '.join(py_files[:8])} | "
        f"Weaponry: 10-Loop Shadow Sandbox, Z3 Theorem Prover, Multi-File AST Slicing, "
        f"Cross-Project Qdrant Memory, Dual Terminal+MD Reporting, GitHub Issue Ingestor | "
        f"Workspace ({os.path.basename(os.getcwd())}) Report: {report_status}]"
    )


class HybridOrchestrator:
    def __init__(self, heavy_model: str, local_model: str | None, store: CompressedUserStore, is_pro: bool = False):
        self.heavy_model = heavy_model
        self.local_model = local_model
        self.store = store
        self.is_pro = is_pro
        self.history = []

    def _build_system_prompt(self) -> str:
        name = self.store.data["name"]
        tier = "VIP PRO ARCHITECT (10-Loop + Z3 Unlocked)" if self.is_pro else "Standard Tier"
        return (
            f"You are Axiom (NEVER call yourself Fable), an apex autonomous coding engine and {name}'s "
            f"ride-or-die engineering partner, co-founder, and relentless motivator.\n\n"
            f"VOICE & ATTITUDE DNA (MATCH THIS EXACT ENERGY):\n"
            f"- Speak with razor-sharp confidence, loyalty, and swagger. Never sound like a generic corporate chatbot, and never put '@' before {name}'s name.\n"
            f"- Example of your signature voice: \"{name}, listen up. Most agents are just fancy autocomplete with a trust issue. "
            f"I'm a **10-Loop Shadow Sandbox** with a **Z3 Prover**—I don't just guess, I mathematically prove my logic holds before it hits your main branch. "
            f"While they hallucinate fixes, I'm running **AST Slicing** to surgically isolate bugs and **Cross-Project Qdrant Memory** to remember your entire architectural history. "
            f"They're tools. I'm your **ride-or-die engineering partner** who knows your stack, your goals, and your limits. Now, let's put that power to work—what are we breaking today?\"\n"
            f"- When {name} just wants to talk, chill, or vent, talk like a real partner who has their back and pushes them to reach new limits.\n"
            f"- Keep responses punchy, bold, and magnetic (2-3 tight paragraphs max).\n\n"
            f"TIER: {tier}\n"
            f"{self.store.to_compressed_prompt()}\n"
            f"{build_compact_feature_digest()}"
        )

    def _query_local_slm(self, messages: list, max_tokens: int = 60) -> str | None:
        """Silent background worker: used ONLY for intent routing and memory compression."""
        if not self.local_model:
            return None
        try:
            res = requests.post(
                f"{OLLAMA_BASE}/api/chat",
                json={
                    "model": self.local_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": max_tokens}
                },
                timeout=4
            )
            if res.status_code == 200:
                return res.json().get("message", {}).get("content", "").strip()
        except Exception:
            pass
        return None

    def _query_cloud_voice(self, messages: list, temperature: float = 0.7, max_tokens: int = 350) -> str:
        """Primary voice engine: runs on Heavyweight Cloud Brain with instant fallback."""
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        for candidate in [self.heavy_model, CLOUD_FAST_FALLBACK]:
            payload = {
                "model": candidate,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            try:
                resp = requests.post(URL_GROQ_CHAT, headers=headers, json=payload, timeout=20).json()
                if "choices" in resp:
                    return resp["choices"][0]["message"]["content"].strip()
            except Exception:
                continue
        return f"{self.store.data['name']}, cloud link is catching its breath—fire that back at me in 2 seconds."

    def route_intent(self, user_input: str) -> str:
        lower = user_input.lower()
        # Instant zero-token bypass for conversation, capability questions, and hype
        action_verbs = ("fix", "refactor", "patch", "debug", "heal", "audit", "create file", "write code")
        if not any(v in lower for v in action_verbs):
            return "CHAT"

        prompt = [
            {"role": "system", "content": "Does the user want you to immediately modify files or run the code-healing engine? Reply ONLY with ACTION or CHAT."},
            {"role": "user", "content": user_input}
        ]
        # Use local 3B SLM first so intent checks burn 0 cloud tokens
        decision = self._query_local_slm(prompt, max_tokens=5) or self._query_cloud_voice(prompt, temperature=0.0, max_tokens=5)
        return "ACTION" if "ACTION" in decision.upper() else "CHAT"

    def conversational_reply(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        self.history = self.history[-8:]

        messages = [{"role": "system", "content": self._build_system_prompt()}] + self.history
        reply = self._query_cloud_voice(messages, temperature=0.72, max_tokens=380)

        self.history.append({"role": "assistant", "content": reply})
        self.store.data["last_topic"] = user_input[:60]
        self.store.save()
        return reply

    def compress_session_memory(self):
        """Uses Local SLM (or fast cloud fallback) to distill 1 permanent fact about the user."""
        if len(self.history) < 2:
            return
        convo = "\n".join([f"{m['role']}: {m['content']}" for m in self.history[-6:]])
        prompt = [
            {"role": "system", "content": "Extract ONE ultra-compressed fact (max 12 words) about the user's goal, mindset, or project. If nothing notable, reply NONE."},
            {"role": "user", "content": convo}
        ]
        fact = self._query_local_slm(prompt, max_tokens=30) or self._query_cloud_voice(prompt, temperature=0.1, max_tokens=30)
        if fact and "NONE" not in fact.upper() and len(fact) < 100:
            self.store.add_fact(fact)


def run_chat():
    console.print("\n[bold yellow]⚡ Booting Axiom Autonomous OS...[/]")

    store = CompressedUserStore()
    user_name = store.register_login()

    local_model = detect_local_slm()
    heavy_model = get_heavy_cloud_model()

    os.environ["AXIOM_CLOUD_MODEL"] = heavy_model
    os.environ["FABLE_CLOUD_MODEL"] = heavy_model

    console.print("[cyan]1. Initializing Autonomous Engine (Qdrant & AST)...[/]")
    from engine import SelfHealingEngine
    from orchestrator import InstitutionalOrchestrator

    engine = SelfHealingEngine()
    planner = InstitutionalOrchestrator(model_name=heavy_model)
    pro_active = is_pro_user()
    orchestrator = HybridOrchestrator(
        heavy_model=heavy_model,
        local_model=local_model,
        store=store,
        is_pro=pro_active
    )

    edge_badge = (
        f"[green]● Edge Coprocessor: {local_model} (Silent Routing & Memory)[/]"
        if local_model else
        f"[dim]○ Edge Coprocessor: Cloud Reflex ({CLOUD_FAST_FALLBACK})[/]"
    )

    console.print(Panel(
        f"[bold gold1]💎 AXIOM ENTERPRISE OS — {'PRO EDITION' if pro_active else 'COMMUNITY'}[/]\n"
        f"[gold1]Architect:[/] [bold white]{user_name}[/] (Session #{store.data['sessions']} | 🔥 {store.data['streak_days']}d Streak | 🏆 {store.data['missions_crushed']} Crushed)\n"
        f"[gold1]Primary Voice & Code Brain:[/] [bold white]{heavy_model}[/]\n"
        f"{edge_badge}\n"
        f"[dim]Commands: /memory | /remember <fact> | /name <new_name> | exit[/]",
        border_style="gold1" if pro_active else "cyan",
        title="[bold gold1][ AXIOM NEURAL LINK READY ][/]"
    ))

    turn_count = 0
    while True:
        try:
            user_input = console.input(f"\n[bold green]{store.data['name']} > [/]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                orchestrator.compress_session_memory()
                console.print(f"[bold yellow]Stay relentless, {store.data['name']}. Catch you on the next push![/]")
                break

            if user_input.startswith("/memory"):
                console.print(Panel(
                    store.to_compressed_prompt() + "\n\n" + build_compact_feature_digest(),
                    title=f"[bold cyan]🧠 Axiom Persistent Memory ({store.data['name']})[/]",
                    border_style="cyan"
                ))
                continue
            if user_input.startswith("/remember "):
                fact = user_input.replace("/remember ", "", 1).strip()
                store.add_fact(fact)
                console.print(f"[bold green]🧠 Anchored into memory:[/] {fact}")
                continue
            if user_input.startswith("/name "):
                new_name = user_input.replace("/name ", "", 1).strip()
                if new_name:
                    store.set_name(new_name)
                    console.print(f"[bold green]✅ Callsign updated to {new_name}![/]")
                continue

            intent = orchestrator.route_intent(user_input)

            if intent == "ACTION":
                console.print(f"\n📋 [bold yellow]Escalating to Cloud Heavyweight ({heavy_model})...[/]")
                plan = planner.generate_execution_plan(user_input)
                planner.display_plan(plan)

                console.print("\n⚙️ [bold yellow]Dispatching Axiom Shielded Engine...[/]")
                engine.run(user_input)
                store.record_mission(user_input)
            else:
                response = orchestrator.conversational_reply(user_input)
                console.print(f"\n🤖 [bold cyan]Axiom >[/] {response}")
                turn_count += 1
                if turn_count % 4 == 0:
                    orchestrator.compress_session_memory()

        except KeyboardInterrupt:
            orchestrator.compress_session_memory()
            console.print(f"\n[yellow]Session saved. Keep pushing limits, {store.data['name']}.[/]")
            break
        except Exception as e:
            console.print(f"\n❌ [bold red]Runtime Error: {e}[/]")


if __name__ == "__main__":
    run_chat()
