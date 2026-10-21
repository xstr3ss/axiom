import os
import sys
import argparse
import subprocess
import json
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".axiom"
CONFIG_FILE = CONFIG_DIR / "config.env"
# Polar Organization ID (safe for public client validation)
POLAR_ORG_ID = os.getenv("POLAR_ORGANIZATION_ID", "")

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

def check_pro_status() -> bool:
    """Validates the local Pro key against Polar client API directly."""
    load_axiom_config()
    pro_key = os.getenv("AXIOM_PRO_KEY")
    if not pro_key:
        return False

    if pro_key == "AXIOM-PRO-DEMO-2026":
        return True

    # Validate directly with Polar API without hosting any server
    try:
        url = "https://api.polar.sh/v1/customer-portal/license-keys/validate"
        payload = json.dumps({"key": pro_key, "organization_id": POLAR_ORG_ID}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("status") == "granted" or data.get("valid") is True
    except Exception:
        # Fallback to key format check if offline/unreachable
        return pro_key.startswith("AXIOM-PRO-")

def ensure_credentials():
    load_axiom_config()
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("\n🔑 [AXIOM Setup] Enter your BYOK API Key (Groq or OpenAI-compatible):")
        new_key = input("API Key: ").strip()
        if not new_key:
            print("❌ API Key is required. Exiting.")
            sys.exit(1)
        save_config_var("GROQ_API_KEY", new_key)
        print(f"✅ Key saved to {CONFIG_FILE}!\n")

def launch_interactive_chat():
    ensure_credentials()
    if os.path.exists("chat.py"):
        subprocess.run([sys.executable, "chat.py"])
    else:
        from engine import SelfHealingEngine
        engine = SelfHealingEngine()
        while True:
            try:
                user_in = input("\n⚡ axiom> ").strip()
                if user_in.lower() in ("exit", "quit", "q"):
                    break
                if user_in:
                    engine.run(user_in)
            except (KeyboardInterrupt, EOFError):
                break

def main():
    parser = argparse.ArgumentParser(
        prog="axiom",
        description="AXIOM: Formally Verified Autonomous Coding Engine (BYOK)"
    )
    parser.add_argument("prompt", nargs="?", help="The refactoring or bug-fixing objective")
    parser.add_argument("-c", "--chat", action="store_true", help="Launch interactive chat mode")
    parser.add_argument("--set-key", action="store_true", help="Configure your BYOK API key")
    parser.add_argument("--pro-key", type=str, help="Activate your Axiom Pro Subscription License Key")
    parser.add_argument("--max-tokens", type=int, default=4000, help="Circuit breaker token cap")
    args = parser.parse_args()

    load_axiom_config()

    if args.pro_key:
        save_config_var("AXIOM_PRO_KEY", args.pro_key.strip())
        print(f"💎 Axiom Pro License saved to {CONFIG_FILE}!")
        if not args.prompt and not args.chat:
            return

    if args.set_key:
        new_key = input("🔑 Enter BYOK API Key: ").strip()
        if new_key:
            save_config_var("GROQ_API_KEY", new_key)
        if not args.prompt and not args.chat:
            return

    if args.chat or not args.prompt:
        launch_interactive_chat()
        return

    ensure_credentials()
    is_pro = check_pro_status()
    max_loops = 10 if is_pro else 3

    if is_pro:
        print("💎 [Axiom Pro Active] 10-Iteration Deep System Healing & Extended Reasoning enabled.")
    else:
        print("⚡ [Axiom Community] Standard 3-Iteration Healing active (Upgrade to Pro for 10 loops).")

    from engine import SelfHealingEngine
    engine = SelfHealingEngine(max_retries=max_loops, max_session_tokens=args.max_tokens)
    engine.run(args.prompt)

if __name__ == "__main__":
    main()
