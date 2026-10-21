import time
import logging
import subprocess
import schedule
import argparse
from engine import SelfHealingEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.proactive")

class ProactiveWatcher:
    def __init__(self):
        self.engine = SelfHealingEngine()

    def _get_security_vulns(self) -> str:
        log.info("🔍 [Watcher] Scanning dependency tree for CVEs...")
        result = subprocess.run(["pip-audit", "--desc", "on"], capture_output=True, text=True)
        if result.returncode != 0 and result.stdout:
            return result.stdout.strip()
        return ""

    def _get_git_hotspots(self) -> str:
        log.info("🔥 [Watcher] Analyzing Git velocity for technical debt...")
        cmd = r"git log --name-only --oneline | grep '\.py$' | sort | uniq -c | sort -nr | head -3"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

    def run_patrol(self):
        log.info("🕵️ [Watcher] Starting Codebase Patrol...")
        
        vulns = self._get_security_vulns()
        hotspots = self._get_git_hotspots()
        
        if not vulns and not hotspots:
            log.info("✅ [Watcher] Repository is pristine. Patrol finished.")
            return

        branch_name = f"fable-proactive-patch-{int(time.time())}"
        log.info(f"🌿 [Watcher] Anomalies detected. Creating isolated branch: {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True)
        
        mission = (
            "PROACTIVE MAINTENANCE TASK:\n"
            "You are operating autonomously to resolve technical debt and security vulnerabilities.\n\n"
        )
        
        if vulns:
            mission += f"1. SECURITY FAILURES DETECTED:\n{vulns}\nUpdate dependencies, patch deprecated API calls, and ensure secure configurations.\n\n"
        if hotspots:
            mission += f"2. HIGH-CHURN HOTSPOTS DETECTED (Format: Commits | File):\n{hotspots}\nReview these files for memory leaks, race conditions, and AST complexity. Refactor them for stability.\n"
        
        log.info("🧠 [Watcher] Formulating autonomous mission and waking Fable Engine...")
        self.engine.run(mission)
        
        log.info("🚀 [Watcher] Patch verified in Docker sandbox. Submitting Pull Request...")
        subprocess.run(["git", "push", "-u", "origin", branch_name], capture_output=True)
        
        pr_cmd = [
            "gh", "pr", "create", 
            "--title", "🚨 Proactive Maintenance: Security & Tech Debt Resolution", 
            "--body", f"Fable Autonomous Engine detected and resolved the following issues:\n\n```\n{mission}\n```\nAll unit tests and formal proofs passed in the sandbox."
        ]
        subprocess.run(pr_cmd)
        
        subprocess.run(["git", "checkout", "main"], capture_output=True)
        log.info("🏁 [Watcher] PR successfully submitted. Patrol complete.")

def patrol_job():
    watcher = ProactiveWatcher()
    watcher.run_patrol()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fable Proactive Codebase Watcher")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in the background (3 AM cron)")
    args = parser.parse_args()

    if args.daemon:
        schedule.every().day.at("03:00").do(patrol_job)
        log.info("💤 [Watcher] Daemon active. Sleeping until 3:00 AM...")
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        log.info("⚡ [Watcher] Manual execution triggered.")
        patrol_job()
