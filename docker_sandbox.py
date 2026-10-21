import os
import subprocess
import logging

log = logging.getLogger("axiom.sandbox")

DOCKERFILE_CONTENT = """FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
RUN pip install --no-cache-dir pytest z3-solver
WORKDIR /workspace
"""

def ensure_sandbox_image():
    """Checks if axiom-sandbox:latest exists; auto-builds it on first run if missing."""
    check = subprocess.run(
        ["docker", "image", "inspect", "axiom-sandbox:latest"],
        capture_output=True
    )
    if check.returncode != 0:
        print("🐳 [Sandbox] First-time setup: Building 'axiom-sandbox:latest' Docker image (~20s)...")
        if not os.path.exists("Dockerfile.axiom"):
            with open("Dockerfile.axiom", "w") as f:
                f.write(DOCKERFILE_CONTENT)
        subprocess.run(
            ["docker", "build", "-t", "axiom-sandbox:latest", "-f", "Dockerfile.axiom", "."],
            check=True
        )
        print("✅ [Sandbox] Fast verification image built successfully!")

def run_tests(test_target: str, workspace_dir: str = None) -> tuple[bool, str]:
    """
    Executes pytest inside an ephemeral Docker container mounted to an isolated
    shadow workspace with zero bytecode or pytest cache artifacts written to disk.
    """
    ensure_sandbox_image()
    mount_path = os.path.abspath(workspace_dir) if workspace_dir else os.getcwd()

    cmd = [
        "docker", "run", "--rm",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-v", f"{mount_path}:/workspace",
        "-w", "/workspace",
        "axiom-sandbox:latest",
        "bash", "-c",
        f"python -B -m pytest -p no:cacheprovider {test_target} -v && chmod -R 777 /workspace > /dev/null 2>&1 || true"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        output = result.stdout + "\n" + result.stderr
        passed = (" 0 failed" in output or (" passed" in output and " failed" not in output and "ERROR" not in output))
        return passed, output

    except subprocess.TimeoutExpired:
        return False, "❌ Sandbox Error: Execution timed out after 15s."
    except Exception as e:
        return False, f"❌ Sandbox Critical Error: {str(e)}"
