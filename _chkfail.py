import subprocess

for run_id in ["26005588794", "26005588804", "26005588800"]:
    r = subprocess.run(["gh", "run", "view", run_id, "--log-failed"],
                       capture_output=True, text=True, cwd="C:/Fiverr/Fiverr")
    out = r.stdout + r.stderr
    lines = out.split('\n')
    print(f"\n=== RUN {run_id} ===")
    print('\n'.join(lines[:60]))
