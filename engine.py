import logging
import re
import os
import time
import ast
import copy
import shutil
import tempfile
import stat
from datetime import datetime
from contextlib import contextmanager
from config import Config
from llm import LLMClient
from docker_sandbox import run_tests
from memory import VectorMemory
from critic import CriticAgent
from git_ops import GitManager
from explorer import WorkspaceExplorer
from distiller import DistillationEngine
from verifier import FormalVerifier
from triage import TriageAgent
from semantic_guard import ASTSemanticAuditor

logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
log = logging.getLogger("axiom.engine")

class TokenBudgetExceeded(Exception):
    """Raised when the session token circuit breaker trips."""
    pass

class TokenBudgetGuard:
    def __init__(self, max_tokens: int = 12000):
        self.max_tokens = int(os.getenv("FABLE_MAX_TOKENS", max_tokens))
        self.used_tokens = 0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def check_pre_flight(self, prompt: str) -> int:
        est_input = self.estimate_tokens(prompt)
        if self.used_tokens + est_input > self.max_tokens:
            raise TokenBudgetExceeded(
                f"Circuit Breaker Tripped! Incoming prompt (~{est_input} tokens) "
                f"would exceed session cap ({self.used_tokens}/{self.max_tokens} tokens)."
            )
        return est_input

    def record_usage(self, prompt: str, completion: str) -> str:
        spent = self.estimate_tokens(prompt) + self.estimate_tokens(completion)
        self.used_tokens += spent
        return f"🪙 Token Meter: +{spent} tokens | Session Total: {self.used_tokens}/{self.max_tokens}"

