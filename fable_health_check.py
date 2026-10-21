import time
import subprocess
import os

# Create novel test cases that are NOT in SWE-bench
TEST_CASES = {
    "math_bug.py": {
        "code": "def calculate_tax(subtotal, tax_rate):\n    return subtotal + (subtotal / tax_rate)\n\nprint(calculate_tax(100, 0))",
        "instruction": "Fix the ZeroDivisionError and ensure the tax calculation multiplies the rate instead of dividing by it."
    },
    "string_bug.py": {
        "code": "def reverse_words(sentence):\n    words = sentence.split(' ')\n    return words.reverse()\n\nprint(reverse_words('hello world'))",
        "instruction": "Fix the bug where the function returns None because .reverse() is an in-place operation. Return the actual reversed string."
    }
}

def setup_test_environment():
    os.makedirs("audit_workspace", exist_ok=True)
    for filename, data in TEST_CASES.items():
        with open(f"audit_workspace/{filename}", "w") as f:
            f.write(data["code"])

def run_diagnostic():
    print("=== 🩺 FABLE AUTONOMOUS HEALTH CHECK ===")
    setup_test_environment()
    
    passed = 0
    for filename, data in TEST_CASES.items():
        print(f"\n[Testing] Scenario: {filename}")
        start_time = time.time()
        
        # Trigger Fable's engine in the background
        cmd = f"python -c \"from engine_test import SelfHealingEngine; e = SelfHealingEngine(); e.run('Workspace: audit_workspace/{filename}. {data['instruction']}')\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        execution_time = time.time() - start_time
        
        # Check if Fable fixed the file successfully
        verify_cmd = f"python audit_workspace/{filename}"
        verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
        
        if verify_result.returncode == 0 and "None" not in verify_result.stdout:
            print(f"✅ PASSED in {execution_time:.2f} seconds")
            passed += 1
        else:
            print(f"❌ FAILED in {execution_time:.2f} seconds")
            print(f"Reason: {verify_result.stderr.strip() or 'Invalid output'}")

    print(f"\n=== 📊 AUDIT COMPLETE ===")
    print(f"Resolution Rate: {(passed/len(TEST_CASES))*100}%")
    print(f"Average Execution Speed: {execution_time:.2f}s per task")
    print("=========================")

if __name__ == "__main__":
    run_diagnostic()
