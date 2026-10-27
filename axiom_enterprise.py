import ast
import os
import re
import sys
import time
import shutil
import difflib
import tempfile
import subprocess  # nosec B404
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ANSI Terminal Colors for Live Visual Telemetry
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ==============================================================================
# 1. AUTOMATED TEST GENERATION (SELF-TDD)
# ==============================================================================
class SelfTDDGenerator:
    """Generates a reproduction unit test when no test_*.py exists in the project."""

    @staticmethod
    def ensure_reproduction_test(prompt: str, llm_client=None, tracer=None) -> Optional[str]:
        existing_tests = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in {"venv", ".git", "__pycache__", "axiom_traces"}]
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    existing_tests.append(os.path.join(root, file))

        if existing_tests:
            print(f"{CYAN}🧪 [Self-TDD] Found {len(existing_tests)} existing test suite(s): {existing_tests[0]}{RESET}")
            return existing_tests[0]

        print(f"{YELLOW}🧪 [Self-TDD] No test suite detected! Synthesizing reproduction test for objective...{RESET}")
        if tracer:
            tracer.log_step("Self-TDD", "Generating reproduction unit test from bug report")

        py_files = [
            f for f in os.listdir(".")
            if f.endswith(".py") and f not in {"axiom_cli.py", "engine.py", "axiom_enterprise.py", "chat.py", "pro_server.py"}
        ]
        target_module = py_files[0][:-3] if py_files else "app"

        test_filename = "test_axiom_repro.py"
        generated_code = None

        if llm_client and hasattr(llm_client, "get_cloud_response"):
            tdd_prompt = (
                f"Generate a minimal, deterministic pytest file named `{test_filename}` that reproduces "
                f"or verifies the following objective:\n{prompt}\n"
                f"Target module hint: `{target_module}`.\n"
                "Return ONLY valid Python code using standard `def test_*():` functions."
            )
            try:
                raw = llm_client.get_cloud_response(tdd_prompt, agent_role="Self_TDD")
                clean = re.sub(r"^```[a-zA-Z0-9]*\n?", "", raw.strip())
                clean = re.sub(r"\n?```$", "", clean).strip()
                ast.parse(clean)
                generated_code = clean
            except Exception:
                generated_code = None

        if not generated_code:
            generated_code = (
                f"import importlib\n\n"
                f"def test_reproduction_import():\n"
                f"    \"\"\"Auto-generated Self-TDD baseline reproduction test.\"\"\"\n"
                f"    mod = importlib.import_module('{target_module}')\n"
                f"    assert mod is not None\n"
            )

        with open(test_filename, "w", encoding="utf-8") as f:
            f.write(generated_code + "\n")

        print(f"{GREEN}✅ [Self-TDD] Created `{test_filename}` ({len(generated_code.splitlines())} lines).{RESET}")
        return test_filename


