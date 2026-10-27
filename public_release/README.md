<div align="center">

# ⚡ AXIOM
### The Autonomous Coding Engine That Does Not Guess. It Proves.
**Dual Z3 Formal Verification • 0.3s Shadow Sandboxing • Recursive AST Dependency Slicing • Qdrant Anti-Pattern Memory**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Verification: Z3 Solver](https://img.shields.io/badge/Formal_Proof-Z3_Theorem_Prover-success.svg)](https://github.com/Z3Prover/z3)
[![Host Safety: 100% Shadow Isolated](https://img.shields.io/badge/Host_Safety-100%25_Shadow_Isolated-blueviolet.svg)]()

[🚀 Quickstart](#-quickstart-byok) • [🧠 The 6 Problems Axiom Solves](#-the-6-problems-other-ai-agents-fail-at) • [⚖️ Free vs. Pro](#-tier-comparison) • [💎 Get Axiom Pro](https://polar.sh/axiom)

</div>

---

## 🚨 The Fundamental Flaw in AI Coding Agents

Most AI coding agents operate on **blind empirical guessing**:
1. They rewrite code and run unit tests. If tests pass, they ship it. But unit tests only evaluate specific arbitrary numbers written by humans—missing edge cases and arithmetic vulnerabilities.
2. They modify your working files directly, often corrupting code trees during failed iterations.
3. When stuck in hallucination loops, their context window balloons, draining API credits rapidly.

**Axiom is built on formal verification and shadow isolation.** Patches are never promoted to your hard drive until they survive isolated sandbox testing AND the **Z3 Theorem Prover** mathematically proves all boundary constraints hold.

---

## 🧠 The 6 Problems Other AI Agents Fail At

| The AI Failure Mode | What Other Agents Do | How Axiom Solves It |
| :--- | :--- | :--- |
| **1. Passing-Test Vulnerabilities** | Green Pytest = Ship it | **Z3 Algebraic Theorem Prover** synthesizes invariants to block illegal states |
| **2. Host Workspace Pollution** | Writes directly to local project disk | **0.3s Ephemeral Docker Shadow Workspace** keeps host files locked |
| **3. Infinite Runaway Token Drain** | Context window balloons during failure loops | **Pre-Flight Token Circuit Breaker** terminates before exceeding caps |
| **4. Context Bloat & Missing Modules** | Dumps whole repo or misses dotted imports | **Transitive AST Slicer** parses Abstract Syntax Trees for linked files |
| **5. Repetitive Hallucination Loops** | Repeats identical failed patches | **Qdrant Vector Anti-Pattern Memory** explicitly injects past failures |
| **6. Destructive Regressions** | Fixes 1 test while breaking 3 others | **High-Score Checkpointing & Auto-Rollback** restores highest-passing snapshot |

---

## ⚡ Real Terminal Proof: Z3 Catching What Unit Tests Miss

```text
🤖 [Sandbox] ➔ Baseline Pytest: 1 passed in 0.01s
🤖 [Shadow Workspace] ➔ 🛡️ Isolated staging created at /tmp/axiom_shadow_w2g (Host files locked)
🤖 [Semantic Gate] ➔ 🛡️ Semantic integrity verified for src/math_engine/calculator.py.
🤖 [Z3 Verifier] ➔ Synthesizing algebraic proof for src/math_engine/calculator.py...
🤖 [Z3 Verifier] ➔ ❌ Counter-example found by Z3 Theorem Solver:
Z3_SAT: FAILED -> [balance = 0, amount = 1] (Negative balance vulnerability detected!)

🤖 [Engine] ➔ Pipeline Iteration 2: Synthesizing strict boundary guards...
🤖 [Z3 Verifier] ➔ 📐 Mathematical boundaries of calculator.py proven safe (Z3_UNSAT: PROVED).
🤖 [Sandbox] ➔ ✅ Tests & Formal Audit Passed! Promoting verified files to Host...
```

---

## 🚀 Quickstart (BYOK)

Both Free and Pro tiers use **BYOK (Bring Your Own Key)**—enter your Groq or OpenAI key once, and all execution runs locally on your machine with zero server fees.

### 1. Installation
```bash
git clone https://github.com/xstr3ss/axiom.git
cd axiom
pip install --no-build-isolation --no-deps -e .
```

### 2. Configure Your BYOK API Key
```bash
axiom --set-key
```

### 3. Run Axiom
```bash
# Launch interactive chat mode
axiom --chat

# Execute autonomous verification loop on any objective
axiom "Verify against tests/test_math.py. Refactor apply_withdrawal in src/math_engine/calculator.py to use type hints and protect against negative balances."
```

---

## ⚖️ Tier Comparison

| Feature | Axiom Community (Free) | Axiom Pro ($19/mo) |
| :--- | :--- | :--- |
| **Pricing Model** | **BYOK** (Bring Your Own Key) | **BYOK** (Bring Your Own Key) |
| **API Provider** | Groq / OpenAI-compatible | Groq / OpenAI-compatible |
| **Formal Verification** | Full Z3 Algebraic Prover | Full Z3 Algebraic Prover |
| **Sandbox Isolation** | 0.3s Docker Shadow Workspace | 0.3s Docker Shadow Workspace |
| **Self-Healing Depth** | **3 Iterations** (Ideal for single-file & isolated bugs) | **10 Iterations** (Deep search for cascading multi-module regressions) |
| **Local Anti-Pattern Memory** | Session-only Vector Store | Persistent Cross-Session Hive Memory |
| **Host Protection Guarantee** | 100% Host File Lock on Failure | 100% Host File Lock on Failure |

### Upgrade to Axiom Pro
To unlock 10 deep self-healing iterations for complex codebases:
1. Subscribe at **[polar.sh/axiom](https://polar.sh/axiom)**.
2. Activate your key in your terminal:
```bash
axiom --pro-key AXIOM-PRO-YOUR-KEY-HERE
```

---

## 📄 License
Licensed under the **Apache 2.0 License**. Architected by **Shyam Shukla**.
