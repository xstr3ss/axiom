import os
import time
import shutil
import tempfile
import subprocess
from github import Github
from engine import SelfHealingEngine
from risk_gate import analyze_workspace_risk

def execute_multi_repo_healing(
    repo_names: list[str],
    prompt: str,
    github_token: str,
    groq_api_key: str
) -> dict:
    """
    Clones multiple repositories into a unified workspace, applies coordinated
    fixes across each repo, runs the AST Risk Gate, and pushes synchronized branches.
    """
    os.environ["GROQ_API_KEY"] = groq_api_key
    gh = Github(github_token)
    base_dir = os.getcwd()
    sync_id = int(time.time())
    sync_branch = f"fable-sync-{sync_id}"
    root_staging = tempfile.mkdtemp(prefix="fable_multirepo_")

    results = {}

    try:
        # 1. Clone all target repositories into sub-workspaces
        repo_dirs = {}
        for full_name in repo_names:
            short_name = full_name.split("/")[-1]
            target_dir = os.path.join(root_staging, short_name)
            clone_url = f"https://x-access-token:{github_token}@github.com/{full_name}.git"
            print(f"🌐 [Multi-Repo] Cloning {full_name} -> {target_dir}...")
            subprocess.run(["git", "clone", clone_url, target_dir], check=True, capture_output=True, text=True)
            repo_dirs[full_name] = (target_dir, clone_url)

        # 2. Run Self-Healing + Risk Gate across each repository with shared context
        peer_list = ", ".join(repo_names)
        for full_name, (target_dir, clone_url) in repo_dirs.items():
            print(f"🔧 [Multi-Repo] Running coordinated healing on {full_name}...")
            coordinated_prompt = (
                f"[Multi-Repo Coordinated Task across: {peer_list}]\n"
                f"Active Repository: {full_name}\n"
                f"Task: {prompt}"
            )

            try:
                os.chdir(target_dir)
                engine = SelfHealingEngine()
                engine.run(coordinated_prompt)
            finally:
                os.chdir(base_dir)

            # Evaluate AST Risk Gate before pushing
            risk = analyze_workspace_risk(target_dir)
            if not risk["passed"]:
                results[full_name] = {
                    "status": "blocked_by_risk_gate",
                    "score": risk["score"],
                    "report": risk["report_markdown"]
                }
                print(f"🛑 [Multi-Repo] {full_name} blocked by Risk Gate ({risk['score']}/100)")
                continue

            # Check modified files
            status_out = subprocess.check_output(["git", "status", "--porcelain"], cwd=target_dir, text=True)
            modified = [line[3:].strip() for line in status_out.splitlines() if line.strip()]

            # Push synchronized branch
            subprocess.run(["git", "config", "user.name", "Fable AI Coordinator"], cwd=target_dir, check=True)
            subprocess.run(["git", "config", "user.email", "fable-bot@ai.local"], cwd=target_dir, check=True)
            subprocess.run(["git", "checkout", "-b", sync_branch], cwd=target_dir, check=True)
            subprocess.run(["git", "add", "-A"], cwd=target_dir, check=True)
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", f"Fable Multi-Repo Sync ({sync_id})"],
                cwd=target_dir,
                check=True
            )
            subprocess.run(["git", "push", "-f", clone_url, sync_branch], cwd=target_dir, check=True)

            results[full_name] = {
                "status": "pushed",
                "branch": sync_branch,
                "modified_files": modified,
                "risk_score": risk["score"]
            }
            print(f"✅ [Multi-Repo] Pushed synchronized branch '{sync_branch}' to {full_name}")

        return {
            "sync_branch": sync_branch,
            "repositories": results
        }
    finally:
        shutil.rmtree(root_staging, ignore_errors=True)