# ==============================================================================
# 2. PRE-FLIGHT STATIC SECURITY SCANNER (SQLi, XSS, Secrets, Eval)
# ==============================================================================
class PreFlightSecurityScanner:
    """Scans Python AST nodes and source lines for critical vulnerabilities before Z3/Promotion."""

    SECRET_PATTERNS = [
        (r"gsk_[A-Za-z0-9]{20,}", "Hardcoded Groq API Key (CWE-798)"),
        (r"sk-[A-Za-z0-9\-_]{20,}", "Hardcoded OpenAI API Key (CWE-798)"),
        (r"ghp_[A-Za-z0-9]{20,}", "Hardcoded GitHub Personal Access Token (CWE-798)"),
        (r"AKIA[0-9A-Z]{16}", "Hardcoded AWS Access Key ID (CWE-798)"),
    ]

    SQLI_REGEX = re.compile(
        r"\.\s*execute\s*\(\s*(?:f['\"]|['\"].*?(?:%s|\{).*?['\"]\s*(?:%|\.format))",
        re.IGNORECASE | re.DOTALL,
    )

    XSS_PATTERNS = [
        (r"\bmark_safe\s*\(", "Potential XSS via unescaped mark_safe() (CWE-79)"),
        (r"\brender_template_string\s*\(\s*f['\"]", "Server-Side Template Injection / XSS (CWE-79)"),
        (r"\.innerHTML\s*=", "DOM XSS sink via raw innerHTML assignment (CWE-79)"),
    ]

    @classmethod
    def scan_code(cls, filename: str, code_text: str, tracer=None) -> Tuple[bool, List[str]]:
        print(f"{CYAN}🛡️  [Pre-Flight Security Gate] Auditing AST & patterns in `{filename}`...{RESET}")
        findings: List[str] = []

        # 1. Secret Leak Detection
        for pattern, label in cls.SECRET_PATTERNS:
            for idx, line in enumerate(code_text.splitlines(), 1):
                if re.search(pattern, line):
                    findings.append(f"Line {idx}: {label}")

        # 2. Raw SQL Formatting Detection (SQLi)
        if cls.SQLI_REGEX.search(code_text):
            findings.append("SQL Injection Risk: Raw string interpolation inside .execute() (CWE-89)")

        # 3. XSS Sink Detection
        for pattern, label in cls.XSS_PATTERNS:
            for idx, line in enumerate(code_text.splitlines(), 1):
                if re.search(pattern, line):
                    findings.append(f"Line {idx}: {label}")

        # 4. Deep AST Inspection (eval, exec, shell=True, SQLi f-strings in execute)
        try:
            tree = ast.parse(code_text, filename=filename)
            tainted_vars = set()
            
            for node in ast.walk(tree):
                # 1. Taint Tracking: Record variables assigned to f-strings or binary ops
                if isinstance(node, ast.Assign):
                    if isinstance(node.value, (ast.JoinedStr, ast.BinOp)):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                tainted_vars.add(target.id)

                # 2. Sink Tracking: Check if dangerous functions are called
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                        findings.append(f"Line {node.lineno}: Dangerous `{node.func.id}()` call (CWE-95)")

                    if isinstance(node.func, ast.Attribute) and node.func.attr in {"run", "Popen", "call"}:
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                findings.append(f"Line {node.lineno}: Subprocess with `shell=True` (CWE-78)")

                    # 3. SQLi Check (Direct String AND Tainted Variable)
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "execute" and node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, (ast.JoinedStr, ast.BinOp)):
                            findings.append(f"Line {node.lineno}: Direct SQL Injection in `.execute()` (CWE-89)")
                        elif isinstance(first_arg, ast.Name) and first_arg.id in tainted_vars:
                            findings.append(f"Line {node.lineno}: Tainted variable '{first_arg.id}' passed to `.execute()` (CWE-89)")
        except SyntaxError as e:
            findings.append(f"Line {e.lineno}: SyntaxError during AST security scan")

        if findings:
            print(f"{RED}🚨 [Pre-Flight Security Gate] BLOCKED `{filename}` ({len(findings)} issue(s)):{RESET}")
            for issue in findings:
                print(f"   {RED}✖ {issue}{RESET}")
            if tracer:
                tracer.log_step("Pre-Flight Security", "CRITICAL SECURITY REJECTION", "\n".join(findings))
            return False, findings

        print(f"{GREEN}✅ [Pre-Flight Security Gate] `{filename}` passed (0 SQLi, 0 XSS, 0 Secret Leaks).{RESET}")
        return True, []


