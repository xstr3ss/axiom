import logging
import subprocess
import re
from llm import LLMClient

log = logging.getLogger("fable.explorer")

class WorkspaceExplorer:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def investigate(self, issue_description: str, max_steps: int = 4) -> str:
        log.info("🗺️ [Explorer] Analyzing repository to locate target files...")

        transcript = f"ISSUE TO SOLVE:\n{issue_description}\n\nExplore the workspace to find relevant files."

        for step in range(1, max_steps + 1):
            prompt = (
                f"You are the Fable Explorer Agent. Your goal is to gather context to solve the ISSUE.\n"
                f"Transcript so far:\n{transcript}\n\n"
                f"RULES:\n"
                f"1. To explore, output a SINGLE read-only bash command (e.g. ls, grep, cat) using EXACTLY this format:\n"
                f"COMMAND: <your bash command>\n"
                f"2. If you have found the files and read their contents, you are ready to code. Output EXACTLY:\n"
                f"DONE: <Detailed summary of the files, their current code, and what needs changing>"
            )

            # The Explorer requires high reasoning, so we force it to the Cloud model
            response = self.llm.generate(prompt, force_cloud=True).strip()

            if response.startswith("DONE:"):
                log.info("✅ [Explorer] Investigation complete. Context gathered.")
                return response.replace("DONE:", "").strip()

            if "COMMAND:" in response:
                # Extract the exact command
                cmd_line = [line for line in response.split("\n") if line.startswith("COMMAND:")][0]
                command = cmd_line.replace("COMMAND:", "").strip()

                log.info(f"🕵️ [Explorer] Step {step}/{max_steps} | Running: {command}")

                # === THE AST PRUNER INTERCEPTION LAYER ===
                # If the AI tries to cat a python file, we intercept and compress it instead.
                # Example interception: "cat engine.py" -> "python ast_pruner.py engine.py"
                
                actual_command_to_run = command
                cat_match = re.search(r'cat\s+([a-zA-Z0-9_\-\.\/]+\.py)', command)
                
                if cat_match:
                    target_file = cat_match.group(1)
                    # We rewrite the command to use the AST pruner
                    actual_command_to_run = f"python ast_pruner.py {target_file}"
                    log.info(f"🗜️ [Explorer] Intercepted 'cat'. Pruning {target_file} via AST...")

                try:
                    proc = subprocess.run(actual_command_to_run, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
                    
                    # We can increase the output cap now because the files are compressed!
                    output = proc.stdout[:8000] 
                    if not output.strip():
                        output = "<no output>"
                except Exception as e:
                    output = f"Error executing command: {e}"

                transcript += f"\n\nYOU RAN: {command}\nOUTPUT:\n{output}"
            # Open explorer.py and replace the final 'else:' block (around line 43) with this:
            else:
                log.warning("⚠️ [Explorer] Agent got eager and broke format. Treating as exploration context.")
                return transcript + f"\n\nEAGER AGENT OUTPUT:\n{response}"

        log.warning("🗺️ [Explorer] Reached max exploration steps.")
        return "Exploration timed out. Proceed with limited context."
