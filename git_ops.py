import os
import subprocess
import logging

log = logging.getLogger("axiom.git")

class GitManager:
    def commit(self, success: bool):
        # Force Git to never open an interactive prompt or editor
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_EDITOR"] = "true"

        try:
            # Stage changes with a strict 3-second timeout (respecting .gitignore)
            subprocess.run(
                ["git", "add", "--all"],
                timeout=3,
                env=env,
                capture_output=True,
                check=False
            )

            msg = "Auto-commit: Axiom Multi-Agent Loop"
            if not success:
                msg += " (Failed Run Snapshot)"

            # Commit with --no-verify and --no-gpg-sign so hooks/GPG never block
            res = subprocess.run(
                ["git", "commit", "-m", msg, "--no-verify", "--no-gpg-sign"],
                timeout=3,
                env=env,
                capture_output=True,
                text=True
            )
            if res.returncode == 0:
                print("📝 [Git] Committed successfully.")
            else:
                print("ℹ️ [Git] Working tree clean or commit skipped.")

        except subprocess.TimeoutExpired:
            print("⚠️ [Git] Git operation timed out after 3s — skipping auto-commit.")
        except Exception as e:
            print(f"⚠️ [Git] Auto-commit skipped: {e}")
