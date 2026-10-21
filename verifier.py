import os
import subprocess
import logging
import re

log = logging.getLogger("axiom.verifier")

class FormalVerifier:
    def __init__(self, llm):
        self.llm = llm

    def generate_and_run_proof(self, filename: str, code: str, shadow_dir: str) -> tuple[bool, str]:
        prompt = f"""
You are an elite formal verification compiler.
Your objective is to mathematically prove that the following Python code contains no silent overflows, unhandled edge cases, or domain boundary violations.

Target File: {filename}

Write a standalone Python script using the 'z3' library. 
1. Model the function's inputs as Z3 symbolic variables.
2. Model the function's logic and constraints.
3. Assert the negation of the expected safe boundaries (to search for a counter-example).
4. Print 'Z3_UNSAT: PROVED' if the solver cannot find a counter-example (meaning the code is mathematically safe).
5. Print 'Z3_SAT: FAILED' if a counter-example is found.

CODE TO PROVE:
{code}

Return ONLY the raw python script. Do not use markdown backticks.
"""
        
        try:
            # Command the Cloud Brain to write the Z3 Proof
            z3_script = self.llm.get_cloud_response(prompt, agent_role="Z3_Architect")
        except Exception as e:
            return False, f"LLM failed to generate proof: {e}"
            
        # Clean markdown fences
        z3_script = re.sub(r'^```[a-zA-Z0-9]*\n?', '', z3_script.strip())
        z3_script = re.sub(r'\n?```$', '', z3_script).strip()
        
        # Save the proof script into the isolated shadow directory
        proof_file = f"proof_{os.path.basename(filename).replace('.py', '')}.py"
        proof_path = os.path.join(shadow_dir, proof_file)
        
        with open(proof_path, "w") as f:
            f.write(z3_script)
            
        # Execute the Z3 Proof inside the secure Docker Sandbox
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.path.abspath(shadow_dir)}:/workspace",
            "-w", "/workspace",
            "axiom-sandbox:latest",
            "python", proof_file
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = res.stdout + res.stderr
            
            if "Z3_UNSAT" in output or "PROVED" in output:
                return True, f"Mathematical boundaries of {os.path.basename(filename)} proven safe."
            else:
                return False, f"Counter-example found by Z3 Theorem Solver:\n{output.strip()}"
        except Exception as e:
            return False, f"Z3 Execution failed: {str(e)}"
