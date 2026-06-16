import subprocess, sys, glob, os
from pathlib import Path

os.chdir(r"C:\Fiverr\Fiverr")

EXCLUDE = {"test_queue_processor.py","test_collection_orchestrator.py",
           "test_cycle062_smoke_aliases.py","test_post_cycle_review_coverage.py"}
files = sorted(p for p in Path("tests/unit").glob("test_*.py")
               if p.name not in EXCLUDE)

r = subprocess.run(
    [sys.executable, "-m", "pytest", *[str(f) for f in files],
     "--timeout=8", "--tb=no", "-q"],
    capture_output=False,
    text=True,
    cwd=r"C:\Fiverr\Fiverr"
)
sys.exit(r.returncode)