class TraceLogger:
    def __init__(self, max_retries: int = 3, max_session_tokens: int = 4000):
        self.trace_dir = "axiom_traces"
        os.makedirs(self.trace_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trace_file = os.path.join(self.trace_dir, f"trace_{timestamp}.md")
        self.steps = []
        with open(self.trace_file, "w") as f:
            f.write(f"# 🚀 Axiom Telemetry Trace | {timestamp}\n\n")

    def log_step(self, agent_name: str, action: str, details: str = ""):
        step = {"agent": agent_name, "action": action, "timestamp": time.time()}
        self.steps.append(step)
        with open(self.trace_file, "a") as f:
            f.write(f"### 🤖 [{agent_name}] - {action}\n")
            if details:
                f.write(f"{details}\n")
            f.write("\n---\n")

        color = "\033[94m"
        if "❌" in action or "Error" in action or "Tripped" in action:
            color = "\033[91m"
        elif "✅" in action or "Passed" in action or "Promoted" in action:
            color = "\033[92m"
        elif "⚠️" in action or "REGRESSION" in action or "🪙" in action:
            color = "\033[93m"
        elif "Local SLM" in action or "Cloud Brain" in action or "Shadow" in action:
            color = "\033[95m"
        elif "Memory" in action or "Qdrant" in action:
            color = "\033[96m"

        print(f"\n{color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
        print(f"{color}🤖 [{agent_name}] ➔ {action}\033[0m")
        if details:
            print(f"\n\033[37m{details}\033[0m")
        print(f"{color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")

    @contextmanager
    def measure(self, agent_name: str, action: str, details: str = ""):
        yield
        self.log_step(agent_name, action, details=details)

class SelfHealingEngine:
    def __init__(self):
        log.info("🚨 [Engine] Initializing Shielded Zero-Pollution Architecture...")
        self.cfg = Config()
        self.llm = LLMClient(self.cfg)
        self.memory = VectorMemory()
        self.critic = CriticAgent(self.llm)
        self.git = GitManager()
        self.explorer = WorkspaceExplorer(self.llm)
        self.distiller = DistillationEngine()
        self.verifier = FormalVerifier(self.llm)
        self.tracer = TraceLogger()
        self.budget = TokenBudgetGuard(max_tokens=max_session_tokens)
        self.max_retries = max_retries
        self.current_objective = ""

    def _parse_test_score(self, test_output: str) -> int:
        match = re.search(r'(\d+)\s+passed', test_output)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _clean_code_block(text: str) -> str:
        text = text.strip()
        text = re.sub(r'^```[a-zA-Z0-9]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        return text.strip()

    def _discover_relevant_files(self, target_test: str, prompt: str) -> dict:
        files = {}
        queue = [target_test]
        visited = set()
        base_dir = os.getcwd()

        # Catch paths like src/core/module.py from the prompt
        import re
        for word in re.findall(r'[a-zA-Z0-9_\-\.\/]+\.(?:py|json|yaml)', prompt):
            if os.path.exists(word):
                queue.append(word)

        def resolve_import(module_name):
            parts = module_name.split('.')
            path_py = os.path.join(base_dir, *parts) + ".py"
            path_init = os.path.join(base_dir, *parts, "__init__.py")
            if os.path.exists(path_py): return os.path.relpath(path_py, base_dir)
            if os.path.exists(path_init): return os.path.relpath(path_init, base_dir)
            return None

        while queue:
            current = queue.pop(0)
            if current in visited or not os.path.exists(current):
                continue
            visited.add(current)
            
            with open(current, "r", encoding="utf-8") as f:
                content = f.read()
            files[current] = content

            if current.endswith(".py"):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                cand = resolve_import(alias.name)
                                if cand and cand not in visited: queue.append(cand)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            # e.g., from src.core import engine
                            cand = resolve_import(node.module)
                            if cand and cand not in visited: queue.append(cand)
                            # e.g., from src.core.engine import run
                            for alias in node.names:
                                cand_sub = resolve_import(f"{node.module}.{alias.name}")
                                if cand_sub and cand_sub not in visited: queue.append(cand_sub)
                except SyntaxError:
                    pass
        return files

    def _stitch_patch(self, filename: str, search_str: str, replace_str: str, files_context: dict, shadow_dir: str) -> bool:
        if filename.startswith("test_"):
            self.tracer.log_step("Stitcher", f"🛡️ Protected: Blocked modification to test file {filename}")
            return False

        search_clean = self._clean_code_block(search_str)
        replace_clean = self._clean_code_block(replace_str)

        if not replace_clean:
            return False

        original = files_context.get(filename, "")
        candidate = None

        if not original or not search_clean:
            candidate = replace_clean + "\n"
        elif search_clean in original:
            candidate = original.replace(search_clean, replace_clean, 1)
        else:
            orig_lines = [line.rstrip() for line in original.splitlines()]
            search_lines = [line.rstrip() for line in search_clean.splitlines()]
            orig_joined = "\n".join(orig_lines)
            search_joined = "\n".join(search_lines)
            if search_joined in orig_joined:
                candidate = orig_joined.replace(search_joined, replace_clean, 1) + "\n"
            elif filename.endswith(".py"):
                try:
                    patch_tree = ast.parse(replace_clean)
                    patch_funcs = [n.name for n in patch_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    if len(original.splitlines()) < 40:
                        candidate = replace_clean + "\n"
                    elif len(patch_funcs) == 1:
                        old_func = TriageAgent.extract_function(original, patch_funcs[0])
                        if old_func and old_func in original:
                            candidate = original.replace(old_func, replace_clean, 1)
                except SyntaxError:
                    pass

        if candidate is None:
            self.tracer.log_step("Stitcher", f"⚠️ Regex/AST Mismatch: Could not merge patch for {filename}")
            return False

        if filename.endswith(".py"):
            try:
                ast.parse(candidate)
            except SyntaxError as e:
                self.tracer.log_step("Stitcher", f"❌ AST Syntax Error in patch for {filename}: {e}")
                return False

        files_context[filename] = candidate
        shadow_file_path = os.path.join(shadow_dir, filename)
        os.makedirs(os.path.dirname(shadow_file_path), exist_ok=True)
        with open(shadow_file_path, "w") as f:
            f.write(candidate)
        self.tracer.log_step("Stitcher", f"✅ Staged AST-verified patch in Shadow Workspace: {filename}")
        return True

    def resolve_error(self, error_output: str, files_context: dict, prompt: str, initial_score: int = 0):
        self.tracer.log_step("Engine", "Initiating Shielded Self-Healing Pipeline (Shadow Mode)")
        self.tracer.log_step("Sandbox", f"Initial Failure Detected (Baseline: {initial_score} passed)", details=error_output)
        success, current_error = False, error_output
        retries, max_retries = 0, getattr(self, 'max_retries', 3)
        best_score, best_files_snapshot = initial_score, copy.deepcopy(files_context)

        final_successful_patch = ""
        final_condensed_error = ""
        in_session_failures = []

        # 🛡️ CREATE ISOLATED SHADOW WORKSPACE WITH ROOT-SAFE CLEANUP
        shadow_dir = tempfile.mkdtemp(prefix="axiom_shadow_")
        self.tracer.log_step("Shadow Workspace", f"🛡️ Isolated staging created at {shadow_dir} (Host files locked)")
        for fname, fcontent in files_context.items():
            target_path = os.path.join(shadow_dir, fname)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w") as f:
                f.write(fcontent)

        try:
            while not success and retries < max_retries:
                retries += 1
                self.tracer.log_step("Engine", f"Pipeline Iteration {retries}/{max_retries}")

                with self.tracer.measure("Pipeline Step 1", "Multi-File AST Slicing (Local SLM 3B)"):
                    failing_funcs_context = ""
                    targets = set(re.findall(r'([a-zA-Z0-9_]+\.py)(?:.*?)in ([a-zA-Z0-9_]+)', current_error))
                    if targets:
                        for fname, func in targets:
                            if fname in files_context and func != "<module>":
                                extracted_graph = TriageAgent.build_dependency_graph(fname, func, files_context)
                                if extracted_graph:
                                    failing_funcs_context += extracted_graph

                with self.tracer.measure("Pipeline Step 2", "Log Condenser (Local SLM 3B)"):
                    condensed_error = TriageAgent.condense_error(current_error, self.llm)
                    final_condensed_error = condensed_error

                with self.tracer.measure("Pipeline Step 2.5", "Qdrant Memory Retrieval (Local DB)"):
                    prior_knowledge = "No exact historical match found. Rely on general intelligence."
                    try:
                        if hasattr(self.memory, 'search'):
                            results = self.memory.search(condensed_error, limit=1)
                            if results:
                                prior_knowledge = results[0].payload.get("patch", prior_knowledge)
                    except Exception as e:
                        self.tracer.log_step("Memory", f"Retrieval bypassed or failed: {e}")

                editable_files = {k: v for k, v in files_context.items() if not k.startswith("test_")}
                test_files = {k: v for k, v in files_context.items() if k.startswith("test_")}

                code_context = "EDITABLE SOURCE FILES:\n" + "\n".join([f"FILE: {k}\n```\n{v}\n```" for k, v in editable_files.items()])
                test_context = "READ-ONLY TEST SUITE:\n" + "\n".join([f"FILE: {k}\n```\n{v}\n```" for k, v in test_files.items()])

                anti_pattern_prompt = ""
                if in_session_failures:
                    anti_pattern_prompt = "\n🛑 PREVIOUS FAILED ATTEMPTS (DO NOT REPEAT THESE):\n"
                    for idx, item in enumerate(in_session_failures):
                        anti_pattern_prompt += f"Attempt {idx+1} Patch:\n{item['patch']}\nResulting Error:\n{item['error']}\n---\n"

                repair_prompt = (
                    f"You are a strict cross-boundary architect. Fix the bug to achieve this OBJECTIVE: {prompt}\n\n"
                    f"PRIOR KNOWLEDGE FROM TRAINING DB:\n{prior_knowledge}\n"
                    f"{anti_pattern_prompt}"
                    f"CRITICAL RULES:\n"
                    f"1. DO NOT output FILE blocks for any test_*.py files.\n"
                    f"2. Ensure all methods return the exact types expected by the READ-ONLY TEST SUITE.\n"
                    f"3. Do NOT wrap code inside SEARCH/REPLACE blocks with markdown backticks.\n\n"
                    f"{code_context}\n\n"
                    f"{test_context}\n\n"
                    f"CONDENSED ERROR:\n{condensed_error}\n\n"
                    f"Return ONLY the fixed code using this exact format for each file:\n"
                    f"FILE: filename.ext\n<<<<<<< SEARCH\n[exact old code to replace]\n=======\n[complete fixed code]\n>>>>>>> REPLACE\n"
                )

                try:
                    self.budget.check_pre_flight(repair_prompt)
                except TokenBudgetExceeded as e:
                    self.tracer.log_step("Circuit Breaker", f"⚡ {str(e)} — Halting safely without touching host files.")
                    break

                with self.tracer.measure("Pipeline Step 3", "Strategic Patching (Cloud Brain 120B)"):
                    repair_response = self.llm.get_cloud_response(repair_prompt, agent_role="Healer_Escalated")
                    final_successful_patch = repair_response
                    meter_msg = self.budget.record_usage(repair_prompt, repair_response)
                    self.tracer.log_step("Budget Guard", meter_msg)

                with self.tracer.measure("Pipeline Step 4", "Patch Stitching & AST Merge (Shadow Staging)"):
                    blocks = re.split(r'FILE:\s*([a-zA-Z0-9_\-\.\/]+)', repair_response)
                    for i in range(1, len(blocks), 2):
                        filename = blocks[i].strip()
                        content = blocks[i+1]

                        search_match = re.search(r'<<<<<<<\s*SEARCH\s*\n?(.*?)\n?=======', content, re.DOTALL)
                        replace_match = re.search(r'=======\s*\n?(.*?)\n?>>>>>>>\s*REPLACE', content, re.DOTALL)

                        if search_match and replace_match:
                            self._stitch_patch(filename, search_match.group(1), replace_match.group(1), files_context, shadow_dir)
                        else:
                            cleaned = self._clean_code_block(content)
                            if cleaned:
                                self._stitch_patch(filename, "", cleaned, files_context, shadow_dir)

                with self.tracer.measure("Pipeline Step 5", "Pre-Flight Linter & Sandbox (Shadow Docker Mount)"):
                    target_test = next((f for f in files_context.keys() if os.path.basename(f).startswith("test_")), list(files_context.keys())[0])
                    success, current_error = run_tests(test_target=target_test, workspace_dir=shadow_dir)
                    current_score = self._parse_test_score(current_error)

                if success:
                    # 🛡️ ZERO-TOKEN SEMANTIC GATE
                    semantic_ok = True
                    for fname, fcontent in editable_files.items():
                        orig_code = best_files_snapshot.get(fname, "")
                        ok, reason = ASTSemanticAuditor.verify_patch_integrity(fname, orig_code, fcontent, test_files)
                        if not ok:
                            semantic_ok = False
                            success = False
                            current_error = f"CRITICAL SEMANTIC REJECTION: {reason}"
                            self.tracer.log_step("Semantic Gate", f"❌ Blocked Phantom Success in {fname}", details=reason)
                            in_session_failures.append({"patch": repair_response, "error": reason})
                            break
                        else:
                            self.tracer.log_step("Semantic Gate", f"🛡️ {reason}")

                            # 🧠 Z3 FORMAL VERIFICATION HOOK
                            if not os.path.basename(fname).startswith("test_") and "__init__" not in fname:
                                self.tracer.log_step("Z3 Verifier", f"Synthesizing algebraic proof for {fname}...")
                                z3_ok, z3_reason = self.verifier.generate_and_run_proof(fname, fcontent, shadow_dir)
                                if not z3_ok:
                                    semantic_ok = False
                                    success = False
                                    current_error = f"CRITICAL Z3 REJECTION: {z3_reason}"
                                    self.tracer.log_step("Z3 Verifier", f"❌ {z3_reason}")
                                    in_session_failures.append({"patch": repair_response, "error": z3_reason})
                                    break
                                else:
                                    self.tracer.log_step("Z3 Verifier", f"📐 {z3_reason}")

                    if semantic_ok:
                        self.tracer.log_step("Sandbox", "✅ Tests & Semantic Audit Passed! Promoting verified files to Host...")
                        for fname, fcontent in files_context.items():
                            if not fname.startswith("test_"):
                                with open(fname, "w") as f:
                                    f.write(fcontent)
                        self.tracer.log_step("Shadow Workspace", "✅ Atomic Promotion Complete. Real environment updated safely.")
                        break
                else:
                    self.tracer.log_step("Sandbox", f"❌ Tests Failed in Shadow ({current_score} passed)", details=current_error)
                    in_session_failures.append({"patch": repair_response, "error": condensed_error})
                    final_successful_patch = ""

                if current_score > best_score:
                    self.tracer.log_step("Checkpoint", f"🎯 High Score: {current_score} passed tests. Shadow snapshot saved.")
                    best_score, best_files_snapshot = current_score, copy.deepcopy(files_context)
                elif current_score < best_score:
                    self.tracer.log_step("Checkpoint", f"⚠️ REGRESSION: Rolled back shadow workspace to checkpoint ({best_score} passed).")
                    files_context = copy.deepcopy(best_files_snapshot)
                    for fname, fcontent in files_context.items():
                        target_path = os.path.join(shadow_dir, fname)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, "w") as f:
                            f.write(fcontent)
        finally:
            shutil.rmtree(shadow_dir, ignore_errors=True)

        if success and final_successful_patch:
            with self.tracer.measure("Memory", "Distilling and Committing Resolution to Qdrant"):
                try:
                    if hasattr(self.memory, 'store'):
                        self.memory.store(text=final_condensed_error, metadata={"patch": final_successful_patch, "type": "resolution"})
                    self.tracer.log_step("Memory", "✅ Saved successful resolution vector to memory.")
                except Exception as e:
                    self.tracer.log_step("Memory", f"⚠️ Failed to commit to DB: {e}")

            with self.tracer.measure("Git", "Committing Changes"):
                self.git.commit(success)
        elif not success and len(in_session_failures) > 0:
            with self.tracer.measure("Memory", "Logging Poisoned Path to Anti-Pattern Database"):
                try:
                    if hasattr(self.memory, 'store'):
                        self.memory.store(text=final_condensed_error, metadata={"failed_patches": [f["patch"] for f in in_session_failures], "type": "anti_pattern"})
                    self.tracer.log_step("Memory", "✅ Saved anti-pattern vector to memory (Host workspace remained untouched).")
                except Exception as e:
                    pass

        return success

    def run(self, prompt: str):
        self.current_objective = prompt
        self.tracer.log_step("Engine", "Simulation Started", details=prompt)

        existing_tests = []
        for root, _, filenames in os.walk("."):
            if any(part.startswith('.') and part != '.' for part in root.split(os.sep)) or "venv" in root or "__pycache__" in root:
                continue
            for f in filenames:
                if f.startswith("test_") and f.endswith(".py"):
                    existing_tests.append(os.path.relpath(os.path.join(root, f), "."))

        if not existing_tests:
            log.error("No tests found in directory. Exiting.")
            print("No tests found in directory. Exiting.")
            return

        target_test = next((f for f in existing_tests if f in prompt), None)
        if not target_test:
            self.tracer.log_step("Explorer", "No exact test named. Deducing target via Local SLM...")
            target_test = self.explorer.deduce_test_target(prompt, existing_tests)
        self.tracer.log_step("Engine", f"Detected target test suite ({target_test}). Entering Refactor Mode.")

        files = self._discover_relevant_files(target_test, prompt)
        self.tracer.log_step("Workspace", f"AST-Scoped Context Loaded ({len(files)} files): {', '.join(files.keys())}")

        success, current_error = run_tests(test_target=target_test)
        initial_score = self._parse_test_score(current_error)

        proactive_keywords = ["refactor", "rewrite", "architect", "migrate", "fix"]
        is_refactor_intent = any(kw in prompt.lower() for kw in proactive_keywords)

        if not success or is_refactor_intent:
            if success and is_refactor_intent:
                self.tracer.log_step("Engine", "🔍 Proactive intent detected. Forcing engineering loop despite passing tests.")
            self.resolve_error(current_error, files, prompt, initial_score=initial_score)
        else:
            self.tracer.log_step("Engine", "✅ SUCCESS - All tests currently passing. No refactor needed.")
            self.git.commit(True)

if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Fix the bugs"
    SelfHealingEngine().run(prompt)
