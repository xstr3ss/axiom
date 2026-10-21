import os
import tempfile
import subprocess
from dotenv import load_dotenv
from engine import SelfHealingEngine
from risk_gate import analyze_workspace_risk

load_dotenv()

print("\n========================================================")
print("🚀 STARTING FABLE END-TO-END SELF-HEALING SIMULATION")
print("========================================================\n")

# 1. Create a temporary testing sandbox directory
sim_dir = tempfile.mkdtemp(prefix="fable_sim_workspace_")
base_dir = os.getcwd()

try:
    os.chdir(sim_dir)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Fable Test Bot"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "bot@fable.local"], check=True, capture_output=True)

    # 2. Plant a broken math module with a failing unit test
    print("🌱 Planting broken module and failing test case...")
    with open("target_module.py", "w") as f:
        f.write("# Broken implementation\ndef calculate_discount(price: float, discount: float) -> float:\n    # Bug: returns negative or wrong math\n    return price - (discount * 2)\n")

    with open("test_target.py", "w") as f:
        f.write("from target_module import calculate_discount\n\ndef test_discount():\n    assert calculate_discount(100.0, 0.2) == 80.0\n")

    subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial broken commit"], check=True, capture_output=True)

    # Verify pytest fails initially
    res = subprocess.run(["pytest", "test_target.py"], capture_output=True, text=True)
    print(f"❌ Initial Pytest Status (Expected Fail): Exit code {res.returncode}")

    # 3. Trigger Fable Self-Healing Engine using local Tier 1 Model & Z3 Verification context
    print("\n🤖 [Fable Engine] Activating self-healing loop on local Tier 1 brain...")
    prompt = (
        "The pytest suite for `target_module.py` is failing because calculate_discount computes price - (discount * 2) "
        "instead of applying a percentage discount (e.g. price * (1 - discount)). "
        "Fix `target_module.py` so that calculate_discount(100.0, 0.2) returns 80.0 correctly."
    )

    engine = SelfHealingEngine()
    engine.run(prompt)

    # 4. Run AST Risk Gate on the generated fix
    print("\n🛡️ Running Enterprise AST Risk & Compliance Gate...")
    risk = analyze_workspace_risk(sim_dir)
    print(risk["report_markdown"])

    # 5. Re-run Pytest to verify fix
    print("\n🧪 Verifying final test suite execution...")
    final_res = subprocess.run(["pytest", "test_target.py"], capture_output=True, text=True)
    print(final_res.stdout)
    if final_res.returncode == 0:
        print("🎉 SUCCESS: Fable successfully self-healed the bug end-to-end!")
    else:
        print("⚠️ Simulation completed, check file diffs above.")

finally:
    os.chdir(base_dir)
    # Uncomment line below if you want to clean up the temp sim folder automatically
    # subprocess.run(["rm", "-rf", sim_dir])
    print(f"\n📁 Simulation workspace preserved at: {sim_dir}")