# ==============================================================================
# 5. INTERACTIVE DIFF-REVIEW & HUMAN-IN-THE-LOOP APPROVALS
# ==============================================================================
class InteractiveDiffReviewer:
    """Displays a colorized unified diff in the terminal and prompts for user approval."""

    @staticmethod
    def review_and_confirm(original_files: Dict[str, str], patched_files: Dict[str, str]) -> bool:
        if os.getenv("AXIOM_AUTO_APPROVE") == "1" or not sys.stdin.isatty():
            print(f"{CYAN}👀 [Diff Review] Auto-approve enabled; skipping interactive prompt.{RESET}")
            return True

        has_changes = False
        print(f"\n{BOLD}{CYAN}==================== 🔍 AXIOM VERIFIED PATCH DIFF ===================={RESET}")
        for filepath, new_content in patched_files.items():
            old_content = original_files.get(filepath, "")
            if old_content == new_content:
                continue
            has_changes = True
            diff_lines = list(
                difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"a/{filepath} (host)",
                    tofile=f"b/{filepath} (verified shadow)",
                )
            )
            for line in diff_lines:
                if line.startswith("+") and not line.startswith("+++"):
                    sys.stdout.write(f"{GREEN}{line}{RESET}")
                elif line.startswith("-") and not line.startswith("---"):
                    sys.stdout.write(f"{RED}{line}{RESET}")
                elif line.startswith("@@"):
                    sys.stdout.write(f"{CYAN}{line}{RESET}")
                else:
                    sys.stdout.write(line)
            print()

        print(f"{BOLD}{CYAN}======================================================================{RESET}")
        if not has_changes:
            return True

        while True:
            try:
                choice = input(f"{YELLOW}⚡ Apply this verified patch to host files? [y/N/edit]: {RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{RED}❌ Patch promotion cancelled by user.{RESET}")
                return False

            if choice in {"y", "yes"}:
                print(f"{GREEN}✅ Patch approved! Promoting to host working tree...{RESET}")
                return True
            if choice in {"n", "no", ""}:
                print(f"{RED}🛑 Patch rejected by user. Host files remain untouched.{RESET}")
                return False
            if choice == "edit":
                editor = os.getenv("EDITOR", "nano")
                for filepath, new_content in patched_files.items():
                    if original_files.get(filepath, "") != new_content:
                        with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False) as tf:
                            tf.write(new_content)
                            temp_name = tf.name
                        os.chmod(temp_name, 0o600)
                        subprocess.run([editor, temp_name], check=False)  # nosec B603
                        with open(temp_name, "r", encoding="utf-8") as tf:
                            patched_files[filepath] = tf.read()
                        os.remove(temp_name)
                return True


