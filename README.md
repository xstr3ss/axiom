<div align="center">

# ⚡ AXIOM
### The Autonomous Coding Engine That Doesn't Guess. It Proves.
**Shadow Docker Sandboxing • Recursive AST Slicing • Qdrant Anti-Pattern Memory • Z3 Formal Verification**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)]([https://opensource.org/licenses/Apache-2.0](https://opensource.org/licenses/Apache-2.0))
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Verification: Z3 Solver](https://img.shields.io/badge/Formal_Proof-Z3_Theorem_Prover-success.svg)](https://github.com/Z3Prover/z3)
[![Architecture: Zero Pollution](https://img.shields.io/badge/Host_Safety-100%25_Shadow_Isolated-blueviolet.svg)]()

</div>

---

## 🚨 Why AXIOM?

99% of AI coding agents today operate on **blind optimism**:
1. They dump your entire repository into an LLM context window (burning thousands of tokens).
2. They overwrite your local files directly on your host machine—breaking working code and polluting your Git tree.
3. Even when they run unit tests, **unit tests only check the specific numbers a human remembered to write down.**

**Axiom is architected differently.** Built as a **Shielded, Zero-Pollution Multi-Agent Pipeline**, Axiom never touches your working directory until a patch survives both **empirical unit testing (`pytest`)** inside a 0.3-second isolated Docker shadow workspace AND **algebraic formal verification (`Z3 Theorem Solver`)** across infinite input boundaries.

---

## ⚡ See Axiom Catch What Unit Tests Miss

Suppose you have a withdrawal function and a passing unit test (`assert calc.apply_withdrawal(100, 20) == 80`). Standard CI/CD turns green and ships it. **Watch what happens when Axiom audits it:**

```text
🤖 [Sandbox] ➔ Baseline Pytest: 1 passed in 0.01s
🤖 [Shadow Workspace] ➔ 🛡️ Isolated staging created at /tmp/axiom_shadow_jzmv2cpd (Host files locked)
🤖 [Semantic Gate] ➔ 🛡️ AST semantic integrity verified for src/math_engine/calculator.py.
🤖 [Z3 Verifier] ➔ Synthesizing algebraic proof for src/math_engine/calculator.py...
🤖 [Z3 Verifier] ➔ ❌ Counter-example found by Z3 Theorem Solver:
Z3_SAT: FAILED -> [balance = 0, amount = 1] (Illegal negative state proven possible!)

🤖 [Engine] ➔ Pipeline Iteration 2: Auto-synthesizing boundary guards...
🤖 [Stitcher] ➔ ✅ Staged AST-verified patch in Shadow Workspace: src/math_engine/calculator.py
🤖 [Z3 Verifier] ➔ 📐 Mathematical boundaries of calculator.py proven safe (Z3_UNSAT).
🤖 [Shadow Workspace] ➔ ✅ Atomic Promotion Complete. Real environment updated safely.
```

---

## 🚀 30-Second Quickstart (Bring Your Own Key)

### 1. Install Axiom CLI in Your Terminal
```bash
git clone [https://github.com/xstr3ss/](https://github.com/xstr3ss/)axiom.git
cd axiom
pip install --no-build-isolation --no-deps -e .
```

### 2. Configure Your API Key (BYOK)
On your first run (or anytime via `--set-key`), Axiom stores your API key locally in `~/.axiom/config.env`:
```bash
axiom --set-key
```

### 3. Unleash Axiom on Any Repository
```bash
# Fix a failing test suite across nested directories
axiom "tests/test_math.py is failing. Trace the imports in src/ and fix the validation logic."

# Proactively refactor & formally verify existing code
axiom "Verify against tests/test_math.py. Refactor apply_withdrawal in src/math_engine/calculator.py to enforce strict non-negative bounds."
```

---

## 🛡️ Key Engineering Guarantees

* **Zero Host Pollution:** If Axiom hits its token cap or fails to prove a patch, your host workspace is never modified. Failed trajectories are logged to Qdrant's Anti-Pattern database so Axiom never repeats the same mistake twice.
* **Hard Token Circuit Breaker:** Set `--max-tokens 4000` (default) to guarantee an autonomous loop never drains your API credits.
* **0.3-Second Sandbox Latency:** Pre-baked container execution with automatic first-run image building and zero `.pyc` or `.pytest_cache` host permission issues.

---

## 🗺️ Roadmap & Axiom Pro

* [x] Shielded Shadow Workspace & Atomic Host Promotion
* [x] Recursive Transitive AST Dependency Slicer
* [x] Qdrant Vector Memory (Success & Anti-Pattern Distillation)
* [x] Z3 Formal Theorem Proving Gate
* [ ] **Polyglot Tree-Sitter Slicing** (TypeScript, Rust, Go, Solidity)
* [ ] **Monte Carlo Tree Search (MCTS)** parallel container swarms
* [ ] **Axiom Pro Cloud (`axiom login`)**: Zero-setup managed 120B inference + Global Hive-Mind Qdrant memory

---

## 📄 License
Licensed under the **Apache 2.0 License**. Created by **Shyam Shukla**.
