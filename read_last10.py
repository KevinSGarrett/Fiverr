
import subprocess, sys

# Run the last-10 a-m files
result = subprocess.run(
    [r"C:\Fiverr\Fiverr\.venv\Scripts\python.exe", "-m", "pytest",
     r"tests\unit\test_llm_tasks.py",
     r"tests\unit\test_lock_manager.py",
     r"tests\unit\test_lock_manager_integration.py",
     r"tests\unit\test_lock_manager_stable_coverage.py",
     r"tests\unit\test_market_writes.py",
     r"tests\unit\test_merge_gate.py",
     r"tests\unit\test_migration_08_r2_columns.py",
     r"tests\unit\test_model_gate.py",
     r"tests\unit\test_models.py",
     r"tests\unit\test_monitors.py",
     "--timeout=8", "--tb=short", "-q"],
    capture_output=True, text=True, cwd=r"C:\Fiverr\Fiverr"
)
print(result.stdout[-3000:] if result.stdout else "(no stdout)")
if result.stderr:
    print("STDERR:", result.stderr[-500:])
print("Exit:", result.returncode)
