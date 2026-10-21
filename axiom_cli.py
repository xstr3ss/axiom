import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".axiom"
CONFIG_FILE = CONFIG_DIR / "config.env"

def load_axiom_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        load_dotenv(CONFIG_FILE, override=True)
    load_dotenv()

def save_config_var(key: str, value: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v
    existing[key] = value
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    os.environ[key] = value

def ensure_credentials():
    load_axiom_config()
    pro_key = os.getenv("AXIOM_PRO_KEY")
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

    if pro_key:
        print(f"💎 [Axiom Pro] Authenticated with Pro License ({pro_key[:10]}...)")
        return

    if not api_key:
        print("\n🔑 [AXIOM Setup] Choose how to power Axiom:")
        print("  1. Enter your free BYOK API Key (Groq / OpenAI)")
        print("  2. Enter an Axiom Pro Subscription License Key (AXIOM-PRO-...)")
        choice = input("\nPaste Key: ").strip()
        if not choice:
            print("❌ A key is required to run Axiom. Exiting.")
            sys.exit(1)
        if choice.startswith("AXIOM-PRO-") or choice.startswith("ax_pro_"):
            save_config_var("AXIOM_PRO_KEY", choice)
            print("✅ Axiom Pro License activated! Routing via Axiom Cloud.")
        else:
            save_config_var("GROQ_API_KEY", choice)
            print(f"✅ BYOK API Key saved locally to {CONFIG_FILE}!")

def launch_interactive_chat():
    """Connects directly to chat.py for interactive terminal sessions."""
    ensure_credentials()
    if os.path.exists("chat.py"):
        subprocess.run([sys.executable, "chat.py"])
    else:
        print("💬 Launching Axiom Interactive Mode (Type 'exit' to quit)...")
        from engine import SelfHealingEngine
        engine = SelfHealingEngine(max_session_tokens=4000)
        while True:
            try:
                user_in = input("\n⚡ axiom> ").strip()
                if user_in.lower() in ("exit", "quit", "q"):
                    break
                if user_in:
                    engine.run(user_in)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Exiting Axiom.")
                break

def main():
    parser = argparse.ArgumentParser(
        prog="axiom",
        description="AXIOM: Shielded, Z3 Formally Verified Autonomous Coding Engine"
    )
    parser.add_argument("prompt", nargs="?", help="The refactoring or bug-fixing objective")
    parser.add_argument("-c", "--chat", action="store_true", help="Launch interactive chat mode (chat.py)")
    parser.add_argument("--set-key", action="store_true", help="Configure or update your BYOK API key")
    parser.add_argument("--pro-key", type=str, help="Activate your paid Axiom Pro Subscription License Key")
    parser.add_argument("--max-tokens", type=int, default=4000, help="Session token circuit-breaker cap")
    args = parser.parse_args()

    load_axiom_config()

    if args.pro_key:
        save_config_var("AXIOM_PRO_KEY", args.pro_key.strip())
        print(f"💎 Axiom Pro License saved to {CONFIG_FILE}!")
        if not args.prompt and not args.chat:
            return

    if args.set_key:
        new_key = input("🔑 Enter your BYOK API Key (Groq/OpenAI): ").strip()
        if new_key:
            save_config_var("GROQ_API_KEY", new_key)
            print(f"✅ BYOK Key saved to {CONFIG_FILE}!")
        if not args.prompt and not args.chat:
            return

    # If user runs 'axiom --chat' or 'axiom' with no prompt, launch chat.py!
    if args.chat or not args.prompt:
        launch_interactive_chat()
        return

    ensure_credentials()
    from engine import SelfHealingEngine
    engine = SelfHealingEngine(max_session_tokens=args.max_tokens)
    engine.run(args.prompt)

if __name__ == "__main__":
    main()
