import os
import ast
import sys
import json
import urllib.request

SKIP_FILES = {"axiom_cli.py", "engine.py", "audit_line_by_line.py", "audit_repo.py"}
SKIP_DIRS = {"venv", ".git", "__pycache__", "axiom_traces", "axiom_cli.build", "axiom_cli.dist", "axiom_cli.onefile-build"}

# 1. Auto-detect installed Foundation-Sec model tag
try:
    with urllib.request.urlopen("http://localhost:11434/api/tags") as resp:  # nosec B310
        models = json.loads(resp.read().decode("utf-8")).get("models", [])
        sec_models = [m["name"] for m in models if "foundation-sec" in m["name"].lower()]
        if not sec_models:
            print("❌ Error: Could not find Foundation-Sec in 'ollama list'.")
            sys.exit(1)
        model_name = sec_models[0]
except Exception as e:
    print(f"❌ Failed to connect to Ollama daemon: {e}")
    sys.exit(1)

# 2. Discover all remaining Python files in the repository
target_files = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith((".build", ".dist", ".onefile-build"))]
    for file in sorted(files):
        if file.endswith(".py") and file not in SKIP_FILES:
            rel_path = os.path.relpath(os.path.join(root, file), ".")
            target_files.append(rel_path)

print(f"🔎 Found {len(target_files)} remaining Python files to audit: {target_files}\n")

for target_file in target_files:
    with open(target_file, "r", encoding="utf-8") as f:
        source_text = f.read()
        lines = source_text.splitlines(keepends=True)

    if not lines:
        continue

    try:
        tree = ast.parse(source_text, filename=target_file)
    except SyntaxError as e:
        print(f"❌ SyntaxError in {target_file}: {e}")
        continue

    chunks = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for subnode in node.body:
                if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    chunks.append((f"Class {node.name}.{subnode.name}()", subnode.lineno, subnode.end_lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append((f"Function {node.name}()", node.lineno, node.end_lineno))

    if not chunks:
        chunks.append(("Module Global Scope", 1, len(lines)))

    print("##################################################")
    print(f"📂 FILE: {target_file} ({len(lines)} lines, {len(chunks)} AST blocks)")
    print("##################################################\n")

    for label, start_line, end_line in chunks:
        snippet = "".join([f"{i:04d}: {lines[i-1]}" for i in range(start_line, end_line + 1)])
        print("==================================================")
        print(f"🔍 [{target_file}] {label} (Lines {start_line:04d} to {end_line:04d})")
        print("==================================================")

        prompt = (
            f"TARGET PYTHON AST BLOCK ({target_file} - {label}, lines {start_line}-{end_line}):\n"
            f"```python\n{snippet}```\n\n"
            "STRICT ANTI-HALLUCINATION RULES (MANDATORY):\n"
            "1. In Python, `subprocess.run([...])` with a list defaults to `shell=False` and is SAFE from shell injection. Do NOT flag it unless `shell=True` is explicitly present.\n"
            "2. Do NOT claim `try/except`, `timeout`, or loop `break` statements are missing if they are visible in the lines above.\n"
            "3. Do NOT speculate about functions defined outside this block. Only audit the exact lines shown.\n"
            "4. Do NOT recommend `shlex.quote()` on variables that are never passed to a shell command.\n"
            "5. If the code in these lines has no concrete, exploitable vulnerability, output ONLY the word: PASS\n"
            "6. If and ONLY if a real, exploitable flaw exists in these exact lines, provide:\n"
            "   - Line Number\n"
            "   - CWE & Proof of Exploitability\n"
            "   - Exact Python Fix\n"
        )

        payload = json.dumps({
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_ctx": 8192,
                "temperature": 0.0,
                "top_p": 0.1,
                "repeat_penalty": 1.15
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req) as resp:  # nosec B310
            for raw_line in resp:
                data = json.loads(raw_line.decode("utf-8"))
                sys.stdout.write(data.get("response", ""))
                sys.stdout.flush()
        print("\n")
