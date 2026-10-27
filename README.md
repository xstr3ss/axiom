# 🧬 Axiom: Autonomous Self-Healing CI/CD Engine

Axiom is an autonomous self-healing engine that ingests GitHub issues, slices the AST to locate vulnerabilities, formally verifies patches using the Z3 theorem prover, and pushes parameterized fixes back to your repository.

## 🚀 1. Global Local Installation

Install Axiom globally on your machine so it stays synced with the engine files:

```bash
git clone [https://github.com/xstr3ss/axiom.git](https://github.com/xstr3ss/axiom.git)
cd axiom
pip install -e . --break-system-packages
```

### CLI Usage
Run Axiom against any repository or GitHub issue URL:

```bash
python3 axiom_cli.py --pro-key "$AXIOM_PRO_KEY" --issue "[https://github.com/your-username/your-repo/issues/1](https://github.com/your-username/your-repo/issues/1)"
```

---

## 🤖 2. Autonomous GitHub Actions Setup (For Any Repo)

To let Axiom automatically heal issues opened in your own repository:

1. Go to your repository **Settings -> Secrets and variables -> Actions**.
2. Add your **`GROQ_API_KEY`** and **`AXIOM_PRO_KEY`** secrets.
3. Create `.github/workflows/axiom-healer.yml` with the following configuration:

```yaml
name: Axiom Autonomous Self-Healing CI

on:
  issues:
    types: [opened, edited]
  workflow_dispatch:
    inputs:
      issue_url:
        description: "Target GitHub Issue URL"
        required: true
        type: string

jobs:
  autonomous-heal:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Start Qdrant Vector Memory
        run: docker run -d -p 6333:6333 qdrant/qdrant

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Execute Axiom 10-Loop Healing Engine
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          AXIOM_PRO_KEY: ${{ secrets.AXIOM_PRO_KEY }}
        run: |
          ISSUE_TARGET="${{ github.event.inputs.issue_url || github.event.issue.html_url }}"
          python3 axiom_cli.py --pro-key "$AXIOM_PRO_KEY" --issue "$ISSUE_TARGET"

      - name: Commit & Push Formally Verified Patch
        run: |
          git config user.name "axiom-bot"
          git config user.email "bot@axiom.ai"
          git add -A
          git diff --staged --quiet || git commit -m "fix(axiom): Z3-verified autonomous patch for issue"
          git pull --rebase origin main
          git push
```

---

## 🧠 Core Architecture
- **Multi-Model Routing:** Groq Cloud (120B / 70B) + Local Ollama (3B).
- **Vector Memory:** Qdrant DB for indexing AST slices, anti-patterns, and verified resolutions.
- **Formal Verification:** Z3 Solver verification before committing patches.
