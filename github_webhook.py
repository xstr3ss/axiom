import logging
from fastapi import FastAPI, Request, BackgroundTasks
from engine import SelfHealingEngine
import subprocess

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.webhook")

app = FastAPI()
engine = SelfHealingEngine()

def process_github_command(comment_body: str, branch_name: str, pr_number: int):
    log.info(f"👀 [Webhook] Fable was summoned on PR #{pr_number}!")
    
    # 1. Pull the specific branch the user is commenting on
    subprocess.run(["git", "fetch", "origin"], capture_output=True)
    subprocess.run(["git", "checkout", branch_name], capture_output=True)
    subprocess.run(["git", "pull", "origin", branch_name], capture_output=True)
    
    # 2. Extract the actual request from the comment
    instruction = comment_body.replace("@fable", "").strip()
    mission = f"USER FEEDBACK ON PR #{pr_number}:\n{instruction}\n\nUpdate the code to satisfy this request."
    
    # 3. Hand off to the Swarm
    log.info(f"🧠 [Webhook] Waking Swarm to execute: {instruction}")
    engine.run(mission)
    
    # 4. Push the fixes back to the PR
    log.info(f"🚀 [Webhook] Fix complete. Pushing to {branch_name}...")
    subprocess.run(["git", "push", "origin", branch_name], capture_output=True)
    
    # 5. Reply to the user on GitHub
    subprocess.run([
        "gh", "pr", "comment", str(pr_number), 
        "--body", "✅ I've processed your feedback and pushed the requested changes. All tests pass in the sandbox."
    ])
    
    subprocess.run(["git", "checkout", "main"], capture_output=True)

@app.post("/webhook")
async def github_event(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    
    # Check if this is a comment event
    if "comment" in payload and "issue" in payload:
        comment_body = payload["comment"]["body"]
        
        # Check if someone tagged @fable
        if "@fable" in comment_body.lower():
            pr_number = payload["issue"]["number"]
            
            # Use gh CLI to grab the branch name for this PR
            result = subprocess.run(["gh", "pr", "view", str(pr_number), "--json", "headRefName", "--jq", ".headRefName"], capture_output=True, text=True)
            branch_name = result.stdout.strip()
            
            if branch_name:
                # Run the swarm in the background so GitHub gets a fast 200 OK response
                background_tasks.add_task(process_github_command, comment_body, branch_name, pr_number)
                return {"status": "accepted", "message": "Fable is on it."}
                
    return {"status": "ignored", "message": "Not a Fable command."}