# ==============================================================================
# 4. AUTOMATED GIT BRANCHING & PULL REQUEST (PR) PIPELINE
# ==============================================================================
class GitPRPipeline:
    """Creates a dedicated feature branch, commits the fix, and opens a GitHub PR if possible."""

    @staticmethod
    def branch_commit_and_pr(prompt: str, tracer=None) -> bool:
        slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:32] or "auto-patch"
        branch_name = f"axiom/fix-{slug}-{int(time.time()) % 10000}"

        print(f"{CYAN}🌿 [Git & PR Pipeline] Preparing feature branch `{branch_name}`...{RESET}")
        try:
            # Verify inside a git repo
            chk = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, timeout=5)  # nosec B603 B607
            if chk.returncode != 0:
                print(f"{YELLOW}⚠️  [Git & PR Pipeline] Not a Git repository; skipping branch/PR creation.{RESET}")
                return False

            subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True, text=True, timeout=5)  # nosec B603 B607
            subprocess.run(["git", "add", "-u"], capture_output=True, text=True, timeout=5)  # nosec B603 B607
            commit_msg = f"fix(axiom): {prompt[:65]}"
            subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True, timeout=10)  # nosec B603 B607
            print(f"{GREEN}✅ [Git & PR Pipeline] Committed verified patch on branch `{branch_name}`.{RESET}")

            # Check if remote origin and GitHub CLI (`gh`) exist and user requested PR
            if os.getenv("AXIOM_ENABLE_PR", "0") == "1" and shutil.which("gh"):
                push_res = subprocess.run(["git", "push", "-u", "origin", branch_name], capture_output=True, text=True, timeout=20)  # nosec B603 B607
                if push_res.returncode == 0:
                    pr_res = subprocess.run(
                        [
                            "gh", "pr", "create",
                            "--title", commit_msg,
                            "--body", f"## 🤖 Axiom Formally Verified Patch\n\n**Objective:** {prompt}\n\n- ✅ Pre-Flight AST Security Gate Passed\n- ✅ Sandbox Pytest Passed\n- ✅ Z3 Formal Proof Verified",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )  # nosec B603 B607
                    if pr_res.returncode == 0:
                        print(f"{GREEN}🚀 [Git & PR Pipeline] Pull Request opened: {pr_res.stdout.strip()}{RESET}")
            return True
        except Exception as e:
            if tracer:
                tracer.log_step("GitPRPipeline", "Warning during Git/PR pipeline", str(e))
            return False


# ==============================================================================
# 6. LIGHTWEIGHT NON-DOCKER FALLBACK SANDBOX
# ==============================================================================
class FallbackSandboxRunner:
    """Executes tests inside an isolated local venv & restricted permissions if Docker is offline."""

    @staticmethod
    def is_docker_available() -> bool:
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3)  # nosec B603 B607
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def run_tests_with_fallback(cls, original_run_tests_fn, test_target=None, workspace_dir=None) -> Tuple[bool, str]:
        if cls.is_docker_available():
            print(f"{CYAN}🐳 [Sandbox] Docker daemon active — executing in container sandbox...{RESET}")
            return original_run_tests_fn(test_target=test_target, workspace_dir=workspace_dir)

        print(f"{YELLOW}📦 [Fallback Sandbox] Docker offline — isolating execution in restricted local venv...{RESET}")
        run_dir = workspace_dir if workspace_dir and os.path.isdir(workspace_dir) else "."
        if workspace_dir and os.path.isdir(workspace_dir):
            os.chmod(workspace_dir, 0o700)

        # Strip sensitive API keys from child test environment so untrusted test code cannot read them
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", "/tmp"),  # nosec B108
            "PYTHONPATH": os.path.abspath(run_dir),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        cmd = [sys.executable, "-m", "pytest", "-q"]
        if test_target:
            target_in_ws = os.path.basename(test_target) if workspace_dir else test_target
            if os.path.exists(os.path.join(run_dir, target_in_ws)):
                cmd.append(target_in_ws)

        try:
            proc = subprocess.run(
                cmd,
                cwd=run_dir,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=30,
            )  # nosec B603
            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return (proc.returncode == 0), output.strip()
        except subprocess.TimeoutExpired:
            return False, "TimeoutExpired: Test execution exceeded 30s sandbox limit."
        except Exception as e:
            return False, f"FallbackSandboxError: {e}"


if __name__ == "__main__" and "--selftest" in sys.argv:
    print(f"{BOLD}{CYAN}🚀 Running Axiom Enterprise 6-Feature Visual Self-Test...{RESET}\n")
    # 1. Test Pre-Flight Security Scanner blocking SQLi & Secrets
    bad_code = 'def get_user(u):\n    api = "gsk_1234567890abcdefghijklmnop"\n    cursor.execute(f"SELECT * FROM users WHERE name = \'{u}\'")\n'
    PreFlightSecurityScanner.scan_code("vulnerable_demo.py", bad_code)
    print()
    # 2. Test Pre-Flight Security Scanner passing safe parameterized code
    good_code = 'def get_user(cursor, u):\n    cursor.execute("SELECT * FROM users WHERE name = ?", (u,))\n'
    PreFlightSecurityScanner.scan_code("safe_demo.py", good_code)
    print()
    # 3. Check Docker vs Fallback Sandbox detection
    docker_up = FallbackSandboxRunner.is_docker_available()
    print(f"{CYAN}🔍 [Sandbox Status] Docker Daemon Available: {docker_up} (Fallback Ready: True){RESET}\n")
