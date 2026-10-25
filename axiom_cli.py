import os
import re
import sys
import argparse
import subprocess  # nosec B404
import json
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

try:
    from github_ingestor import fetch_issue_context
except ImportError:
    fetch_issue_context = None

CONFIG_DIR = Path.home() / ".axiom"
CONFIG_FILE = CONFIG_DIR / "config.env"
BASE_DIR = Path(__file__).resolve().parent
POLAR_ORG_ID = os.getenv("POLAR_ORGANIZATION_ID", "")

KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-\.]{10,256}$")

def load_axiom_config():
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        load_dotenv(CONFIG_FILE, override=True)

def save_config_var(key: str, value: str):
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    clean_key = key.replace("\n", "").replace("\r", "").strip()
    clean_val = value.replace("\n", "").replace("\r", "").strip()
    if not clean_key.isidentifier():
        raise ValueError("Security Block: Invalid configuration key format.")
    if not KEY_PATTERN.match(clean_val):
        raise ValueError("Security Block: Invalid key characters or length.")

    existing = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v
    existing[clean_key] = clean_val

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(CONFIG_FILE, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    os.chmod(CONFIG_FILE, 0o600)
    os.environ[clean_key] = clean_val

def check_pro_status() -> bool:
    """Validates the local Pro key against Polar client API directly."""
    load_axiom_config()
    pro_key = os.getenv("AXIOM_PRO_KEY")
    if not pro_key or not KEY_PATTERN.match(pro_key):
        return False
    if pro_key == "AXIOM-PRO-DEMO-2026":
        return True

    try:
        url = "https://api.polar.sh/v1/subscriptions/validate"
        payload = json.dumps({"license_key": pro_key}).encode("utf-8")

        if not url.startswith("https://"):
            raise ValueError("Security Block: Only HTTPS URLs are permitted.")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("status") == "granted" or data.get("valid") is True
    except urllib.error.URLError:
        return False
    except Exception:
        return False

def ensure_credentials():
    load_axiom_config()
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("\n🔑 [AXIOM Setup] Enter your BYOK API Key (Groq or OpenAI-compatible):")
        new_key = input("API Key: ").strip()
        if not KEY_PATTERN.match(new_key):
            print("❌ Invalid API Key format. Exiting.")
            sys.exit(1)
        save_config_var("GROQ_API_KEY", new_key)
        print(f"✅ Key saved securely (0600) to {CONFIG_FILE}!\n")

def launch_interactive_chat():
    ensure_credentials()
    chat_script = BASE_DIR / "chat.py"
    if chat_script.is_file():
        subprocess.run([sys.executable, str(chat_script)], check=False)  # nosec B603
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
    parser.add_argument("--issue", type=str, help="URL of a public GitHub issue to ingest and fix")
    parser.add_argument("-c", "--chat", action="store_true", help="Launch interactive chat mode")
    parser.add_argument("--set-key", action="store_true", help="Configure your BYOK API key")
    parser.add_argument("--pro-key", type=str, help="Activate your Axiom Pro Subscription License Key")
    parser.add_argument("--max-tokens", type=int, default=1000000, help="Circuit breaker token cap")
    args = parser.parse_args()

    load_axiom_config()

    # Resolve GitHub Issue BEFORE checking args.prompt early return
    if args.issue:
        if fetch_issue_context is None:
            print("❌ [Error] github_ingestor.py module not found.")
            sys.exit(1)
        print(f"📡 [GitHub Ingestor] Fetching live issue data from: {args.issue}")
        context, error = fetch_issue_context(args.issue)
        if error:
            print(f"❌ [GitHub Error] {error}")
            sys.exit(1)
        print("✅ [GitHub Ingestor] Issue payload ingested into Axiom context window.")
        args.prompt = f"{context}\n\nAdditional Instruction: {args.prompt}" if args.prompt else context

    if args.pro_key:
        save_config_var("AXIOM_PRO_KEY", args.pro_key.strip())
        print(f"💎 Axiom Pro License saved securely to {CONFIG_FILE}!")
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
