import os
import ast
import subprocess

HIGH_RISK_PATHS = ("auth", "security", "billing", "payment", "migration", ".env", ".github/workflows")
DANGEROUS_CALLS = {"eval", "exec", "system", "popen", "rmtree"}

def analyze_workspace_risk(repo_dir: str) -> dict:
    """Scans uncommitted git changes in repo_dir and returns a Risk Assessment."""
    score = 0
    reasons = []
    modified_files = []

    status_out = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=repo_dir, text=True
    )

    for line in status_out.splitlines():
        if not line.strip():
            continue
        status_code = line[:2].strip()
        rel_path = line[3:].strip().strip('"')
        modified_files.append(rel_path)

        # 1. Check for sensitive paths
        for sensitive in HIGH_RISK_PATHS:
            if sensitive in rel_path.lower():
                score += 45
                reasons.append(f"Touches protected path `{rel_path}` (matched `{sensitive}`)")

        # 2. Check if a test file was deleted
        if status_code == "D" and "test" in rel_path.lower():
            score += 60
            reasons.append(f"Deletes test suite file `{rel_path}`")

        # 3. Perform AST static analysis on modified Python files
        full_path = os.path.join(repo_dir, rel_path)
        if os.path.isfile(full_path) and rel_path.endswith(".py"):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                tree = ast.parse(source, filename=rel_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func_name = ""
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        if func_name in DANGEROUS_CALLS:
                            score += 35
                            reasons.append(f"AST detected high-risk call `{func_name}()` in `{rel_path}` (line {node.lineno})")
            except SyntaxError:
                score += 80
                reasons.append(f"SyntaxError introduced in `{rel_path}`")

    final_score = min(score, 100)
    passed = final_score < 70

    report = [
        f"### 🛡️ Fable Enterprise Risk & Compliance Report",
        f"- **Risk Score:** `{final_score}/100` ({'✅ PASSED' if passed else '🛑 COMPLIANCE HOLD'})",
        f"- **Files Evaluated:** {', '.join(f'`{f}`' for f in modified_files) if modified_files else 'None'}",
    ]
    if reasons:
        report.append("- **Risk Triggers:**")
        for r in reasons:
            report.append(f"  - ⚠️ {r}")
    else:
        report.append("- **Risk Triggers:** None detected. Clean AST diff.")

    if not passed:
        report.append("\n🔒 **Action Required:** Score reached threshold (70+). Autonomous push blocked pending senior engineer sign-off (`@fable --approve`).")

    return {
        "score": final_score,
        "passed": passed,
        "reasons": reasons,
        "report_markdown": "\n".join(report)
    }

if __name__ == "__main__":
    res = analyze_workspace_risk(".")
    print(res["report_markdown"])
