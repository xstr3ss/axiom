import json
import os
from datasets import load_dataset

print("==================================================")
print("🏭 FABLE DATA FACTORY: COMPILING MASTER CURRICULUM")
print("==================================================")

# ---------------------------------------------------------
# 1. SFT Trajectories (Tool Use & Patching)
# ---------------------------------------------------------
print("📡 Downloading SWE-bench (Agentic Trajectories)...")
try:
    swe = load_dataset("princeton-nlp/SWE-bench_Lite", split="train[:300]")
    with open("sft_trajectories.jsonl", "w", encoding="utf-8") as f:
        for row in swe:
            trajectory = {
                "messages": [
                    {"role": "system", "content": "You are Fable. Use tools to investigate, then output SEARCH/REPLACE blocks."},
                    {"role": "user", "content": f"Fix this issue:\n{row['problem_statement']}"},
                    {"role": "assistant", "content": "Action: ls -la"},
                    {"role": "tool", "content": "Observation: target_module.py  test_target.py"},
                    {"role": "assistant", "content": f"Action: cat target_module.py"},
                    {"role": "tool", "content": "Observation: [File contents hidden for brevity]"},
                    {"role": "assistant", "content": f"<<<<<<< SEARCH\n# Target code\n=======\n{row['patch'][:500]}\n>>>>>>> REPLACE"}
                ]
            }
            f.write(json.dumps(trajectory) + "\n")
    print("✅ sft_trajectories.jsonl compiled (300 records).")
except Exception as e:
    print(f"⚠️ Failed to pull SWE-bench: {e}")

# ---------------------------------------------------------
# 2. SFT Recovery (Traceback Debugging)
# ---------------------------------------------------------
print("📡 Compiling Traceback Recovery Data...")
try:
    # Synthesizing structured traceback recovery pairs
    with open("sft_recovery.jsonl", "w", encoding="utf-8") as f:
        for i in range(200): # Generating synthetic structural examples
            recovery = {
                "messages": [
                    {"role": "system", "content": "You are Fable. Fix the code based on the pytest traceback."},
                    {"role": "user", "content": "AssertionError: 99.6 == 80.0\nE + where 99.6 = calculate_discount(100.0, 0.2)"},
                    {"role": "assistant", "content": "<<<<<<< SEARCH\n    return price - (discount * 2)\n=======\n    return price * (1 - discount)\n>>>>>>> REPLACE"}
                ]
            }
            f.write(json.dumps(recovery) + "\n")
    print("✅ sft_recovery.jsonl compiled (200 records).")
except Exception as e:
    print(f"⚠️ Failed to generate recovery data: {e}")

# ---------------------------------------------------------
# 3. DPO (Format Enforcing)
# ---------------------------------------------------------
print("📡 Compiling DPO Preference Pairs (Strict Formatting)...")
try:
    dpo_data = load_dataset("m-a-p/CodeFeedback-Filtered-Instruction", split="train[:300]")
    with open("dpo_preferences.jsonl", "w", encoding="utf-8") as f:
        for row in dpo_data:
            dpo_pair = {
                "prompt": f"Feature Request: {row['query'][:200]}...",
                "chosen": f"<<<<<<< SEARCH\n# Old logic\n=======\n{row['answer'][:300]}\n>>>>>>> REPLACE",
                "rejected": f"Here is the code:\n```python\n{row['answer'][:300]}\n```" # Penalize standard markdown
            }
            f.write(json.dumps(dpo_pair) + "\n")
    print("✅ dpo_preferences.jsonl compiled (300 records).")
except Exception as e:
    print(f"⚠️ Failed to pull CodeFeedback: {e}")

print("==================================================")
print("🏆 MASTER CURRICULUM READY. 0 TOKENS CONSUMED.")
print("==================================================")
