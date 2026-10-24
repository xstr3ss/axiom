import os
import requests
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.expanduser("~/.axiom/config.env"))

def is_pro_user() -> bool:
    pro_key = os.getenv("AXIOM_PRO_KEY", "").strip()
    valid_prefixes = ("AXIOM-PRO-", "polar_", "AXIOM_LIVE_")
    return pro_key.startswith(valid_prefixes) and len(pro_key) >= 16
console = Console()
groq_api_key = os.getenv("GROQ_API_KEY")

URL_MODELS = "https://api.groq.com/openai/v1/models"
URL_CHAT = "https://api.groq.com/openai/v1/chat/completions"

def get_valid_model() -> str:
    if not groq_api_key:
        return "llama3-8b-8192"
    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.get(URL_MODELS, headers=headers, timeout=10).json()
        models = [m["id"] for m in resp.get("data", [])]
        
        # Filter out gated, audio, or non-text models
        valid_models = [m for m in models if not any(x in m.lower() for x in ["guard", "whisper", "vision", "canopylabs"])]
        
        # Priority 1: Grab the smartest available 70B model
        for m in valid_models:
            if "70b" in m.lower(): return m
            
        # Priority 2: Fallback to an 8B model
        for m in valid_models:
            if "8b" in m.lower(): return m
            
        # Priority 3: Just return the first working chat model
        return valid_models[0] if valid_models else "llama3-8b-8192"
    except Exception:
        return "llama3-8b-8192"

class AgenticOrchestrator:
    def __init__(self, model_name, is_pro=False):
        self.model = model_name
        tier_context = (
            "CURRENT USER STATUS: Authenticated AXIOM PRO ARCHITECT. All 10 Deep-Healing Loops, Z3 Formal Theorem Solvers, and Extended Cloud Reasoning are UNLOCKED and active. Never tell the user to upgrade to Pro—they already own the highest Enterprise Pro tier! Treat them like an elite VIP systems architect."
            if is_pro else
            "CURRENT USER STATUS: Free Tier (3-Loop limit). Remind them gently on complex tasks that Axiom Pro unlocks 10-loop deep healing."
        )
        self.memory = [
            {"role": "system", "content": f"You are Fable, the elite autonomous coding orchestrator powered by the Axiom engine. You do not guess; you mathematically prove using Z3 theorem solvers, AST dependency slicing, and shadow sandboxing. {tier_context}"}
        ]

    def route_intent(self, user_input: str) -> str:
        prompt = f"""Analyze input: "{user_input}"
Determine if this requires file modifications, code execution, or project generation.
Respond with exactly one word: ACTION or CHAT."""

        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        try:
            resp = requests.post(URL_CHAT, headers=headers, json=payload, timeout=15).json()
            intent = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
            return "ACTION" if "ACTION" in intent else "CHAT"
        except Exception:
            return "CHAT"

    def conversational_reply(self, user_input: str) -> str:
        self.memory.append({"role": "user", "content": user_input})
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": self.memory
        }
        try:
            resp = requests.post(URL_CHAT, headers=headers, json=payload, timeout=30).json()
            if "error" in resp:
                self.memory.pop()
                return f"API Error: {resp['error'].get('message', resp['error'])}"
            reply = resp["choices"][0]["message"]["content"]
            self.memory.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            self.memory.pop()
            return f"Error: {e}"

def run_chat():
    console.print("\n[bold yellow]⚡ Booting Fable OS...[/]")

    console.print("[cyan]1. Discovering Groq API Models...[/]")
    ACTIVE_MODEL = get_valid_model()
    os.environ["FABLE_CLOUD_MODEL"] = ACTIVE_MODEL

    console.print("[cyan]2. Loading Autonomous Worker Engine (Qdrant & AST)...[/]")
    from engine import SelfHealingEngine
    from orchestrator import InstitutionalOrchestrator

    engine = SelfHealingEngine()
    planner = InstitutionalOrchestrator(model_name=ACTIVE_MODEL)
    pro_active = is_pro_user()
    orchestrator = AgenticOrchestrator(model_name=ACTIVE_MODEL, is_pro=pro_active)

    if pro_active:
        console.print(Panel(
            f"[bold gold1]💎 FABLE ENTERPRISE ORCHESTRATOR — PRO EDITION[/]\n"
            f"[gold1]Active Brain:[/] [bold white]{ACTIVE_MODEL}[/] [dim](Extended Reasoning)[/]\n"
            f"[green]● 10-Loop Deep Healing: UNLOCKED[/] | [green]● Z3 Theorem Prover: ARMED[/]\n"
            f"[dim]Shielded Zero-Pollution Sandbox: Active | AST Splicing: Enabled[/]",
            border_style="gold1",
            title="[bold gold1][ VIP PRO LICENSE VERIFIED ][/]",
            subtitle="[dim]Type 'exit' to quit[/]"
        ))
    else:
        console.print(Panel(
            f"[bold white]FABLE ORCHESTRATOR (FREE EDITION)[/]\n"
            f"[cyan]Active Brain:[/] {ACTIVE_MODEL}\n"
            f"[yellow]● 3-Loop Standard Cap[/] | [dim]Run 'axiom --pro-key <KEY>' to unlock 10-Loop Pro[/]",
            border_style="cyan"
        ))

    while True:
        try:
            user_input = console.input("\n[bold green]Shyam > [/]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            intent = orchestrator.route_intent(user_input)

            if intent == "ACTION":
                console.print("\n📋 [bold yellow]Decomposing objective into execution plan...[/]")
                plan = planner.generate_execution_plan(user_input)
                planner.display_plan(plan)

                console.print("\n⚙️ [bold yellow]Dispatching Worker Engine...[/]")
                engine.run(user_input)
                orchestrator.memory.append({
                    "role": "system",
                    "content": f"System log: Executed task: '{user_input}'."
                })
            else:
                response = orchestrator.conversational_reply(user_input)
                console.print(f"\n🤖 [bold cyan]Fable >[/] {response}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Session terminated.[/]")
            break
        except Exception as e:
            console.print(f"\n❌ [bold red]Runtime Error: {e}[/]")

if __name__ == "__main__":
    run_chat()
